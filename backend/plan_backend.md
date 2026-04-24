# MVP-backend med enkel script-CLI

## Sammanfattning

Bygg en Python-backend med `uv`, `FastAPI` och `Pydantic` som kan ta emot text och dokument, extrahera textinnehåll, skicka det till en konfigurerbar LLM-provider, validera svaret mot `ConsultingRequestV1`, returnera strukturerad JSON och spara både resultat och råunderlag lokalt på disk.

MVP:n är synkron, filbaserad och leverantörsagnostisk. Samma kärnflöde exponeras via både REST och ett enkelt Python-script som körs med `uv run`.

## Implementation

### 1. Projektstruktur och grundkomponenter

- Skapa backendprojekt med `uv` och dela upp koden i moduler:
  - `app/config.py`
  - `app/contracts.py`
  - `app/ingest.py`
  - `app/llm.py`
  - `app/pipeline.py`
  - `app/storage.py`
  - `app/api.py`
  - `scripts/extract.py`
- Använd `pydantic-settings` för startup-konfig.
- Använd `httpx` för LLM-anrop.
- Använd en enkel PDF-läsare för MVP, helst `pypdf`.

### 2. Kontrakt och interna modeller

- Implementera `ConsultingRequestV1` som Pydantic-modell och gör den till enda sanningskällan för strukturerat resultat.
- Lägg till interna modeller för:
  - `IngestedSource`
  - `ExtractionRequest`
  - `StoredRecord`
  - `IndexEntry`
- Exportera JSON Schema från `ConsultingRequestV1` för framtida structured outputs och extern validering.

### 3. LLM-providerlager

- Definiera ett provider-interface, t.ex. `extract_structured_request(source: IngestedSource) -> ConsultingRequestV1`.
- Välj provider via config vid startup, t.ex. `LLM_PROVIDER=openai_compatible`.
- Första implementationen använder ett OpenAI-kompatibelt REST-gränssnitt med config för:
  - `LLM_BASE_URL`
  - `LLM_API_KEY`
  - `LLM_MODEL`
  - `LLM_TIMEOUT_SECONDS`
- Promptning hålls intern till providerlagret och versioneras med `prompt_version`.
- Providerlagret validerar alltid modellsvaret med Pydantic.
- Vid invalid JSON, schemafel eller refusal returneras kontrollerat fel och posten markeras som `failed` eller `needs_review`.

### 4. Ingest och pipeline

- Stöd i MVP:
  - råtext via API
  - textfiler
  - PDF-filer
- Normalisera all input till `IngestedSource` med `source`, `content.parts` och metadata.
- För API:
  - stöd för `multipart/form-data` med filupload
  - stöd för JSON-body med titel, text och metadata
- För script-CLI:
  - körs som `uv run python scripts/extract.py <path>`
  - stöd för en eller flera filvägar
  - ingen installerad executable i `PATH`
- Pipelineflöde:
  1. Läs källa
  2. Extrahera text
  3. Bygg `IngestedSource`
  4. Anropa provider
  5. Validera mot `ConsultingRequestV1`
  6. Berika med `processing`
  7. Spara råmaterial + strukturerad post + indexrad
  8. Returnera resultat

### 5. Lagring på disk

- Lagra under en tydlig katalog, t.ex.:
  - `data/requests/<request_id>.json`
  - `data/raw/<request_id>/...`
  - `data/index/requests.json`
- Använd en fil per strukturerad post.
- Spara råinnehåll separat för replay och spårbarhet.
- Håll en separat indexfil med minimifält för listning och sortering:
  - `request_id`
  - `received_at`
  - `source.kind`
  - `primary_role.normalized`
  - `sector.normalized`
  - `location.city`
  - `quality.review_status`
  - `quality.overall_confidence`
  - `stored_at`
- Kapsla lagringen bakom ett repository-interface så att JSON-filer senare kan bytas mot databas.

### 6. API och script-gränssnitt

- REST-endpoints i MVP:
  - `POST /extract`
  - `GET /requests`
  - `GET /requests/{request_id}`
- Script för MVP:
  - `uv run python scripts/extract.py <file> [<file> ...]`
- Scriptet ska:
  - processa en eller flera filer
  - skriva resultat till stdout som JSON
  - spara till datastore
- Eventuella `list` och `show`-script kan vänta till senare om vi vill hålla första versionen mindre.

## Publika interfaces och typer

- `ConsultingRequestV1` är det publika resultatkontraktet för både API och script.
- REST-API och script ska returnera samma JSON-struktur.
- Startup-konfig ska ske via miljövariabler, inte kodändringar.

## Testplan

- `uv run python scripts/extract.py sample.txt` ger strukturerad JSON och sparar post.
- `uv run python scripts/extract.py a.txt b.pdf` processar flera filer i följd.
- `POST /extract` fungerar för både filupload och textpayload.
- Ogiltigt LLM-svar fångas upp och returnerar kontrollerat fel.
- Giltigt men osäkert resultat kan markeras `needs_review`.
- `GET /requests` läser från indexfilen och kan sortera på datum.
- `GET /requests/{request_id}` returnerar samma post som tidigare sparats.
- Script och API ska ge samma kontrakt för samma input.

## Antaganden

- MVP är synkron och utan jobbkö.
- MVP stödjer text och PDF, men inte OCR, Word eller riktig webb-crawl.
- Filbaserad lagring är godkänd för hackathon/MVP.
- Endast en LLM-provider behöver implementeras initialt, men adaptergränssnittet ska stödja fler senare.
- Dashboard ingår inte i denna implementation, men API och indexfil ska göra nästa steg enkelt.
