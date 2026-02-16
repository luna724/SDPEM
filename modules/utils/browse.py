import tkinter as tk
from tkinter import filedialog
from tkfilebrowser import askopendirnames


def _with_root(fn):
    root = tk.Tk()
    root.withdraw()
    try:
        return fn()
    finally:
        root.destroy()


def select_folder() -> str:
    return _with_root(lambda: filedialog.askdirectory(title="Select a Folder") or "")


def select_folders() -> list[str]:
    result = _with_root(lambda: askopendirnames(title="Select Folders"))
    return list(result) if result else []


def select_file() -> str:
    return _with_root(lambda: filedialog.askopenfilename(title="Select a File") or "")


def select_files() -> list[str]:
    result = _with_root(lambda: filedialog.askopenfilenames(title="Select Files"))
    return list(result) if result else []