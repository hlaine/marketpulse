# Chatbot For Dataset Questions

## Summary
Build the chatbot as an Angular UI, but route all database and OpenAI work through the FastAPI backend. The frontend should not talk directly to SQLite or OpenAI. The backend becomes the controlled agent that sends schema and compact data context to OpenAI, runs only validated read-only SQL locally, and sends query results back to the model for a Swedish answer.

This follows OpenAI's tool/function-calling flow: the model gets tools, the app executes the tools, and the model receives tool results for the final answer.

## Key Changes
- Add backend endpoint `POST /chat` with payload `{ "message": string, "conversation_id"?: string }` and response `{ "answer": string, "sql"?: string[], "rows"?: object[], "warnings"?: string[] }`.
- Create a separate analysis chat provider in the backend, independent of the current extraction LLM, using an internal `run_readonly_sql` tool.
- Do not send the whole database to the model. Send only:
  - compact schema for `requests`, `request_technologies`, and analysis views,
  - business rules, for example use `COUNT(DISTINCT request_id)` for technology summaries,
  - optional top lists of known roles, technologies, and cities to help normalization.
- Run SQL in the backend against `db/marketpulse.sqlite3` in read-only mode and allow only `SELECT`/`WITH`.
- Block destructive or broad commands: `DELETE`, `UPDATE`, `INSERT`, `DROP`, `ALTER`, `VACUUM`, `ATTACH`, `PRAGMA`, and multiple statements.
- Set query limits, timeout/progress handler, and max rows in the response.

## Frontend
- Add a chatbot panel in the Angular dashboard, with message list, input, loading/error state, and an expandable debug display for used SQL.
- Frontend calls only backend `/chat`; no API key, SQLite access, or OpenAI logic in Angular.
- Answers should clearly be able to mention that statistics are based on local snapshot data.

## Example Flow
- User: "hur många förfrågningar om .net utvecklare inkom under 2025?"
- Backend sends schema and question to the model.
- The model suggests/calls SQL, for example a join between `requests` and `request_technologies`, filtered by `received_at` during 2025 and `.NET`.
- Backend validates and runs SQL read-only.
- Backend sends the result back to the model.
- The model answers in Swedish with count, short method, and any uncertainty around the role/technology definition.

## Test Plan
- Backend unit tests for SQL validation: allow `SELECT`, deny writes, deny multi-statement, deny `PRAGMA`/`ATTACH`.
- Backend API test for `/chat` with mocked OpenAI provider that makes a SQL tool call and returns a summarized answer.
- Data test with local SQLite for the example question about `.NET` during 2025.
- Frontend component/service test for chat input, loading state, error state, and answer rendering.
- Manual acceptance: ask top roles, `.NET 2025`, technologies per sector, and remote/hybrid distribution.

## Assumptions
- MVP does not need streaming; normal request/response is enough.
- The chat should answer in Swedish by default.
- Backend may use the OpenAI API, but the database stays local and only aggregated query results are sent onward.
- The current `openai_compatible` extraction provider remains intact; the chatbot gets its own provider/logic for analysis.
