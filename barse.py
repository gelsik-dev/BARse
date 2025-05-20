import struct
import tkinter as tk
import customtkinter
from PIL import Image
from tkinter import ttk, filedialog, messagebox
import os

MAX_VALUE = 999999999
MIN_DETECT_VALUE = 1000
MAX_DISPLAY_RECORDS = 20
MAX_RECORD_FILES = 20

class BARsaveEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BARsave-editor")
        self.geometry("1090x800")
        self.resizable(False, False)

        try:
            icon = tk.PhotoImage(file="_internal/icon.png")
            self.iconphoto(False, icon)
        except Exception as e:
            print("Load icon = NO :(", e)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 10), rowheight=25,
                        background="#f9f9f9", fieldbackground="#f9f9f9", foreground="#222")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"),
                        background="#004d99", foreground="white")
        style.configure("TLabel", font=("Arial", 11))
        style.configure("TButton", font=("Arial", 11))
        style.map('TButton', background=[('active', '#0059cc')], foreground=[('active', 'white')])

        main_frame = ttk.Frame(self, padding=15)

        logo_image = customtkinter.CTkImage(
            light_image=Image.open("_internal/logo.png"),
            dark_image=Image.open("_internal/logo.png"),
            size=(200, 200)
        )
        
        logo_label = customtkinter.CTkLabel(self, image=logo_image, text="")
        logo_label.pack(pady=20)

        self.label_title = ttk.Label(
            main_frame, text="BARsave-editor",
            font=("Arial", 26, "bold"), foreground="#004d99"
        )
        self.label_title.pack(pady=(0, 10))

        description = (
            "Load a 'save.bin' file, automatically detect the first value >= 1000, "
            "show records and allow replacing one value with another (max allowed 999,999,999)."
        )
        self.label_desc = ttk.Label(
            main_frame, text=description, wraplength=1060,
            justify="center", foreground="#333333"
        )
        self.label_desc.pack(pady=(0, 15))

        frame_controls = ttk.Frame(main_frame)
        frame_controls.pack(fill="x", pady=(0, 15))

        ttk.Label(frame_controls, text="Value to find:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_search = ttk.Entry(frame_controls, width=15)
        self.entry_search.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_controls, text="Replacement value:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.entry_replace = ttk.Entry(frame_controls, width=15)
        self.entry_replace.grid(row=0, column=3, padx=5, pady=5)
        self.entry_replace.insert(0, str(MAX_VALUE))

        self.btn_load = ttk.Button(frame_controls, text="Load save.bin", command=self.load_file)
        self.btn_load.grid(row=0, column=4, padx=15, pady=5)

        self.btn_save = ttk.Button(frame_controls, text="Save modified file", command=self.save_file, state="disabled")
        self.btn_save.grid(row=0, column=5, padx=15, pady=5)

        self.btn_export_txt = ttk.Button(
            frame_controls, text="Export records to TXT files",
            command=self.export_records_txt, state="disabled"
        )
        self.btn_export_txt.grid(row=0, column=6, padx=15, pady=5)

        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=("index", "value"), show="headings", height=25)
        self.tree.heading("index", text="Index")
        self.tree.heading("value", text="Value")
        self.tree.column("index", width=100, anchor="center")
        self.tree.column("value", width=180, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.status_var = tk.StringVar(value="Waiting for file to load...")
        self.label_status = ttk.Label(self, textvariable=self.status_var, foreground="#004d99", font=("Arial", 10, "italic"))

        footer = "BARsave-editor - © 2025 Gelsik"
        self.label_footer = ttk.Label(self, text=footer, foreground="gray", font=("Arial", 9))
        self.label_footer.pack(side="bottom", pady=5)
        self.label_status.pack(side="bottom", pady=10)
        main_frame.pack(fill="both", expand=True)

        self.file_content = None
        self.integers = None
        self.filepath = None

    def validate_values(self):
        try:
            search_val = int(self.entry_search.get())
            replace_val = int(self.entry_replace.get())
        except ValueError:
            messagebox.showerror("Value error", "Values must be integers.")
            return None, None

        if not (0 <= search_val <= MAX_VALUE):
            messagebox.showerror("Value error", f"Value to find must be between 0 and {MAX_VALUE}.")
            return None, None
        if not (0 <= replace_val <= MAX_VALUE):
            messagebox.showerror("Value error", f"Replacement value must be between 0 and {MAX_VALUE}.")
            return None, None
        return search_val, replace_val

    def load_file(self):
        filepath = filedialog.askopenfilename(title="Open save.bin", filetypes=[("BIN files", "*.bin")])
        if not filepath:
            return

        try:
            with open(filepath, "rb") as file:
                self.file_content = file.read()

            if len(self.file_content) < 4:
                raise ValueError("File too small.")

            num_values = len(self.file_content) // 4
            self.integers = list(struct.unpack(f"<{num_values}I", self.file_content[:num_values * 4]))
            self.filepath = filepath

            detected_value = None
            detected_index = None
            for i, val in enumerate(self.integers):
                if val >= MIN_DETECT_VALUE:
                    detected_value = val
                    detected_index = i
                    break

            self.tree.delete(*self.tree.get_children())
            for idx, val in enumerate(self.integers[:MAX_DISPLAY_RECORDS]):
                self.tree.insert("", "end", values=(idx, val))

            if detected_value is not None:
                self.entry_search.delete(0, tk.END)
                self.entry_search.insert(0, str(detected_value))
                self.status_var.set(f"Detected value {detected_value} at position {detected_index}.")
            else:
                self.entry_search.delete(0, tk.END)
                self.entry_search.insert(0, "0")
                self.status_var.set("No value >= 1000 detected in the file.")

            self.btn_save.config(state="normal")
            self.btn_export_txt.config(state="normal")
            self.export_records_txt(ask_path=False)

        except Exception as e:
            messagebox.showerror("File load error", str(e))
            self.status_var.set("Error loading the file.")

    def save_file(self):
        if self.integers is None or self.file_content is None:
            messagebox.showwarning("No file", "Load a valid file first.")
            return

        search_val, replace_val = self.validate_values()
        if search_val is None:
            return

        count_replaced = 0
        for i in range(len(self.integers)):
            if self.integers[i] == search_val:
                self.integers[i] = replace_val
                count_replaced += 1

        if count_replaced == 0:
            messagebox.showinfo("Info", f"No occurrences of value {search_val} found to replace.")
            self.status_var.set(f"No occurrences of value {search_val} found.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Save modified file", defaultextension=".bin",
            filetypes=[("BIN files", "*.bin")]
        )
        if not filepath:
            return

        try:
            packed = struct.pack(f"<{len(self.integers)}I", *self.integers)
            modified_content = packed + self.file_content[len(self.integers) * 4:]

            with open(filepath, "wb") as file:
                file.write(modified_content)

            self.status_var.set(f"File saved successfully: {filepath} ({count_replaced} values replaced).")
            messagebox.showinfo("Saved", f"File saved successfully. {count_replaced} values replaced.")
        except Exception as e:
            messagebox.showerror("File save error", str(e))
            self.status_var.set("Error saving the file.")

    def export_records_txt(self, ask_path=True):
        if self.integers is None:
            messagebox.showwarning("No data", "Load a valid file first to export.")
            return

        if ask_path:
            filepath = filedialog.asksaveasfilename(
                title="Save records as TXT", defaultextension=".txt",
                filetypes=[("Text files", "*.txt")]
            )
            if not filepath:
                return
            base_folder = os.path.dirname(filepath)
        else:
            if self.filepath is None:
                messagebox.showerror("No file path", "Load a file first to auto-export.")
                return
            base_folder = os.path.join(os.path.dirname(self.filepath), "records_txt")
            os.makedirs(base_folder, exist_ok=True)

        total_records = len(self.integers)
        files_saved = 0

        for start_index in range(0, total_records, MAX_DISPLAY_RECORDS):
            if files_saved >= MAX_RECORD_FILES:
                break
            end_index = min(start_index + MAX_DISPLAY_RECORDS, total_records)
            filename = f"records_{files_saved + 1}.txt"
            fullpath = os.path.join(base_folder, filename)

            try:
                with open(fullpath, "w") as f:
                    for idx in range(start_index, end_index):
                        f.write(f"Index {idx}: {self.integers[idx]}\n")
                files_saved += 1
            except Exception as e:
                messagebox.showerror("Export error", f"Error saving file {filename}:\n{str(e)}")
                break

        if files_saved > 0:
            self.status_var.set(f"Exported {files_saved} TXT files with records.")
            if ask_path:
                messagebox.showinfo("Exported", f"Exported {files_saved} TXT files with records.")
        else:
            self.status_var.set("No files exported.")

if __name__ == "__main__":
    app = BARsaveEditor()
    app.mainloop()
