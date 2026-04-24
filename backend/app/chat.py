from __future__ import annotations

import json
import re
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import quote

import httpx

from app.config import Settings
from app.models import ChatQueryResult, ChatRequest, ChatResponse, ProviderUsage


DISALLOWED_SQL_TOKENS = {
    "alter",
    "analyze",
    "attach",
    "create",
    "delete",
    "detach",
    "drop",
    "insert",
    "pragma",
    "reindex",
    "replace",
    "update",
    "vacuum",
}

DEFAULT_MAX_ROWS = 80
DEFAULT_PROGRESS_STEPS = 1_000_000


class ChatError(RuntimeError):
    pass


class UnsafeQueryError(ChatError):
    pass


def validate_readonly_sql(sql: str) -> str:
    query = sql.strip()
    if not query:
        raise UnsafeQueryError("SQL query is empty.")

    if query.count(";") > 1 or (";" in query and not query.endswith(";")):
        raise UnsafeQueryError("Only one SQL statement is allowed.")
    query = query[:-1].strip() if query.endswith(";") else query

    first_token_match = re.match(r"^\s*([a-zA-Z]+)\b", query)
    if not first_token_match:
        raise UnsafeQueryError("SQL query must start with SELECT or WITH.")
    if first_token_match.group(1).lower() not in {"select", "with"}:
        raise UnsafeQueryError("Only SELECT and WITH queries are allowed.")

    lowered = re.sub(r"'(?:''|[^'])*'", "''", query.lower())
    for token in DISALLOWED_SQL_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", lowered):
            raise UnsafeQueryError(f"SQL token is not allowed: {token}.")
    return query


class ReadOnlySqlRunner:
    def __init__(
        self,
        database_path: Path,
        max_rows: int = DEFAULT_MAX_ROWS,
        progress_steps: int = DEFAULT_PROGRESS_STEPS,
    ) -> None:
        self.database_path = database_path
        self.max_rows = max_rows
        self.progress_steps = progress_steps

    def run(self, sql: str) -> ChatQueryResult:
        query = validate_readonly_sql(sql)
        database_uri = f"file:{quote(str(self.database_path))}?mode=ro"
        wrapped_query = f"SELECT * FROM ({query}) AS chat_query LIMIT ?"
        with sqlite3.connect(database_uri, uri=True) as connection:
            connection.row_factory = sqlite3.Row
            connection.set_progress_handler(self._abort_query, self.progress_steps)
            try:
                rows = connection.execute(wrapped_query, (self.max_rows,)).fetchall()
            except sqlite3.Error as exc:
                raise ChatError(f"SQL query failed: {exc}") from exc
        payload = [dict(row) for row in rows]
        return ChatQueryResult(sql=query, rows=payload, row_count=len(payload))

    def _abort_query(self) -> int:
        return 1


def build_schema_context(runner: ReadOnlySqlRunner) -> str:
    context_queries = [
        """
        SELECT name, type, sql
        FROM sqlite_schema
        WHERE type IN ('table', 'view')
          AND name NOT LIKE 'sqlite_%'
        ORDER BY type, name
        """,
        """
        SELECT primary_role AS value, request_count
        FROM demand_by_role
        ORDER BY request_count DESC, primary_role
        LIMIT 20
        """,
        """
        SELECT technology AS value, category, request_count
        FROM demand_by_technology
        ORDER BY request_count DESC, technology
        LIMIT 30
        """,
        """
        SELECT location_city AS value, request_count
        FROM demand_by_city
        ORDER BY request_count DESC, location_city
        LIMIT 20
        """,
    ]
    sections = []
    for query in context_queries:
        result = runner.run(query)
        sections.append(json.dumps(result.rows, ensure_ascii=False))
    return "\n\n".join(
        [
            "SQLite schema rows:",
            sections[0],
            "Known roles:",
            sections[1],
            "Known technologies:",
            sections[2],
            "Known cities:",
            sections[3],
            (
                "Rules: answer in Swedish. Treat the database as a local snapshot. "
                "Prefer views for summaries. Use COUNT(DISTINCT request_id) when "
                "counting technology demand. Query only aggregated or compact rows."
            ),
        ]
    )


class AnalysisChatProvider(ABC):
    @abstractmethod
    def answer(self, request: ChatRequest, runner: ReadOnlySqlRunner) -> ChatResponse:
        raise NotImplementedError


class MockAnalysisChatProvider(AnalysisChatProvider):
    def answer(self, request: ChatRequest, runner: ReadOnlySqlRunner) -> ChatResponse:
        normalized = request.message.lower()
        if any(token in normalized for token in [".net", "dotnet", "net utveckl"]):
            year_match = re.search(r"\b(20\d{2})\b", normalized)
            year = int(year_match.group(1)) if year_match else 2025
            sql = f"""
            SELECT COUNT(DISTINCT r.request_id) AS request_count
            FROM requests r
            WHERE r.received_at >= '{year}-01-01'
              AND r.received_at < '{year + 1}-01-01'
              AND (
                LOWER(r.primary_role) LIKE '%.net%'
                OR LOWER(r.primary_role) LIKE '%net developer%'
                OR EXISTS (
                  SELECT 1
                  FROM request_technologies t
                  WHERE t.request_id = r.request_id
                    AND LOWER(COALESCE(t.normalized_value, t.raw_value)) IN ('.net', 'net')
                )
              )
            """
            result = runner.run(sql)
            count = result.rows[0]["request_count"] if result.rows else 0
            return ChatResponse(
                answer=(
                    f"Det inkom {count} förfrågningar som matchar .NET under {year} "
                    "i den lokala databassnapshoten."
                ),
                conversation_id=request.conversation_id,
                sql=[result.sql],
                rows=result.rows,
            )

        sql = """
        SELECT primary_role, request_count
        FROM demand_by_role
        ORDER BY request_count DESC, primary_role
        LIMIT 5
        """
        result = runner.run(sql)
        roles = ", ".join(
            f"{row['primary_role'] or 'okänd'} ({row['request_count']})"
            for row in result.rows
        )
        return ChatResponse(
            answer=(
                "Jag kan svara på frågor genom read-only SQL mot den lokala "
                f"databassnapshoten. Just nu är topprollerna: {roles}."
            ),
            conversation_id=request.conversation_id,
            sql=[result.sql],
            rows=result.rows,
        )


class OpenAIResponsesAnalysisProvider(AnalysisChatProvider):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        timeout_seconds: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.http_client = http_client or httpx.Client(timeout=timeout_seconds)

    def answer(self, request: ChatRequest, runner: ReadOnlySqlRunner) -> ChatResponse:
        schema_context = build_schema_context(runner)
        first_payload = {
            "model": self.model_name,
            "input": [
                {"role": "system", "content": self._system_prompt(schema_context)},
                {"role": "user", "content": request.message},
            ],
            "tools": [self._sql_tool_schema()],
            "tool_choice": "auto",
        }
        first_response = self._post_response(first_payload)
        sql_results = self._execute_tool_calls(first_response, runner)

        if sql_results:
            tool_outputs = [
                {
                    "type": "function_call_output",
                    "call_id": item["call_id"],
                    "output": json.dumps(item["result"].model_dump(), ensure_ascii=False),
                }
                for item in sql_results
            ]
            final_response = self._post_response(
                {
                    "model": self.model_name,
                    "previous_response_id": first_response.get("id"),
                    "input": tool_outputs,
                    "tools": [self._sql_tool_schema()],
                }
            )
        else:
            final_response = first_response

        usage = self._usage(final_response)
        results = [item["result"] for item in sql_results]
        return ChatResponse(
            answer=self._extract_output_text(final_response),
            conversation_id=request.conversation_id,
            sql=[result.sql for result in results],
            rows=results[-1].rows if results else [],
            usage=usage,
        )

    def _post_response(self, payload: dict) -> dict:
        response = self.http_client.post(
            f"{self.base_url}/responses",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def _execute_tool_calls(
        self, response: dict, runner: ReadOnlySqlRunner
    ) -> list[dict]:
        tool_results = []
        for item in response.get("output") or []:
            if item.get("type") != "function_call":
                continue
            if item.get("name") != "run_readonly_sql":
                continue
            arguments = json.loads(item.get("arguments") or "{}")
            sql = arguments.get("sql")
            if not isinstance(sql, str):
                raise ChatError("run_readonly_sql requires a SQL string.")
            tool_results.append(
                {
                    "call_id": item.get("call_id"),
                    "result": runner.run(sql),
                }
            )
        return tool_results

    def _extract_output_text(self, response: dict) -> str:
        output_text = response.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()
        for item in response.get("output") or []:
            if item.get("type") != "message":
                continue
            parts = item.get("content") or []
            texts = [
                part.get("text")
                for part in parts
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ]
            if texts:
                return "\n".join(texts).strip()
        raise ChatError("Model response did not contain an answer.")

    def _usage(self, response: dict) -> ProviderUsage | None:
        usage = response.get("usage")
        if not isinstance(usage, dict):
            return None
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        total_tokens = usage.get("total_tokens")
        return ProviderUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    def _system_prompt(self, schema_context: str) -> str:
        return (
            "You answer questions about consulting request demand. "
            "Use the SQL tool when data is needed. "
            "Only request read-only SQLite SELECT/WITH queries. "
            "Keep answers concise, in Swedish, and mention uncertainty or local snapshot limitations when relevant.\n\n"
            f"{schema_context}"
        )

    def _sql_tool_schema(self) -> dict:
        return {
            "type": "function",
            "name": "run_readonly_sql",
            "description": "Run a validated read-only SQLite SELECT/WITH query against the local Market Pulse database.",
            "strict": True,
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "A single read-only SQLite SELECT or WITH query.",
                    }
                },
                "required": ["sql"],
            },
        }


class AnalysisChatService:
    def __init__(
        self,
        settings: Settings,
        provider: AnalysisChatProvider | None = None,
        runner: ReadOnlySqlRunner | None = None,
    ) -> None:
        self.settings = settings
        self.runner = runner or ReadOnlySqlRunner(settings.database_path)
        self.provider = provider or build_analysis_chat_provider(settings)

    def answer(self, request: ChatRequest) -> ChatResponse:
        return self.provider.answer(request, self.runner)


def build_analysis_chat_provider(settings: Settings) -> AnalysisChatProvider:
    if settings.llm_provider == "mock":
        return MockAnalysisChatProvider()
    if settings.llm_provider == "openai_compatible":
        if not settings.llm_base_url or not settings.llm_api_key:
            raise ChatError("OpenAI-compatible chat requires base URL and API key.")
        return OpenAIResponsesAnalysisProvider(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model_name=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    raise ChatError(f"Unsupported chat provider: {settings.llm_provider}")
