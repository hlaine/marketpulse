# Extraktionskontrakt

| Fält | Värde |
| --- | --- |
| Kontraktsversion | `1.0` |
| Runtime-modell | `ConsultingRequestV1` |
| Syfte | Människovänlig beskrivning av vad som sparas efter extraktion |
| Notering | `backend/app/contracts.py` implementerar detta idag, men det här dokumentet är den avsedda mänskliga ändringsytan. |

## Syfte

Det här dokumentet beskriver det strukturerade objekt som sparas efter att extractor pipeline har bearbetat en konsultförfrågan. En förfrågan kan komma från e-post, webbsida, dokument, portalexport, manuell anteckning eller annan källa.

Målet är att göra sparad data lätt att förstå, diskutera och ändra. Ändra det här dokumentet först när produkt- eller datakontraktet ska förändras. Be sedan Codex uppdatera runtime-implementation, promptar, lagring, index och tester så att de följer dokumentet.

## Ändringsflöde

1. Ändra `contract.md` så att dokumentet beskriver den data vi vill spara.
2. Be Codex uppdatera `backend/app/contracts.py`, extractor provider/prompt, storage/indexering, API/script-beteende och tester.
3. Kör backendens testsvit.
4. Kontrollera några genererade request-JSON-filer och säkerställ att den sparade formen följer dokumentet.

## Toppnivåobjekt

Varje lyckad extraktion sparar ett toppnivåobjekt för en konsultförfrågan.

| Fält | Obligatoriskt | Typ | Betydelse |
| --- | --- | --- | --- |
| `schema_version` | Ja | string | Version av det sparade extraktionsobjektet. Nuvarande värde är `1.0`. |
| `request_id` | Ja | string | Internt unikt id för den extraherade förfrågan. Används för uppslag, rådatamappar och index. |
| `source` | Ja | object | Metadata om var förfrågan kom ifrån. |
| `content` | Ja | object | Textbärande delar som användes som input till extraktorn. |
| `demand` | Ja | object | Den affärsrelevanta konsultförfrågan som extraherats från källan. |
| `quality` | Ja | object | Confidence, review status och varningar för extraktionen. |
| `processing` | Ja | object | Metadata om när och hur extraktionen skapades. |

## Återkommande fältmönster

Många fält följer samma mönster så att vi kan spara både spårbarhet och analysvänliga värden.

| Mönster | Betydelse |
| --- | --- |
| `raw` | Originaluttrycket från källan, till exempel `senior .NET-utvecklare` eller `Malmö / hybrid`. |
| `normalized` | Ett renare värde som används för gruppering, filtrering och dashboards, till exempel `.NET Developer` eller `hybrid`. |
| `confidence` | Tal från `0.0` till `1.0` som uppskattar hur säker extraktorn är på fältet. |
| `evidence` | Korta utdrag från källtexten som visar varför värdet sattes. |

Varje `evidence`-objekt innehåller:

| Fält | Betydelse |
| --- | --- |
| `snippet` | Kort textutdrag från källan. |
| `source_part` | Var utdraget kom från, till exempel `title`, `message`, `document`, `attachment`, `web_page`, `metadata` eller `other`. |

Använd `null` när ett värde är okänt eller inte bör gissas. Använd tomma listor när ett upprepat fält saknar kända värden.

## Source

`source` beskriver var förfrågan kom ifrån och hur den kan spåras tillbaka.

| Fält | Obligatoriskt | Kan vara null | Exempel | Betydelse |
| --- | --- | --- | --- | --- |
| `kind` | Ja | Nej | `email` | Källkategori. Tillåtna värden idag: `email`, `web_page`, `document`, `portal_posting`, `chat_message`, `manual_note`, `other`. |
| `source_ref` | Ja | Nej | `email-export://0004` | Stabil referens till originalkälla, fil, export-id, URL eller import-id. |
| `received_at` | Ja | Ja | `2025-03-12T09:30:00Z` | När förfrågan togs emot eller publicerades. För mail-exporter ska detta vara mailets datum, inte processningstid. |
| `sender_name` | Ja | Ja | `Johan Bergström` | Avsändarens namn när det finns. |
| `sender_organization` | Ja | Ja | `Konsult Partners` | Avsändarorganisation när den finns. |
| `sender_domain` | Ja | Ja | `konsultpartners.se` | Domän eller organisationssignal som kan användas för gruppering. |
| `origin_url` | Ja | Ja | `https://example.com/request/123` | Original-URL från webbsida eller portal när den finns. |
| `content_types` | Ja | Nej | `["text/html", "application/pdf"]` | MIME-/innehållstyper som användes som extraktionsinput. |

## Content

`content` beskriver de textdelar som extraktorn såg. Objektet behöver inte bära all råtext för alltid, men det ska innehålla tillräckligt för att förstå vad som processades och stödja evidens.

| Fält | Obligatoriskt | Kan vara null | Betydelse |
| --- | --- | --- | --- |
| `title` | Ja | Ja | Läsbar titel, mailämne, dokumenttitel eller titel baserad på filnamn. |
| `language` | Ja | Ja | Huvudspråk om det är känt, till exempel `sv` eller `en`. |
| `parts` | Ja | Nej | Lista med textbärande delar som användes som input. |

Varje objekt i `content.parts` innehåller:

| Fält | Obligatoriskt | Kan vara null | Exempel | Betydelse |
| --- | --- | --- | --- | --- |
| `part_id` | Ja | Nej | `body` | Stabilt id inom denna förfrågan, till exempel `title`, `body` eller `attachment`. |
| `kind` | Ja | Nej | `message` | Delkategori: `title`, `message`, `document`, `attachment`, `web_page`, `metadata` eller `other`. |
| `mime_type` | Ja | Ja | `text/html` | MIME-typ när den är känd. |
| `text_excerpt` | Ja | Ja | `Kund söker senior .NET-utvecklare...` | Extraherat textutdrag som modellen använt eller som sparas för snabb inspektion. |

## Demand

`demand` är det viktigaste affärsobjektet. Det beskriver vilken konsultförfrågan källan innehåller.

### Roller

| Fält | Obligatoriskt | Typ | Betydelse |
| --- | --- | --- | --- |
| `primary_role` | Ja | normalized value | Den huvudsakliga efterfrågade rollen eller profilen. Exempel på normaliserade värden: `.NET Developer`, `Backend Engineer`, `Data Engineer`, `Solution Architect`. |
| `secondary_roles` | Ja | lista av tagged values | Övriga roller eller profiler som nämns i förfrågan. Tom lista om inga hittas. |

`primary_role` ska vara en tydlig huvudroll när det går att avgöra. Om förfrågan nämner flera profiler utan tydlig huvudroll bör extraktorn hellre sätta lägre confidence och använda `secondary_roles` än att låtsas vara säker.

### Senioritet

| Fält | Obligatoriskt | Typ | Betydelse |
| --- | --- | --- | --- |
| `seniority` | Ja | normalized value | Efterfrågad erfarenhetsnivå. Nuvarande normaliserade värden: `junior`, `mid`, `senior`, `lead`, `architect`, `unknown`. |

Använd `unknown` när senioritet inte anges tydligt.

### Tekniker

`technologies` är en lista. Varje objekt beskriver en teknik, plattform, framework, programmeringsspråk, databas, molnplattform eller verktyg som nämns.

| Fält | Obligatoriskt | Exempel | Betydelse |
| --- | --- | --- | --- |
| `raw` | Ja | `.NET Core` | Originaluttryck för tekniken. |
| `normalized` | Ja, kan vara null | `.NET` | Standardiserat tekniknamn för analys. |
| `category` | Ja | `framework` | Ett av `language`, `framework`, `cloud`, `database`, `tool`, `platform`, `other`. |
| `importance` | Ja, kan vara null | `required` | Om tekniken är `required`, `preferred` eller bara `mentioned`. |
| `confidence` | Ja | `0.86` | Confidence för denna teknikextraktion. |
| `evidence` | Ja | list | Utdrag som stödjer tekniken. |

### Certifieringar

`certifications` är en lista med certifieringar eller formella meriter.

Varje objekt använder `raw`, `normalized`, `importance`, `confidence` och `evidence`.

Exempel: `AZ-104`, `AWS Certified Solutions Architect`, `Scrum Master`.

### Språk

`languages` är en lista med krav eller önskemål på talade eller skrivna språk.

| Fält | Betydelse |
| --- | --- |
| `raw` | Originaluttryck, till exempel `svenska och engelska`. |
| `normalized` | Standardiserat språknamn, till exempel `Swedish` eller `English`. |
| `proficiency` | `basic`, `professional`, `fluent`, `native` eller `null`. |
| `importance` | `required`, `preferred`, `mentioned` eller `null`. |
| `confidence` | Confidence för språkextraktionen. |
| `evidence` | Stödjande utdrag. |

### Sektor

| Fält | Obligatoriskt | Typ | Betydelse |
| --- | --- | --- | --- |
| `sector` | Ja | normalized value | Kund- eller uppdragssektor. Nuvarande normaliserade värden: `public`, `private`, `unknown`. |

Använd `unknown` när sektor inte går att avgöra med rimlig säkerhet.

### Plats

| Fält | Obligatoriskt | Kan vara null | Betydelse |
| --- | --- | --- | --- |
| `raw` | Ja | Ja | Originaluttryck för plats, till exempel `Malmö / hybrid`. |
| `city` | Ja | Ja | Stad om den är känd, till exempel `Malmö` eller `Stockholm`. |
| `country` | Ja | Ja | Land om det är känt. |
| `confidence` | Ja | Nej | Confidence för platsextraktionen. |
| `evidence` | Ja | Nej | Stödjande utdrag. |

### Remote Mode

| Fält | Obligatoriskt | Typ | Betydelse |
| --- | --- | --- | --- |
| `remote_mode` | Ja | normalized value | Arbetsplatsmodell. Nuvarande normaliserade värden: `onsite`, `hybrid`, `remote`, `unknown`. |

### Kommersiellt

`commercial` innehåller signaler om start, längd, volym, omfattning och pris.

| Fält | Obligatoriskt | Kan vara null | Exempel | Betydelse |
| --- | --- | --- | --- | --- |
| `start_date` | Ja | Ja | `2025-04-01T00:00:00Z` | Tolkat startdatum när det är tillräckligt exakt. |
| `start_date_raw` | Ja | Ja | `ASAP`, `2025-04-01` | Ursprungligt startuttryck. |
| `duration_raw` | Ja | Ja | `6 months` | Ursprungligt uttryck för uppdragslängd. |
| `duration_months` | Ja | Ja | `6` | Tolkad längd i månader när det är säkert nog. |
| `allocation_percent` | Ja | Ja | `100` | Efterfrågad omfattning. |
| `positions_count` | Ja | Ja | `2` | Antal konsulter eller positioner. |
| `rate_amount` | Ja | Ja | `950` | Prisnivå när den nämns. |
| `rate_currency` | Ja | Ja | `SEK` | Valuta för prisnivå. |
| `rate_unit` | Ja | Ja | `hour` | Nuvarande värden: `hour`, `day`, `month` eller `null`. |
| `confidence` | Ja | Nej | `0.72` | Samlad confidence för kommersiell extraktion. |
| `evidence` | Ja | Nej | list | Stödjande utdrag. |

### Sammanfattning

| Fält | Obligatoriskt | Betydelse |
| --- | --- | --- |
| `text` | Ja | Kort, människoläsbar sammanfattning av förfrågan. |
| `confidence` | Ja | Confidence för sammanfattningen. |

## Quality

`quality` beskriver om det extraherade objektet är tillräckligt pålitligt för analys.

| Fält | Obligatoriskt | Exempel | Betydelse |
| --- | --- | --- | --- |
| `overall_confidence` | Ja | `0.84` | Samlad confidence från `0.0` till `1.0`. |
| `review_status` | Ja | `partial` | Nuvarande värden: `ok`, `partial`, `needs_review`, `failed`. |
| `warnings` | Ja | `["Primary role could not be identified confidently."]` | Människoläsbara varningar. Tom lista om inga finns. |

Föreslagen tolkning:

| Status | Betydelse |
| --- | --- |
| `ok` | Tillräckligt bra för normal analys. |
| `partial` | Användbart, men vissa fält kan vara ofullständiga eller osäkra. |
| `needs_review` | Spara posten, men verifiera innan den används som underlag. |
| `failed` | Extraktionen misslyckades eller posten bör inte användas i analys. |

## Processing

`processing` beskriver hur det strukturerade objektet skapades.

| Fält | Obligatoriskt | Exempel | Betydelse |
| --- | --- | --- | --- |
| `processed_at` | Ja | `2026-04-24T10:15:00Z` | När extractor pipeline skapade objektet. |
| `extractor_model` | Ja | `gpt-5.4` eller `heuristic-local` | Modell eller provider-implementation som användes. |
| `prompt_version` | Ja | `consulting_request_v1` | Prompt-/kontraktsversion som användes vid extraktion. |

## Det som inte sparas här

Det här objektet är det strukturerade extraktionsresultatet. Det ska inte ses som hela råarkivet.

Det som inte ingår direkt i objektet:

- full råtext från e-post, utöver utdrag
- binära bilagor
- originalfiler
- fullständigt PDF-innehåll om det lagras separat
- provider request/response-loggar om vi inte lägger till ett separat audit-lager

Sådant bör sparas eller refereras separat via rålagring och `source.source_ref`.

## Exempelform

Det här exemplet är avsiktligt förkortat. Det visar formen, inte alla möjliga fältvärden.

```json
{
  "schema_version": "1.0",
  "request_id": "abc123",
  "source": {
    "kind": "email",
    "source_ref": "email-export://0004",
    "received_at": "2025-03-12T09:30:00Z",
    "sender_name": "Johan Bergström",
    "sender_organization": "Konsult Partners",
    "sender_domain": "konsultpartners.se",
    "origin_url": null,
    "content_types": ["text/html"]
  },
  "content": {
    "title": "New Request: .NET Developer",
    "language": "en",
    "parts": [
      {
        "part_id": "body",
        "kind": "message",
        "mime_type": "text/html",
        "text_excerpt": "They are looking for a .NET Developer..."
      }
    ]
  },
  "demand": {
    "primary_role": {
      "raw": ".NET Developer",
      "normalized": ".NET Developer",
      "confidence": 0.92,
      "evidence": [
        {
          "snippet": "looking for a .NET Developer",
          "source_part": "message"
        }
      ]
    },
    "secondary_roles": [],
    "seniority": {
      "raw": null,
      "normalized": "unknown",
      "confidence": 0.35,
      "evidence": []
    },
    "technologies": [
      {
        "raw": ".NET",
        "normalized": ".NET",
        "category": "framework",
        "importance": "required",
        "confidence": 0.9,
        "evidence": []
      }
    ],
    "certifications": [],
    "languages": [],
    "sector": {
      "raw": "e-commerce",
      "normalized": "private",
      "confidence": 0.75,
      "evidence": []
    },
    "location": {
      "raw": "Malmö (on-site)",
      "city": "Malmö",
      "country": "Sweden",
      "confidence": 0.9,
      "evidence": []
    },
    "remote_mode": {
      "raw": "on-site",
      "normalized": "onsite",
      "confidence": 0.9,
      "evidence": []
    },
    "commercial": {
      "start_date": "2025-04-01T00:00:00Z",
      "start_date_raw": "2025-04-01",
      "duration_raw": "6 months",
      "duration_months": 6,
      "allocation_percent": null,
      "positions_count": 1,
      "rate_amount": 950,
      "rate_currency": "SEK",
      "rate_unit": "hour",
      "confidence": 0.8,
      "evidence": []
    },
    "summary": {
      "text": "Request for a .NET Developer in Malmö for a 6 month assignment.",
      "confidence": 0.85
    }
  },
  "quality": {
    "overall_confidence": 0.84,
    "review_status": "ok",
    "warnings": []
  },
  "processing": {
    "processed_at": "2026-04-24T10:15:00Z",
    "extractor_model": "gpt-5.4",
    "prompt_version": "consulting_request_v1"
  }
}
```

## Ändringschecklista

När kontraktet ändras ska implementationen uppdateras i samma riktning:

- Uppdatera `backend/app/contracts.py`.
- Uppdatera extractor prompts och provider-parsning.
- Uppdatera storage/indexering för nya eller ändrade analysfält.
- Uppdatera API och script-beteende om förväntningar på input/output ändras.
- Uppdatera tester och syntetiska fixtures.
- Kör `cd backend && uv run python -m unittest discover -s tests`.
