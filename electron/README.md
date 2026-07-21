# SteamChecker

Ein kleines Desktop-Tool, das Steam-Workshop-Items für **Project Zomboid** prüft —
erkennt gelöschte / private / nicht existierende Items und veraltete Mods, zieht
automatisch die Mod-IDs und gleicht sie gegen deine Server-Config ab. **Kein
Steam-Login nötig.**

Electron-Rewrite des ursprünglichen Python/C#/Go-Tools — läuft dadurch mit
identischem Look auf **macOS und Windows**.

## Features

- Workshop-IDs (mit `;` getrennt) einfügen → Live-Prüfung mit Fortschritt
- Ampel-Status: **OK** / **Warnung** (Outdated, B42) / **Problem** (gelöscht, privat, Fehler)
- Automatische Mod-ID-Extraktion (auch mehrere IDs pro Item)
- **Bereinigte Liste** — kopiert die sauberen IDs ohne die geflaggten
- **Mod-ID-Abgleich** gegen deine Server-Config (vorhanden / fehlt / zusätzlich)
- Klick auf eine ID öffnet die Workshop-Seite im Browser

Der eigentliche HTTP-Request läuft im Electron-Main-Prozess (kein CORS-Problem
wie im Browser); die Titel-/Mod-ID-Extraktion ist ein 1:1-Port der Python-Logik.

## Entwicklung

```bash
npm install
npm run dev        # Electron + Vite Dev-Server
npm run build      # Production-Bundle nach dist/
npm run package    # electron-builder (aktuelle Plattform)
```

## Aufbau

- `src/main/checker.ts` — Fetch + Titel-/Mod-ID-Extraktion + Warnregeln
- `src/main/index.ts` — Fenster + IPC (`steam:check`, `shell:openExternal`)
- `src/preload/index.ts` — `window.api`-Brücke
- `src/renderer/App.tsx` — komplette UI
- `src/renderer/lib/checker.ts` — Parsing der Eingaben + Vergleichslogik
