# Steam Workshop Item Checker für Zomboid

Ein modernes Tool zum Prüfen und Verwalten von Steam Workshop Items. Verfügbar als **CLI** (Kommandozeile) und **WPF GUI** (grafische Oberfläche).

**English version below — Deutsche Version zuerst.**

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

**Start der WPF-App:**
```powershell
cd .\SteamCheckerWPF
dotnet build
dotnet run
```

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
    ├── App.xaml                # App config
    └── SteamCheckerWPF.csproj  # GUI project file
```

---

## 🤝 Contributions

Issues and pull requests are welcome. If you have improvements, new patterns for detection, or UI enhancements, feel free to contribute!

---

## 📄 License

Everything is free to use – go for it!

---

## 🔗 Links

- **GitHub**: [iamrealguexoxo/SteamChecker](https://github.com/iamrealguexoxo/SteamChecker)
- **Author**: iamrealguexoxo
- **Last Updated**: October 2025
