import os
import platform
import string
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import ttk, messagebox, simpledialog
from typing import Optional

import tkinter as tk

from file_explorer import (
    NativeFilesystem, DirectoryNavigator,
    search_by_name, SearchOptions,
    get_metadata, get_size_formatted,
    OperationHistory,
    CreateFileCommand, CreateDirectoryCommand,
    DeleteFileCommand, DeleteDirectoryCommand,
    RenameCommand, CopyCommand, MoveCommand,
    ConfigManager, ConflictStrategy,
    setup_logging, PathNotFoundError, PermissionDeniedError,
)

# ── Icons ────────────────────────────────────────────────────────────

DIR_ICON = "\U0001F4C1"
FILE_ICONS = {
    "txt": "\U0001F4DD", "md": "\U0001F4D6", "py": "\U0001F40D",
    "js": "\U0001F310", "ts": "\U0001F310", "html": "\U0001F310",
    "css": "\U0001F3A8", "json": "\u2699", "xml": "\u2699",
    "yaml": "\u2699", "yml": "\u2699", "csv": "\U0001F4CA",
    "pdf": "\U0001F4D1", "doc": "\U0001F4DD", "docx": "\U0001F4DD",
    "xls": "\U0001F4CA", "xlsx": "\U0001F4CA", "ppt": "\U0001F4CA",
    "pptx": "\U0001F4CA",
    "png": "\U0001F5BC", "jpg": "\U0001F5BC", "jpeg": "\U0001F5BC",
    "gif": "\U0001F5BC", "bmp": "\U0001F5BC", "ico": "\U0001F5BC",
    "svg": "\U0001F5BC", "webp": "\U0001F5BC",
    "mp3": "\U0001F3B5", "wav": "\U0001F3B5", "flac": "\U0001F3B5",
    "aac": "\U0001F3B5", "ogg": "\U0001F3B5",
    "mp4": "\U0001F3AC", "avi": "\U0001F3AC", "mkv": "\U0001F3AC",
    "mov": "\U0001F3AC", "wmv": "\U0001F3AC",
    "zip": "\U0001F4E6", "rar": "\U0001F4E6", "7z": "\U0001F4E6",
    "gz": "\U0001F4E6", "tar": "\U0001F4E6",
    "exe": "\u2699", "msi": "\u2699", "dll": "\u2699",
    "lnk": "\U0001F517", "url": "\U0001F517",
    "iso": "\U0001F4BF", "img": "\U0001F4BF",
    "ttf": "\U0001F520", "otf": "\U0001F520",
    "bat": "\U0001F4AC", "ps1": "\U0001F4AC", "sh": "\U0001F4AC",
    "log": "\U0001F4DD", "tmp": "\U0001F4DD", "ini": "\u2699",
    "cfg": "\u2699",
}
DEFAULT_FILE_ICON = "\U0001F4C4"


def file_icon(path: Path) -> str:
    if path.is_dir():
        return DIR_ICON
    return FILE_ICONS.get(path.suffix.lstrip(".").lower(), DEFAULT_FILE_ICON)


# ── Theme ────────────────────────────────────────────────────────────

FONT = "Segoe UI"
FONT_MONO = "Consolas"
BG = "#ffffff"
FG = "#1a1a1a"
SEL_BG = "#0078d4"
SEL_FG = "#ffffff"
HOVER_BG = "#e5f3ff"
ROW_ALT = "#f7f7f7"
HEADER_BG = "#f0f0f0"
BORDER = "#e0e0e0"
STATUS_BG = "#f5f5f5"


def apply_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", font=(FONT, 9), background=BG, foreground=FG)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=FG)
    style.configure("TButton", font=(FONT, 9), padding=(8, 3), relief=tk.FLAT,
                    background=HEADER_BG, foreground=FG)
    style.map("TButton", background=[("active", "#d0d0d0"), ("pressed", "#c0c0c0")])
    style.configure("Toolbutton.TButton", font=(FONT, 9), padding=(6, 2), relief=tk.FLAT,
                    background=BG)
    style.map("Toolbutton.TButton", background=[("active", HOVER_BG)])
    style.configure("Treeview", font=(FONT, 9), background=BG, foreground=FG,
                    fieldbackground=BG, rowheight=26)
    style.map("Treeview", background=[("selected", SEL_BG)], foreground=[("selected", SEL_FG)])
    style.configure("Treeview.Heading", font=(FONT, 9, "bold"), background=HEADER_BG,
                    foreground="#333333", padding=(6, 4), relief=tk.FLAT)
    style.map("Treeview.Heading", background=[("active", "#e4e4e4")])
    style.configure("VSeparator.TSeparator", background=BORDER)
    style.configure("Sash", background=BORDER, sashthickness=2)
    style.configure("Status.TLabel", font=(FONT, 9), background=STATUS_BG, foreground="#555555")
    style.configure("Breadcrumb.TFrame", background="#f8f8f8")
    style.configure("Details.TLabel", font=(FONT, 9), background="#fafafa", foreground="#333333")
    style.configure("Details.TFrame", background="#fafafa", relief=tk.SUNKEN, borderwidth=1)

    root.option_add("*Font", (FONT, 9))
    if platform.system() == "Windows":
        root.option_add("*Menu.font", (FONT, 9))
        root.option_add("*Entry.font", (FONT, 9))


# ── Helpers ──────────────────────────────────────────────────────────

def _list_drives() -> list[str]:
    if platform.system() != "Windows":
        return ["/"]
    return [f"{l}:\\" for l in string.ascii_uppercase if os.path.exists(f"{l}:\\")]


def _friendly_date(ts: float) -> str:
    dt = datetime.fromtimestamp(ts)
    now = datetime.now()
    if dt.date() == now.date():
        return f"Today {dt.strftime('%H:%M')}"
    if dt.date() == (now - timedelta(days=1)).date():
        return f"Yesterday {dt.strftime('%H:%M')}"
    if dt.year == now.year:
        return dt.strftime("%b %d, %H:%M")
    return dt.strftime("%b %d %Y")


def get_file_type(path: Path) -> str:
    if path.is_dir():
        return "Folder"
    ext = path.suffix.lower()
    known = {
        ".txt": "Text Document", ".py": "Python File", ".md": "Markdown",
        ".json": "JSON File", ".csv": "CSV File", ".html": "HTML Document",
        ".css": "Stylesheet", ".js": "JavaScript", ".ts": "TypeScript",
        ".exe": "Application", ".dll": "Application Extension",
        ".zip": "Compressed Folder", ".rar": "Compressed Folder", ".7z": "Compressed Folder",
        ".pdf": "PDF Document", ".png": "PNG Image", ".jpg": "JPEG Image",
        ".jpeg": "JPEG Image", ".gif": "GIF Image", ".ico": "Icon", ".bmp": "BMP Image",
        ".svg": "SVG Image", ".mp3": "MP3 Audio", ".mp4": "MP4 Video", ".avi": "AVI Video",
        ".mkv": "MKV Video", ".mov": "Movie", ".lnk": "Shortcut", ".url": "Internet Shortcut",
        ".doc": "Word Document", ".docx": "Word Document", ".xls": "Excel Spreadsheet",
        ".xlsx": "Excel Spreadsheet", ".ppt": "PowerPoint", ".pptx": "PowerPoint",
        ".iso": "Disc Image", ".ttf": "TrueType Font", ".otf": "OpenType Font",
        ".xml": "XML Document", ".yaml": "YAML File", ".yml": "YAML File",
        ".ini": "Configuration", ".cfg": "Configuration", ".log": "Text Document",
        ".tmp": "Temporary File", ".msi": "Installer Package", ".bat": "Batch Script",
        ".ps1": "PowerShell Script", ".sh": "Shell Script",
        ".wav": "Wave Audio", ".flac": "FLAC Audio", ".aac": "AAC Audio",
        ".wmv": "WMV Video", ".webp": "WebP Image", ".tar": "TAR Archive",
        ".gz": "GZip Archive", ".img": "Disc Image",
    }
    return known.get(ext, f"{ext.upper()} File")


def open_with_os(path: Path) -> None:
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file:\n{e}")


def open_terminal(path: Path) -> None:
    try:
        if platform.system() == "Windows":
            subprocess.run(["start", "cmd"], cwd=str(path), shell=True, check=False)
        elif platform.system() == "Darwin":
            subprocess.run(["open", "-a", "Terminal", str(path)], check=False)
        else:
            subprocess.run(["x-terminal-emulator"], cwd=str(path), check=False)
    except Exception as e:
        messagebox.showerror("Error", f"Could not open terminal:\n{e}")


def copy_to_clipboard(text: str) -> None:
    r = tk.Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(text)
    r.update()
    r.destroy()


# ── Properties Dialog ────────────────────────────────────────────────

class PropertiesDialog(tk.Toplevel):
    def __init__(self, parent, path: Path, fs: NativeFilesystem) -> None:
        super().__init__(parent)
        self.title(f"{path.name} Properties")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        try:
            meta = get_metadata(fs, path)
        except Exception:
            meta = None

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        rows = [("Name:", path.name), ("Path:", str(path.resolve())), ("Type:", get_file_type(path))]
        if meta:
            rows += [
                ("Size:", get_size_formatted(meta.size)),
                ("Created:", _friendly_date(meta.created)),
                ("Modified:", _friendly_date(meta.modified)),
                ("Accessed:", _friendly_date(meta.accessed)),
                ("Hidden:", "Yes" if meta.is_hidden else "No"),
                ("Read-only:", "Yes" if meta.is_readonly else "No"),
            ]

        for i, (label, value) in enumerate(rows):
            ttk.Label(frame, text=label, anchor=tk.E, font=("", 9, "bold")).grid(
                row=i, column=0, sticky=tk.E, padx=(0, 8), pady=2)
            ttk.Label(frame, text=value, anchor=tk.W).grid(
                row=i, column=1, sticky=tk.W, pady=2)

        ttk.Button(frame, text="Close", command=self.destroy).grid(
            row=len(rows), column=0, columnspan=2, pady=(12, 0))
        tw = len(str(path.resolve())) * 7 + 160
        self.geometry(f"{max(tw, 320)}x{30 + len(rows) * 26}")


# ── Breadcrumb Bar ───────────────────────────────────────────────────

class BreadcrumbBar(ttk.Frame):
    def __init__(self, parent, app: "App") -> None:
        super().__init__(parent, style="Breadcrumb.TFrame")
        self.app = app
        self._editing = False

        self.inner = ttk.Frame(self, style="Breadcrumb.TFrame")
        self.inner.pack(fill=tk.X, expand=True, padx=4, pady=2)

        self.entry = ttk.Entry(self)
        self.entry.bind("<Return>", self._on_entry_commit)
        self.entry.bind("<Escape>", self._on_entry_cancel)
        self.entry.bind("<FocusOut>", self._on_entry_cancel)

    def show(self, path: Path) -> None:
        for w in self.inner.winfo_children():
            w.destroy()

        parts = []
        p = path
        while p.parent != p:
            parts.append(p)
            p = p.parent
        parts.append(p)
        parts.reverse()

        for i, part in enumerate(parts):
            if i > 0:
                ttk.Label(self.inner, text="\u203A", font=("Segoe UI", 10),
                          foreground="#999", background="#f8f8f8").pack(side=tk.LEFT)
            display = part.name if part.name else str(part)
            is_last = (i == len(parts) - 1)
            lbl = tk.Label(self.inner, text=display,
                           font=("Segoe UI", 9, "bold" if is_last else "normal"),
                           fg=SEL_BG if is_last else "#555555", bg="#f8f8f8",
                           padx=8, pady=2, cursor="hand2")
            lbl.bind("<Button-1>", lambda e, p=part: self.app.navigate_to(p))
            lbl.bind("<Enter>", lambda e, w=lbl: w.configure(bg="#e8e8e8"))
            lbl.bind("<Leave>", lambda e, w=lbl: w.configure(bg="#f8f8f8"))
            lbl.pack(side=tk.LEFT)

        click_area = tk.Label(self.inner, text="", bg="#f8f8f8")
        click_area.pack(side=tk.LEFT, fill=tk.X, expand=True)
        click_area.bind("<Button-1>", lambda e: self._start_edit(str(path)))

    def _start_edit(self, current_path: str) -> None:
        if self._editing:
            return
        self._editing = True
        self.inner.pack_forget()
        self.entry.pack(fill=tk.X, expand=True, padx=4, pady=2)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, current_path)
        self.entry.selection_range(0, tk.END)
        self.entry.focus()

    def _on_entry_commit(self, event=None) -> None:
        val = self.entry.get().strip()
        self._editing = False
        self.entry.pack_forget()
        self.inner.pack(fill=tk.X, expand=True, padx=4, pady=2)
        if val:
            self.app.go_to_path(val)

    def _on_entry_cancel(self, event=None) -> None:
        if not self._editing:
            return
        self._editing = False
        self.entry.pack_forget()
        self.inner.pack(fill=tk.X, expand=True, padx=4, pady=2)


# ── File List ────────────────────────────────────────────────────────

class FileListFrame(ttk.Frame):
    def __init__(self, parent, app: "App") -> None:
        super().__init__(parent)
        self.app = app

        columns = ("icon", "name", "size", "type", "modified", "created")
        self.tree = ttk.Treeview(self, columns=columns, show="headings",
                                 selectmode="extended")
        col_defs = [
            ("icon",     " ",      38,  28,  tk.CENTER),
            ("name",     "Name",   260, 120, tk.W),
            ("size",     "Size",   100, 60,  tk.E),
            ("type",     "Type",   140, 70,  tk.W),
            ("modified", "Date Modified", 150, 80, tk.W),
            ("created",  "Date Created",  150, 80, tk.W),
        ]
        for col, text, width, minw, anchor in col_defs:
            self.tree.heading(col, text=text, command=lambda c=col: app.sort_by(c))
            self.tree.column(col, width=width, minwidth=minw, anchor=anchor)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def populate(self, entries: list[Path], show_hidden: bool) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, entry in enumerate(entries):
            if not show_hidden and entry.name.startswith("."):
                continue
            ico = file_icon(entry)
            try:
                meta = get_metadata(self.app.fs, entry)
                size = get_size_formatted(meta.size) if meta.is_file else ""
                modified = _friendly_date(meta.modified)
                created = _friendly_date(meta.created)
            except Exception:
                size = modified = created = ""
            file_type = get_file_type(entry)
            tag = "dir" if entry.is_dir() else ("even" if i % 2 == 0 else "odd")
            self.tree.insert("", tk.END, iid=str(entry),
                             values=(ico, entry.name, size, file_type, modified, created),
                             tags=(tag,))
        self.tree.tag_configure("dir", font=(FONT, 9, "bold"), foreground="#1a1a1a")
        self.tree.tag_configure("even", background=BG)
        self.tree.tag_configure("odd", background=ROW_ALT)

    def update_sort_indicators(self, key: str, reverse: bool) -> None:
        arrow = "\u25B2" if not reverse else "\u25BC"
        titles = {"icon": " ", "name": "Name", "size": "Size", "type": "Type",
                  "modified": "Date Modified", "created": "Date Created"}
        for col, text in titles.items():
            if col == key:
                self.tree.heading(col, text=f"{text} {arrow}")
            else:
                self.tree.heading(col, text=text)

    def on_double_click(self, event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        path = Path(sel[0])
        if path.is_dir():
            self.app.navigate_to(path)
        elif path.is_file():
            open_with_os(path)

    def on_right_click(self, event) -> None:
        sel = self.tree.identify_row(event.y)
        if sel:
            self.tree.selection_set(sel)
        self.app.show_context_menu(event, Path(sel) if sel else None)

    def on_select(self, event=None) -> None:
        self.app._update_status()

    def get_selected_paths(self) -> list[Path]:
        return [Path(iid) for iid in self.tree.selection()]


# ── Details Panel ────────────────────────────────────────────────────

class DetailsPanel(ttk.Frame):
    def __init__(self, parent, app: "App") -> None:
        super().__init__(parent, style="Details.TFrame", height=28)
        self.app = app
        self._label = ttk.Label(self, text="Select a file to preview",
                                style="Details.TLabel")
        self._label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=2)
        self.pack_propagate(False)

    def show(self, path: Optional[Path]) -> None:
        if path is None:
            self._label.configure(text="")
            return
        try:
            meta = get_metadata(self.app.fs, path)
            name = path.name
            ftype = get_file_type(path)
            if meta.is_file:
                size = get_size_formatted(meta.size)
                if path.suffix.lower() in (".txt", ".py", ".md", ".json", ".csv",
                                           ".xml", ".ini", ".cfg", ".log", ".yml",
                                           ".yaml", ".html", ".css", ".js", ".bat", ".ps1"):
                    try:
                        preview = path.read_text(encoding="utf-8", errors="replace")[:200]
                        lines = preview.split("\n")
                        if len(lines) > 3:
                            lines = lines[:3]
                            lines.append("...")
                        text = f"{ftype} | {size} | {' '.join(lines)}"
                    except Exception:
                        text = f"{ftype} | {size}"
                else:
                    text = f"{ftype} | {size} | Modified {_friendly_date(meta.modified)}"
            else:
                try:
                    cnt = len(list(path.iterdir()))
                    text = f"Folder | {cnt} items"
                except Exception:
                    text = "Folder"
            self._label.configure(text=f"  {file_icon(path)}  {name}  \u2014  {text}")
        except Exception:
            self._label.configure(text="")


# ── Directory Tree ───────────────────────────────────────────────────

class DirectoryTreeFrame(ttk.Frame):
    def __init__(self, parent, app: "App") -> None:
        super().__init__(parent)
        self.app = app
        self._populating = False

        self.tree = ttk.Treeview(self, show="tree", selectmode="browse")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Button-3>", self.on_right_click)

        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def init_tree(self) -> None:
        self._populating = True
        self.tree.delete(*self.tree.get_children())

        qa = self.tree.insert("", tk.END, iid="__qa__",
                              text="\u26A1 Quick Access", open=True)
        for name in ("Desktop", "Downloads", "Documents", "Pictures", "Music", "Videos"):
            fp = Path.home() / name
            if fp.exists():
                self.tree.insert(qa, tk.END, iid=str(fp), text=f"{DIR_ICON} {name}")

        pc_label = "This PC" if platform.system() == "Windows" else "Computer"
        pc = self.tree.insert("", tk.END, iid="__pc__",
                              text=f"\U0001F5BF {pc_label}", open=True)
        for drive in _list_drives():
            p = Path(drive)
            label = f"{DIR_ICON} Local Disk ({drive[0]})" if platform.system() == "Windows" else f"{DIR_ICON} {p}"
            self.tree.insert(pc, tk.END, iid=str(p), text=label)

        self._populating = False

    def on_select(self, event=None) -> None:
        if self._populating:
            return
        sel = self.tree.selection()
        if not sel or sel[0] in ("__qa__", "__pc__"):
            return
        path = Path(sel[0])
        if path.is_dir():
            self.app.navigate_to(path)

    def on_right_click(self, event) -> None:
        sel = self.tree.identify_row(event.y)
        if sel and sel not in ("__qa__", "__pc__"):
            self.tree.selection_set(sel)
            path = Path(sel)
            if path.is_dir():
                self.app.show_context_menu(event, path)

    def select_drive(self, path: Path) -> None:
        self._populating = True
        anchor = Path(path.anchor)
        if self.tree.exists(str(anchor)):
            self.tree.selection_set(str(anchor))
            self.tree.see(str(anchor))
        self._populating = False


# ── Toolbar ──────────────────────────────────────────────────────────

class ToolbarFrame(ttk.Frame):
    def __init__(self, parent, app: "App") -> None:
        super().__init__(parent)
        self.app = app

        self.btn_back = ttk.Button(self, text="\u25C0", width=3,
                                   style="Toolbutton.TButton", command=app.go_back)
        self.btn_forward = ttk.Button(self, text="\u25B6", width=3,
                                      style="Toolbutton.TButton", command=app.go_forward)
        self.btn_up = ttk.Button(self, text="\u25B2", width=3,
                                 style="Toolbutton.TButton", command=app.go_up)
        self.btn_refresh = ttk.Button(self, text="\u21BB", width=3,
                                      style="Toolbutton.TButton", command=app.refresh)
        self.btn_new_folder = ttk.Button(self, text="\U0001F4C1 +Folder", width=8,
                                         style="Toolbutton.TButton", command=app.new_folder)
        self.btn_new_file = ttk.Button(self, text="\U0001F4C4 +File", width=7,
                                       style="Toolbutton.TButton", command=app.new_file)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self, textvariable=self.search_var, width=18)
        self.search_entry.bind("<Return>", lambda e: app.search(self.search_var.get()))

        self.btn_search = ttk.Button(self, text="Search", width=6,
                                     style="Toolbutton.TButton",
                                     command=lambda: app.search(self.search_var.get()))
        self.btn_clear = ttk.Button(self, text="\u2715", width=2,
                                    style="Toolbutton.TButton", command=app.clear_search)

        self.btn_back.pack(side=tk.LEFT, padx=1)
        self.btn_forward.pack(side=tk.LEFT, padx=1)
        self.btn_up.pack(side=tk.LEFT, padx=1)
        self.btn_refresh.pack(side=tk.LEFT, padx=1)
        ttk.Separator(self, orient=tk.VERTICAL, style="VSeparator.TSeparator")\
            .pack(side=tk.LEFT, fill=tk.Y, padx=4)
        self.btn_new_folder.pack(side=tk.LEFT, padx=1)
        self.btn_new_file.pack(side=tk.LEFT, padx=1)

        ttk.Separator(self, orient=tk.VERTICAL, style="VSeparator.TSeparator")\
            .pack(side=tk.RIGHT, fill=tk.Y, padx=4)
        self.btn_clear.pack(side=tk.RIGHT, padx=1)
        self.btn_search.pack(side=tk.RIGHT, padx=1)
        self.search_entry.pack(side=tk.RIGHT, padx=2)
        ttk.Label(self, text="\U0001F50D", font=(FONT, 9)).pack(side=tk.RIGHT)


# ── Status Bar ───────────────────────────────────────────────────────

class StatusBar(ttk.Frame):
    def __init__(self, parent) -> None:
        super().__init__(parent, style="Breadcrumb.TFrame")
        self.left = ttk.Label(self, anchor=tk.W, padding=(8, 2), style="Status.TLabel")
        self.right = ttk.Label(self, anchor=tk.E, padding=(8, 2), style="Status.TLabel")
        self.left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.right.pack(side=tk.RIGHT)

    def set(self, left: str = "", right: str = "") -> None:
        self.left.configure(text=left)
        self.right.configure(text=right)


# ── Main Application ─────────────────────────────────────────────────

class App:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("File Explorer")
        self.root.geometry("1200x780+100+50")
        self.root.minsize(800, 500)
        apply_theme(self.root)

        self.fs = NativeFilesystem()
        self.nav = DirectoryNavigator(self.fs, Path.cwd())
        self.history = OperationHistory(limit=50)
        self.config = ConfigManager()
        self._search_results: Optional[list[Path]] = None
        self._sort_key: str = "name"
        self._sort_reverse: bool = False
        self._clipboard_paths: list[Path] = []
        self._clipboard_is_cut: bool = False

        self._build_ui()
        self._build_menu()
        self._bind_shortcuts()

        self.root.lift()
        self.root.focus_force()
        self.root.attributes("-topmost", True)
        self.root.after(100, lambda: self.root.attributes("-topmost", False))

    def _build_ui(self) -> None:
        self.toolbar = ToolbarFrame(self.root, self)
        self.toolbar.pack(fill=tk.X, padx=4, pady=(4, 0))

        self.breadcrumb = BreadcrumbBar(self.root, self)
        self.breadcrumb.pack(fill=tk.X)

        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X)

        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=4)

        self.dir_tree = DirectoryTreeFrame(paned, self)
        self.file_list = FileListFrame(paned, self)
        paned.add(self.dir_tree, weight=1)
        paned.add(self.file_list, weight=3)

        self.details = DetailsPanel(self.root, self)
        self.details.pack(fill=tk.X, padx=4)

        self.status = StatusBar(self.root)
        self.status.pack(fill=tk.X)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root, font=(FONT, 9))
        self.root.config(menu=menubar)

        fm = tk.Menu(menubar, tearoff=0, font=(FONT, 9))
        fm.add_command(label="New File", command=self.new_file, accelerator="Ctrl+N")
        fm.add_command(label="New Folder", command=self.new_folder, accelerator="Ctrl+Shift+N")
        fm.add_separator()
        fm.add_command(label="Open in Terminal", command=self._open_terminal_here, accelerator="Ctrl+`")
        fm.add_separator()
        fm.add_command(label="Exit", command=self.root.quit, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=fm)

        em = tk.Menu(menubar, tearoff=0, font=(FONT, 9))
        em.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        em.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        em.add_separator()
        em.add_command(label="Copy", command=self.copy_selected, accelerator="Ctrl+C")
        em.add_command(label="Paste", command=self.paste_items, accelerator="Ctrl+V")
        em.add_command(label="Copy Path", command=self._copy_path, accelerator="Ctrl+Shift+C")
        em.add_separator()
        em.add_command(label="Select All", command=self._select_all, accelerator="Ctrl+A")
        em.add_command(label="Invert Selection", command=self._invert_selection, accelerator="Ctrl+I")
        em.add_separator()
        em.add_command(label="Rename", command=self.rename_selected, accelerator="F2")
        em.add_command(label="Delete", command=self.delete_selected, accelerator="Del")
        menubar.add_cascade(label="Edit", menu=em)

        vm = tk.Menu(menubar, tearoff=0, font=(FONT, 9))
        self._show_hidden_var = tk.BooleanVar(value=False)
        vm.add_checkbutton(label="Show Hidden Files", variable=self._show_hidden_var,
                           command=self.refresh, accelerator="Ctrl+H")
        vm.add_command(label="Refresh", command=self.refresh, accelerator="F5")
        menubar.add_cascade(label="View", menu=vm)

        hm = tk.Menu(menubar, tearoff=0, font=(FONT, 9))
        hm.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=hm)

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-N>", lambda e: self.new_folder())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-c>", lambda e: self.copy_selected())
        self.root.bind("<Control-v>", lambda e: self.paste_items())
        self.root.bind("<Control-C>", lambda e: self._copy_path())
        self.root.bind("<Control-a>", lambda e: self._select_all())
        self.root.bind("<Control-i>", lambda e: self._invert_selection())
        self.root.bind("<Control-I>", lambda e: self._invert_selection())
        self.root.bind("<F2>", lambda e: self.rename_selected())
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<F5>", lambda e: self.refresh())
        self.root.bind("<Control-h>", lambda e: self._toggle_hidden())
        self.root.bind("<Control-f>", lambda e: self.toolbar.search_entry.focus())
        self.root.bind("<Control-grave>", lambda e: self._open_terminal_here())

    def _load_file_list(self) -> None:
        show_hidden = self.config.get("show_hidden_files")
        self._show_hidden_var.set(show_hidden if isinstance(show_hidden, bool) else False)
        self.breadcrumb.show(self.nav.current)
        self._search_results = None
        try:
            entries = self.nav.list_contents(show_hidden=self._show_hidden_var.get())
        except (PathNotFoundError, PermissionDeniedError):
            entries = []
        self._sort_and_populate(entries)

    def _init_async(self) -> None:
        self._load_file_list()
        self._update_status()
        self.root.after(10, self._init_tree_async)

    def _init_tree_async(self) -> None:
        try:
            self.dir_tree.init_tree()
            self.dir_tree.select_drive(self.nav.current)
        except Exception:
            pass

    def _toggle_hidden(self) -> None:
        self._show_hidden_var.set(not self._show_hidden_var.get())
        self.config.set("show_hidden_files", self._show_hidden_var.get())
        self.refresh()

    def refresh(self) -> None:
        self.breadcrumb.show(self.nav.current)
        self._search_results = None
        try:
            entries = self.nav.list_contents(show_hidden=self._show_hidden_var.get())
        except (PathNotFoundError, PermissionDeniedError):
            entries = []
        self._sort_and_populate(entries)
        self._update_status()

    def _sort_and_populate(self, entries: list[Path]) -> None:
        key = self._sort_key
        rev = self._sort_reverse
        if key == "name":
            entries.sort(key=lambda p: (not p.is_dir(), p.name.lower()), reverse=rev)
        elif key == "size":
            def sz(p):
                try:
                    return (0, get_metadata(self.fs, p).size) if p.is_file() else (1, 0)
                except Exception:
                    return (0, 0)
            entries.sort(key=sz, reverse=rev)
        elif key == "type":
            entries.sort(key=lambda p: (get_file_type(p), p.name.lower()), reverse=rev)
        elif key == "modified":
            def mt(p):
                try:
                    return (0, get_metadata(self.fs, p).modified)
                except Exception:
                    return (0, 0)
            entries.sort(key=mt, reverse=rev)
        elif key == "created":
            def ct(p):
                try:
                    return (0, get_metadata(self.fs, p).created)
                except Exception:
                    return (0, 0)
            entries.sort(key=ct, reverse=rev)
        self.file_list.populate(entries, self._show_hidden_var.get())
        self.file_list.update_sort_indicators(key, rev)

    def sort_by(self, key: str) -> None:
        if self._sort_key == key:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_key = key
            self._sort_reverse = False
        self.refresh()

    def _update_status(self) -> None:
        try:
            total = len(self.nav.list_contents(show_hidden=self._show_hidden_var.get()))
        except Exception:
            total = 0
        sel = self.file_list.get_selected_paths()
        if sel:
            sizes = []
            for p in sel:
                try:
                    sizes.append(get_metadata(self.fs, p).size)
                except Exception:
                    pass
            right = f"{len(sel)} / {total} selected  ({get_size_formatted(sum(sizes))})"
        else:
            right = f"{total} items"
        self.status.set(left=str(self.nav.current), right=right)
        self.details.show(sel[0] if sel else None)

    def navigate_to(self, path: Path) -> None:
        try:
            self.nav.go_to(path)
            self.refresh()
        except (PathNotFoundError, PermissionDeniedError) as e:
            messagebox.showerror("Navigation Error", str(e))

    def go_back(self) -> None:
        if self.nav.go_back():
            self.refresh()

    def go_forward(self) -> None:
        if self.nav.go_forward():
            self.refresh()

    def go_up(self) -> None:
        self.nav.go_up()
        self.refresh()

    def go_to_path(self, path_str: str) -> None:
        try:
            p = Path(path_str).expanduser().resolve()
            if p.is_dir():
                self.navigate_to(p)
            else:
                messagebox.showwarning("Invalid Path", f"Not a directory:\n{p}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def new_file(self) -> None:
        name = simpledialog.askstring("New File", "File name:", initialvalue="new_file.txt",
                                      parent=self.root)
        if not name:
            return
        try:
            cmd = CreateFileCommand(self.fs, self.nav.current / name)
            result = cmd.execute()
            if result.success:
                self.history.push(cmd)
                self.refresh()
            else:
                messagebox.showerror("Error", result.error or "Failed to create file")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def new_folder(self) -> None:
        name = simpledialog.askstring("New Folder", "Folder name:", initialvalue="New Folder",
                                      parent=self.root)
        if not name:
            return
        try:
            cmd = CreateDirectoryCommand(self.fs, self.nav.current / name)
            result = cmd.execute()
            if result.success:
                self.history.push(cmd)
                self.refresh()
            else:
                messagebox.showerror("Error", result.error or "Failed to create folder")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_selected(self) -> None:
        paths = self.file_list.get_selected_paths()
        if not paths:
            return
        msg = f"Delete '{paths[0].name}'?" if len(paths) == 1 else f"Delete {len(paths)} items?"
        if not messagebox.askyesno("Confirm Delete", msg, parent=self.root):
            return
        for path in paths:
            try:
                cmd = (DeleteDirectoryCommand(self.fs, path, recursive=True)
                       if path.is_dir() else DeleteFileCommand(self.fs, path))
                cmd.execute()
                self.history.push(cmd)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        self.refresh()

    def rename_selected(self) -> None:
        paths = self.file_list.get_selected_paths()
        if not paths:
            return
        path = paths[0]
        name = simpledialog.askstring("Rename", "New name:", initialvalue=path.name,
                                      parent=self.root)
        if not name or name == path.name:
            return
        try:
            cmd = RenameCommand(self.fs, path, path.parent / name)
            result = cmd.execute()
            if result.success:
                self.history.push(cmd)
                self.refresh()
            else:
                messagebox.showerror("Error", result.error or "Rename failed")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def copy_selected(self) -> None:
        self._clipboard_paths = self.file_list.get_selected_paths()
        self._clipboard_is_cut = False
        self.status.set(left="\u2713 Copied to clipboard")

    def paste_items(self) -> None:
        if not self._clipboard_paths:
            return
        for src in self._clipboard_paths:
            try:
                cmd = (MoveCommand(self.fs, src, self.nav.current / src.name, ConflictStrategy.RENAME)
                       if self._clipboard_is_cut
                       else CopyCommand(self.fs, src, self.nav.current / src.name, ConflictStrategy.RENAME))
                result = cmd.execute()
                if result.success:
                    self.history.push(cmd)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        self._clipboard_paths = []
        self.refresh()

    def _copy_path(self) -> None:
        sel = self.file_list.get_selected_paths()
        if sel:
            copy_to_clipboard(str(sel[0].resolve()))
            self.status.set(left="\u2713 Path copied")

    def _select_all(self) -> None:
        self.file_list.tree.selection_set(self.file_list.tree.get_children())

    def _invert_selection(self) -> None:
        all_items = set(self.file_list.tree.get_children())
        sel = set(self.file_list.tree.selection())
        self.file_list.tree.selection_set(list(all_items - sel))

    def _open_terminal_here(self) -> None:
        open_terminal(self.nav.current)

    def search(self, pattern: str) -> None:
        pattern = pattern.strip()
        if not pattern:
            self.clear_search()
            return
        try:
            opts = SearchOptions(pattern=pattern, root_path=self.nav.current, recursive=True,
                                 case_sensitive=False, max_results=500,
                                 include_hidden=self._show_hidden_var.get())
            results = search_by_name(self.fs, opts)
            self._search_results = [r.path for r in results]
            if not results:
                self.status.set(left=f"No results for '{pattern}'")
                self.file_list.populate([], self._show_hidden_var.get())
                return
            self._sort_and_populate([r.path for r in results])
            self.status.set(left=f"{len(results)} result(s) for '{pattern}'")
        except Exception as e:
            messagebox.showerror("Search Error", str(e))

    def clear_search(self) -> None:
        self.toolbar.search_var.set("")
        self._search_results = None
        self.refresh()

    def undo(self) -> None:
        result = self.history.undo()
        self.refresh()
        if result is None:
            self.status.set(left="Nothing to undo")

    def redo(self) -> None:
        result = self.history.redo()
        self.refresh()
        if result is None:
            self.status.set(left="Nothing to redo")

    def show_context_menu(self, event, path: Optional[Path]) -> None:
        menu = tk.Menu(self.root, tearoff=0, font=(FONT, 9))
        if path is None:
            menu.add_command(label=f"{DIR_ICON} New Folder", command=self.new_folder)
            menu.add_command(label=f"{DEFAULT_FILE_ICON} New File", command=self.new_file)
            menu.add_separator()
            menu.add_command(label="Paste", command=self.paste_items)
            menu.add_separator()
            menu.add_command(label="\u2B22 Open in Terminal", command=self._open_terminal_here)
        else:
            menu.add_command(label=f"{file_icon(path)} Open", command=lambda: open_with_os(path))
            if path.is_dir():
                menu.add_command(label="\U0001F4C2 Open in New Tab",
                                 command=lambda: self.navigate_to(path))
            menu.add_command(label="\u2B22 Open in Terminal",
                             command=lambda: open_terminal(path))
            menu.add_separator()
            menu.add_command(label="\u2713 Copy", command=self.copy_selected)
            menu.add_command(label="\U0001F4CB Copy as Path",
                             command=lambda: copy_to_clipboard(str(path.resolve())))
            menu.add_separator()
            menu.add_command(label="\u270F Rename", command=self.rename_selected)
            menu.add_command(label="\u2716 Delete", command=self.delete_selected)
            menu.add_separator()
            menu.add_command(label="\u2699 Properties",
                             command=lambda: PropertiesDialog(self.root, path, self.fs))
        menu.tk_popup(event.x_root, event.y_root)

    def _show_about(self) -> None:
        messagebox.showinfo("About File Explorer",
                            "File Explorer v0.1.0\n\n"
                            "Python + Tkinter\n"
                            "file_explorer core \u2014 265 tests passing\n"
                            "Zero external dependencies.")

    def run(self) -> None:
        self.root.after(10, self._init_async)
        self.root.mainloop()


def main() -> None:
    setup_logging()
    App().run()


if __name__ == "__main__":
    main()
