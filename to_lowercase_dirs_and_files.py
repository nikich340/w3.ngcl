from pathlib import Path
import tkinter as tk
from tkinter import filedialog

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    directory_path = filedialog.askdirectory(title="Select a Directory")

    if directory_path:
        paths = Path(directory_path).rglob("*")
        for path in paths:
            if any(char.isupper() for char in path.name):
                new_path = path.with_name(path.name.lower())
                path.rename(new_path)
                print(f"Renamed: {str(path)} -> {str(new_path)}")

main()
input("DONE!")
