# AGENTS.md

Detta dokument ger kod-agenter snabb kontext om Market Pulse-repot och hur databasen under `db/` ska användas.

## Projektöversikt

- Projektet innehåller data och kod för att extrahera, lagra och analysera konsultförfrågningar.
- Datakontraktet för extraherad struktur beskrivs i `contract.md`.
- SQLite-databasen finns i `db/marketpulse.sqlite3` och används som lokal analys- och utvecklingsdatabas.

## Viktiga mappar

- `backend/` - backendkod, kontrakt, extraktion och lagring.
- `frontend/` - UI och visualiseringar.
- `data/` - testdata och exporter.
- `db/` - lokal SQLite-databas.

## Databas: grundregler för agenter

- Använd databasen som read-only om inte användaren uttryckligen ber om migrering, import eller datafix.
- Kör inte destruktiva SQL-kommandon som `DELETE`, `UPDATE`, `DROP`, `VACUUM INTO` eller schemaändringar utan uttrycklig instruktion.
- Om du behöver analysera innehåll, börja med views och aggregeringar innan du läser `record_json`.
- Om du rapporterar statistik, nämn gärna att datat är en lokal snapshot och kan innehålla ofullständigt normaliserade värden.

## Databasfil

- Sökväg: `db/marketpulse.sqlite3`
- Typ: SQLite 3
- Typisk åtkomst från terminal:

```bash
sqlite3 db/marketpulse.sqlite3 ".tables"
sqlite3 -header -column db/marketpulse.sqlite3 "SELECT * FROM demand_by_role ORDER BY request_count DESC LIMIT 10;"
```

## Huvudtabeller

### `requests`

Primär tabell med en rad per konsultförfrågan.

Nyckelfält:

- `request_id` - primärnyckel.
- `received_at` - när förfrågan kom in.
- `source_kind` - källa, ofta `email`.
- `sender_organization`, `sender_domain` - avsändarsignaler.
- `primary_role`, `seniority`, `sector` - huvudklassificering.
- `location_city`, `remote_mode` - plats och arbetsmodell.
- `rate_amount`, `rate_currency`, `rate_unit`, `duration_months` - kommersiella signaler.
- `review_status`, `overall_confidence` - kvalitetsfält.
- `record_json` - full sparad JSON för djupare inspektion.

### `request_technologies`

En rad per teknik som extraherats från en förfrågan.

Nyckelfält:

- `request_id` - FK till `requests`.
- `technology_key` - teknisk identifierare inom requesten.
- `raw_value`, `normalized_value` - rått och normaliserat tekniknamn.
- `category` - till exempel `language`, `cloud`, `database`, `tool`, `platform`.
- `importance` - till exempel `required`, `preferred`, `mentioned`.
- `confidence`, `position` - säkerhet och ordning.

### `request_languages`

Språkkrav per förfrågan. Tabellen finns i schemat men kan vara tom i nuvarande snapshot.

### `request_certifications`

Certifieringar per förfrågan. Tabellen finns i schemat men kan vara tom i nuvarande snapshot.

## Views för analys

Använd dessa först när du vill ge en snabb översikt:

- `demand_by_role` - antal förfrågningar per roll.
- `demand_by_city` - antal förfrågningar per stad.
- `demand_by_sector` - antal förfrågningar per sektor.
- `demand_by_technology` - aggregerad teknikefterfrågan.
- `demand_monthly` - månadsvis trend per roll.

Exempel:

```bash
sqlite3 -header -column db/marketpulse.sqlite3 "SELECT * FROM demand_by_technology ORDER BY request_count DESC LIMIT 15;"
sqlite3 -header -column db/marketpulse.sqlite3 "SELECT * FROM demand_monthly ORDER BY year_month DESC, request_count DESC LIMIT 20;"
```

## Rekommenderat arbetssatt for agenter

Nar en anvandare ber om analys av databasen:

1. Lista tabeller och views.
2. Kontrollera radantal i huvudtabellerna.
3. Sammanfatta tidsomfang, volym och centrala fordelningar.
4. Anvand views for topproller, stader, sektorer och tekniker.
5. Peka ut datakvalitetsproblem som tomma falt, inkonsekvent casing eller o-normaliserade varden.
6. Las `record_json` bara om fragan kraver finkornig felsokning eller kontraktsverifiering.

## Vanliga SQL-fragor

Topproller:

```sql
SELECT primary_role, COUNT(*) AS count
FROM requests
GROUP BY primary_role
ORDER BY count DESC, primary_role
LIMIT 10;
```

Topptekniker:

```sql
SELECT COALESCE(normalized_value, raw_value) AS technology,
       category,
       COUNT(DISTINCT request_id) AS request_count
FROM request_technologies
GROUP BY COALESCE(normalized_value, raw_value), category
ORDER BY request_count DESC, technology
LIMIT 15;
```

Datakvalitet for remote mode:

```sql
SELECT remote_mode, COUNT(*) AS count
FROM requests
GROUP BY remote_mode
ORDER BY count DESC;
```

Saknade sektorvarden:

```sql
SELECT COUNT(*) AS missing_sector
FROM requests
WHERE sector IS NULL OR TRIM(sector) = '';
```

## Nar `record_json` bor anvandas

Anvand `record_json` nar du behover:

- verifiera att lagrad JSON foljer `contract.md`,
- felsoka skillnader mellan extraherad struktur och SQL-kolumner,
- hitta falt som annu inte materialiserats i separata tabeller eller views.

Exempel:

```bash
sqlite3 -header -column db/marketpulse.sqlite3 "SELECT request_id, record_json FROM requests WHERE request_id = '...' ;"
```

## Koppling till datakontraktet

- Se `contract.md` for avsedd betydelse av falt och normaliserade varden.
- Om databasen och kontraktet verkar divergera ska agenten rapportera det tydligt.
- Om användaren ber om schema- eller kontraktsandring: uppdatera forst `contract.md`, sedan runtimekod, lagring, index och tester.

## Praktiska riktlinjer

- Foredra `sqlite3 -header -column` for lasbara resultat i terminalen.
- Anvand `COUNT(DISTINCT request_id)` for tekniksammanstallningar, sa att samma request inte dubbelraknas.
- Var explicit med null/blank-varden i analyser.
- Normalisera inte data i databasen pa eget initiativ; foresla SQL eller kodandringar och invanta uppdrag om skrivande andringar kravs.
