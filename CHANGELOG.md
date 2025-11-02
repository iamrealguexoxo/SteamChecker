# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

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

