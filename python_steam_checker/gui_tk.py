import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List

from .core import SteamWorkshopCore, compare_mod_ids


class SteamCheckerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Steam Workshop Checker (Python GUI)")
        self.geometry("980x640")

        self.core = SteamWorkshopCore()

        self._build_ui()
        self._results_cache = []  # store last results

    def _build_ui(self):
        # --- Gray theme setup (robust, no external deps) ---
        BG = "#1e1e1e"      # base background (dark gray)
        FG = "#e6e6e6"      # primary text
        ACCENT = "#00bcd4"  # cyan accent
        BTN_BG = "#2b2b2b"  # button base bg
        BTN_BG_HOVER = "#3a3a3a"
        BTN_BG_PRESSED = "#1f1f1f"
        BTN_BG_DISABLED = "#2a2a2a"
        WARN = "#ffc107"    # amber
        BAD = "#ef5350"     # red
        OKC = "#8bc34a"     # green

        self.configure(bg=BG)
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure('Dark.TFrame', background=BG)
        style.configure('Dark.TLabel', background=BG, foreground=FG)
        style.configure('Dark.TButton', background=BTN_BG, foreground=FG, padding=6, relief='flat')
        style.map('Dark.TButton',
                  background=[('active', BTN_BG_HOVER), ('pressed', BTN_BG_PRESSED), ('disabled', BTN_BG_DISABLED)],
                  foreground=[('disabled', '#9e9e9e')])
        style.configure('Dark.TEntry', fieldbackground='#1a1a1a', background='#1a1a1a', foreground=FG)
        style.configure('Dark.Treeview', background='#141414', fieldbackground='#141414', foreground=FG, bordercolor='#333333', rowheight=22)
        style.map('Dark.Treeview', background=[('selected', '#2d3e50')], foreground=[('selected', '#ffffff')])
        # Headings
        style.configure('Treeview.Heading', background='#262626', foreground=FG)
        style.configure('Dark.Horizontal.TProgressbar', background=ACCENT, troughcolor=BG)

        top = ttk.Frame(self, style='Dark.TFrame')
        top.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(top, text="Workshop-IDs (mit ';' trennen):", style='Dark.TLabel').pack(anchor=tk.W)
        self.ids_text = tk.Text(top, height=3, bg='#151515', fg=FG, insertbackground=FG, highlightthickness=1, highlightbackground="#333333", relief='solid', borderwidth=1)
        self.ids_text.pack(fill=tk.X)

        btns = ttk.Frame(top, style='Dark.TFrame')
        btns.pack(fill=tk.X, pady=(6, 0))

        self.btn_check = ttk.Button(btns, text="Prüfen", command=self.on_check, style='Dark.TButton')
        self.btn_check.pack(side=tk.LEFT)

        self.btn_remove_warn = ttk.Button(btns, text="Warnungs-Mods entfernen", command=self.on_remove_warnings, style='Dark.TButton')
        self.btn_remove_warn.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_compare = ttk.Button(btns, text="Mod-IDs vergleichen", command=self.on_compare, style='Dark.TButton')
        self.btn_compare.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_about = ttk.Button(btns, text="ℹ Über", command=self.on_about, style='Dark.TButton')
        self.btn_about.pack(side=tk.RIGHT)

        # Progress + Status
        prog_row = ttk.Frame(top, style='Dark.TFrame')
        prog_row.pack(fill=tk.X, pady=(6, 0))
        self.prog = ttk.Progressbar(prog_row, orient="horizontal", mode="determinate", style='Dark.Horizontal.TProgressbar')
        self.prog.pack(fill=tk.X)
        self.status_var = tk.StringVar(value="Bereit.")
        ttk.Label(top, textvariable=self.status_var, style='Dark.TLabel').pack(anchor=tk.W, pady=(4, 0))

        mid = ttk.Frame(self, style='Dark.TFrame')
        mid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "status", "title", "warning")
        self.tree = ttk.Treeview(mid, columns=columns, show="headings", style='Dark.Treeview')
        self.tree.heading("id", text="Workshop-ID")
        self.tree.heading("status", text="Status")
        self.tree.heading("title", text="Titel + Mod-ID")
        self.tree.heading("warning", text="Warnung")

        self.tree.column("id", width=140)
        self.tree.column("status", width=90)
        self.tree.column("title", width=540)
        self.tree.column("warning", width=140)

        vsb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        bottom = ttk.Frame(self, style='Dark.TFrame')
        bottom.pack(fill=tk.X, padx=10, pady=8)

        self.summary_var = tk.StringVar(value="")
        ttk.Label(bottom, textvariable=self.summary_var, style='Dark.TLabel').pack(anchor=tk.W)

        self.clean_var = tk.StringVar(value="")
        ttk.Label(bottom, text="Bereinigte Liste:", style='Dark.TLabel').pack(anchor=tk.W, pady=(8, 0))
        self.clean_entry = ttk.Entry(bottom, textvariable=self.clean_var, style='Dark.TEntry')
        self.clean_entry.pack(fill=tk.X)

        self.btn_copy = ttk.Button(bottom, text="In Zwischenablage kopieren", command=self.on_copy_clean, style='Dark.TButton')
        self.btn_copy.pack(anchor=tk.E, pady=(6, 0))

        # Styles for row tags on dark background
        self.tree.tag_configure("ok", background="#141414", foreground=OKC)
        self.tree.tag_configure("warn", background="#141414", foreground=WARN)
        self.tree.tag_configure("deleted", background="#141414", foreground=BAD)
        self.tree.tag_configure("error", background="#141414", foreground=BAD)
        self.tree.tag_configure("notitle", background="#141414", foreground="#ffb74d")

    def on_check(self):
        raw = self.ids_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("Hinweis", "Bitte Workshop-IDs angeben (mit ';' trennen).")
            return

        ids = [x.strip() for x in raw.split(";") if x.strip().isdigit()]
        if not ids:
            messagebox.showwarning("Hinweis", "Keine gültigen, numerischen IDs gefunden.")
            return

        self.status_var.set(f"Prüfe {len(ids)} Items… Bitte warten…")
        self.btn_check.configure(state=tk.DISABLED)
        threading.Thread(target=self._check_bg, args=(ids,), daemon=True).start()

    def _check_bg(self, ids: List[str]):
        # Initialize
        self._results_cache = []
        ok: List = []
        deleted: List = []
        notitle: List = []
        errors: List = []

        def init_ui(total: int):
            self.tree.delete(*self.tree.get_children())
            self.prog.configure(maximum=total, value=0)
            self.summary_var.set("")
            self.clean_var.set("")

        self.after(0, init_ui, len(ids))

        for idx, total, r in self.core.check_many_iter(ids):
            # Update aggregations
            self._results_cache.append(r)
            if r.status == "OK":
                ok.append(r)
            elif r.status == "GELÖSCHT":
                deleted.append(r)
            elif r.status == "NO_TITLE":
                notitle.append(r)
            else:
                errors.append(r)

            def add_row(rr=r, i=idx, t=total):
                tag = "ok"
                if rr.status == "GELÖSCHT":
                    tag = "deleted"
                elif rr.status == "NO_TITLE":
                    tag = "notitle"
                elif rr.status not in ("OK", "GELÖSCHT", "NO_TITLE"):
                    tag = "error"
                elif rr.warning:
                    tag = "warn"

                self.tree.insert("", tk.END, values=(rr.id, rr.status, rr.title_with_mod or "", rr.warning or ""), tags=(tag,))
                self.prog.configure(value=i)
                self.status_var.set(f"Abruf {i}/{t} – ID {rr.id}")
                self.summary_var.set(
                    f"✅ OK: {len(ok)}    ⚠️ Kein Titel: {len(notitle)}    ❌ GELÖSCHT: {len(deleted)}    🚫 Fehler: {len(errors)}"
                )

            self.after(0, add_row)

        def finish_ui():
            self.status_var.set("Fertig.")
            self.btn_check.configure(state=tk.NORMAL)
            self.btn_remove_warn.configure(state=tk.NORMAL)
            self.btn_compare.configure(state=tk.NORMAL)

        self.after(0, finish_ui)

    def on_remove_warnings(self):
        if not self._results_cache:
            messagebox.showinfo("Info", "Bitte zuerst prüfen.")
            return
        ok = [r for r in self._results_cache if r.status == "OK"]
        with_warn_ids = {r.id for r in ok if r.warning}
        remaining = [r.id for r in ok if r.id not in with_warn_ids]
        self.clean_var.set(";".join(remaining))
        if with_warn_ids:
            messagebox.showinfo("Bereinigt", f"Entfernt: {len(with_warn_ids)}    Verbleibend: {len(remaining)}")
        else:
            messagebox.showinfo("Bereinigt", "Es gibt keine Warnungen — nichts zu entfernen.")

    def on_compare(self):
        if not self.core.workshop_results:
            messagebox.showinfo("Info", "Bitte zuerst prüfen, damit Mod-IDs vorliegen.")
            return
        s = simpledialog.askstring("Mod-IDs vergleichen", "Mod-IDs eingeben (mit ';' trennen):", parent=self)
        if s is None:
            return
        ids = [x.strip() for x in s.split(";") if x.strip()]
        found, missing, extra = compare_mod_ids(ids, self.core.workshop_results)

        msg_lines = [
            f"✅ VORHANDEN: {len(found)}",
            f"❌ FEHLT: {len(missing)}",
            f"ℹ️  ZUSÄTZLICH: {len(extra)}",
        ]
        if missing:
            msg_lines.append("\nFehlende Mod-IDs:")
            msg_lines.extend([f"  - {m}" for m in missing])
        if extra:
            msg_lines.append("\nZusätzliche Workshop-Mods (nicht in deiner Liste):")
            msg_lines.extend([f"  [{wid}] {mid}" for wid, mid in extra])

        messagebox.showinfo("Vergleich", "\n".join(msg_lines))

    def on_copy_clean(self):
        s = self.clean_var.get().strip()
        if not s:
            messagebox.showinfo("Info", "Keine bereinigte Liste vorhanden.")
            return
        self.clipboard_clear()
        self.clipboard_append(s)
        messagebox.showinfo("Kopiert", "Bereinigte Liste in die Zwischenablage kopiert.")

    def on_about(self):
        AboutWindow(self)


class AboutWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Über dieses Tool")
        self.resizable(False, False)
        # Gray background (aligned with main window)
        BG = "#1e1e1e"; FG = "#e6e6e6"
        self.configure(padx=16, pady=12, bg=BG)

        # Try to load animated GIF frames
        gif_path = self._resolve_gif_path()
        self.frames = []
        self.frame_index = 0
        self.anim_label = tk.Label(self, bg=BG)
        self.anim_label.pack()
        tk.Label(self, text="made with ♥ by iamguexoxo", bg=BG, fg=FG).pack(pady=(8, 0))

        if gif_path and os.path.exists(gif_path):
            try:
                # Load frames from the GIF using Tk's PhotoImage with index
                # Keep loading sequentially until it fails
                i = 0
                while True:
                    frame = tk.PhotoImage(file=gif_path, format=f"gif -index {i}")
                    self.frames.append(frame)
                    i += 1
            except Exception:
                pass

        if self.frames:
            self._animate()
        else:
            # Fallback text if GIF not found
            tk.Label(self, text="Bart GIF nicht gefunden.\nLege eine Datei 'bart.gif' unter\npython_steam_checker/assets/ ab.", justify=tk.CENTER, bg=BG, fg=FG).pack(pady=(8, 0))
        ttk.Button(self, text="Schließen", command=self.destroy).pack(pady=(10, 0))

    def _resolve_gif_path(self) -> str:
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "assets", "bart.gif")

    def _animate(self):
        if not self.frames:
            return
        self.anim_label.configure(image=self.frames[self.frame_index])
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        # Typical GIF frame delay ~ 100 ms
        self.after(100, self._animate)


def main():
    app = SteamCheckerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
