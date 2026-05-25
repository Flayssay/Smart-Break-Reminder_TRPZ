import os
import json
import time
import random
import psutil
import customtkinter as ctk

from pynput import keyboard, mouse
from plyer import notification

# ==========================================
# COLORS
# ==========================================

DARK_BG = "#11141a"
CARD_BG = "#161b22"
ACCENT_GREEN = "#059669"
TEXT_MUTED = "#6b7280"

ctk.set_appearance_mode("Dark")

# ==========================================
# BREAK SUGGESTIONS
# ==========================================

BREAK_SUGGESTIONS = [
    {
        "title": "Випийте води",
        "desc": "Навіть невелике зневоднення погіршує концентрацію."
    },
    {
        "title": "Прогуляйтесь",
        "desc": "2-3 хвилини ходьби покращують кровообіг."
    },
    {
        "title": "Гімнастика для очей",
        "desc": "Подивіться 20 секунд на далекий об'єкт."
    },
    {
        "title": "Розімніть шию",
        "desc": "Повільно поверніть голову вліво і вправо."
    },
    {
        "title": "Провітріть кімнату",
        "desc": "Свіже повітря допомагає мозку працювати краще."
    }
]

# ==========================================
# CONFIG MANAGER
# ==========================================

class ConfigManager:

    def __init__(self, filename="sbr_settings.json"):

        self.filename = filename

        self.default_config = {
            "work_duration": 50,
            "break_duration": 10,
            "idle_threshold": 5,
            "autostart": True,
            "volume": 70,
            "exceptions": [
                "dota2.exe"
            ]
        }

        self.config = self.load_config()

    def load_config(self):

        if os.path.exists(self.filename):

            try:

                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)

            except Exception:
                return self.default_config

        return self.default_config

    def save_config(self):

        with open(self.filename, "w", encoding="utf-8") as f:

            json.dump(
                self.config,
                f,
                indent=4,
                ensure_ascii=False
            )

# ==========================================
# ACTIVITY LISTENER
# ==========================================

class ActivityListener:

    def __init__(self, callback):

        self.callback = callback

        self.kb_listener = None
        self.mouse_listener = None

    def _on_event(self, *args):

        self.callback()

    def start(self):

        self.kb_listener = keyboard.Listener(
            on_press=self._on_event
        )

        self.mouse_listener = mouse.Listener(
            on_move=self._on_event,
            on_click=self._on_event
        )

        self.kb_listener.start()
        self.mouse_listener.start()

    def stop(self):

        if self.kb_listener:
            self.kb_listener.stop()

        if self.mouse_listener:
            self.mouse_listener.stop()

# ==========================================
# SETTINGS WINDOW
# ==========================================

class SettingsWindow(ctk.CTkToplevel):

    def __init__(self, parent, config_manager):

        super().__init__(parent)

        self.cfg = config_manager

        self.title("Налаштування")

        self.geometry("420x430")

        self.configure(fg_color=DARK_BG)

        self.resizable(False, False)

        self.attributes("-topmost", True)

        ctk.CTkLabel(
            self,
            text="Налаштування",
            font=("Arial", 24, "bold"),
            text_color="white"
        ).pack(anchor="w", padx=25, pady=(25, 20))

        # ==========================================
        # WORK DURATION
        # ==========================================

        work_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        work_frame.pack(fill="x", padx=25)

        ctk.CTkLabel(
            work_frame,
            text="Час роботи",
            font=("Arial", 15),
            text_color="white"
        ).pack(side="left")

        self.work_lbl = ctk.CTkLabel(
            work_frame,
            text=f"{self.cfg.config['work_duration']} хв",
            font=("Arial", 15, "bold"),
            text_color=ACCENT_GREEN
        )

        self.work_lbl.pack(side="right")

        self.work_slider = ctk.CTkSlider(
            self,
            from_=15,
            to=120,
            number_of_steps=21,
            progress_color=ACCENT_GREEN,
            button_color=ACCENT_GREEN,
            command=self.update_work
        )

        self.work_slider.set(
            self.cfg.config["work_duration"]
        )

        self.work_slider.pack(
            fill="x",
            padx=25,
            pady=(5, 20)
        )

        # ==========================================
        # BREAK DURATION
        # ==========================================

        break_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        break_frame.pack(fill="x", padx=25)

        ctk.CTkLabel(
            break_frame,
            text="Час перерви",
            font=("Arial", 15),
            text_color="white"
        ).pack(side="left")

        self.break_lbl = ctk.CTkLabel(
            break_frame,
            text=f"{self.cfg.config['break_duration']} хв",
            font=("Arial", 15, "bold"),
            text_color=ACCENT_GREEN
        )

        self.break_lbl.pack(side="right")

        self.break_slider = ctk.CTkSlider(
            self,
            from_=1,
            to=30,
            number_of_steps=29,
            progress_color=ACCENT_GREEN,
            button_color=ACCENT_GREEN,
            command=self.update_break
        )

        self.break_slider.set(
            self.cfg.config["break_duration"]
        )

        self.break_slider.pack(
            fill="x",
            padx=25,
            pady=(5, 20)
        )

        # ==========================================
        # VOLUME
        # ==========================================

        vol_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        vol_frame.pack(fill="x", padx=25)

        ctk.CTkLabel(
            vol_frame,
            text="Гучність сповіщень",
            font=("Arial", 15),
            text_color="white"
        ).pack(side="left")

        self.vol_lbl = ctk.CTkLabel(
            vol_frame,
            text=f"{self.cfg.config['volume']}%",
            font=("Arial", 15, "bold"),
            text_color=ACCENT_GREEN
        )

        self.vol_lbl.pack(side="right")

        self.vol_slider = ctk.CTkSlider(
            self,
            from_=0,
            to=100,
            number_of_steps=10,
            progress_color=ACCENT_GREEN,
            button_color=ACCENT_GREEN,
            command=self.update_volume
        )

        self.vol_slider.set(
            self.cfg.config["volume"]
        )

        self.vol_slider.pack(
            fill="x",
            padx=25,
            pady=(5, 20)
        )

    def update_work(self, value):

        value = int(value)

        self.work_lbl.configure(
            text=f"{value} хв"
        )

        self.cfg.config["work_duration"] = value

        self.cfg.save_config()

    def update_break(self, value):

        value = int(value)

        self.break_lbl.configure(
            text=f"{value} хв"
        )

        self.cfg.config["break_duration"] = value

        self.cfg.save_config()

    def update_volume(self, value):

        value = int(value)

        self.vol_lbl.configure(
            text=f"{value}%"
        )

        self.cfg.config["volume"] = value

        self.cfg.save_config()

# ==========================================
# EXCEPTIONS WINDOW
# ==========================================

class ExceptionsWindow(ctk.CTkToplevel):

    def __init__(self, parent, config_manager):

        super().__init__(parent)

        self.cfg = config_manager

        self.title("Список винятків")

        self.geometry("420x450")

        self.configure(fg_color=DARK_BG)

        self.resizable(False, False)

        self.attributes("-topmost", True)

        ctk.CTkLabel(
            self,
            text="Список винятків",
            font=("Arial", 24, "bold"),
            text_color="white"
        ).pack(anchor="w", padx=25, pady=(25, 20))

        add_btn = ctk.CTkButton(
            self,
            text="+ Додати процес",
            fg_color=ACCENT_GREEN,
            hover_color="#047857",
            height=42,
            corner_radius=10,
            command=self.add_exception
        )

        add_btn.pack(fill="x", padx=25, pady=(0, 15))

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=CARD_BG
        )

        self.scroll.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 25)
        )

        self.render_exceptions()

    def render_exceptions(self):

        for widget in self.scroll.winfo_children():
            widget.destroy()

        for item in self.cfg.config["exceptions"]:

            row = ctk.CTkFrame(
                self.scroll,
                fg_color="transparent"
            )

            row.pack(fill="x", pady=5)

            ctk.CTkLabel(
                row,
                text=item,
                font=("Arial", 14),
                text_color="white"
            ).pack(side="left", padx=10)

            ctk.CTkButton(
                row,
                text="✕",
                width=30,
                fg_color="transparent",
                text_color="#ef4444",
                hover=False,
                command=lambda x=item: self.delete_exception(x)
            ).pack(side="right", padx=10)

    def add_exception(self):

        dialog = ctk.CTkInputDialog(
            text="Введіть назву процесу:",
            title="Новий виняток"
        )

        result = dialog.get_input()

        if result and result.strip():

            result = result.strip().lower()

            if result not in self.cfg.config["exceptions"]:

                self.cfg.config["exceptions"].append(result)

                self.cfg.save_config()

                self.render_exceptions()

    def delete_exception(self, name):

        self.cfg.config["exceptions"].remove(name)

        self.cfg.save_config()

        self.render_exceptions()

# ==========================================
# BREAK WINDOW
# ==========================================

class BreakOverlay(ctk.CTkToplevel):

    def __init__(self, parent, duration_minutes, on_complete):

        super().__init__(parent)

        self.on_complete = on_complete

        self.remaining_seconds = duration_minutes * 60

        self.configure(fg_color=DARK_BG)

        self.geometry("700x500")

        self.resizable(False, False)

        self.attributes("-topmost", True)

        self.grab_set()

        self.suggestion = random.choice(
            BREAK_SUGGESTIONS
        )

        ctk.CTkLabel(
            self,
            text="Час зробити перерву",
            font=("Arial", 28, "bold"),
            text_color=ACCENT_GREEN
        ).pack(pady=(40, 15))

        self.timer_lbl = ctk.CTkLabel(
            self,
            text="",
            font=("Arial", 72, "bold"),
            text_color="white"
        )

        self.timer_lbl.pack(pady=(0, 20))

        card = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=16
        )

        card.pack(
            fill="x",
            padx=40,
            pady=20
        )

        ctk.CTkLabel(
            card,
            text=self.suggestion["title"],
            font=("Arial", 20, "bold"),
            text_color="white"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            card,
            text=self.suggestion["desc"],
            font=("Arial", 14),
            text_color=TEXT_MUTED,
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 20))

        done_btn = ctk.CTkButton(
            self,
            text="Повернутись до роботи",
            fg_color=ACCENT_GREEN,
            hover_color="#047857",
            height=50,
            corner_radius=12,
            command=self.finish
        )

        done_btn.pack(
            fill="x",
            padx=40,
            pady=(15, 0)
        )

        self.update_timer()

        self.tick()

    def update_timer(self):

        m, s = divmod(
            self.remaining_seconds,
            60
        )

        self.timer_lbl.configure(
            text=f"{m:02d}:{s:02d}"
        )

    def tick(self):

        if self.remaining_seconds > 0:

            self.remaining_seconds -= 1

            self.update_timer()

            self.after(1000, self.tick)

        else:

            self.finish()

    def finish(self):

        self.on_complete()

        self.destroy()

# ==========================================
# MAIN APP
# ==========================================

class SmartBreakApp(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title("Smart Break")

        self.geometry("400x500")

        self.configure(fg_color=DARK_BG)

        self.resizable(False, False)

        self.cfg = ConfigManager()

        self.last_input = time.time()

        self.work_seconds = 0

        self.is_break_open = False

        self.timer_running = False

        self.build_ui()

        self.listener = ActivityListener(
            self.user_activity
        )

        self.listener.start()

        self.after(1000, self.engine)

    # ==========================================
    # UI
    # ==========================================

    def build_ui(self):

        header = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=25,
            pady=(25, 20)
        )

        ctk.CTkLabel(
            header,
            text="Smart Break",
            font=("Arial", 24, "bold"),
            text_color="white"
        ).pack(side="left")

        self.status_lbl = ctk.CTkLabel(
            self,
            text="Готово до запуску",
            font=("Arial", 14),
            text_color=TEXT_MUTED
        )

        self.status_lbl.pack(pady=(25, 5))

        self.timer_lbl = ctk.CTkLabel(
            self,
            text=f"{self.cfg.config['work_duration']:02d}:00",
            font=("Arial", 72, "bold"),
            text_color=ACCENT_GREEN
        )

        self.timer_lbl.pack(pady=(10, 5))

        ctk.CTkLabel(
            self,
            text="залишилось до перерви",
            font=("Arial", 14),
            text_color=TEXT_MUTED
        ).pack()

        # ==========================================
        # START BUTTON
        # ==========================================

        self.start_btn = ctk.CTkButton(
            self,
            text="Запустити",
            fg_color=ACCENT_GREEN,
            hover_color="#047857",
            height=52,
            corner_radius=12,
            font=("Arial", 16, "bold"),
            command=self.toggle_timer
        )

        self.start_btn.pack(
            fill="x",
            padx=25,
            pady=(45, 12)
        )

        # ==========================================
        # SETTINGS BUTTON
        # ==========================================

        settings_btn = ctk.CTkButton(
            self,
            text="Налаштування",
            fg_color=CARD_BG,
            hover_color="#1d2430",
            height=50,
            corner_radius=12,
            font=("Arial", 15),
            command=self.open_settings
        )

        settings_btn.pack(
            fill="x",
            padx=25,
            pady=(0, 10)
        )

        # ==========================================
        # EXCEPTIONS BUTTON
        # ==========================================

        exceptions_btn = ctk.CTkButton(
            self,
            text="Список винятків",
            fg_color=CARD_BG,
            hover_color="#1d2430",
            height=50,
            corner_radius=12,
            font=("Arial", 15),
            command=self.open_exceptions
        )

        exceptions_btn.pack(
            fill="x",
            padx=25
        )

    # ==========================================
    # TIMER CONTROL
    # ==========================================

    def toggle_timer(self):

        self.timer_running = not self.timer_running

        if self.timer_running:

            self.start_btn.configure(
                text="Пауза",
                fg_color="#dc2626",
                hover_color="#b91c1c"
            )

            self.status_lbl.configure(
                text="Таймер активний",
                text_color=ACCENT_GREEN
            )

        else:

            self.start_btn.configure(
                text="Продовжити",
                fg_color=ACCENT_GREEN,
                hover_color="#047857"
            )

            self.status_lbl.configure(
                text="Таймер призупинено",
                text_color="#f59e0b"
            )

    # ==========================================
    # USER ACTIVITY
    # ==========================================

    def user_activity(self):

        if not self.is_break_open:
            self.last_input = time.time()

    def is_exception_running(self):

        try:

            for proc in psutil.process_iter(['name']):

                name = proc.info['name']

                if name and name.lower() in self.cfg.config["exceptions"]:
                    return True

        except Exception:
            pass

        return False

    # ==========================================
    # ENGINE
    # ==========================================

    def engine(self):

        if not self.is_break_open and self.timer_running:

            current_time = time.time()

            idle = (
                current_time - self.last_input
            ) >= (
                self.cfg.config["idle_threshold"] * 60
            )

            game_running = self.is_exception_running()

            if not idle and not game_running:

                self.work_seconds += 1

            total = self.cfg.config["work_duration"] * 60

            remaining = max(
                0,
                total - self.work_seconds
            )

            m, s = divmod(
                remaining,
                60
            )

            self.timer_lbl.configure(
                text=f"{m:02d}:{s:02d}"
            )

            if self.work_seconds >= total:

                self.start_break()

        self.after(1000, self.engine)

    # ==========================================
    # BREAK LOGIC
    # ==========================================

    def start_break(self):

        self.is_break_open = True

        notification.notify(
            title="Smart Break",
            message="Час зробити перерву!",
            timeout=3
        )

        BreakOverlay(
            self,
            self.cfg.config["break_duration"],
            self.break_finished
        )

    def break_finished(self):

        self.is_break_open = False

        self.work_seconds = 0

        self.last_input = time.time()

        self.status_lbl.configure(
            text="Перерва завершена",
            text_color=ACCENT_GREEN
        )

        self.timer_lbl.configure(
            text=f"{self.cfg.config['work_duration']:02d}:00"
        )

    # ==========================================
    # WINDOWS
    # ==========================================

    def open_settings(self):

        SettingsWindow(
            self,
            self.cfg
        )

    def open_exceptions(self):

        ExceptionsWindow(
            self,
            self.cfg
        )

    # ==========================================
    # CLOSE APP
    # ==========================================

    def destroy(self):

        self.listener.stop()

        super().destroy()

# ==========================================
# START APP
# ==========================================

if __name__ == "__main__":

    app = SmartBreakApp()

    app.mainloop()