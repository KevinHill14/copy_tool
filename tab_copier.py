"""
Tab Copier - office data-entry helper.

Workflow:
  1. Put the values from "Form A" into a CSV file, one value per row,
     in the same order you'll tab through the fields on "Form B".
     (A header row is optional - see sample_data.csv)
  2. Load the CSV in this tool.
  3. Click into the first field of Form B and paste (Ctrl+V) - that's value #1.
  4. Press Tab like you normally would to move to the next field.
     This tool watches for Tab globally (even while Form B has focus,
     not this window) and automatically copies the NEXT value onto your
     clipboard the instant you press Tab, so Ctrl+V always has the right
     thing ready.
  5. Keep tabbing + pasting until you reach the end of the list.

Tab still behaves completely normally in every other app - this only
listens for the key, it never blocks or intercepts it.
"""

import csv
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import keyboard
import pyperclip

APP_TITLE = "Tab Copier"


class TabCopierApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("480x420")
        self.root.minsize(420, 360)

        self.values: list[str] = []
        self.headers: list[str] = []
        self.index = 0
        self.enabled = tk.BooleanVar(value=True)
        self.csv_path = None
        self.hotkey_lock = threading.Lock()

        self._build_ui()
        self._register_hotkeys()

    # ---------- UI ----------

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)

        ttk.Button(top, text="Load CSV...", command=self.load_csv).pack(side="left")
        ttk.Button(top, text="Reset to start", command=self.reset).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(top, text="Listening for Tab", variable=self.enabled).pack(
            side="right"
        )

        self.file_label = ttk.Label(self.root, text="No file loaded", foreground="#666")
        self.file_label.pack(fill="x", padx=10)

        self.progress_label = ttk.Label(self.root, text="0 / 0", font=("Segoe UI", 11, "bold"))
        self.progress_label.pack(pady=(10, 0))

        # Current value about to be copied
        ttk.Label(self.root, text="On deck (will be copied on next Tab press):").pack(
            anchor="w", padx=10, pady=(14, 0)
        )
        self.current_field_label = ttk.Label(self.root, text="", foreground="#666")
        self.current_field_label.pack(anchor="w", padx=10)
        self.current_value = tk.Text(self.root, height=3, wrap="word")
        self.current_value.pack(fill="x", padx=10, pady=(2, 10))
        self.current_value.configure(state="disabled")

        # Next value preview
        ttk.Label(self.root, text="Next up after that:").pack(anchor="w", padx=10)
        self.next_field_label = ttk.Label(self.root, text="", foreground="#666")
        self.next_field_label.pack(anchor="w", padx=10)
        self.next_value = tk.Text(self.root, height=2, wrap="word")
        self.next_value.pack(fill="x", padx=10, pady=(2, 10))
        self.next_value.configure(state="disabled")

        nav = ttk.Frame(self.root)
        nav.pack(fill="x", padx=10, pady=4)
        ttk.Button(nav, text="<- Back", command=self.step_back).pack(side="left")
        ttk.Button(nav, text="Copy current now", command=self.copy_current_manual).pack(
            side="left", padx=8
        )
        ttk.Button(nav, text="Skip ->", command=self.step_forward_only).pack(side="left")

        self.status = ttk.Label(self.root, text="Load a CSV to begin.", foreground="#0a5")
        self.status.pack(side="bottom", fill="x", padx=10, pady=8)

    # ---------- CSV handling ----------

    def load_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = [row for row in reader if row]
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Could not read CSV:\n{e}")
            return

        if not rows:
            messagebox.showwarning(APP_TITLE, "That CSV file is empty.")
            return

        # Two supported layouts:
        #  - Two columns: "Field Name, Value" (any number of rows)
        #  - One column: just values (field names shown as Row 1, Row 2, ...)
        headers = []
        values = []
        for row in rows:
            if len(row) >= 2:
                headers.append(row[0])
                values.append(row[1])
            else:
                headers.append(f"Row {len(values) + 1}")
                values.append(row[0])

        self.headers = headers
        self.values = values
        self.index = 0
        self.csv_path = path
        self.file_label.config(text=f"Loaded: {os.path.basename(path)} ({len(values)} values)")
        self.status.config(
            text="Ready. Click into the first field on your other form, then press Tab.",
            foreground="#0a5",
        )
        self._refresh_display()

    def reset(self):
        self.index = 0
        self._refresh_display()
        self.status.config(text="Reset to the first value.", foreground="#0a5")

    # ---------- Display ----------

    def _refresh_display(self):
        total = len(self.values)
        self.progress_label.config(text=f"{min(self.index, total)} / {total}")

        def set_box(box, text):
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.insert("1.0", text)
            box.configure(state="disabled")

        if not self.values:
            set_box(self.current_value, "")
            set_box(self.next_value, "")
            self.current_field_label.config(text="")
            self.next_field_label.config(text="")
            return

        if self.index < total:
            self.current_field_label.config(text=self.headers[self.index])
            set_box(self.current_value, self.values[self.index])
        else:
            self.current_field_label.config(text="(done)")
            set_box(self.current_value, "-- all values copied --")

        nxt = self.index + 1
        if nxt < total:
            self.next_field_label.config(text=self.headers[nxt])
            set_box(self.next_value, self.values[nxt])
        else:
            self.next_field_label.config(text="")
            set_box(self.next_value, "")

    # ---------- Copy logic ----------

    def _copy_current_to_clipboard(self):
        if self.index >= len(self.values):
            return
        pyperclip.copy(self.values[self.index])

    def _advance(self):
        """Copy the current value, then move the pointer forward."""
        with self.hotkey_lock:
            if not self.values:
                return
            self._copy_current_to_clipboard()
            field_name = self.headers[self.index]
            self.index += 1
            self.root.after(0, self._refresh_display)
            self.root.after(
                0,
                lambda: self.status.config(
                    text=f"Copied '{field_name}' to clipboard.", foreground="#0a5"
                ),
            )

    def _on_tab_pressed(self, event=None):
        if not self.enabled.get():
            return
        if not self.values:
            return
        self._advance()

    def copy_current_manual(self):
        """Copy the current value without advancing (for re-pasting)."""
        if not self.values or self.index >= len(self.values):
            return
        self._copy_current_to_clipboard()
        self.status.config(
            text=f"Re-copied '{self.headers[self.index]}' to clipboard.", foreground="#0a5"
        )

    def step_forward_only(self):
        """Move the pointer forward without copying (for skipping a field)."""
        if self.index < len(self.values):
            self.index += 1
        self._refresh_display()

    def step_back(self):
        if self.index > 0:
            self.index -= 1
        self._refresh_display()
        self.status.config(text="Moved back one value.", foreground="#0a5")

    # ---------- Global hotkey ----------

    def _register_hotkeys(self):
        # suppress=False: Tab still does its normal job everywhere else.
        keyboard.on_press_key("tab", self._on_tab_pressed, suppress=False)


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    app = TabCopierApp(root)

    def on_close():
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
