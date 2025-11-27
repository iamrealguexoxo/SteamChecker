from __future__ import annotations

import os
import sys
from dataclasses import asdict
from typing import List, Optional

from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication, QColor
from PySide6.QtQml import QQmlApplicationEngine

from .core import SteamWorkshopCore, compare_mod_ids, CheckResult


class ResultModel(QAbstractListModel):
    RoleId = Qt.UserRole + 1
    RoleStatus = Qt.UserRole + 2
    RoleTitle = Qt.UserRole + 3
    RoleWarning = Qt.UserRole + 4
    RoleColor = Qt.UserRole + 5
    RoleCompare = Qt.UserRole + 6

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._items: List[CheckResult] = []
        self._cmp_tags: dict[str, str] = {}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None
        item = self._items[index.row()]

        if role == self.RoleId:
            return item.id
        if role == self.RoleStatus:
            return item.status
        if role == self.RoleTitle:
            return item.title_with_mod or ""
        if role == self.RoleWarning:
            return item.warning or ""
        if role == self.RoleColor:
            # Return a hex color string to bind in QML
            if item.status == "OK" and item.warning:
                return "#ffc107"  # warn
            elif item.status == "OK":
                return "#8bc34a"  # ok
            elif item.status == "NO_TITLE":
                return "#ffb74d"  # orange
            else:
                # deleted or error
                if item.status == "GELÖSCHT" or item.status not in ("OK", "GELÖSCHT", "NO_TITLE"):
                    return "#ef5350"  # red
                return "#e6e6e6"
        if role == self.RoleCompare:
            return self._cmp_tags.get(item.id, "")
        return None

    def roleNames(self):  # type: ignore[override]
        return {
            self.RoleId: b"wid",
            self.RoleStatus: b"status",
            self.RoleTitle: b"title",
            self.RoleWarning: b"warning",
            self.RoleColor: b"fgColor",
            self.RoleCompare: b"compareTag",
        }

    def clear(self):
        if not self._items:
            return
        self.beginResetModel()
        self._items.clear()
        self._cmp_tags.clear()
        self.endResetModel()

    def addResult(self, res: CheckResult):
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append(res)
        self.endInsertRows()

    def items(self) -> List[CheckResult]:
        return list(self._items)

    def clearCompareTags(self):
        if not self._cmp_tags:
            return
        self._cmp_tags.clear()
        if self._items:
            top_left = self.index(0, 0)
            bottom_right = self.index(len(self._items) - 1, 0)
            self.dataChanged.emit(top_left, bottom_right, [self.RoleCompare])

    def _index_by_wid(self, wid: str) -> int:
        for i, it in enumerate(self._items):
            if it.id == wid:
                return i
        return -1

    def setCompareTag(self, wid: str, tag: str):
        row = self._index_by_wid(wid)
        if row < 0:
            return
        prev = self._cmp_tags.get(wid)
        if prev == tag:
            return
        self._cmp_tags[wid] = tag
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx, [self.RoleCompare])


class CheckWorkerSignals(QObject):
    progress = Signal(int, int, object)  # idx, total, CheckResult
    finished = Signal(dict)  # workshop_results map


class CheckWorker(QObject):
    def __init__(self, ids: List[str]):
        super().__init__()
        self.ids = ids
        self.core = SteamWorkshopCore()
        self.signals = CheckWorkerSignals()
        self._stop = False

    @Slot()
    def run(self):
        self.core.workshop_results.clear()
        for idx, total, res in self.core.check_many_iter(self.ids):
            if self._stop:
                break
            self.signals.progress.emit(idx, total, res)
        self.signals.finished.emit(self.core.workshop_results)

    def stop(self):
        self._stop = True


class Controller(QObject):
    # UI update signals
    progressChanged = Signal(int, int)
    statusChanged = Signal(str)
    summaryChanged = Signal(str)
    cleanedListChanged = Signal(str)
    comparisonReady = Signal(str)
    runningChanged = Signal(bool)
    finished = Signal()

    def __init__(self, model: ResultModel):
        super().__init__()
        self.model = model
        self.results: List[CheckResult] = []
        self.workshop_map: dict[str, str] = {}
        self._running = False
        self._canceled = False
        self._cleaned_cache = ""
        self._thread = None  # type: ignore
        self._worker: Optional[CheckWorker] = None

    @Slot(str)
    def startCheck(self, raw_ids: str):
        raw = (raw_ids or "").strip()
        if not raw:
            self.statusChanged.emit("❌ Keine IDs eingegeben!")
            return
        ids = [s.strip() for s in raw.split(";") if s.strip().isdigit()]
        if not ids:
            self.statusChanged.emit("❌ Keine gültigen IDs gefunden!")
            return

        # Reset state
        self.results = []
        self.workshop_map = {}
        self.model.clear()
        self.model.clearCompareTags()
        self.progressChanged.emit(0, len(ids))
        self.summaryChanged.emit("")
        self.cleanedListChanged.emit("")
        self.statusChanged.emit(f"Prüfe {len(ids)} Items…")
        self._canceled = False
        self._running = True
        self.runningChanged.emit(True)

        # Start worker in QThread
        from PySide6.QtCore import QThread

        self._thread = QThread()
        self._worker = CheckWorker(ids)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.signals.progress.connect(self._on_worker_progress)
        self._worker.signals.finished.connect(self._on_worker_finished)
        # Clean up thread when finished
        self._worker.signals.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    @Slot()
    def cancel(self):
        if self._worker is not None:
            self._canceled = True
            self._worker.stop()
            self.statusChanged.emit("Abbruch angefordert…")

    @Slot()
    def removeWarnings(self):
        if not self.results:
            self.statusChanged.emit("Bitte zuerst prüfen.")
            return
        ok = [r for r in self.results if r.status == "OK"]
        with_warn = {r.id for r in ok if r.warning}
        remaining = [r.id for r in ok if r.id not in with_warn]
        cleaned = ";".join(remaining)
        self._cleaned_cache = cleaned
        self.cleanedListChanged.emit(cleaned)
        if with_warn:
            self.statusChanged.emit(f"Entfernt: {len(with_warn)} – Verbleibend: {len(remaining)}")
        else:
            self.statusChanged.emit("Keine Warnungen gefunden.")

    @Slot(str)
    def compareModIds(self, config_ids_text: str):
        if not self.workshop_map:
            self.statusChanged.emit("Bitte zuerst prüfen.")
            return
        config_ids = [s.strip() for s in (config_ids_text or "").split(";") if s.strip()]
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
        self.comparisonReady.emit("\n".join(lines))
        self.statusChanged.emit("Vergleich abgeschlossen.")

        # Mark rows according to comparison for quick visual scanning
        cfg_set = set(config_ids)
        for r in self.results:
            mids = r.mod_ids or []
            if not mids:
                self.model.setCompareTag(r.id, "none")
                continue
            in_cfg = [m in cfg_set for m in mids]
            if all(in_cfg):
                tag = "match"
            elif any(in_cfg):
                tag = "mixed"
            else:
                tag = "extra"
            self.model.setCompareTag(r.id, tag)

    @Slot()
    def copyCleaned(self):
        s = self._cleaned_cache.strip()
        if not s:
            self.statusChanged.emit("Keine bereinigte Liste vorhanden.")
            return
        QGuiApplication.clipboard().setText(s)
        self.statusChanged.emit("Bereinigte Liste kopiert.")

    # Internal slots
    @Slot(int, int, object)
    def _on_worker_progress(self, idx: int, total: int, res_obj: object):
        res: CheckResult = res_obj  # type: ignore
        self.results.append(res)
        self.model.addResult(res)

        self.progressChanged.emit(idx, total)
        self.statusChanged.emit(f"Abruf {idx}/{total} – ID {res.id}")

        ok = len([r for r in self.results if r.status == "OK"]) 
        no_title = len([r for r in self.results if r.status == "NO_TITLE"]) 
        deleted = len([r for r in self.results if r.status == "GELÖSCHT"]) 
        errors = len([r for r in self.results if r.status not in ("OK", "GELÖSCHT", "NO_TITLE")])
        self.summaryChanged.emit(
            f"✅ OK: {ok}    ⚠️ Kein Titel: {no_title}    ❌ GELÖSCHT: {deleted}    🚫 Fehler: {errors}"
        )

    @Slot(dict)
    def _on_worker_finished(self, workshop_map: dict):
        self.workshop_map = workshop_map
        if self._canceled:
            self.statusChanged.emit("Abgebrochen.")
        else:
            self.statusChanged.emit("Fertig.")
        self._running = False
        self.runningChanged.emit(False)
        self.finished.emit()


def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # Model + controller
    model = ResultModel()
    controller = Controller(model)

    # Expose context properties
    ctx = engine.rootContext()
    ctx.setContextProperty("resultModel", model)
    ctx.setContextProperty("controller", controller)
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    # Provide absolute file URL for QML AnimatedImage
    bart_path = os.path.join(assets_dir, "bart.gif")
    has_bart = os.path.exists(bart_path)
    if has_bart:
        # Ensure file:/// URL with forward slashes
        bart_url = "file:///" + bart_path.replace("\\", "/")
    else:
        bart_url = ""
    ctx.setContextProperty("assetsDir", assets_dir.replace("\\", "/"))
    ctx.setContextProperty("bartGifUrl", bart_url)
    ctx.setContextProperty("hasBartGif", has_bart)

    # Load QML
    qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qml", "Main.qml")
    engine.load(qml_path)
    if not engine.rootObjects():
        sys.exit("Failed to load QML UI")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
