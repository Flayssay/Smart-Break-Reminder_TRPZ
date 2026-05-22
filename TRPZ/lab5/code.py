import os
import json
import time
import threading
import customtkinter as ctk
from pynput import keyboard, mouse
from plyer import notification

# Ініціалізація стилю графічного інтерфейсу
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ConfigManager:
    """Клас для роботи з локальними налаштуваннями додатку через JSON"""
    def __init__(self, filename="sbr_settings.json"):
        self.filename = filename
        self.default_config = {
            "work_duration": 50,  # у хвилинах
            "break_duration": 10,  # у хвилинах
            "idle_threshold": 5,   # у хвилинах (природний відпочинок)
            "autostart": False,
            "sound_enabled": True
        }
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return self.default_config
        return self.default_config

    def save_config(self, new_config):
        self.config.update(new_config)
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)


class ActivityListener:
    """Фоновий потік, який перехоплює рухи миші та натискання клавіш"""
    def __init__(self, on_activity_callback):
        self.on_activity = on_activity_callback
        self.keyboard_listener = None
        self.mouse_listener = None

    def _on_key_press(self, key):
        self.on_activity()

    def _on_mouse_move(self, x, y):
        self.on_activity()

    def _on_mouse_click(self, x, y, button, pressed):
        if pressed:
            self.on_activity()

    def start(self):
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self.mouse_listener = mouse.Listener(on_move=self._on_mouse_move, on_click=self._on_mouse_click)
        
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def stop(self):
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()


class BreakOverlayWindow(ctk.CTkToplevel):
    """Повноекранне вікно примусового відпочинку (Enforcement Screen)"""
    def __init__(self, parent, duration_minutes, on_close_callback):
        super().__init__(parent)
        self.title("Time to Break!")
        self.on_close_callback = on_close_callback
        self.remaining_seconds = duration_minutes * 60

        # Робимо вікно на весь екран поверх усіх інших вікон
        self.attributes("-topmost", True)
        self.attributes("-fullscreen", True)
        self.configure(fg_color="#1a1a1a")

        # Контент вікна
        self.label_title = ctk.CTkLabel(self, text="TAKE A BREAK", font=("Arial", 46, "bold"), text_color="#e74c3c")
        self.label_title.pack(expand=True, pady=(100, 10))

        self.label_tip = ctk.CTkLabel(self, text="Look away from the screen. Stand up and stretch your body.", font=("Arial", 18))
        self.label_tip.pack(expand=True, pady=10)

        self.label_timer = ctk.CTkLabel(self, text="", font=("Arial", 72, "bold"), text_color="#3498db")
        self.label_timer.pack(expand=True, pady=20)

        self.update_timer_display()
        self.countdown()

    def update_timer_display(self):
        mins, secs = divmod(self.remaining_seconds, 60)
        self.label_timer.configure(text=f"{mins:02d}:{secs:02d}")

    def countdown(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_timer_display()
            self.after(1000, self.countdown)
        else:
            self.on_close_callback()
            self.destroy()


class SmartBreakReminderApp(ctk.CTk):
    """Головне вікно додатку / Панель управління конфігураціями"""
    def __init__(self):
        super().__init__()
        self.title("Smart Break Reminder v1.0")
        self.geometry("500 x 450")
        self.resizable(False, False)

        # Ініціалізація логічних компонентів
        self.config_manager = ConfigManager()
        self.last_activity_time = time.time()
        self.work_seconds_accumulated = 0
        self.is_break_active = False
        self.is_tracking = True

        # Створення елементів UI інтерфейсу
        self.create_widgets()

        # Запуск фонового моніторингу периферії
        self.listener = ActivityListener(self.register_user_activity)
        self.listener.start()

        # Запуск головного циклу обробки таймерів програми (кожен крок - 1 секунда)
        self.tracker_thread_active = True
        self.after(1000, self.core_timer_loop)

    def create_widgets(self):
        # Заголовок панелі
        self.title_label = ctk.CTkLabel(self, text="SBR Control Dashboard", font=("Arial", 22, "bold"))
        self.title_label.pack(pady=15)

        # Фрейм для налаштування таймерів
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.pack(fill="x", padx=20, pady=10)

        # Слайдер робочої сесії
        self.work_label = ctk.CTkLabel(self.settings_frame, text=f"Work Duration: {self.config_manager.config['work_duration']} min")
        self.work_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.work_slider = ctk.CTkSlider(self.settings_frame, from_=5, to=120, number_of_steps=23, command=self.update_work_label)
        self.work_slider.set(self.config_manager.config['work_duration'])
        self.work_slider.grid(row=0, column=1, padx=15, pady=10)

        # Слайдер тривалості перерви
        self.break_label = ctk.CTkLabel(self.settings_frame, text=f"Break Duration: {self.config_manager.config['break_duration']} min")
        self.break_label.grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.break_slider = ctk.CTkSlider(self.settings_frame, from_=1, to=30, number_of_steps=29, command=self.update_break_label)
        self.break_slider.set(self.config_manager.config['break_duration'])
        self.break_slider.grid(row=1, column=1, padx=15, pady=10)

        # Статистична інформація в реальному часі
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=20, pady=15)

        self.status_indicator = ctk.CTkLabel(self.stats_frame, text="Status: Monitoring Active", font=("Arial", 14), text_color="#2ecc71")
        self.status_indicator.pack(anchor="w", padx=15)

        self.progress_label = ctk.CTkLabel(self.stats_frame, text="Time worked in current session: 00:00", font=("Arial", 13))
        self.progress_label.pack(anchor="w", padx=15, pady=5)

        # Кнопки управління
        self.btn_save = ctk.CTkButton(self, text="Save & Apply Config", fg_color="#27ae60", hover_color="#219653", command=self.save_settings)
        self.btn_save.pack(pady=15)

        self.btn_preset_pomodoro = ctk.CTkButton(self, text="Load Pomodoro Preset (25/5)", fg_color="#2c3e50", command=self.apply_pomodoro)
        self.btn_preset_pomodoro.pack(pady=5)

    def update_work_label(self, value):
        self.work_label.configure(text=f"Work Duration: {int(value)} min")

    def update_break_label(self, value):
        self.break_label.configure(text=f"Break Duration: {int(value)} min")

    def apply_pomodoro(self):
        self.work_slider.set(25)
        self.break_slider.set(5)
        self.update_work_label(25)
        self.update_break_label(5)
        self.save_settings()

    def save_settings(self):
        new_cfg = {
            "work_duration": int(self.work_slider.get()),
            "break_duration": int(self.break_slider.get())
        }
        self.config_manager.save_config(new_cfg)
        notification.notify(
            title="Smart Break Reminder",
            message="Configuration saved and applied successfully!",
            timeout=3
        )

    def register_user_activity(self):
        """Викликається фоновим слухачем при будь-якій дії миші/клавіатури"""
        if not self.is_break_active:
            self.last_activity_time = time.time()

    def core_timer_loop(self):
        """Головний логічний цикл аналізу станів (Секундний такт)"""
        if self.is_tracking and not self.is_break_active:
            current_time = time.time()
            idle_duration = current_time - self.last_activity_time
            idle_threshold_seconds = self.config_manager.config["idle_threshold"] * 60

            # Інтелектуальний аналіз Idle Time (природна відсутність користувача)
            if idle_duration >= idle_threshold_seconds:
                if self.work_seconds_accumulated > 0:
                    self.work_seconds_accumulated = 0
                    self.status_indicator.configure(text="Status: Reset due to Idle Sleep", text_color="#f39c12")
            else:
                self.work_seconds_accumulated += 1
                self.status_indicator.configure(text="Status: Monitoring Active", text_color="#2ecc71")

            # Оновлення показників таймера на екрані
            mins, secs = divmod(self.work_seconds_accumulated, 60)
            self.progress_label.configure(text=f"Time worked in current session: {mins:02d}:{secs:02d}")

            # Перевірка на досягнення ліміту втоми
            target_work_seconds = self.config_manager.config["work_duration"] * 60
            if self.work_seconds_accumulated >= target_work_seconds:
                self.trigger_break_sequence()

        # Повторний запуск лічильника через 1 секунду
        self.after(1000, self.core_timer_loop)

    def trigger_break_sequence(self):
        """Запуск алгоритму блокування екрану для відпочинку"""
        self.is_break_active = True
        self.status_indicator.configure(text="Status: BREAK ENFORCED", text_color="#e74c3c")
        
        # Системний пуш-нотифікація Windows
        notification.notify(
            title="Work Session Expired!",
            message="Step away from your computer immediately.",
            timeout=5
        )

        # Відкриття повноекранного блокувальника
        BreakOverlayWindow(self, self.config_manager.config["break_duration"], self.end_break_sequence)

    def end_break_sequence(self):
        """Повернення системи в робочий режим після закінчення відпочинку"""
        self.is_break_active = False
        self.work_seconds_accumulated = 0
        self.last_activity_time = time.time()
        self.status_indicator.configure(text="Status: Monitoring Active", text_color="#2ecc71")
        
        notification.notify(
            title="Break Finished",
            message="You can safely return to your work now.",
            timeout=5
        )

    def destroy(self):
        # Безпечне відключення фонових хуків при закритті вікна
        self.listener.stop()
        super().destroy()


if __name__ == "__main__":
    # Точка входу в десктопний додаток
    app = SmartBreakReminderApp()
    app.mainloop()