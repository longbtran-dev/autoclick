"""
Auto Clicker GUI Module
Modern Dark-themed Graphical User Interface built with Tkinter.
Features:
- Action buttons placed prominently at the top so they are always visible on any screen size.
- 2-column compact dashboard layout (fits 1366x768 and scaled laptop screens).
- Global hotkeys (F6 toggle, F7 pick coordinates).
- Precision timer, jitter delay, custom repeat count, and live stats.
"""

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Optional

import keyboard

from autoclicker_core import AutoClicker, get_current_cursor_pos
from config_manager import load_config, save_config

# Color Palette (Modern Dark Theme)
BG_MAIN = "#181825"
BG_CARD = "#1e1e2e"
BG_INPUT = "#11111b"
BORDER_COLOR = "#313244"
TEXT_MAIN = "#cdd6f4"
TEXT_MUTED = "#a6adc8"
ACCENT_GREEN = "#a6e3a1"
ACCENT_RED = "#f38ba8"
ACCENT_BLUE = "#89b4fa"
ACCENT_YELLOW = "#f9e2af"
ACCENT_PEACH = "#fab387"


class AutoClickerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Auto Clicker Pro - Điều Khiển Tự Động")
        # Compact dimensions to guarantee 100% visibility on all displays/laptops
        self.root.geometry("650x540")
        self.root.minsize(620, 500)
        self.root.configure(bg=BG_MAIN)

        # Load persisted configuration
        self.config = load_config()

        # Engine instance
        self.clicker = AutoClicker()
        self.clicker.on_click_callback = self._on_click_update
        self.clicker.on_state_change = self._on_state_change

        # Global hotkey handles
        self._current_toggle_hotkey = ""
        self._current_pick_hotkey = ""
        self._is_picking_coord = False

        # Build UI with Top-Action-First Layout
        self._setup_styles()
        self._build_top_header_and_controls()
        self._build_dashboard_body()
        self._build_bottom_bar()

        # Apply initial settings
        self._apply_loaded_config()

        # Setup Hotkeys
        self._register_hotkeys()

        # Periodic UI update (mouse coordinate, stats)
        self._schedule_periodic_updates()

        # Clean exit handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_styles(self) -> None:
        """Configure ttk styles to match dark theme."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Main.TFrame", background=BG_MAIN)
        style.configure("Card.TFrame", background=BG_CARD)

        style.configure(
            "CardTitle.TLabel",
            background=BG_CARD,
            foreground=ACCENT_BLUE,
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "Normal.TLabel",
            background=BG_CARD,
            foreground=TEXT_MAIN,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Muted.TLabel",
            background=BG_CARD,
            foreground=TEXT_MUTED,
            font=("Segoe UI", 8),
        )

        style.configure(
            "Dark.TCombobox",
            fieldbackground=BG_INPUT,
            background=BG_CARD,
            foreground=TEXT_MAIN,
            darkcolor=BORDER_COLOR,
            lightcolor=BORDER_COLOR,
        )

    def _build_top_header_and_controls(self) -> None:
        """
        Header and BIG Action Buttons placed prominently at the TOP.
        Ensures the START / STOP buttons are NEVER hidden or scrolled off-screen.
        """
        top_container = tk.Frame(self.root, bg=BG_MAIN, padx=12, pady=8)
        top_container.pack(fill="x")

        # 1. Header Info Row (Title, Status Badge, Live Stats)
        info_row = tk.Frame(top_container, bg=BG_MAIN)
        info_row.pack(fill="x", pady=(0, 6))

        # Title & Subtitle
        title_box = tk.Frame(info_row, bg=BG_MAIN)
        title_box.pack(side="left")

        lbl_title = tk.Label(
            title_box,
            text="⚡ AUTO CLICKER PRO",
            font=("Segoe UI", 13, "bold"),
            bg=BG_MAIN,
            fg=TEXT_MAIN,
        )
        lbl_title.pack(anchor="w")

        # Right-side status and stats
        status_box = tk.Frame(info_row, bg=BG_MAIN)
        status_box.pack(side="right")

        self.lbl_stat_clicks = tk.Label(
            status_box,
            text="Đã click: 0",
            bg="#11111b",
            fg=ACCENT_GREEN,
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=3,
        )
        self.lbl_stat_clicks.pack(side="left", padx=4)

        self.lbl_stat_cps = tk.Label(
            status_box,
            text="0.0 CPS",
            bg="#11111b",
            fg=ACCENT_YELLOW,
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=3,
        )
        self.lbl_stat_cps.pack(side="left", padx=4)

        self.status_badge = tk.Label(
            status_box,
            text="⏹ ĐÃ DỪNG",
            font=("Segoe UI", 9, "bold"),
            bg="#313244",
            fg=ACCENT_RED,
            padx=12,
            pady=3,
        )
        self.status_badge.pack(side="left", padx=(4, 0))

        # 2. PROMINENT ACTION BUTTONS (Start & Stop) - High visibility!
        btn_box = tk.Frame(top_container, bg=BORDER_COLOR, padx=1, pady=1)
        btn_box.pack(fill="x", pady=(2, 4))

        btn_inner = tk.Frame(btn_box, bg=BG_CARD, padx=8, pady=8)
        btn_inner.pack(fill="x")

        # START BUTTON (Green, Bold, Big)
        self.btn_start = tk.Button(
            btn_inner,
            text="▶ BẮT ĐẦU CHẠY (Phím F6)",
            command=self.start_clicker,
            bg="#1b4d3e",
            fg="#a6e3a1",
            activebackground="#266d58",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            pady=8,
            cursor="hand2",
        )
        self.btn_start.pack(side="left", expand=True, fill="x", padx=(0, 6))

        # STOP BUTTON (Red, Bold, Big)
        self.btn_stop = tk.Button(
            btn_inner,
            text="⏹ DỪNG LẠI (Phím F6)",
            command=self.stop_clicker,
            bg="#4a2530",
            fg="#f38ba8",
            activebackground="#6b3545",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            pady=8,
            cursor="hand2",
            state="disabled",
        )
        self.btn_stop.pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _create_subcard(self, parent: tk.Widget, title: str) -> tk.Frame:
        """Create a compact card container."""
        outer = tk.Frame(parent, bg=BORDER_COLOR, padx=1, pady=1)
        outer.pack(fill="both", expand=True, pady=4)

        inner = tk.Frame(outer, bg=BG_CARD, padx=10, pady=8)
        inner.pack(fill="both", expand=True)

        if title:
            lbl = tk.Label(
                inner,
                text=title,
                bg=BG_CARD,
                fg=ACCENT_BLUE,
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            )
            lbl.pack(fill="x", pady=(0, 4))

        return inner

    def _build_dashboard_body(self) -> None:
        """2-Column Layout for Settings (Left: Interval & Repeat, Right: Options & Location)."""
        body_frame = tk.Frame(self.root, bg=BG_MAIN, padx=12, pady=2)
        body_frame.pack(fill="both", expand=True)

        # Left Column
        left_col = tk.Frame(body_frame, bg=BG_MAIN)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._build_interval_section(left_col)
        self._build_repeat_section(left_col)

        # Right Column
        right_col = tk.Frame(body_frame, bg=BG_MAIN)
        right_col.pack(side="right", fill="both", expand=True, padx=(6, 0))

        self._build_mouse_options_section(right_col)
        self._build_location_section(right_col)

    def _build_interval_section(self, parent: tk.Widget) -> None:
        """Left Column Card 1: Interval and Jitter."""
        card = self._create_subcard(parent, "⏱ THỜI GIAN CLICK (INTERVAL)")

        inputs_frame = tk.Frame(card, bg=BG_CARD)
        inputs_frame.pack(fill="x", pady=2)

        self.var_hours = tk.StringVar(value=str(self.config.get("hours", 0)))
        self.var_mins = tk.StringVar(value=str(self.config.get("minutes", 0)))
        self.var_secs = tk.StringVar(value=str(self.config.get("seconds", 0)))
        self.var_ms = tk.StringVar(value=str(self.config.get("milliseconds", 100)))

        fields = [
            ("Giờ", self.var_hours, 4),
            ("Phút", self.var_mins, 4),
            ("Giây", self.var_secs, 4),
            ("Mili-giây", self.var_ms, 6),
        ]

        for label_text, var, width in fields:
            sub = tk.Frame(inputs_frame, bg=BG_CARD)
            sub.pack(side="left", expand=True, fill="x", padx=2)

            lbl = tk.Label(
                sub, text=label_text, bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8)
            )
            lbl.pack(anchor="w")

            ent = tk.Entry(
                sub,
                textvariable=var,
                width=width,
                bg=BG_INPUT,
                fg=TEXT_MAIN,
                insertbackground=ACCENT_BLUE,
                relief="flat",
                font=("Segoe UI", 9, "bold"),
                justify="center",
            )
            ent.pack(fill="x", pady=1, ipady=2)

        # Jitter row
        jitter_row = tk.Frame(card, bg=BG_CARD)
        jitter_row.pack(fill="x", pady=(4, 0))

        self.var_use_jitter = tk.BooleanVar(value=self.config.get("use_jitter", False))
        chk_jit = tk.Checkbutton(
            jitter_row,
            text="Độ trễ ngẫu nhiên: ±",
            variable=self.var_use_jitter,
            bg=BG_CARD,
            fg=TEXT_MAIN,
            selectcolor=BG_INPUT,
            activebackground=BG_CARD,
            activeforeground=TEXT_MAIN,
            font=("Segoe UI", 8),
        )
        chk_jit.pack(side="left")

        self.var_jitter_ms = tk.StringVar(value=str(self.config.get("jitter_ms", 15)))
        ent_jit = tk.Entry(
            jitter_row,
            textvariable=self.var_jitter_ms,
            width=4,
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=ACCENT_BLUE,
            relief="flat",
            font=("Segoe UI", 8),
            justify="center",
        )
        ent_jit.pack(side="left", padx=2, ipady=1)

        lbl_jit_ms = tk.Label(
            jitter_row, text="ms", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8)
        )
        lbl_jit_ms.pack(side="left")

    def _build_repeat_section(self, parent: tk.Widget) -> None:
        """Left Column Card 2: Repeat Mode."""
        card = self._create_subcard(parent, "🔁 SỐ LẦN LẶP (REPEAT)")

        self.var_repeat_mode = tk.StringVar(
            value=self.config.get("repeat_mode", "infinite")
        )

        rb_inf = tk.Radiobutton(
            card,
            text="Lặp vô tận (cho đến khi bấm Dừng)",
            value="infinite",
            variable=self.var_repeat_mode,
            bg=BG_CARD,
            fg=TEXT_MAIN,
            selectcolor=BG_INPUT,
            activebackground=BG_CARD,
            activeforeground=TEXT_MAIN,
            font=("Segoe UI", 8),
        )
        rb_inf.pack(anchor="w", pady=1)

        row_cnt = tk.Frame(card, bg=BG_CARD)
        row_cnt.pack(fill="x", pady=1)

        rb_cnt = tk.Radiobutton(
            row_cnt,
            text="Lặp cố định:",
            value="count",
            variable=self.var_repeat_mode,
            bg=BG_CARD,
            fg=TEXT_MAIN,
            selectcolor=BG_INPUT,
            activebackground=BG_CARD,
            activeforeground=TEXT_MAIN,
            font=("Segoe UI", 8),
        )
        rb_cnt.pack(side="left")

        self.var_repeat_count = tk.StringVar(
            value=str(self.config.get("repeat_count", 100))
        )
        ent_cnt = tk.Entry(
            row_cnt,
            textvariable=self.var_repeat_count,
            width=6,
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=ACCENT_BLUE,
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            justify="center",
        )
        ent_cnt.pack(side="left", padx=4, ipady=1)

        lbl_times = tk.Label(
            row_cnt, text="lần", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8)
        )
        lbl_times.pack(side="left")

    def _build_mouse_options_section(self, parent: tk.Widget) -> None:
        """Right Column Card 1: Mouse Button & Click Type."""
        card = self._create_subcard(parent, "🖱 TÙY CHỌN CHUỘT (OPTIONS)")

        row = tk.Frame(card, bg=BG_CARD)
        row.pack(fill="x")

        # Buttons (Left, Right, Middle)
        b_frame = tk.Frame(row, bg=BG_CARD)
        b_frame.pack(side="left", expand=True, fill="both")

        lbl_btn = tk.Label(
            b_frame, text="Phím chuột:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8)
        )
        lbl_btn.pack(anchor="w")

        self.var_button = tk.StringVar(value=self.config.get("mouse_button", "left"))
        for text, val in [("Chuột trái", "left"), ("Chuột phải", "right"), ("Chuột giữa", "middle")]:
            rb = tk.Radiobutton(
                b_frame,
                text=text,
                value=val,
                variable=self.var_button,
                bg=BG_CARD,
                fg=TEXT_MAIN,
                selectcolor=BG_INPUT,
                activebackground=BG_CARD,
                activeforeground=TEXT_MAIN,
                font=("Segoe UI", 8),
            )
            rb.pack(anchor="w", pady=1)

        # Click Types
        t_frame = tk.Frame(row, bg=BG_CARD)
        t_frame.pack(side="left", expand=True, fill="both")

        lbl_typ = tk.Label(
            t_frame, text="Kiểu click:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8)
        )
        lbl_typ.pack(anchor="w")

        self.var_click_type = tk.StringVar(value=self.config.get("click_type", "single"))
        for text, val in [("Click đơn", "single"), ("Click đúp", "double"), ("3 lần", "triple"), ("Giữ chuột", "hold")]:
            rb = tk.Radiobutton(
                t_frame,
                text=text,
                value=val,
                variable=self.var_click_type,
                bg=BG_CARD,
                fg=TEXT_MAIN,
                selectcolor=BG_INPUT,
                activebackground=BG_CARD,
                activeforeground=TEXT_MAIN,
                font=("Segoe UI", 8),
            )
            rb.pack(anchor="w", pady=1)

    def _build_location_section(self, parent: tk.Widget) -> None:
        """Right Column Card 2: Cursor Position (Current vs Fixed)."""
        card = self._create_subcard(parent, "📍 VỊ TRÍ CON TRỎ (LOCATION)")

        self.var_location_mode = tk.StringVar(
            value=self.config.get("location_mode", "current")
        )

        rb_curr = tk.Radiobutton(
            card,
            text="Tại vị trí chuột hiện tại",
            value="current",
            variable=self.var_location_mode,
            bg=BG_CARD,
            fg=TEXT_MAIN,
            selectcolor=BG_INPUT,
            activebackground=BG_CARD,
            activeforeground=TEXT_MAIN,
            font=("Segoe UI", 8),
        )
        rb_curr.pack(anchor="w", pady=1)

        row_fix = tk.Frame(card, bg=BG_CARD)
        row_fix.pack(fill="x", pady=2)

        rb_fix = tk.Radiobutton(
            row_fix,
            text="Tọa độ cố định:",
            value="fixed",
            variable=self.var_location_mode,
            bg=BG_CARD,
            fg=TEXT_MAIN,
            selectcolor=BG_INPUT,
            activebackground=BG_CARD,
            activeforeground=TEXT_MAIN,
            font=("Segoe UI", 8),
        )
        rb_fix.pack(side="left")

        lbl_x = tk.Label(row_fix, text="X:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8))
        lbl_x.pack(side="left")
        self.var_fixed_x = tk.StringVar(value=str(self.config.get("fixed_x", 500)))
        ent_x = tk.Entry(
            row_fix,
            textvariable=self.var_fixed_x,
            width=5,
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=ACCENT_BLUE,
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            justify="center",
        )
        ent_x.pack(side="left", padx=2, ipady=1)

        lbl_y = tk.Label(row_fix, text="Y:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8))
        lbl_y.pack(side="left", padx=(4, 0))
        self.var_fixed_y = tk.StringVar(value=str(self.config.get("fixed_y", 500)))
        ent_y = tk.Entry(
            row_fix,
            textvariable=self.var_fixed_y,
            width=5,
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=ACCENT_BLUE,
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            justify="center",
        )
        ent_y.pack(side="left", padx=2, ipady=1)

        # Button pick coordinate
        self.btn_pick_coord = tk.Button(
            row_fix,
            text="📍 Lấy [F7]",
            command=self._start_pick_coordinate,
            bg="#313244",
            fg=ACCENT_PEACH,
            activebackground="#45475a",
            activeforeground=ACCENT_PEACH,
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=1,
            cursor="hand2",
        )
        self.btn_pick_coord.pack(side="left", padx=(6, 0))

        self.lbl_pick_hint = tk.Label(
            card,
            text="",
            bg=BG_CARD,
            fg=ACCENT_PEACH,
            font=("Segoe UI", 8, "italic"),
        )
        self.lbl_pick_hint.pack(anchor="w")

    def _build_bottom_bar(self) -> None:
        """Bottom toolbar: Hotkey selector, Always on Top, Reset, and Live Mouse position."""
        bottom_frame = tk.Frame(self.root, bg="#11111b", padx=12, pady=6)
        bottom_frame.pack(side="bottom", fill="x")

        # Left controls
        lbl_hk = tk.Label(
            bottom_frame, text="Phím tắt Bật/Tắt:", bg="#11111b", fg=TEXT_MAIN, font=("Segoe UI", 8)
        )
        lbl_hk.pack(side="left")

        self.cbo_hotkey = ttk.Combobox(
            bottom_frame,
            values=["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
            width=5,
            state="readonly",
        )
        self.cbo_hotkey.set(self.config.get("hotkey_toggle", "F6"))
        self.cbo_hotkey.pack(side="left", padx=(4, 12))
        self.cbo_hotkey.bind("<<ComboboxSelected>>", self._on_hotkey_changed)

        self.var_always_top = tk.BooleanVar(value=self.config.get("always_on_top", True))
        chk_top = tk.Checkbutton(
            bottom_frame,
            text="📌 Luôn nổi trên cùng",
            variable=self.var_always_top,
            command=self._toggle_always_on_top,
            bg="#11111b",
            fg=TEXT_MAIN,
            selectcolor=BG_INPUT,
            activebackground="#11111b",
            activeforeground=TEXT_MAIN,
            font=("Segoe UI", 8),
        )
        chk_top.pack(side="left", padx=(0, 12))

        btn_reset = tk.Button(
            bottom_frame,
            text="🔄 Reset đếm",
            command=self._reset_counters,
            bg="#313244",
            fg=TEXT_MAIN,
            activebackground="#45475a",
            activeforeground=TEXT_MAIN,
            relief="flat",
            font=("Segoe UI", 8),
            padx=6,
            pady=1,
            cursor="hand2",
        )
        btn_reset.pack(side="left")

        # Right: Live mouse tracker
        self.lbl_live_cursor = tk.Label(
            bottom_frame,
            text="Con trỏ: X=0 | Y=0",
            bg="#11111b",
            fg=TEXT_MUTED,
            font=("Segoe UI", 8),
        )
        self.lbl_live_cursor.pack(side="right")

    def _apply_loaded_config(self) -> None:
        """Apply loaded configuration values to window attributes."""
        self._toggle_always_on_top()

    def _toggle_always_on_top(self) -> None:
        """Update window topmost attribute."""
        is_top = self.var_always_top.get()
        self.root.attributes("-topmost", is_top)

    def _parse_interval_ms(self) -> float:
        """Calculate total milliseconds from hours, mins, secs, ms entries."""
        try:
            h = float(self.var_hours.get().strip() or 0)
            m = float(self.var_mins.get().strip() or 0)
            s = float(self.var_secs.get().strip() or 0)
            ms = float(self.var_ms.get().strip() or 0)
            total = (h * 3600 + m * 60 + s) * 1000 + ms
            return max(0.5, total)
        except ValueError:
            return 100.0

    def _gather_config(self) -> dict:
        """Gather current UI parameters into a config dict."""
        interval_ms = self._parse_interval_ms()

        jitter_ms = 0.0
        if self.var_use_jitter.get():
            try:
                jitter_ms = max(0.0, float(self.var_jitter_ms.get().strip() or 0))
            except ValueError:
                jitter_ms = 0.0

        try:
            fixed_x = int(self.var_fixed_x.get().strip() or 0)
            fixed_y = int(self.var_fixed_y.get().strip() or 0)
        except ValueError:
            fixed_x, fixed_y = 0, 0

        try:
            repeat_count = max(1, int(self.var_repeat_count.get().strip() or 100))
        except ValueError:
            repeat_count = 100

        return {
            "interval_ms": interval_ms,
            "random_jitter_ms": jitter_ms,
            "mouse_button": self.var_button.get(),
            "click_type": self.var_click_type.get(),
            "location_mode": self.var_location_mode.get(),
            "fixed_x": fixed_x,
            "fixed_y": fixed_y,
            "repeat_mode": self.var_repeat_mode.get(),
            "repeat_count": repeat_count,
        }

    def start_clicker(self) -> None:
        """Start auto clicker with current settings."""
        if self.clicker.is_running:
            return

        cfg = self._gather_config()
        self.clicker.set_config(**cfg)
        self.clicker.start()

    def stop_clicker(self) -> None:
        """Stop auto clicker."""
        if not self.clicker.is_running:
            return
        self.clicker.stop()

    def toggle_clicker(self) -> None:
        """Toggle auto clicker start/stop (called by hotkey or button)."""
        if self.clicker.is_running:
            self.stop_clicker()
        else:
            self.start_clicker()

    def _on_state_change(self, is_running: bool) -> None:
        """Callback from engine when state changes. Thread-safe GUI dispatch."""
        self.root.after(0, self._update_ui_state, is_running)

    def _update_ui_state(self, is_running: bool) -> None:
        """Update GUI elements when running state toggles."""
        if is_running:
            self.status_badge.config(
                text="▶ ĐANG CHẠY",
                bg="#1e3a2f",
                fg=ACCENT_GREEN,
            )
            self.btn_start.config(state="disabled", bg="#152b22")
            self.btn_stop.config(state="normal", bg="#992b43")
        else:
            self.status_badge.config(
                text="⏹ ĐÃ DỪNG",
                bg="#313244",
                fg=ACCENT_RED,
            )
            self.btn_start.config(state="normal", bg="#1b4d3e")
            self.btn_stop.config(state="disabled", bg="#4a2530")

    def _on_click_update(self, total_clicks: int, current_cps: float) -> None:
        """Callback from engine on each click."""
        self.root.after_idle(self._update_stats_display, total_clicks, current_cps)

    def _update_stats_display(self, total_clicks: int, current_cps: float) -> None:
        """Update total clicks and CPS display labels."""
        self.lbl_stat_clicks.config(text=f"Đã click: {total_clicks:,}")
        self.lbl_stat_cps.config(text=f"{current_cps:.1f} CPS")

    def _reset_counters(self) -> None:
        """Reset click counters."""
        self.clicker.reset_counter()
        self.lbl_stat_clicks.config(text="Đã click: 0")
        self.lbl_stat_cps.config(text="0.0 CPS")

    def _start_pick_coordinate(self) -> None:
        """Initiate coordinate picking mode."""
        self._is_picking_coord = True
        self.btn_pick_coord.config(
            text="⏳ Bấm F7", bg="#fab387", fg="#11111b"
        )
        self.lbl_pick_hint.config(
            text="👉 Di chuột tới điểm cần click rồi bấm F7 để lưu!"
        )

    def _confirm_pick_coordinate(self) -> None:
        """Confirm and capture current mouse position."""
        x, y = get_current_cursor_pos()
        self.var_fixed_x.set(str(x))
        self.var_fixed_y.set(str(y))
        self.var_location_mode.set("fixed")

        self._is_picking_coord = False
        self.btn_pick_coord.config(
            text="📍 Lấy [F7]", bg="#313244", fg=ACCENT_PEACH
        )
        self.lbl_pick_hint.config(
            text=f"✓ Đã lưu: X={x}, Y={y}"
        )

    def _register_hotkeys(self) -> None:
        """Register global system hotkeys for Start/Stop and Pick Coordinate."""
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

        toggle_key = self.cbo_hotkey.get().strip().upper()
        pick_key = "F7"

        self._current_toggle_hotkey = toggle_key
        self._current_pick_hotkey = pick_key

        self.btn_start.config(text=f"▶ BẮT ĐẦU CHẠY (Phím {toggle_key})")
        self.btn_stop.config(text=f"⏹ DỪNG LẠI (Phím {toggle_key})")

        def on_toggle_pressed():
            self.root.after(0, self.toggle_clicker)

        def on_pick_pressed():
            self.root.after(0, self._confirm_pick_coordinate)

        try:
            keyboard.add_hotkey(toggle_key.lower(), on_toggle_pressed)
            if toggle_key.upper() != pick_key.upper():
                keyboard.add_hotkey(pick_key.lower(), on_pick_pressed)
        except Exception as e:
            print(f"[Warning] Could not bind hotkeys: {e}")

    def _on_hotkey_changed(self, event=None) -> None:
        """User selected a new hotkey from the combobox."""
        self._register_hotkeys()

    def _schedule_periodic_updates(self) -> None:
        """Periodic timer (every 150ms) to update live cursor position with minimal overhead."""
        try:
            x, y = get_current_cursor_pos()
            self.lbl_live_cursor.config(text=f"Con trỏ: X={x} | Y={y}")
        except Exception:
            pass

        self.root.after(150, self._schedule_periodic_updates)

    def _on_closing(self) -> None:
        """Save settings, stop engine, and clean up on exit."""
        if self.clicker.is_running:
            self.clicker.stop()

        try:
            keyboard.unhook_all()
        except Exception:
            pass

        config_to_save = {
            "hours": int(self.var_hours.get().strip() or 0),
            "minutes": int(self.var_mins.get().strip() or 0),
            "seconds": int(self.var_secs.get().strip() or 0),
            "milliseconds": float(self.var_ms.get().strip() or 100),
            "use_jitter": self.var_use_jitter.get(),
            "jitter_ms": float(self.var_jitter_ms.get().strip() or 15),
            "mouse_button": self.var_button.get(),
            "click_type": self.var_click_type.get(),
            "location_mode": self.var_location_mode.get(),
            "fixed_x": int(self.var_fixed_x.get().strip() or 0),
            "fixed_y": int(self.var_fixed_y.get().strip() or 0),
            "repeat_mode": self.var_repeat_mode.get(),
            "repeat_count": int(self.var_repeat_count.get().strip() or 100),
            "hotkey_toggle": self.cbo_hotkey.get(),
            "hotkey_pick": "F7",
            "always_on_top": self.var_always_top.get(),
        }
        save_config(config_to_save)

        self.root.destroy()
