"""
AutoClicker Core Module
High-precision, multi-threaded mouse automation engine using Windows API.
Optimized for 0% idle CPU overhead (no aggressive spin-waiting).
"""

import ctypes
import ctypes.wintypes
import random
import threading
import time
from typing import Callable, Optional, Tuple

# Windows API Setup
user32 = ctypes.windll.user32
winmm = ctypes.windll.winmm

# Mouse Event Flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def get_current_cursor_pos() -> Tuple[int, int]:
    """Get the current cursor position (X, Y) across all monitors."""
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


def set_cursor_pos(x: int, y: int) -> None:
    """Move cursor directly to specified screen coordinate."""
    user32.SetCursorPos(int(x), int(y))


class AutoClicker:
    """
    High-performance, CPU-friendly AutoClicker engine.
    Uses Win32 mouse_event and timeBeginPeriod for millisecond precision without CPU pegging.
    """

    def __init__(self):
        self._is_running = False
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

        # Configuration parameters
        self.interval_ms: float = 100.0
        self.random_jitter_ms: float = 0.0
        self.mouse_button: str = "left"
        self.click_type: str = "single"
        self.location_mode: str = "current"
        self.fixed_x: int = 0
        self.fixed_y: int = 0
        self.repeat_mode: str = "infinite"
        self.repeat_count: int = 100

        # Statistics
        self.total_clicks: int = 0
        self.session_clicks: int = 0
        self.start_time: float = 0.0
        self.current_cps: float = 0.0
        self._last_ui_update: float = 0.0

        # Callbacks
        self.on_click_callback: Optional[Callable[[int, float], None]] = None
        self.on_state_change: Optional[Callable[[bool], None]] = None

        # Internal state
        self._is_holding = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def set_config(
        self,
        interval_ms: float = 100.0,
        random_jitter_ms: float = 0.0,
        mouse_button: str = "left",
        click_type: str = "single",
        location_mode: str = "current",
        fixed_x: int = 0,
        fixed_y: int = 0,
        repeat_mode: str = "infinite",
        repeat_count: int = 100,
    ) -> None:
        self.interval_ms = max(1.0, float(interval_ms))
        self.random_jitter_ms = max(0.0, float(random_jitter_ms))
        self.mouse_button = mouse_button.lower()
        self.click_type = click_type.lower()
        self.location_mode = location_mode.lower()
        self.fixed_x = int(fixed_x)
        self.fixed_y = int(fixed_y)
        self.repeat_mode = repeat_mode.lower()
        self.repeat_count = max(1, int(repeat_count))

    def start(self) -> bool:
        if self._is_running:
            return False

        self._is_running = True
        self._stop_event.clear()
        self.session_clicks = 0
        self.start_time = time.perf_counter()
        self.current_cps = 0.0
        self._last_ui_update = self.start_time

        if self.on_state_change:
            try:
                self.on_state_change(True)
            except Exception:
                pass

        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()
        return True

    def stop(self) -> bool:
        if not self._is_running:
            return False

        self._is_running = False
        self._stop_event.set()

        if self._is_holding:
            self._release_held_button()

        if self.on_state_change:
            try:
                self.on_state_change(False)
            except Exception:
                pass

        return True

    def toggle(self) -> bool:
        if self._is_running:
            self.stop()
            return False
        else:
            self.start()
            return True

    def reset_counter(self) -> None:
        self.total_clicks = 0
        self.session_clicks = 0
        self.current_cps = 0.0
        if self.on_click_callback:
            try:
                self.on_click_callback(0, 0.0)
            except Exception:
                pass

    def _precision_sleep(self, duration_sec: float) -> None:
        """
        CPU-friendly sleep routine.
        Uses time.sleep with timeBeginPeriod(1) and yields CPU via time.sleep(0),
        preventing 100% CPU lock while maintaining millisecond precision.
        """
        if duration_sec <= 0:
            return

        end_time = time.perf_counter() + duration_sec

        # Sleep the majority of time
        while time.perf_counter() < end_time:
            if self._stop_event.is_set():
                break
            rem = end_time - time.perf_counter()
            if rem > 0.003:
                time.sleep(rem - 0.002)
            elif rem > 0.0005:
                time.sleep(0.0005)
            else:
                # Yield CPU time slice to other threads
                time.sleep(0)

    def _press_and_release(self, down_flag: int, up_flag: int, hold_delay_sec: float = 0.002) -> None:
        user32.mouse_event(down_flag, 0, 0, 0, 0)
        if hold_delay_sec > 0:
            self._precision_sleep(hold_delay_sec)
        user32.mouse_event(up_flag, 0, 0, 0, 0)

    def _get_button_flags(self) -> Tuple[int, int]:
        if self.mouse_button == "right":
            return MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
        elif self.mouse_button == "middle":
            return MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP
        else:
            return MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP

    def _release_held_button(self) -> None:
        _, up_flag = self._get_button_flags()
        user32.mouse_event(up_flag, 0, 0, 0, 0)
        self._is_holding = False

    def _execute_click(self) -> None:
        if self.location_mode == "fixed":
            set_cursor_pos(self.fixed_x, self.fixed_y)

        down_flag, up_flag = self._get_button_flags()

        if self.click_type == "single":
            self._press_and_release(down_flag, up_flag, 0.002)
        elif self.click_type == "double":
            self._press_and_release(down_flag, up_flag, 0.002)
            self._precision_sleep(0.035)
            self._press_and_release(down_flag, up_flag, 0.002)
        elif self.click_type == "triple":
            for i in range(3):
                self._press_and_release(down_flag, up_flag, 0.002)
                if i < 2:
                    self._precision_sleep(0.030)
        elif self.click_type == "hold":
            if not self._is_holding:
                user32.mouse_event(down_flag, 0, 0, 0, 0)
                self._is_holding = True

    def _run_loop(self) -> None:
        # Request 1ms resolution from OS
        winmm.timeBeginPeriod(1)

        try:
            while not self._stop_event.is_set():
                self._execute_click()
                self.total_clicks += 1
                self.session_clicks += 1

                now = time.perf_counter()
                elapsed = max(0.0001, now - self.start_time)
                self.current_cps = self.session_clicks / elapsed

                # Throttle UI notifications to max 10 times per second to prevent GUI lag
                is_last_click = (self.repeat_mode == "count" and self.session_clicks >= self.repeat_count)
                if (now - self._last_ui_update >= 0.1) or is_last_click:
                    self._last_ui_update = now
                    if self.on_click_callback:
                        try:
                            self.on_click_callback(self.total_clicks, self.current_cps)
                        except Exception:
                            pass

                if is_last_click:
                    break

                base_delay_ms = self.interval_ms
                if self.random_jitter_ms > 0:
                    jitter = random.uniform(-self.random_jitter_ms, self.random_jitter_ms)
                    delay_ms = max(1.0, base_delay_ms + jitter)
                else:
                    delay_ms = base_delay_ms

                self._precision_sleep(delay_ms / 1000.0)

        finally:
            if self._is_holding:
                self._release_held_button()

            winmm.timeEndPeriod(1)
            self._is_running = False

            if self.on_state_change:
                try:
                    self.on_state_change(False)
                except Exception:
                    pass
