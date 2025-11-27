from __future__ import annotations

import os
import sys
from dataclasses import asdict
from typing import List, Optional

from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QBrush, QColor, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QInputDialog,
    QDialog,
)

from .core import SteamWorkshopCore, compare_mod_ids, CheckResult


class CheckWorker(QThread):
    progress = Signal(int, int, object)  # idx, total, CheckResult
    finished = Signal(dict)  # workshop_results map wid -> [modIds]

    def __init__(self, ids: List[str], parent: Optional[QObject] = None):
        super().__init__(parent)
        self.ids = ids
        self.core = SteamWorkshopCore()
        self._stop = False

    def run(self):
        self.core.workshop_results.clear()
        for idx, total, res in self.core.check_many_iter(self.ids):
            if self._stop:
                break
            self.progress.emit(idx, total, res)
        self.finished.emit(self.core.workshop_results)

    def stop(self):
        self._stop = True


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Über dieses Tool")
        self.setModal(True)
        self.resize(360, 300)

        # Layout
        root = QVBoxLayout(self)
        self.label_gif = QLabel()
        self.label_gif.setAlignment(Qt.AlignCenter)
        root.addWidget(self.label_gif)
        root.addWidget(QLabel("made with ♥ by iamguexoxo"))

        # Animated GIF (optional)
        try:
            from PySide6.QtGui import QMovie

            gif_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "bart.gif")
            if os.path.exists(gif_path):
                movie = QMovie(gif_path)
                self.label_gif.setMovie(movie)
                movie.start()
            else:
                self.label_gif.setText("Bart GIF nicht gefunden.\nSpeichere 'bart.gif' unter python_steam_checker/assets/")
        except Exception:
            self.label_gif.setText("GIF konnte nicht geladen werden.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Workshop Checker (Python Qt)")
        self.resize(1000, 700)

        # State
        self.worker: Optional[CheckWorker] = None
        self.results: List[CheckResult] = []
        self.workshop_map: dict[str, str] = {}

        # Root widget
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # IDs input
        root.addWidget(QLabel("Workshop-IDs (mit ';' trennen):"))
        self.txt_ids = QPlainTextEdit()
        self.txt_ids.setPlaceholderText("2709866494;3445949422;3445362877")
        self.txt_ids.setFixedHeight(70)
        root.addWidget(self.txt_ids)

        # Buttons row
        row_btns = QHBoxLayout()
        self.btn_check = QPushButton("Prüfen")
        self.btn_check.clicked.connect(self.on_check)
        row_btns.addWidget(self.btn_check)

        self.btn_remove = QPushButton("Warnungs-Mods entfernen")
        self.btn_remove.clicked.connect(self.on_remove_warnings)
        row_btns.addWidget(self.btn_remove)

        self.btn_compare = QPushButton("Mod-IDs vergleichen")
        self.btn_compare.clicked.connect(self.on_compare)
        row_btns.addWidget(self.btn_compare)

        self.btn_about = QPushButton("ℹ Über")
        self.btn_about.clicked.connect(self.on_about)
        row_btns.addWidget(self.btn_about)

        # Cancel and Theme toggle on the right side
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.on_cancel)
        row_btns.addWidget(self.btn_cancel)

        self.btn_theme = QToolButton()
        self.btn_theme.setText("☀️")  # shows action to switch to Light (current: Dark)
        self.btn_theme.setToolTip("Theme wechseln (Hell/Dunkel)")
        self.btn_theme.clicked.connect(self.on_toggle_theme)
        row_btns.addWidget(self.btn_theme)

        row_btns.addStretch(1)
        root.addLayout(row_btns)

        # Progress + status
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        root.addWidget(self.progress)
        self.lbl_status = QLabel("Bereit.")
        root.addWidget(self.lbl_status)

        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Workshop-ID", "Status", "Titel + Mod-ID(s)", "Warnung"])
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table)

        # Summary + cleaned list
        self.lbl_summary = QLabel("")
        root.addWidget(self.lbl_summary)

        row_clean = QHBoxLayout()
        row_clean.addWidget(QLabel("Bereinigte Liste:"))
        self.txt_clean = QLineEdit()
        row_clean.addWidget(self.txt_clean)
        self.btn_copy = QPushButton("In Zwischenablage kopieren")
        self.btn_copy.clicked.connect(self.on_copy)
        row_clean.addWidget(self.btn_copy)
        root.addLayout(row_clean)

        self._theme = 'dark'
        self.apply_dark_theme()

    def apply_dark_theme(self):
        # Simple dark palette via stylesheet
        self.setStyleSheet(
            """
            QWidget { background-color: #1e1e1e; color: #e6e6e6; }
            QPlainTextEdit, QLineEdit { background: #151515; color: #e6e6e6; border: 1px solid #333; }
            QPushButton { background: #2b2b2b; color: #e6e6e6; padding: 6px; border: 1px solid #3a3a3a; }
            QPushButton:hover { background: #3a3a3a; }
            QPushButton:pressed { background: #1f1f1f; }
            QTableWidget { background: #141414; gridline-color: #333; }
            QHeaderView::section { background: #262626; color: #e6e6e6; padding: 4px; }
            QProgressBar { background: #151515; border: 1px solid #333; padding: 1px; }
            QProgressBar::chunk { background: #00bcd4; }
            """
        )
        self._theme = 'dark'
        self.btn_theme.setText("☀️")

    def apply_light_theme(self):
        self.setStyleSheet(
            """
            QWidget { background-color: #f2f2f2; color: #222; }
            QPlainTextEdit, QLineEdit { background: #ffffff; color: #222; border: 1px solid #cccccc; }
            QPushButton { background: #e6e6e6; color: #222; padding: 6px; border: 1px solid #cfcfcf; }
            QPushButton:hover { background: #e0e0e0; }
            QPushButton:pressed { background: #d5d5d5; }
            QTableWidget { background: #ffffff; gridline-color: #cccccc; color: #222; }
            QHeaderView::section { background: #eaeaea; color: #222; padding: 4px; }
            QProgressBar { background: #ffffff; border: 1px solid #cccccc; padding: 1px; }
            QProgressBar::chunk { background: #1976d2; }
            """
        )
        self._theme = 'light'
        self.btn_theme.setText("🌙")

    # UI actions
    def on_check(self):
        raw = self.txt_ids.toPlainText().strip()
        if not raw:
            self.lbl_status.setText("❌ Keine IDs eingegeben!")
            return
        ids = [s.strip() for s in raw.split(";") if s.strip().isdigit()]
        if not ids:
            self.lbl_status.setText("❌ Keine gültigen IDs gefunden!")
            return

        # Reset UI
        self.results = []
        self.workshop_map = {}
        self.table.setRowCount(0)
        self.progress.setRange(0, len(ids))
        self.progress.setValue(0)
        self.lbl_status.setText(f"Prüfe {len(ids)} Items…")
        self.lbl_summary.setText("")
        self.txt_clean.clear()
        self.set_buttons_enabled(False)
        self.btn_cancel.setEnabled(True)

        # Start worker
        self.worker = CheckWorker(ids)
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def set_buttons_enabled(self, enabled: bool):
        self.btn_check.setEnabled(enabled)
        self.btn_remove.setEnabled(enabled)
        self.btn_compare.setEnabled(enabled)
        # About and theme remain available

    def on_worker_progress(self, idx: int, total: int, res_obj: object):
        res: CheckResult = res_obj  # type: ignore
        self.results.append(res)

        # Add row
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(res.id))
        self.table.setItem(row, 1, QTableWidgetItem(res.status))
        self.table.setItem(row, 2, QTableWidgetItem(res.title_with_mod or ""))
        self.table.setItem(row, 3, QTableWidgetItem(res.warning or ""))

        # Color by status
        color = None
        if res.status == "OK" and res.warning:
            color = QColor("#ffc107")  # warn
        elif res.status == "OK":
            color = QColor("#8bc34a")  # ok
        elif res.status == "GELÖSCHT" or res.status not in ("OK", "GELÖSCHT", "NO_TITLE"):
            color = QColor("#ef5350")  # red
        elif res.status == "NO_TITLE":
            color = QColor("#ffb74d")  # orange

        if color is not None:
            brush = QBrush(color)
            for c in range(4):
                item = self.table.item(row, c)
                if item:
                    item.setForeground(brush)

        # Progress + status
        self.progress.setValue(idx)
        self.lbl_status.setText(f"Abruf {idx}/{total} – ID {res.id}")

        # Live summary
        ok = len([r for r in self.results if r.status == "OK"])
        no_title = len([r for r in self.results if r.status == "NO_TITLE"])
        deleted = len([r for r in self.results if r.status == "GELÖSCHT"])
        errors = len([r for r in self.results if r.status not in ("OK", "GELÖSCHT", "NO_TITLE")])
        self.lbl_summary.setText(
            f"✅ OK: {ok}    ⚠️ Kein Titel: {no_title}    ❌ GELÖSCHT: {deleted}    🚫 Fehler: {errors}"
        )

    def on_worker_finished(self, workshop_map: dict):
        self.workshop_map = workshop_map
        if getattr(self, "_canceled", False):
            self.lbl_status.setText("Abgebrochen.")
        else:
            self.lbl_status.setText("Fertig.")
        self.set_buttons_enabled(True)
        self.btn_cancel.setEnabled(False)
        self._canceled = False

    def on_remove_warnings(self):
        if not self.results:
            self.lbl_status.setText("Bitte zuerst prüfen.")
            return
        ok = [r for r in self.results if r.status == "OK"]
        with_warn = {r.id for r in ok if r.warning}
        remaining = [r.id for r in ok if r.id not in with_warn]
        self.txt_clean.setText(";".join(remaining))
        self.lbl_status.setText(
            f"Entfernt: {len(with_warn)} – Verbleibend: {len(remaining)}" if with_warn else "Keine Warnungen gefunden."
        )

    def on_compare(self):
        if not self.workshop_map:
            self.lbl_status.setText("Bitte zuerst prüfen.")
            return
        text, ok = QInputDialog.getText(self, "Mod-IDs vergleichen", "Mod-IDs (mit ';' trennen):")
        if not ok:
            return
        config_ids = [s.strip() for s in text.split(";") if s.strip()]
        found, missing, extra = compare_mod_ids(config_ids, self.workshop_map)
        lines = [
            f"✅ VORHANDEN: {len(found)}",
            f"❌ FEHLT: {len(missing)}",
            f"ℹ️ ZUSÄTZLICH: {len(extra)}",
        ]
        if missing:
            lines.append("\nFehlende Mod-IDs:")
            lines.extend([f"  - {m}" for m in missing])
        if extra:
            lines.append("\nZusätzliche Workshop-Mods (nicht in deiner Liste):")
            lines.extend([f"  [{wid}] {mid}" for wid, mid in extra])
        self.lbl_status.setText("Vergleich abgeschlossen.")
        # Show as a small dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Vergleich")
        lay = QVBoxLayout(dlg)
        lbl = QLabel("\n".join(lines))
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(lbl)
        dlg.resize(520, 400)
        dlg.exec()

    def on_copy(self):
        s = self.txt_clean.text().strip()
        if not s:
            self.lbl_status.setText("Keine bereinigte Liste vorhanden.")
            return
        QGuiApplication.clipboard().setText(s)
        self.lbl_status.setText("Bereinigte Liste kopiert.")

    def on_about(self):
        AboutDialog(self).exec()

    def on_cancel(self):
        if self.worker and self.worker.isRunning():
            self._canceled = True
            self.worker.stop()
            self.lbl_status.setText("Abbruch angefordert…")
            self.btn_cancel.setEnabled(False)

    def on_toggle_theme(self):
        if self._theme == 'dark':
            self.apply_light_theme()
        else:
            self.apply_dark_theme()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
