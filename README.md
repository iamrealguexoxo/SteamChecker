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


# SteamChecker

A fast CLI checker for Steam Workshop items (e.g., Project Zomboid). You enter one or more Workshop IDs, and the tool checks whether they exist, are deleted/private, extracts the title and Mod ID, and flags problematic entries (e.g., "Outdated" or different versions).

> The repository contains two variants:
> - C#/.NET 9 (recommended) – File: `Program.cs`
> - Python (optional) – File: `steam_workshop_checker_python.py`

---

## Features

- Check multiple Workshop IDs at once (input separated by `;`)
- Status per ID: OK, DELETED, WARNING (no title), ERROR/Timeout
- Title detection via HTML parsing (HtmlAgilityPack) + OpenGraph fallback
- Automatic extraction of the Mod ID from the Workshop page
- Warnings for:
  - "Working Outdated"/"Outdated" → [ATTENTION OUTDATED]
  - Only "B42" in title (without "B41") → [DIFFERENT VERSION]
- Interactive comparison of your own Mod IDs (Config ↔ Workshop)
- Colorful, compact CLI output and summaries

---

## Requirements

- .NET SDK 9.0
- Windows PowerShell, macOS, or Linux Shell (cross-platform, tested on Windows)
- Optional for the Python variant: Python 3.8+ and `requests`

---

## Quick Start (C#/.NET)

1) Clone the repository
2) Dependencies are automatically loaded via NuGet (HtmlAgilityPack)
3) Build and run

```powershell
# In the repo root (folder with SteamChecker.csproj)

dotnet build

dotnet run --project .\SteamChecker.csproj
```

You can also use the existing VS Code tasks:

- Build: "build"
- Watch/Run: "watch" (Hot-reload for quick iteration)
- Publish: "publish"

In VS Code: Terminal → Run Task → select the desired task.

---

## Usage

After starting, you'll be prompted to enter Workshop IDs (separated by `;`):

```
📝 Enter Steam Workshop IDs (separated by ';'):
💡 Example: 2709866494;3445949422;3445362877
➤ 2709866494;3445949422;3445362877
```

The tool fetches the Workshop pages, analyzes the title and Mod ID, and then displays a summary.
Optionally, you can enter your own Mod IDs (e.g., from a server config) to compare them with the found Mod IDs.

### Example Workflow

1) Check IDs → Status/Warnings/Mod IDs are displayed
2) "Do you want to compare your Mod IDs? (y/n)" → `y`
3) Enter your own Mod IDs, again separated by `;` (e.g., `iMeds;SCEEP_Hotwire;GreenHouse`)
4) Result shows: present, missing, additional

---

## Python Variant (optional)

```bash
# Optional: only if you want to try the Python variant
python steam_workshop_checker_python.py
```

The Python version offers very similar functionality (Requests + Regex parsing) and serves as a reference or for quick testing.

---

## Notes & Limitations

- The tool parses HTML from Workshop pages. If Valve/Steam changes the markup, detection (title/Mod ID) may fail.
- Private or deleted items often don't provide a title → classified as WARNING/NO_TITLE or DELETED.
- There's a small delay (600 ms) between requests to avoid overloading the page. With many IDs, this takes correspondingly longer.
- No use of an official Steam API. Rate limits/CAPTCHAs may occur.

---

## Tech Stack

- C# 12, .NET 9.0
- HtmlAgilityPack for robust HTML parsing
- Regex for Mod ID detection

---

## Contributions

Issues and pull requests are welcome. If you have new patterns for detection (e.g., other games/page structures), feel free to open a PR.

---

## License

Everything is free to use – go for it!

---

## Links

- GitHub Repository: [iamrealguexoxo/SteamChecker](https://github.com/iamrealguexoxo/SteamChecker)

