# Frontend - Vue.js 3

Cartella frontend dell'applicazione Software Architecture 2025/2026.

## Installazione

```bash
cd Frontend
npm install
```

## Configurazione

Copia il file `.env.example` in `.env.local`:

```bash
cp .env.example .env.local
```

Modifica `VITE_API_URL` se il backend è su un URL diverso.

## Sviluppo

```bash
npm run dev
```

L'applicazione sarà disponibile su `http://localhost:5173`

## Build

```bash
npm run build
```

## Struttura del Progetto

```
Frontend/
├── src/
│   ├── components/       # Componenti Vue riutilizzabili
│   ├── pages/            # Pagine dell'applicazione
│   ├── services/         # Servizi (API, ecc.)
│   ├── stores/           # Store Pinia (state management)
│   ├── assets/           # Assets statici
│   ├── App.vue           # Componente root
│   ├── main.js           # Entry point
│   ├── router.js         # Configurazione routes
│   └── style.css         # Stili globali
├── public/               # Asset pubblici
├── index.html            # HTML entry point
├── vite.config.js        # Configurazione Vite
├── package.json          # Dipendenze
└── .env.example          # Template variabili d'ambiente
```

## Pagine Disponibili

- **/** - Home (landing page)
- **/login** - Pagina di login
- **/dashboard** - Dashboard principale (protetta da autenticazione)

## Tecnologie

- **Vue.js 3** - Framework frontend
- **Vite** - Build tool
- **Vue Router** - Routing
- **Pinia** - State management
- **Axios** - HTTP client

## Features

- ✅ Autenticazione con JWT
- ✅ Refresh token automatico
- ✅ Route protette (authentication guard)
- ✅ State management centralizzato
- ✅ Gestione team, competizioni, iscrizioni e atleti

