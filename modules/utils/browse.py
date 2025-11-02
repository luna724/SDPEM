import tkinter as tk
from tkinter import filedialog

def select_folder() -> str:
    """
    tkinterを使ってフォルダを選択し、選択されたフォルダのフルパスを返す関数
    """
    root = tk.Tk()
    root.withdraw()  # Tkinterウィンドウを非表示にする
    folder_path = filedialog.askdirectory(title="Select a Folder")
    root.destroy() 
    return folder_path

def select_folders() -> list[str]:
    root = tk.Tk()
    root.withdraw()  # Tkinterウィンドウを非表示にする
    folder_path = filedialog.askdirectory(title="Select a Folder")
    root.destroy() 
    return folder_path


def select_file() -> str:
    root = tk.Tk()
    root.withdraw()  # Tkinterウィンドウを非表示にする
    folder_path = filedialog.askopenfile(title="Select a Folder")
    root.destroy() 
    return folder_path.name if folder_path else ""

def select_files() -> list[str]:
    root = tk.Tk()
    root.withdraw()  # Tkinterウィンドウを非表示にする
    file_paths = filedialog.askopenfilenames(title="Select Files")
    root.destroy() 
    return list(file_paths)