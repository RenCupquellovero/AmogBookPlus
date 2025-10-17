import customtkinter as ctk
from tkinter import messagebox, filedialog, colorchooser, scrolledtext
import json
from datetime import datetime
import os

# ---------------- Appearance Setup ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ---------------- Colors ----------------
PLAYER_COLORS = {
    "Red": "#ff3b30",
    "Blue": "#007aff",
    "Green": "#34c759",
    "Yellow": "#ffcc00",
    "Pink": "#ff69b4",
    "Black": "#1c1c1e",
    "White": "#f2f2f2",
    "Cyan": "#00ffff",
    "Orange": "#ff9500",
    "Purple": "#af52de",
    "Brown": "#a0522d",
    "Lime": "#a8e72e",
    "Maroon": "#800000",
    "Rose": "#ffb6c1",
    "Banana": "#fce570",
    "Gray": "#808080",
    "Tan": "#d2b48c",
    "Coral": "#ff7f50"
}

# fixed dark style constants for immutable sections
IMMUTABLE_DARK_BG = "#1c1c1e"
IMMUTABLE_DARK_FRAME = "#2a2a2c"
IMMUTABLE_TEXT = "white"

# path for persistent notebook file
DEFAULT_NOTEBOOK_PATH = "notebook.txt"

# ---------------- Utilities ----------------
def hex_to_rgb(hexcol: str):
    h = hexcol.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def luminance(hexcol: str):
    r, g, b = hex_to_rgb(hexcol)
    return 0.2126*r + 0.7152*g + 0.0722*b

def readable_text_color(hexcol: str):
    # return black or white depending on background luminance
    return "black" if luminance(hexcol) > 160 else "white"

# ---------------- Mini Overlay ----------------
class MiniOverlay(ctk.CTkToplevel):
    def __init__(self, master, top_n=5):
        super().__init__(master)
        self.title("Mini Bodies Overlay")
        self.geometry("340x180")
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.92)
        self.resizable(False, False)
        try:
            self.configure(fg_color=master.bg_color)
        except Exception:
            pass
        self.master_app = master
        self.top_n = top_n
        self.font_family = getattr(master, "font_family", "Arial")
        self.text_color = getattr(master, "text_color", IMMUTABLE_TEXT)
        self.base_font_size = getattr(master, "base_font_size", 12)

        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)

        self.header = ctk.CTkLabel(self, text="Recent Bodies", font=(self.font_family, self.base_font_size + 2, "bold"), text_color=self.text_color)
        self.header.pack(anchor="w", padx=10, pady=(8,4))

        self.lines_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.lines_frame.pack(fill="both", expand=True, padx=6, pady=4)

        self.line_widgets = []
        for i in range(self.top_n):
            v_lbl = ctk.CTkLabel(self.lines_frame, text="", font=(self.font_family, self.base_font_size, "bold"), anchor="w", text_color=self.text_color)
            d_lbl = ctk.CTkLabel(self.lines_frame, text="", font=(self.font_family, max(self.base_font_size - 1, 9)), anchor="w", text_color=self.text_color)
            v_lbl.pack(fill="x", padx=6, pady=(2,0))
            d_lbl.pack(fill="x", padx=12, pady=(0,4))
            self.line_widgets.append((v_lbl, d_lbl))

        self.update_overlay()

    def start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def do_move(self, event):
        deltax = event.x - self._drag_x
        deltay = event.y - self._drag_y
        self.geometry(f"+{self.winfo_x() + deltax}+{self.winfo_y() + deltay}")

    def update_overlay(self):
        bodies = getattr(self.master_app, "bodies", [])
        recent = bodies[:self.top_n]
        for i in range(self.top_n):
            v_lbl, d_lbl = self.line_widgets[i]
            if i < len(recent):
                entry = recent[i]
                victim = entry.get("victim", "Unknown")
                location = entry.get("location", "Unknown")
                nearby = entry.get("nearby", [])
                time = entry.get("time", "")
                color = PLAYER_COLORS.get(victim, "#000000")
                v_lbl.configure(text=f"#{entry.get('id','?')} {victim} — {time}", text_color=color, font=(self.font_family, self.base_font_size, "bold"))
                nearby_text = ", ".join(nearby) if nearby else "None"
                d_lbl.configure(text=f"Location: {location}  |  Nearby: {nearby_text}", text_color=self.text_color, font=(self.font_family, max(self.base_font_size - 1, 9)))
            else:
                v_lbl.configure(text="")
                d_lbl.configure(text="")
        self.after(1000, self.update_overlay)

# ---------------- Notebook Window (persistent) ----------------
class NotebookWindow(ctk.CTkToplevel):
    def __init__(self, master, path=DEFAULT_NOTEBOOK_PATH):
        super().__init__(master)
        self.title("Notebook")
        self.geometry("700x520")
        self.resizable(True, True)
        self.path = path
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        try:
            self.configure(fg_color=master.bg_color)
        except Exception:
            pass

        header = ctk.CTkLabel(self, text="Notebook", font=(master.font_family, max(master.base_font_size+2, 12), "bold"), text_color=master.text_color)
        header.pack(anchor="w", padx=10, pady=(8,6))

        self.text_widget = scrolledtext.ScrolledText(self, wrap="word", undo=True)
        self.text_widget.pack(fill="both", expand=True, padx=10, pady=(0,10))
        try:
            self.text_widget.configure(font=(master.font_family, master.base_font_size))
        except Exception:
            pass

        self.load_notes()

    def load_notes(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = f.read()
                self.text_widget.delete("1.0", "end")
                self.text_widget.insert("1.0", data)
            except Exception:
                pass

    def save_notes(self):
        try:
            data = self.text_widget.get("1.0", "end-1c")
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(data)
        except Exception:
            pass

    def on_close(self):
        self.save_notes()
        self.destroy()

# ---------------- Main App ----------------
class AmongUsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Among Us - Body Notebook (Customizable)")
        self.geometry("1350x750")
        self.resizable(False, False)

        # default appearance
        self.bg_color = "#ffffff"
        self.font_family = "Arial"
        self.base_font_size = 12
        self.text_color = IMMUTABLE_TEXT
        self.font_alpha = 255

        self.players = list(PLAYER_COLORS.keys())
        self.sus = {p: 0 for p in self.players}
        self.bodies = []
        self.next_id = 1
        self.selected_player = None
        self.mini_overlay = None
        self.notebook_window = None

        # track buttons that should follow player color
        self.colored_buttons = []

        self.available_fonts = [
            "Arial", "Calibri", "Helvetica", "Times New Roman", "Courier New",
            "Verdana", "Trebuchet MS", "Georgia", "Impact", "Comic Sans MS"
        ]

        # Main frames
        self.sidebar = ctk.CTkFrame(self, width=350, corner_radius=12, fg_color=self.bg_color)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)
        self.main = ctk.CTkFrame(self, corner_radius=12, fg_color=self.bg_color)
        self.main.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.build_sidebar()
        self.build_main()

    # ---------------- Sidebar ----------------
    def build_sidebar(self):
        ctk.CTkLabel(self.sidebar, text="Players", font=(self.font_family, 20, "bold"), text_color=self.text_color).pack(pady=10)

        self.player_selector_outer = ctk.CTkFrame(self.sidebar, fg_color=IMMUTABLE_DARK_BG, corner_radius=10)
        self.player_selector_outer.pack(padx=6, pady=5, fill="x")
        player_inner = ctk.CTkFrame(self.player_selector_outer, fg_color=IMMUTABLE_DARK_FRAME, corner_radius=8)
        player_inner.pack(padx=6, pady=6, fill="both")

        grid = ctk.CTkScrollableFrame(player_inner, width=320, height=260, fg_color=IMMUTABLE_DARK_FRAME)
        grid.pack(fill="both", expand=True)
        self.player_buttons = {}
        for i, (name, color) in enumerate(PLAYER_COLORS.items()):
            btn = ctk.CTkButton(
                grid,
                text=name,
                fg_color=color,
                hover_color="#3a3a3c",
                text_color="black" if name not in ["Black", "Maroon", "Gray", "Brown"] else "white",
                width=120,
                height=35,
                corner_radius=10,
                command=lambda n=name: self.select_player(n)
            )
            btn.grid(row=i//2, column=i%2, padx=5, pady=5)
            self.player_buttons[name] = btn
            # player swatch buttons are colored by design; include them so they keep their own color
            # do not add to self.colored_buttons (they already show their color)

        info_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info_frame.pack(pady=8, fill="x", padx=6)
        self.selected_label = ctk.CTkLabel(info_frame, text="No player selected", font=(self.font_family, self.base_font_size, "italic"), text_color=self.text_color)
        self.selected_label.pack(side="left", padx=(0,6))

        # Font, Settings, Log, Mini buttons (these follow selected player's color)
        self.font_btn = ctk.CTkButton(info_frame, text="Font", width=70, height=28, corner_radius=8, command=self.open_font_chooser)
        self.font_btn.pack(side="right", padx=(6,0))
        self.register_colored(self.font_btn)

        self.settings_btn = ctk.CTkButton(info_frame, text="Settings", width=80, height=28, corner_radius=8, command=self.open_settings_color)
        self.settings_btn.pack(side="right", padx=(6,0))
        self.register_colored(self.settings_btn)

        self.log_btn = ctk.CTkButton(info_frame, text="Log", width=60, height=28, corner_radius=8, command=self.open_notebook)
        self.log_btn.pack(side="right", padx=(6,0))
        self.register_colored(self.log_btn)

        self.mini_tab = ctk.CTkButton(info_frame, text="Mini", width=60, height=28, corner_radius=8, command=self.open_mini_overlay)
        self.mini_tab.pack(side="right", padx=(6,0))
        self.register_colored(self.mini_tab)

        # SUS Controls (buttons inside immutable frame but still should adopt player color)
        ctk.CTkLabel(self.sidebar, text="SUS Controls", font=(self.font_family, 16, "bold"), text_color=self.text_color).pack(pady=(8,0))
        self.sus_controls_frame = ctk.CTkFrame(self.sidebar, fg_color=IMMUTABLE_DARK_BG, corner_radius=10)
        self.sus_controls_frame.pack(pady=6, padx=6, fill="x")
        ctrl_inner = ctk.CTkFrame(self.sus_controls_frame, fg_color=IMMUTABLE_DARK_FRAME, corner_radius=8)
        ctrl_inner.pack(padx=6, pady=6, fill="x")
        self.sus_plus_1 = ctk.CTkButton(ctrl_inner, text="+1 SUS", width=80, command=lambda: self.change_sus(1))
        self.sus_plus_1.grid(row=0,column=0,padx=5,pady=6)
        self.register_colored(self.sus_plus_1)
        self.sus_plus_10 = ctk.CTkButton(ctrl_inner, text="+10 SUS", width=80, command=lambda: self.change_sus(10))
        self.sus_plus_10.grid(row=0,column=1,padx=5,pady=6)
        self.register_colored(self.sus_plus_10)
        self.sus_minus_1 = ctk.CTkButton(ctrl_inner, text="-1 SUS", width=80, command=lambda: self.change_sus(-1))
        self.sus_minus_1.grid(row=1,column=0,padx=5,pady=6)
        self.register_colored(self.sus_minus_1)
        self.sus_minus_10 = ctk.CTkButton(ctrl_inner, text="-10 SUS", width=80, command=lambda: self.change_sus(-10))
        self.sus_minus_10.grid(row=1,column=1,padx=5,pady=6)
        self.register_colored(self.sus_minus_10)

        self.reset_sus_btn = ctk.CTkButton(self.sus_controls_frame, text="Reset All SUS", width=180, command=self.reset_sus)
        self.reset_sus_btn.pack(pady=(4,8))
        self.register_colored(self.reset_sus_btn)

        # SUS Leaderboard immutable dark
        ctk.CTkLabel(self.sidebar, text="SUS Leaderboard", font=(self.font_family, 16, "bold"), text_color=self.text_color).pack(pady=(6,4))
        self.sus_container = ctk.CTkScrollableFrame(self.sidebar, width=320, height=200, corner_radius=8, fg_color=IMMUTABLE_DARK_BG)
        self.sus_container.pack(pady=5)
        self.sus_inner = ctk.CTkFrame(self.sus_container, fg_color=IMMUTABLE_DARK_FRAME, corner_radius=6)
        self.sus_inner.pack(fill="both", expand=True, padx=6, pady=6)
        self.refresh_sus_display()

        # Appearance settings
        settings_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        settings_frame.pack(pady=10, fill="x", padx=6)
        ctk.CTkLabel(settings_frame, text="Customize Appearance", font=(self.font_family, 14, "bold"), text_color=self.text_color).pack(pady=5)
        self.bg_entry = ctk.CTkEntry(settings_frame, placeholder_text="Background color (hex)", width=200, fg_color="white", text_color="black")
        self.bg_entry.pack(side="left", padx=(0,6))
        pick_btn = ctk.CTkButton(settings_frame, text="Pick", width=60, command=self.pick_bg_color)
        pick_btn.pack(side="left", padx=(0,6))
        self.register_colored(pick_btn)

        font_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        font_frame.pack(fill="x", pady=(8,0))
        self.font_entry = ctk.CTkEntry(font_frame, placeholder_text="Font (e.g., Arial)")
        self.font_entry.pack(pady=4, fill="x")
        self.font_size_entry = ctk.CTkEntry(font_frame, placeholder_text="Font size (max 40)")
        self.font_size_entry.pack(pady=4, fill="x")
        apply_btn = ctk.CTkButton(settings_frame, text="Apply Settings", command=self.apply_settings)
        apply_btn.pack(pady=6)
        self.register_colored(apply_btn)

        save_btn = ctk.CTkButton(self.sidebar, text="💾 Save Session", command=self.save_session)
        save_btn.pack(pady=4)
        self.register_colored(save_btn)
        load_btn = ctk.CTkButton(self.sidebar, text="📂 Load Session", command=self.load_session)
        load_btn.pack(pady=4)
        self.register_colored(load_btn)

    # ---------------- Main ----------------
    def build_main(self):
        self.title_label = ctk.CTkLabel(self.main, text="Body Report Log", font=(self.font_family, 18, "bold"), text_color=self.text_color)
        self.title_label.pack(pady=10)

        form = ctk.CTkFrame(self.main, fg_color="transparent")
        form.pack(pady=10)

        self.victim = ctk.CTkOptionMenu(form, values=self.players)
        self.victim.grid(row=0,column=0,padx=5,pady=5)
        self.location = ctk.CTkEntry(form, placeholder_text="Body location (e.g., Electrical)")
        self.location.grid(row=0,column=1,padx=5,pady=5)
        self.nearby = ctk.CTkEntry(form, placeholder_text="Players nearby (comma separated)")
        self.nearby.grid(row=1,column=0,columnspan=2,padx=5,pady=5)
        self.notes = ctk.CTkEntry(form, placeholder_text="Notes")
        self.notes.grid(row=2,column=0,columnspan=2,padx=5,pady=5)
        self.add_body_btn = ctk.CTkButton(form, text="➕ Add Body", width=200, command=self.add_body)
        self.add_body_btn.grid(row=3,column=0,columnspan=2,pady=10)
        self.register_colored(self.add_body_btn)

        # Recorded Bodies area must remain dark and non-editable regardless of GUI bg
        self.log_outer = ctk.CTkFrame(self.main, fg_color=IMMUTABLE_DARK_BG, corner_radius=10)
        self.log_outer.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_frame = ctk.CTkScrollableFrame(self.log_outer, label_text="Recorded Bodies", width=900, height=450, fg_color=IMMUTABLE_DARK_FRAME)
        self.log_frame.pack(padx=8, pady=8, fill="both", expand=True)

    # ---------------- Register / Apply player color ----------------
    def register_colored(self, btn):
        if btn not in self.colored_buttons:
            self.colored_buttons.append(btn)

    def apply_player_color(self, color_hex):
        if not color_hex:
            return
        for b in self.colored_buttons:
            try:
                b.configure(fg_color=color_hex, hover_color=color_hex, text_color=readable_text_color(color_hex))
            except Exception:
                pass

    # ---------------- Font chooser ----------------
    def open_font_chooser(self):
        win = ctk.CTkToplevel(self)
        win.title("Choose Font, Size and Color (ARGB)")
        win.geometry("420x300")
        win.transient(self)
        win.grab_set()

        ctk.CTkLabel(win, text="Select Font", font=(self.font_family, 14, "bold")).pack(pady=(10,6))
        font_var = ctk.StringVar(value=self.font_family)
        font_menu = ctk.CTkOptionMenu(win, values=self.available_fonts, variable=font_var, width=320)
        font_menu.pack(pady=(0,10))

        ctk.CTkLabel(win, text="Select Font Size (max 40)", font=(self.font_family, 12)).pack(pady=(6,0))
        size_var = ctk.IntVar(value=self.base_font_size)
        size_menu = ctk.CTkOptionMenu(win, values=[str(s) for s in range(8, 41)], variable=size_var, width=120)
        size_menu.pack(pady=(0,10))

        ctk.CTkLabel(win, text="Font Color (ARGB)", font=(self.font_family, 12)).pack(pady=(6,0))
        argb_frame = ctk.CTkFrame(win, fg_color="transparent")
        argb_frame.pack(pady=(6,6), padx=8, fill="x")
        a_var = ctk.IntVar(value=self.font_alpha)
        try:
            r_val = int(self.text_color[1:3], 16)
            g_val = int(self.text_color[3:5], 16)
            b_val = int(self.text_color[5:7], 16)
        except Exception:
            r_val, g_val, b_val = 255, 255, 255
        r_var = ctk.IntVar(value=r_val)
        g_var = ctk.IntVar(value=g_val)
        b_var = ctk.IntVar(value=b_val)

        def make_slider(label_text, var, row):
            ctk.CTkLabel(argb_frame, text=label_text, width=20).grid(row=row, column=0, sticky="w", padx=(4,6))
            slider = ctk.CTkSlider(argb_frame, from_=0, to=255, number_of_steps=255, variable=var, width=200)
            slider.grid(row=row, column=1, padx=6, pady=4)
            entry = ctk.CTkEntry(argb_frame, width=48, textvariable=var)
            entry.grid(row=row, column=2, padx=(6,4))

        make_slider("A", a_var, 0)
        make_slider("R", r_var, 1)
        make_slider("G", g_var, 2)
        make_slider("B", b_var, 3)

        preview = ctk.CTkLabel(win, text=" Preview ", width=120, height=30, corner_radius=6)
        preview.pack(pady=(6,8))

        def update_preview(*_):
            a = a_var.get(); r = r_var.get(); g = g_var.get(); b = b_var.get()
            try:
                bg = self.bg_color.lstrip("#"); bg_r = int(bg[0:2], 16); bg_g = int(bg[2:4], 16); bg_b = int(bg[4:6], 16)
            except Exception:
                bg_r, bg_g, bg_b = 255, 255, 255
            alpha = a / 255.0
            blend_r = int(alpha * r + (1 - alpha) * bg_r)
            blend_g = int(alpha * g + (1 - alpha) * bg_g)
            blend_b = int(alpha * b + (1 - alpha) * bg_b)
            hexcol = f"#{blend_r:02x}{blend_g:02x}{blend_b:02x}"
            preview.configure(fg_color=hexcol)

        for v in (a_var, r_var, g_var, b_var):
            v.trace_add("write", update_preview)
        update_preview()

        def apply_font_choice():
            chosen_font = font_var.get()
            chosen_size = int(size_var.get())
            if chosen_size > 40:
                chosen_size = 40
            a = a_var.get(); r = r_var.get(); g = g_var.get(); b = b_var.get()
            hex_rgb = f"#{r:02x}{g:02x}{b:02x}"
            self.font_family = chosen_font
            self.base_font_size = chosen_size
            self.text_color = hex_rgb
            self.font_alpha = int(a)
            self._apply_font_to_widgets()
            win.destroy()

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=(6,10))
        ctk.CTkButton(btn_frame, text="Apply", command=apply_font_choice).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Cancel", command=win.destroy).pack(side="right", padx=8)

    # ---------------- Apply fonts/colors globally (skip immutable backgrounds) ----------------
    def _apply_font_to_widgets(self):
        try:
            self.title_label.configure(font=(self.font_family, max(self.base_font_size + 6, 12), "bold"), text_color=self.text_color)
        except Exception:
            pass

        for parent in (self.sidebar, self.main):
            for child in parent.winfo_children():
                if child in (self.player_selector_outer, self.sus_controls_frame, self.sus_container, self.log_outer):
                    continue
                try:
                    child.configure(font=(self.font_family, self.base_font_size), text_color=self.text_color)
                except Exception:
                    try:
                        for sub in child.winfo_children():
                            if sub in (self.player_selector_outer, self.sus_controls_frame, self.sus_container, self.log_outer):
                                continue
                            try:
                                sub.configure(font=(self.font_family, self.base_font_size), text_color=self.text_color)
                            except Exception:
                                pass
                    except Exception:
                        pass

        self.refresh_sus_display()
        for entry_frame in getattr(self, "log_frame", []).winfo_children() if hasattr(self, "log_frame") else []:
            try:
                for grand in entry_frame.winfo_children():
                    try:
                        grand.configure(font=(self.font_family, self.base_font_size), text_color=self.text_color)
                    except Exception:
                        pass
            except Exception:
                pass

        for name, btn in getattr(self, "player_buttons", {}).items():
            try:
                btn.configure(font=(self.font_family, self.base_font_size))
            except Exception:
                pass

        if self.mini_overlay and self.mini_overlay.winfo_exists():
            try:
                self.mini_overlay.font_family = self.font_family
                self.mini_overlay.base_font_size = self.base_font_size
                self.mini_overlay.text_color = self.text_color
                self.mini_overlay.header.configure(font=(self.font_family, self.base_font_size + 2, "bold"), text_color=self.text_color)
            except Exception:
                pass

    # ---------------- Logic: selection and SUS ----------------
    def select_player(self, name):
        self.selected_player = name
        self.selected_label.configure(text=f"Selected: {name}", text_color=PLAYER_COLORS.get(name, "#000000"), font=(self.font_family, self.base_font_size, "italic"))
        # apply player color to all registered buttons
        color = PLAYER_COLORS.get(name, None)
        if color:
            self.apply_player_color(color)

    def change_sus(self, amount):
        if self.selected_player:
            self.sus[self.selected_player] += amount
            if self.sus[self.selected_player] < 0:
                self.sus[self.selected_player] = 0
            self.refresh_sus_display()

    def reset_sus(self):
        if messagebox.askyesno("Confirm", "Reset all SUS values?"):
            for p in self.sus:
                self.sus[p] = 0
            self.refresh_sus_display()

    def refresh_sus_display(self):
        for child in self.sus_inner.winfo_children():
            child.destroy()
        header_frame = ctk.CTkFrame(self.sus_inner, fg_color="transparent")
        header_frame.pack(fill="x", padx=6, pady=(4,2))
        ctk.CTkLabel(header_frame, text="Color", width=60, anchor="w", font=(self.font_family, 11, "bold"), text_color=IMMUTABLE_TEXT).pack(side="left")
        ctk.CTkLabel(header_frame, text="Player", anchor="w", font=(self.font_family, 11, "bold"), text_color=IMMUTABLE_TEXT).pack(side="left", padx=(8,0))
        ctk.CTkLabel(header_frame, text="SUS", anchor="e", font=(self.font_family, 11, "bold"), text_color=IMMUTABLE_TEXT).pack(side="right")
        sorted_sus = sorted(self.sus.items(), key=lambda x: x[1], reverse=True)
        for name, score in sorted_sus:
            row = ctk.CTkFrame(self.sus_inner, fg_color="transparent")
            row.pack(fill="x", padx=6, pady=3)
            swatch = ctk.CTkLabel(row, text="", width=22, height=18, corner_radius=4)
            swatch.configure(fg_color=PLAYER_COLORS.get(name, "#ffffff"))
            swatch.pack(side="left", padx=(0,8))
            pname = ctk.CTkLabel(row, text=name, anchor="w", font=(self.font_family, 11), text_color=IMMUTABLE_TEXT)
            pname.pack(side="left", padx=(0,10))
            score_lbl = ctk.CTkLabel(row, text=str(score), anchor="e", font=(self.font_family, 11), text_color=IMMUTABLE_TEXT)
            score_lbl.pack(side="right")

    # ---------------- Bodies management ----------------
    def add_body(self):
        victim = self.victim.get().strip()
        location = self.location.get().strip()
        nearby = [n.strip() for n in self.nearby.get().split(",") if n.strip()]
        notes = self.notes.get().strip()
        if not victim or not location:
            messagebox.showwarning("Error", "Please specify at least victim and location.")
            return
        entry = {
            "id": self.next_id,
            "victim": victim,
            "location": location,
            "nearby": nearby,
            "notes": notes,
            "time": datetime.now().strftime("%H:%M:%S")
        }
        self.bodies.insert(0, entry)
        self.next_id += 1
        for n in nearby:
            if n in self.sus:
                self.sus[n] += 1
        self.refresh_sus_display()
        self.add_log_entry_ui(entry)
        self.location.delete(0, "end")
        self.nearby.delete(0, "end")
        self.notes.delete(0, "end")

    def add_log_entry_ui(self, entry):
        card = ctk.CTkFrame(self.log_frame, fg_color=IMMUTABLE_DARK_FRAME, corner_radius=8)
        card.pack(fill="x", padx=8, pady=6)
        header = ctk.CTkLabel(card, text=f"#{entry['id']} {entry['victim']} — {entry['time']}",
                              font=(self.font_family, max(self.base_font_size + 2, 12), "bold"),
                              text_color=PLAYER_COLORS.get(entry['victim'], IMMUTABLE_TEXT))
        header.grid(row=0, column=0, sticky="w", padx=8, pady=(6,2))
        del_btn = ctk.CTkButton(card, text="Delete", width=80, command=lambda e=entry, f=card: self.delete_entry(e, f))
        del_btn.grid(row=0, column=1, sticky="e", padx=8, pady=(6,2))
        self.register_colored(del_btn)
        details = f"Location: {entry['location']}  |  Nearby: {', '.join(entry['nearby']) if entry['nearby'] else 'None'}\nNotes: {entry['notes']}"
        lbl = ctk.CTkLabel(card, text=details, font=(self.font_family, self.base_font_size), wraplength=800, justify="left", text_color=self.text_color)
        lbl.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(0,8))

    def delete_entry(self, entry, frame_widget):
        if messagebox.askyesno("Confirm", f"Delete entry #{entry['id']}?"):
            try:
                self.bodies.remove(entry)
            except ValueError:
                pass
            frame_widget.destroy()

    # ---------------- Notebook ----------------
    def open_notebook(self):
        if self.notebook_window and self.notebook_window.winfo_exists():
            self.notebook_window.lift()
            return
        self.notebook_window = NotebookWindow(self, path=DEFAULT_NOTEBOOK_PATH)

    # ---------------- Appearance / settings ----------------
    def pick_bg_color(self):
        color = colorchooser.askcolor(title="Choose background color", initialcolor=self.bg_color)
        if color and color[1]:
            hex_color = color[1]
            self.bg_entry.delete(0, "end")
            self.bg_entry.insert(0, hex_color)

    def open_settings_color(self):
        color = colorchooser.askcolor(title="Choose GUI background color", initialcolor=self.bg_color)
        if not color or not color[1]:
            return
        hex_color = color[1]
        self.bg_entry.delete(0, "end")
        self.bg_entry.insert(0, hex_color)
        try:
            self.bg_color = hex_color
            self.sidebar.configure(fg_color=self.bg_color)
            self.main.configure(fg_color=self.bg_color)
            self.player_selector_outer.configure(fg_color=IMMUTABLE_DARK_BG)
            try:
                for child in self.player_selector_outer.winfo_children():
                    child.configure(fg_color=IMMUTABLE_DARK_FRAME)
            except Exception:
                pass
            self.sus_controls_frame.configure(fg_color=IMMUTABLE_DARK_BG)
            self.sus_inner.configure(fg_color=IMMUTABLE_DARK_FRAME)
            if hasattr(self, "log_outer"):
                self.log_outer.configure(fg_color=IMMUTABLE_DARK_BG)
                self.log_frame.configure(fg_color=IMMUTABLE_DARK_FRAME)
        except Exception:
            messagebox.showwarning("Warning", "Color applied but some widgets may not support the chosen color.")
        self.refresh_sus_display()
        self._apply_font_to_widgets()

    def apply_settings(self):
        bg = self.bg_entry.get().strip()
        font = self.font_entry.get().strip()
        font_size_text = self.font_size_entry.get().strip()
        if bg:
            try:
                self.bg_color = bg
                self.sidebar.configure(fg_color=self.bg_color)
                self.main.configure(fg_color=self.bg_color)
                self.player_selector_outer.configure(fg_color=IMMUTABLE_DARK_BG)
                try:
                    for child in self.player_selector_outer.winfo_children():
                        child.configure(fg_color=IMMUTABLE_DARK_FRAME)
                except Exception:
                    pass
                self.sus_controls_frame.configure(fg_color=IMMUTABLE_DARK_BG)
                self.sus_inner.configure(fg_color=IMMUTABLE_DARK_FRAME)
                if hasattr(self, "log_outer"):
                    self.log_outer.configure(fg_color=IMMUTABLE_DARK_BG)
                    self.log_frame.configure(fg_color=IMMUTABLE_DARK_FRAME)
            except Exception:
                messagebox.showwarning("Warning", "Invalid background color value. Use a valid hex like #ffffff.")
        if font:
            self.font_family = font
        if font_size_text:
            try:
                fs = int(font_size_text)
                if fs > 40:
                    fs = 40
                if fs < 6:
                    fs = 6
                self.base_font_size = fs
            except ValueError:
                messagebox.showwarning("Warning", "Font size must be an integer.")
        self._apply_font_to_widgets()
        messagebox.showinfo("Applied", "Appearance settings applied.")

    # ---------------- Save / Load ----------------
    def save_session(self):
        data = {
            "sus": self.sus,
            "bodies": self.bodies,
            "next_id": self.next_id,
            "settings": {
                "bg_color": self.bg_color,
                "font_family": self.font_family,
                "base_font_size": self.base_font_size,
                "text_color": self.text_color,
                "font_alpha": self.font_alpha
            }
        }
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Saved", f"Session saved to {path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save session: {e}")

    def load_session(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
            return
        if "sus" in data and isinstance(data["sus"], dict):
            self.sus = {k: int(v) for k, v in data["sus"].items()}
        if "bodies" in data and isinstance(data["bodies"], list):
            self.bodies = data["bodies"]
        if "next_id" in data:
            try:
                self.next_id = int(data["next_id"])
            except Exception:
                pass
        settings = data.get("settings", {})
        self.bg_color = settings.get("bg_color", self.bg_color)
        self.font_family = settings.get("font_family", self.font_family)
        self.base_font_size = settings.get("base_font_size", self.base_font_size)
        self.text_color = settings.get("text_color", self.text_color)
        self.font_alpha = settings.get("font_alpha", self.font_alpha)
        try:
            self.sidebar.configure(fg_color=self.bg_color)
            self.main.configure(fg_color=self.bg_color)
            self.player_selector_outer.configure(fg_color=IMMUTABLE_DARK_BG)
            try:
                for child in self.player_selector_outer.winfo_children():
                    child.configure(fg_color=IMMUTABLE_DARK_FRAME)
            except Exception:
                pass
            self.sus_controls_frame.configure(fg_color=IMMUTABLE_DARK_BG)
            self.sus_inner.configure(fg_color=IMMUTABLE_DARK_FRAME)
            if hasattr(self, "log_outer"):
                self.log_outer.configure(fg_color=IMMUTABLE_DARK_BG)
                self.log_frame.configure(fg_color=IMMUTABLE_DARK_FRAME)
        except Exception:
            pass
        self.refresh_sus_display()
        for child in self.log_frame.winfo_children():
            child.destroy()
        for entry in list(self.bodies):
            self.add_log_entry_ui(entry)
        self._apply_font_to_widgets()
        messagebox.showinfo("Loaded", "Session loaded successfully.")

    def open_mini_overlay(self):
        if self.mini_overlay and self.mini_overlay.winfo_exists():
            self.mini_overlay.lift()
            return
        self.mini_overlay = MiniOverlay(self, top_n=5)

# ---------------- Run App ----------------
if __name__ == "__main__":
    app = AmongUsApp()
    app.mainloop()
