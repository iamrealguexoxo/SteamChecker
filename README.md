# Steam Workshop Item Checker für Zomboid

Ein modernes Tool zum Prüfen und Verwalten von Steam Workshop Items. Verfügbar als **CLI** (Kommandozeile) und **WPF GUI** (grafische Oberfläche).

## Für alle, die „einfach nur prüfen“ wollen

Dieses Tool hilft dir, fehlerhafte oder gelöschte Workshop-Mods für deinen Zomboid-Server schnell zu finden – ohne Technik-Wissen.

- Erkennt gelöschte/privat gestellte Items und Mods ohne Titel
- Liest die Mod-ID automatisch aus und warnt bei möglichen Problemen (z. B. „Outdated“)
- Zeigt dir eine bereinigte Liste an, mit der du deine Server-Config leicht aktualisieren kannst
- Keine Installation nötig (fertige ZIP herunterladen, entpacken, starten)
- Kein Steam-Login erforderlich

Schnellstart (Windows App):
1) Lade die neueste Version herunter: https://github.com/iamrealguexoxo/SteamChecker/releases/latest
2) Entpacke die ZIP und starte `SteamCheckerWPF.exe`
3) Füge deine Workshop-IDs ein (Semikolon-getrennt, z. B. `2709866494;3445949422;...`)
4) Klicke auf „Prüfen“ – rot markierte bzw. gelöschte Einträge solltest du entfernen
5) Optional: „Mod-IDs vergleichen“, um deine Config-IDs abzugleichen

Du möchtest lieber die Konsole nutzen? Unten findest du eine einfache Anleitung für die CLI.

**English version below — Deutsche Version zuerst.**

---

## ✨ Neueste Änderungen / Latest changes

<!-- CHANGELOG:START -->
## 1.0.0 — 2025-11-02

### Added
- WPF About dialog with animated logo (`loading.gif`), link, and dynamic version from assembly metadata.
- Version badge in the MainWindow header (reads the same version source as the About dialog).
- "Neueste Änderungen / Latest changes" section in `README.md` with markers for auto-embedding.
- GitHub Action `.github/workflows/update-readme-changelog.yml` that updates the README block from CHANGELOG.
- Release packaging: self-contained publishes for WPF and CLI (win-x64), ZIP artifacts and SHA256 checksums.

### Changed
- CLI: strengthened nullability handling; safer parsing and output; improved interactive prompts.
- WPF helper `pc_automation_tool.cs`: replaced `Thread.Sleep(200)` with `await Task.Delay(200)` in async handler to avoid UI blocking.
- CLI project: excluded `SteamCheckerWPF/**` from default item globs to avoid compiling WPF into CLI publish.

### Fixed
- WPF build configuration: switched to `Microsoft.NET.Sdk.WindowsDesktop` with `<UseWPF>true</UseWPF>` and removed duplicate assembly attributes to resolve previous compile errors.
- CLI publish failure caused by unintended inclusion of WPF sources.
<!-- CHANGELOG:END -->

---

## 🖼️ WPF Graphical Interface (New!)

![Steam Workshop Checker Pro GUI](screenshot-wpf.png)

Die neue **WPF-GUI** bietet eine benutzerfreundliche grafische Oberfläche mit:
- 📝 Intuitive Input-Felder für Workshop-IDs
- ✅ Live-Ergebnisse in übersichtlicher Tabelle
- 🔗 Mod-ID Vergleich mit deiner Config
- 📊 Statistik-Übersicht (OK, Warnungen, Gelöscht, Fehler)
- 💾 Export- und Kopier-Funktionen
- 🎨 Dunkles Design mit farbigen Highlights
 - ℹ️ About-Dialog mit animiertem Logo und dynamischer Versionsanzeige

**Start der WPF-App:**
```powershell
cd .\SteamCheckerWPF
dotnet build
dotnet run
```

### ℹ️ About-Dialog & Version

- Im Hauptfenster rechts oben: Button „ℹ Über“ öffnet den About-Dialog.
- Der Dialog zeigt dein animiertes Logo (`loading.gif`) und „made with ❤ by iamguexoxo“.
- Die Version wird automatisch aus den Assembly-Metadaten gelesen in der Reihenfolge:
  1) `AssemblyInformationalVersion`
  2) `AssemblyFileVersion`
  3) `Assembly.GetName().Version`

So kannst du die angezeigte Version bequem steuern (optional in der `SteamCheckerWPF.csproj`):

```xml
<PropertyGroup>
  <AssemblyVersion>1.2.0.0</AssemblyVersion>
  <FileVersion>1.2.0.0</FileVersion>
  <InformationalVersion>1.2.0-pre</InformationalVersion>
  <!-- ‚InformationalVersion‘ unterstützt SemVer/Pre-release-Suffixe und wird bevorzugt angezeigt. -->
  <!-- Das WPF-Header zeigt „• v<Version>“, der About-Dialog „v<Version>“. -->
  <!-- Das animierte Logo liegt unter SteamCheckerWPF/loading.gif und ist als Resource eingebunden. -->
  <!-- Passe die Datei einfach an, wenn du ein anderes Logo verwenden willst. -->
  <!-- Hinweis: Ein altes WinForms-Tool (pc_automation_tool.cs) ist im WPF-Projekt ausgeschlossen. -->
  <!-- Wenn du es nutzen möchtest, können wir es in ein eigenes WinForms-Projekt auslagern. -->
  
</PropertyGroup>
```

---

## 🐍 Python GUI & CLI

Für alle, die das Tool lieber in Python nutzen möchten, gibt es jetzt eine vollständige Python-Implementierung mit drei Oberflächen (Tkinter, Qt Widgets und QML) plus CLI. Die Python-Version hält Funktionsparität zur ursprünglichen C#-Variante – inklusive Warnungsbereinigung, Mod-ID-Vergleich und neuer Diagnose-Features.

### Kernfunktionen (gelten für alle Python-Frontends)
- 🔄 **Streaming-Prüfung**: Fortschritt, Status-Text und Zusammenfassung aktualisieren sich live.
- 🆔 **Multi-Mod-ID-Erkennung**: Unterstützt mehrere IDs pro Workshop-Eintrag (auch mit Leerzeichen, Klammern oder `&`).
- ⚠️ **Warnungslogik**: Kennzeichnet automatisch "Outdated"-Titel oder reine B42-Mods.
- 🧹 **Warnungs-Mods entfernen**: Ein Klick erzeugt eine bereinigte ID-Liste ohne riskante Mods.
- 🔍 **Mod-ID-Vergleich**: Liefert "VORHANDEN / FEHLT / ZUSÄTZLICH" und markiert Einträge direkt in der Tabelle.
- 📋 **Kontext-Aktionen**: Alle GUIs bieten Copy-Funktionen für Links, IDs und die bereinigte Liste.
- 🌐 **Keine Anmeldung nötig**: Es wird nur die öffentliche Workshop-Seite abgefragt.

### Schnellstart (Python GUI)
```powershell
cd .\SteamChecker
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m python_steam_checker.gui_tk
```

### Alternativ: Moderne Qt-GUI (PySide6)
```powershell
cd .\SteamChecker
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m python_steam_checker.gui_qt
```

### Neu: Qt Quick/QML GUI (Material)
```powershell
cd .\SteamChecker
if (-not (Test-Path .venv313)) { C:\Python313\python.exe -m venv .venv313 }
 .\.venv313\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m python_steam_checker.gui_qml
```
- QML-Oberfläche mit Qt Quick Controls 2 (Material-Theme, Hell/Dunkel-Umschaltung).
- Live-Progress, Abbrechen, „Warnungs-Mods entfernen“, Mod-ID-Vergleich und kopierbare bereinigte Liste.
- Optionales GIF im About-Dialog: lege `python_steam_checker/assets/bart.gif` ab.

Tipps:
- PySide6 ist aktuell nicht für Python 3.14 verfügbar. Verwende bei Bedarf Python 3.13:
```powershell
cd .\SteamChecker
if (-not (Test-Path .venv313)) { C:\Python313\python.exe -m venv .venv313 }
 .\.venv313\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m python_steam_checker.gui_qt
```

### Schnellstart (Python CLI)
```powershell
cd .\SteamChecker
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\steam_workshop_checker_python.py
```

### Python Dateien
- `python_steam_checker/core.py` – Kernlogik (Abruf, Parsing, Warnungen, Vergleich)
- `python_steam_checker/gui_tk.py` – Tkinter GUI (Prüfen, Zusammenfassung, Warnungs-Entfernung, ID-Vergleich, About-Dialog)
- `python_steam_checker/gui_qt.py` – PySide6 GUI (modernes UI, gleiche Features wie Tk, Abbrechen + Theme-Toggle)
- `python_steam_checker/gui_qml.py` + `python_steam_checker/qml/Main.qml` – Qt Quick Material UI mit erweiterten Analyse-Features

### Qt-GUI Features (Zusatz)
- Abbrechen-Button: bricht laufende Prüfungen sauber ab.
- Theme-Toggle: kleines Symbol (🌙/☀️) oben – wechselt zwischen Dunkel/Hell.
- `steam_workshop_checker_python.py` – Konsolenversion (paritätisch zu C#)

### About-Dialog mit animiertem GIF
- Button `ℹ Über` öffnet ein Fenster. Lege deine GIF-Datei unter `python_steam_checker/assets/bart.gif` ab (z. B. tanzender Bart), dann wird sie animiert angezeigt. Ohne GIF erscheint ein Hinweis.

Hinweis: Die Python-GUIs nutzen Worker-Threads, um den UI-Thread nicht zu blockieren, und zeigen eine übersichtliche Tabelle sowie eine bereinigte ID-Liste an.

### QML Material GUI – Highlights
- 📋 **Filterbar**: Drei Live-Filter für Status, Warnung und Vergleichs-Tag (OK / Gemischt / Zusätzlich). Der Filterbereich ist einklappbar.
- 🏷️ **Vergleichs-Badges**: Jeder Eintrag erhält einen farbigen Pillen-Status (OK, Gemischt oder Zusätzlich), sobald ein Mod-ID-Vergleich durchgeführt wurde.
- 🔗 **Klickbare Felder**: Workshop-ID und Titel öffnen direkt den Browser; Rechtsklick bietet "Link kopieren" oder "ID kopieren".
- 📜 **Autoscroll**: Während des Prüfens scrollt die Liste automatisch nach unten, damit die neuesten Resultate sichtbar bleiben.
- 🎨 **Material Dark/Light**: Schneller Theme-Wechsel, abgestimmte Farben und dezente Zeilenhintergründe.
- 🧰 **Kontextdialoge**: Vergleichsergebnis und About-Dialog (mit optionalem `bart.gif`) erscheinen als moderne Popups.

### Tkinter GUI – Highlights
- Klassische Desktop-Oberfläche ohne zusätzliche Dependencies.
- Zeigt dieselben Felder wie Qt/QML und nutzt die neue Multi-ID-Logik im Hintergrund.
- Fortschritt und Zusammenfassung in einem Fenster, inklusive Warnungsbereinigung.

### Qt Widgets GUI – Highlights
- Dark/Light Theme-Toggle, Abbrechen-Button und moderne Controls basierend auf PySide6.
- Tabellarische Darstellung analog zur Tk-Version, inklusive Zugriff auf Vergleichsdialog und bereinigte Liste.

---

## 🇩🇪 Deutsch – CLI (Kommandozeile)

Ein kleines CLI-Tool zum Prüfen von Steam Workshop Items anhand ihrer IDs. Es liest Titel und Mod-ID aus, erkennt gelöschte/private Einträge sowie Warnungen (z. B. „Outdated" oder nur „B42") und bietet dir nun interaktiv an, Mods mit Warnungen aus deiner Liste zu entfernen.

### Features
- Prüfung beliebiger Workshop-IDs (eingeben mit `;` getrennt)
- Ermittelt Titel; erkennt „gelöscht“, „kein Titel“ (z. B. privat) und Fehler
- Extrahiert die Mod-ID aus der Workshop-Seite und zeigt sie an
- Warnungen:
  - [ACHTUNG OUTDATE], wenn Titel „Outdated“ enthält
  - [ANDERE VERSION], wenn Titel „B42“ enthält, aber kein „B41“
- NEU: Interaktive Abfrage, ob Mods mit Warnungen aus der Liste entfernt werden sollen
  - Wenn „Ja“, wird eine bereinigte Liste (Semikolon-getrennt) ausgegeben
- Optionaler Abgleich deiner eigenen Mod-IDs (z. B. aus einer Config) mit den gefundenen Mod-IDs
- Zusammenfassungen und farbige Ausgabe für schnellen Überblick
- Rate-Limit-freundliche Abfragen (kurzer Delay zwischen Anfragen)

### Voraussetzungen
- .NET SDK 9.0+
- Windows PowerShell oder Terminal

### Schnellstart
```powershell
dotnet build
dotnet run --project .\SteamChecker.csproj
```

**Oder die WPF-GUI starten:**
```powershell
cd .\SteamCheckerWPF
dotnet build
dotnet run
```

### Nutzung
1) IDs eingeben (Semikolon-getrennt):
```
2709866494;3445949422;3445362877
```

2) Das Tool prüft die Items und zeigt Ergebnisse plus Zusammenfassung.

3) NEU: Wenn Warnungen gefunden wurden, wirst du gefragt:
```
❓ Möchtest du die Mods mit Warnungen aus deiner Liste entfernen?
(j/n)
```
- „j“/„y“/„yes“ → Es wird eine bereinigte Liste (ohne diese Mods) ausgegeben:
```
✅ AKTUALISIERTE LISTE (ohne Mods mit Warnungen):
1234567890;2345678901;...
📊 12 Mods in deiner Liste verbleibend
```
- „n“ → Keine Änderung, nur Anzeige.

4) Optional: Abgleich deiner Mod-IDs
Nach einem Check wirst du gefragt:
```
🔍 Möchtest du deine Mod-IDs abgleichen? (j/n)
```
- Gib deine Mod-IDs ein (Semikolon-getrennt), z. B.:
```
iMeds;SCEEP_Hotwire;GreenHouse
```
- Du erhältst „VORHANDEN“, „FEHLT“ und „ZUSÄTZLICH“ (Workshop-Mods, die nicht in deiner Liste sind).

### Hinweise & Grenzen
- HTML-Parsing kann brechen, wenn Valve das Markup ändert.
- Private/gelöschte Items liefern oft keinen Titel („NO_TITLE").
- Es gibt eine kurze Verzögerung zwischen Anfragen, um Rate Limits zu vermeiden.
- Erkennung der Mod-ID basiert auf regulären Ausdrücken und kann je nach Beschreibung/Seite variieren.

### Technik-Stack (CLI)
- C# 12, .NET 9.0
- HtmlAgilityPack für robustes HTML-Parsing
- Regex zur Mod-ID-Erkennung

---

## 🇬🇧 English – CLI

A small CLI tool to check Steam Workshop items by their IDs. It reads the title and extracts the Mod ID, detects deleted/private entries and warnings (e.g., “Outdated” or “B42-only”), and now interactively offers to remove mods with warnings from your list.

### Features
- Validate any number of Workshop IDs (semicolon-separated input)
- Reads the item title; detects "deleted", "no title" (e.g., private), and errors
- Extracts the Mod ID from the page and displays it (highlighted in **Cyan/Blue**)
- Warnings:
  - [ACHTUNG OUTDATE] when title contains "Outdated"
  - [ANDERE VERSION] when title contains "B42" but not "B41"
- NEW: Interactive prompt to remove mods with warnings from your list
  - If accepted, prints a cleaned semicolon-separated list
- Optional comparison of your own config Mod IDs with the found Workshop Mod IDs
- Summaries with colored output for quick scanning
- Rate-limit-friendly requests (small delay between calls)

### Requirements
- .NET SDK 9.0+
- Windows PowerShell or terminal

### Quick start
```powershell
dotnet build
dotnet run --project .\SteamChecker.csproj
```

**Or start the WPF GUI:**
```powershell
cd .\SteamCheckerWPF
dotnet build
dotnet run
```

### Usage
1) Enter IDs (semicolon-separated):
```
2709866494;3445949422;3445362877
```

2) The tool checks all items and prints results plus a summary.

3) NEW: If warnings were found, you’ll be asked:
```
❓ Do you want to remove the mods with warnings from your list?
(y/n)
```
- “y”/“yes” → A cleaned list (without those mods) is printed:
```
✅ UPDATED LIST (without mods with warnings):
1234567890;2345678901;...
📊 12 mods remain in your list
```
- “n” → No changes, just display.

4) Optional: Compare your Mod IDs
After a check you’ll be asked:
```
🔍 Do you want to compare your Mod IDs? (y/n)
```
- Enter your Mod IDs (semicolon-separated), e.g.:
```
iMeds;SCEEP_Hotwire;GreenHouse
```
- You’ll get “FOUND”, “MISSING”, and “EXTRA” (Workshop mods not in your list).

### Notes & limitations
- HTML parsing may break if Valve changes the page structure.
- Private/deleted items often return no title ("NO_TITLE").
- There's a short delay between requests to be gentle on rate limits.
- Mod ID extraction is regex-based and may vary with item descriptions/pages.

### Tech Stack (CLI)
- C# 12, .NET 9.0
- HtmlAgilityPack for robust HTML parsing
- Regex for Mod ID detection

---

## 📦 Project Structure

```
SteamChecker/
├── Program.cs                  # CLI Application (main)
├── steam_workshop_checker_python.py  # Python alternative
├── SteamChecker.csproj         # CLI project file
├── SteamChecker.sln            # Solution file
│
└── SteamCheckerWPF/            # WPF GUI Application
    ├── MainWindow.xaml         # UI Layout
    ├── MainWindow.xaml.cs      # UI Logic
  ├── AboutWindow.xaml        # About dialog (animated logo + version)
  ├── AboutWindow.xaml.cs     # About dialog logic
    ├── App.xaml                # App config
  ├── loading.gif             # Animated logo for About dialog
    └── SteamCheckerWPF.csproj  # GUI project file
```

---

## 🤝 Contributions

Issues and pull requests are welcome. If you have improvements, new patterns for detection, or UI enhancements, feel free to contribute!

---

## 📄 License

MIT License

Copyright (c) 2025 iamrealguexoxo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 🔗 Links

- **GitHub**: [iamrealguexoxo/SteamChecker](https://github.com/iamrealguexoxo/SteamChecker)
- **Author**: iamrealguexoxo
- **Last Updated**: November 2025
