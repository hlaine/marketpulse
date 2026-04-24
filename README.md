# Cloud & Code Hackaton 2026

## Projekt - Market Pulse

### Howto

#### Testdata

Under `data/` finns testdata för projektet.

- Katalogen `data/emails/` innehåller exempel mejl exporterat till `json`
- `data/structured.json` innehåller förberedd extraherad data från mejlen.

#### Backend

Backend-appen ligger i `backend/` och är byggd med FastAPI. Den används för att extrahera konsultförfrågningar, spara dem i SQLite och svara på chat-/analysfrågor mot den lokala databasen.

##### Beroenden

Du behöver:

- Python 3.11 eller senare
- `uv` för Python dependency management
- SQLite 3, normalt redan installerat på macOS/Linux

Installera `uv` om det saknas:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verifiera:

```bash
python3 --version
uv --version
sqlite3 --version
```

Backendens Pythonberoenden finns i `backend/pyproject.toml` och installeras av `uv`. Viktiga runtimeberoenden är bland annat FastAPI, Uvicorn, Pydantic, HTTPX, python-multipart och pypdf.

##### Konfiguration

Skapa en lokal `.env` från exemplet om den saknas:

```bash
cd backend
cp .env.example .env
```

För lokal utveckling kan du använda mockad LLM:

```env
MARKET_PULSE_LLM_PROVIDER="mock"
MARKET_PULSE_LLM_MODEL="mock-extractor-v1"
MARKET_PULSE_PROMPT_VERSION="consulting_request_v1_mock"
MARKET_PULSE_DATABASE_PATH="../db/marketpulse.sqlite3"
```

För OpenAI-kompatibel provider, sätt istället:

```env
MARKET_PULSE_LLM_PROVIDER="openai_compatible"
MARKET_PULSE_LLM_BASE_URL="https://api.openai.com/v1"
MARKET_PULSE_LLM_API_KEY="..."
MARKET_PULSE_LLM_MODEL="gpt-5.4"
MARKET_PULSE_PROMPT_VERSION="consulting_request_v1"
```

Databasen ligger som standard i:

```text
db/marketpulse.sqlite3
```

##### Köra backend

Från repo-roten:

```bash
cd backend
uv sync
uv run uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Öppna eller testa healthcheck:

```bash
curl http://127.0.0.1:8000/health
```

Förväntat svar:

```json
{"status":"ok"}
```

##### Vanliga backend-endpoints

Lista sparade förfrågningar:

```bash
curl http://127.0.0.1:8000/requests
```

Ladda upp ett dokument och spara extraherad struktur i databasen:

```bash
curl -F "file=@data/emails/0177_ASAP AI Engineer  AIML  Fintech.json" \
  http://127.0.0.1:8000/documents
```

Stödda filtyper för `POST /documents` är `.json`, `.txt`, `.md`, `.eml` och `.pdf`.

Ställ en chattfråga mot datasetet:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hur många förfrågningar om .net utvecklare inkom under 2025?"}'
```

##### Backendtester

```bash
cd backend
uv run python -m unittest discover -s tests -q
```

#### Frontend

Frontend-appen ligger i `frontend/app` och är byggd med Angular.

##### Installera Angular från scratch

1. Installera Node.js och npm.
2. Verifiera installationen:

```bash
node --version
npm --version
```

3. Installera Angular CLI globalt:

```bash
npm install -g @angular/cli
```

4. Verifiera att Angular CLI finns:

```bash
ng version
```

##### Köra frontend-appen

1. Gå till frontend-katalogen:

```bash
cd frontend/app
```

2. Installera beroenden:

```bash
npm install --legacy-peer-deps
```

Om du får problem med npm-cache på din maskin kan du använda en temporär cache:

```bash
npm install --legacy-peer-deps --cache /tmp/marketpulse-npm-cache
```

3. Starta utvecklingsservern:

```bash
npm start
```

4. Öppna appen i webbläsaren:

```text
http://localhost:4200
```

##### Övriga frontend-kommandon

Bygg appen:

```bash
cd frontend/app
npm run build
```

Kör tester:

```bash
cd frontend/app
npm test -- --watch=false
```
