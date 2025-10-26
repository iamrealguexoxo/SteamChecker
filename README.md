# SteamChecker

Ein schneller CLI-Checker für Steam Workshop Items (z. B. Project Zomboid). Du gibst eine oder mehrere Workshop-IDs ein, und das Tool prüft, ob sie existieren, gelöscht/privat sind, extrahiert den Titel sowie die Mod ID und markiert problematische Einträge (z. B. "Outdated" oder andere Versionen).

> Im Repo sind zwei Varianten enthalten:
> - C#/.NET 9 (empfohlen) – Datei: `Program.cs`
> - Python (Optional) – Datei: `steam_workshop_checker_python.py`

---

## Features

- Mehrere Workshop-IDs auf einmal prüfen (Eingabe per `;` getrennt)
- Status je ID: OK, GELÖSCHT, WARNUNG (kein Titel), FEHLER/Timeout
- Titel-Erkennung via HTML-Parsing (HtmlAgilityPack) + Fallback via OpenGraph
- Automatisches Extrahieren der Mod ID aus der Workshop-Seite
- Warnhinweise bei:
  - "Working Outdated"/"Outdated" → [ACHTUNG OUTDATE]
  - Nur "B42" im Titel (ohne "B41") → [ANDERE VERSION]
- Interaktive Gegenprüfung eigener Mod-IDs (Config ↔ Workshop)
- Farbiges, kompaktes CLI-Output und Zusammenfassungen

---

## Voraussetzungen

- .NET SDK 9.0
- Windows PowerShell, macOS oder Linux Shell (läuft plattformübergreifend, getestet auf Windows)
- Optional für die Python-Variante: Python 3.8+ und `requests`

---

## Schnellstart (C#/.NET)

1) Repository klonen
2) Abhängigkeiten werden automatisch über NuGet geladen (HtmlAgilityPack)
3) Build und Run

```powershell
# Im Repo-Root (Ordner mit SteamChecker.csproj)

dotnet build

dotnet run --project .\SteamChecker.csproj
```

Du kannst auch die vorhandenen VS Code Tasks nutzen:

- Build: "build"
- Watch/Run: "watch" (Hot-reload für schnelle Iteration)
- Publish: "publish"

In VS Code: Terminal → Run Task → gewünschten Task wählen.

---

## Nutzung

Nach dem Start wirst du aufgefordert, Workshop-IDs einzugeben (mit `;` trennen):

```
📝 Steam Workshop IDs eingeben (getrennt mit ';'):
💡 Beispiel: 2709866494;3445949422;3445362877
➤ 2709866494;3445949422;3445362877
```

Das Tool ruft die Workshop-Seiten ab, analysiert Titel und Mod ID und zeigt danach eine Zusammenfassung.
Anschließend kannst du optional deine eigenen Mod-IDs (z. B. aus einer Server-Config) eingeben, um sie mit den gefundenen Mod IDs abzugleichen.

### Beispiel-Workflow

1) IDs prüfen → Status/Warnings/Mod IDs werden angezeigt
2) "Möchtest du deine Mod-IDs abgleichen? (j/n)" → `j`
3) Eigene Mod-IDs eingeben, wieder per `;` getrennt (z. B. `iMeds;SCEEP_Hotwire;GreenHouse`)
4) Ergebnis zeigt: vorhanden, fehlend, zusätzlich

---

## Python-Variante (optional)

```powershell
# Optional: nur wenn du die Python-Variante ausprobieren willst
python .\steam_workshop_checker_python.py
```

Die Python-Version bietet einen sehr ähnlichen Funktionsumfang (Requests + Regex-Parsing) und eignet sich als Referenz oder zum schnellen Testen.

---

## Hinweise & Grenzen

- Das Tool parst HTML von Workshop-Seiten. Wenn Valve/Steam das Markup ändert, kann die Erkennung (Titel/Mod ID) fehlschlagen.
- Private oder gelöschte Items liefern oft keinen Titel → werden als WARNUNG/NO_TITLE oder GELÖSCHT klassifiziert.
- Es gibt ein kleines Delay (600 ms) zwischen Anfragen, um die Seite nicht zu stark zu belasten. Bei vielen IDs dauert es entsprechend länger.
- Keine Nutzung einer offiziellen Steam-API. Rate Limits/CAPTCHAs können auftreten.

---

## Technik-Stack

- C# 12, .NET 9.0
- HtmlAgilityPack für robustes HTML-Parsing
- Regex zur Mod-ID-Erkennung

---

## Beiträge

Issues und Pull Requests sind willkommen. Wenn du neue Muster für die Erkennung hast (z. B. andere Spiele/Seitenstrukturen), eröffne gern ein PR.

---

## Lizenz

alles freeeeeeeeeee, gib ihm
