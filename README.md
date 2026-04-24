# Cloud & Code Hackaton 2026

## Projekt - Market Pulse

### Howto

#### Testdata

Under `data/` finns testdata för projektet.

- Katalogen `data/emails/` innehåller exempel mejl exporterat till `json`
- `data/structured.json` innehåller förberedd extraherad data från mejlen.

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
