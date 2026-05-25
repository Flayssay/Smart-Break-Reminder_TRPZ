import os
import json
import time
import threading
import psutil
import customtkinter as ctk
from pynput import keyboard, mouse
from plyer import notification

# Колірна палітра суворо за твоїми макетами
DARK_BG = "#11141a"        # Глибокий темний фон
CARD_BG = "#161b22"        # Фон карток статистики
ACCENT_GREEN = "#059669"   # Смарагдово-зелений для кнопок і таймера
TEXT_MUTED = "#6b7280"     # Сірий колір для підписів

ctk.set_appearance_mode("Dark")

class ConfigManager:
    def __init__(self, filename="sbr_settings.json"):
        self.filename = filename
        self.default_config = {
            "work_duration": 50,
            "break_duration": 10,
            "idle_threshold": 5,
            "autostart": True,
            "volume": 70,
            "exceptions": ["dota2.exe", "chrome.exe"],
            "total_breaks_month": 124,
            "skipped_exercises": 8
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

    def save_config(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)


class ActivityListener:
    def __init__(self, on_activity_callback):
        self.on_activity = on_activity_callback
        self.kb_listener = None
        self.m_listener = None

    def _on_event(self, *args):
        self.on_activity()

    def start(self):
        self.kb_listener = keyboard.Listener(on_press=self._on_event)
        self.m_listener = mouse.Listener(on_move=self._on_event, on_click=self._on_event)
        self.kb_listener.start()
        self.m_listener.start()

    def stop(self):
        if self.kb_listener: self.kb_listener.stop()
        if self.m_listener: self.m_listener.stop()


class ExceptionsWindow(ctk.CTkToplevel):
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.cfg_m = config_manager
        self.title("Налаштування")
        self.geometry("380x420")
        self.configure(fg_color=DARK_BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text="Налаштування", font=("Arial", 24, "bold"), text_color="white").pack(anchor="w", padx=25, pady=(25, 15))

        auto_frame = ctk.CTkFrame(self, fg_color="transparent")
        auto_frame.pack(fill="x", padx=25, pady=8)
        ctk.CTkLabel(auto_frame, text="Автозапуск системи", font=("Arial", 15), text_color="white").pack(side="left")
        self.auto_sw = ctk.CTkSwitch(auto_frame, text="", progress_color=ACCENT_GREEN, command=self.toggle_auto)
        self.auto_sw.pack(side="right")
        if self.cfg_m.config["autostart"]: self.auto_sw.select()

        vol_frame = ctk.CTkFrame(self, fg_color="transparent")
        vol_frame.pack(fill="x", padx=25, pady=(15, 2))
        ctk.CTkLabel(vol_frame, text="Гучність сповіщень", font=("Arial", 14), text_color=TEXT_MUTED).pack(side="left")
        self.vol_val_lbl = ctk.CTkLabel(vol_frame, text=f"{self.cfg_m.config['volume']}%", font=("Arial", 14), text_color="white")
        self.vol_val_lbl.pack(side="right")
        
        self.vol_slider = ctk.CTkSlider(self, from_=0, to=100, number_of_steps=10, button_color=ACCENT_GREEN, progress_color=ACCENT_GREEN, command=self.update_volume)
        self.vol_slider.set(self.cfg_m.config["volume"])
        self.vol_slider.pack(fill="x", padx=25, pady=(0, 20))

        list_card = ctk.CTkFrame(self, fg_color="#181c24", corner_radius=14)
        list_card.pack(fill="both", expand=True, padx=25, pady=(5, 25))

        hdr_list = ctk.CTkFrame(list_card, fg_color="transparent")
        hdr_list.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(hdr_list, text="Список винятків", font=("Arial", 14, "bold"), text_color="white").pack(side="left")
        ctk.CTkButton(hdr_list, text="+ Додати", font=("Arial", 13, "bold"), text_color=ACCENT_GREEN, fg_color="transparent", width=60, hover=False, command=self.add_exception).pack(side="right")

        self.scroll_box = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.scroll_box.pack(fill="both", expand=True, padx=5, pady=5)
        self.render_exceptions()

    def toggle_auto(self):
        self.cfg_m.config["autostart"] = bool(self.auto_sw.get())
        self.cfg_m.save_config()

    def update_volume(self, val):
        self.cfg_m.config["volume"] = int(val)
        self.vol_val_lbl.configure(text=f"{int(val)}%")
        self.cfg_m.save_config()

    def render_exceptions(self):
        for widget in self.scroll_box.winfo_children(): widget.destroy()
        for item in self.cfg_m.config["exceptions"]:
            row = ctk.CTkFrame(self.scroll_box, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=item, font=("Arial", 14), text_color=TEXT_MUTED).pack(side="left", padx=10)
            ctk.CTkButton(row, text="✕", font=("Arial", 12), text_color="#ef4444", fg_color="transparent", width=20, hover=False, command=lambda idx=item: self.delete_exception(idx)).pack(side="right", padx=10)

    def delete_exception(self, name):
        self.cfg_m.config["exceptions"].remove(name)
        self.cfg_m.save_config()
        self.render_exceptions()

    def add_exception(self):
        dialog = ctk.CTkInputDialog(text="Введіть назву процесу (напр. dota2.exe):", title="Додати виняток")
        res = dialog.get_input()
        if res and res.strip():
            self.cfg_m.config["exceptions"].append(res.strip().lower())
            self.cfg_m.save_config()
            self.render_exceptions()


class ProgressWindow(ctk.CTkToplevel):
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.cfg_m = config_manager
        self.title("Ваш прогрес")
        self.geometry("380x430")
        self.configure(fg_color=DARK_BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text="Ваш прогрес", font=("Arial", 22, "bold"), text_color="white").pack(anchor="w", padx=25, pady=(25, 10))

        chart_card = ctk.CTkFrame(self, fg_color="#181c24", corner_radius=14)
        chart_card.pack(fill="x", padx=25, pady=5)
        ctk.CTkLabel(chart_card, text="АКТИВНІСТЬ ЗА ТИЖДЕНЬ", font=("Arial", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(12, 5))
        
        bar_frame = ctk.CTkFrame(chart_card, fg_color="transparent", height=100)
        bar_frame.pack(fill="x", padx=20, pady=(5, 15))
        bar_frame.pack_propagate(False)
        
        heights = [45, 65, 95, 75]
        colors = ["#374151", "#374151", ACCENT_GREEN, ACCENT_GREEN]
        for h, c in zip(heights, colors):
            col_box = ctk.CTkFrame(bar_frame, fg_color="transparent")
            col_box.pack(side="left", expand=True, fill="both")
            bar = ctk.CTkFrame(col_box, fg_color=c, width=26, height=h, corner_radius=5)
            bar.pack(side="bottom")
            bar.pack_propagate(False)

        stats_card = ctk.CTkFrame(self, fg_color="#181c24", corner_radius=14)
        stats_card.pack(fill="both", expand=True, padx=25, pady=(15, 25))

        r1 = ctk.CTkFrame(stats_card, fg_color="transparent")
        r1.pack(fill="x", padx=15, pady=(15, 8))
        ctk.CTkLabel(r1, text="Всього перерв (місяць)", font=("Arial", 14), text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(r1, text=str(self.cfg_m.config["total_breaks_month"]), font=("Arial", 16, "bold"), text_color="white").pack(side="right")

        r2 = ctk.CTkFrame(stats_card, fg_color="transparent")
        r2.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(r2, text="Пропущено вправ", font=("Arial", 14), text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(r2, text=str(self.cfg_m.config["skipped_exercises"]), font=("Arial", 16, "bold"), text_color="#ef4444").pack(side="right")

        btn_pdf = ctk.CTkButton(stats_card, text="Вивантажити звіт (PDF)", font=("Arial", 14, "bold"), fg_color="#1f242e", text_color="white", hover_color="#282e3b", height=45, corner_radius=10, command=self.pdf_trigger)
        btn_pdf.pack(fill="x", side="bottom", padx=15, pady=15)

    def pdf_trigger(self):
        notification.notify(title="Smart Break", message="Звіт збережено в папку проєкту!", timeout=2)


class FullscreenBreakOverlay(ctk.CTkToplevel):
    def __init__(self, parent, duration_minutes, on_complete):
        super().__init__(parent)
        self.on_complete = on_complete
        self.remaining_seconds = duration_minutes * 60
        self.snooze_count = 0

        self.attributes("-topmost", True)
        self.attributes("-fullscreen", True)
        self.configure(fg_color=DARK_BG)

        ctk.CTkLabel(self, text="Час зробити перерву", font=("Arial", 28, "bold"), text_color=ACCENT_GREEN).pack(pady=(140, 5))
        ctk.CTkLabel(self, text="Ваші очі та спина скажуть \"дякую\"", font=("Arial", 14), text_color=TEXT_MUTED).pack(pady=(0, 40))

        self.timer_lbl = ctk.CTkLabel(self, text="", font=("Arial", 88, "bold"), text_color="white")
        self.timer_lbl.pack(pady=10)

        ex_card = ctk.CTkFrame(self, fg_color="#181c24", corner_radius=16, width=440, height=150)
        ex_card.pack(pady=40)
        ex_card.pack_propagate(False)

        ctk.CTkLabel(ex_card, text="РЕКОМЕНДОВАНА ВПРАВА", font=("Arial", 10, "bold"), text_color=ACCENT_GREEN).pack(anchor="w", padx=20, pady=(15, 2))
        ctk.CTkLabel(ex_card, text="Гімнастика для очей (20-20-20)", font=("Arial", 16, "bold"), text_color="white").pack(anchor="w", padx=20, pady=2)
        
        desc = "Подивіться на об'єкт, який знаходиться на відстані 20\nметрів від вас, протягом 20 секунд. Це допоможе зняти\nнапругу з фокусування."
        ctk.CTkLabel(ex_card, text=desc, font=("Arial", 13), text_color=TEXT_MUTED, justify="left").pack(anchor="w", padx=20, pady=6)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="Виконано", font=("Arial", 14, "bold"), fg_color=ACCENT_GREEN, hover_color="#047857", width=130, height=42, corner_radius=10, command=self.done).pack(side="left", padx=10)
        self.btn_snooze = ctk.CTkButton(btn_frame, text="Відкласти (0/3)", font=("Arial", 14), fg_color="#1f2937", text_color="white", hover_color="#374151", width=130, height=42, corner_radius=10, command=self.snooze)
        self.btn_snooze.pack(side="left", padx=10)

        self.update_clock()
        self.tick()

    def update_clock(self):
        m, s = divmod(self.remaining_seconds, 60)
        self.timer_lbl.configure(text=f"{m:02d}:{s:02d}")

    def tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_clock()
            self.after(1000, self.tick)
        else:
            self.done()

    def done(self):
        self.on_complete(success=True)
        self.destroy()

    def snooze(self):
        if self.snooze_count < 3:
            self.snooze_count += 1
            self.remaining_seconds += 5 * 60
            self.btn_snooze.configure(text=f"Відкласти ({self.snooze_count}/3)")
            if self.snooze_count == 3:
                self.btn_snooze.configure(state="disabled")


class SmartBreakReminderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Break")
        self.geometry("360x490")
        self.configure(fg_color=DARK_BG)
        self.resizable(False, False)

        self.cfg_m = ConfigManager()
        
        # --- НОВІ ЛОГІЧНІ ЛІЧИЛЬНИКИ АВТОМАТИЗАЦІЇ ---
        self.total_seconds_since_start = 0  # Загальний час роботи програми
        self.pure_work_seconds = 0          # Чистий час корисної роботи користувача
        
        self.accumulated_work_time = 0
        self.last_input_timestamp = time.time()
        self.is_break_screen_open = False

        self.build_ui()

        self.listener = ActivityListener(self.intercept_signal)
        self.listener.start()
        self.after(1000, self.engine)

    def build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=25, pady=(25, 15))
        ctk.CTkLabel(hdr, text="Smart Break", font=("Arial", 20, "bold"), text_color="white").pack(side="left")
        
        dots = ctk.CTkFrame(hdr, fg_color="transparent")
        dots.pack(side="right")
        ctk.CTkFrame(dots, fg_color="#2d3139", width=10, height=10, corner_radius=5).pack(side="left", padx=3)
        ctk.CTkFrame(dots, fg_color="#ef4444", width=10, height=10, corner_radius=5).pack(side="left", padx=3)

        self.time_left_lbl = ctk.CTkLabel(self, text="50:00", font=("Arial", 68, "bold"), text_color=ACCENT_GREEN)
        self.time_left_lbl.pack(pady=(25, 2))
        ctk.CTkLabel(self, text="залишилось до перерви", font=("Arial", 13), text_color=TEXT_MUTED).pack(pady=(0, 30))

        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=25, pady=5)

        # ДИНАМІЧНА КАРТКА 1: Години роботи (початкове значення 0 хв)
        self.c1_card = ctk.CTkFrame(cards_frame, fg_color="#181c24", corner_radius=14, height=95)
        self.c1_card.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.c1_card.pack_propagate(False)
        self.hours_val_lbl = ctk.CTkLabel(self.c1_card, text="0 хв", font=("Arial", 24, "bold"), text_color="white")
        self.hours_val_lbl.pack(anchor="w", padx=18, pady=(16, 1))
        ctk.CTkLabel(self.c1_card, text="ГОДИН РОБОТИ", font=("Arial", 11, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=18)

        # ДИНАМІЧНА КАРТКА 2: Ефективність (початкове значення 100%)
        self.c2_card = ctk.CTkFrame(cards_frame, fg_color="#181c24", corner_radius=14, height=95)
        self.c2_card.pack(side="right", expand=True, fill="x", padx=(6, 0))
        self.c2_card.pack_propagate(False)
        self.eff_val_lbl = ctk.CTkLabel(self.c2_card, text="100%", font=("Arial", 26, "bold"), text_color=ACCENT_GREEN)
        self.eff_val_lbl.pack(anchor="w", padx=18, pady=(16, 1))
        ctk.CTkLabel(self.c2_card, text="ЕФЕКТИВНІСТЬ", font=("Arial", 11, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=18)

        btn_settings = ctk.CTkButton(self, text="Налаштування", font=("Arial", 15, "bold"), fg_color=ACCENT_GREEN, hover_color="#047857", height=48, corner_radius=12, command=self.open_settings)
        btn_settings.pack(fill="x", padx=25, pady=(35, 8))

        btn_prog = ctk.CTkButton(self, text="Список винятків", font=("Arial", 15), fg_color="#181c24", text_color="white", hover_color="#202530", height=48, corner_radius=12, command=self.open_progress)
        btn_prog.pack(fill="x", padx=25, pady=4)

    def intercept_signal(self):
        if not self.is_break_screen_open:
            self.last_input_timestamp = time.time()

    def is_exception_running(self):
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() in self.cfg_m.config["exceptions"]:
                    return True
        except Exception: pass
        return False

    def engine(self):
        """Головне ядро розрахунків (Спрацьовує раз на секунду)"""
        if not self.is_break_screen_open:
            self.total_seconds_since_start += 1
            
            curr_t = time.time()
            is_idle = (curr_t - self.last_input_timestamp) >= self.cfg_m.config["idle_threshold"] * 60
            is_game_active = self.is_exception_running()

            # Якщо користувач не афк і не в грі — зараховуємо чисту роботу
            if not is_idle and not is_game_active:
                self.pure_work_seconds += 1
                self.accumulated_work_time += 1
            
            # Якщо користувач відійшов (Idle) — скидаємо лічильник поточної сесії до перерви
            if is_idle and self.accumulated_work_time > 0:
                self.accumulated_work_time = 0

            # --- АВТОМАТИЧНИЙ РОЗРАХУНОК МЕТРИК ДЛЯ КАРТОК ---
            # 1. Форматування часу роботи
            if self.pure_work_seconds < 3600:
                minutes_display = self.pure_work_seconds // 60
                self.hours_val_lbl.configure(text=f"{minutes_display} хв")
            else:
                hours_display = round(self.pure_work_seconds / 3600, 1)
                self.hours_val_lbl.configure(text=f"{hours_display} год")

            # 2. Розрахунок ефективності у відсотках
            if self.total_seconds_since_start > 0:
                efficiency_percentage = int((self.pure_work_seconds / self.total_seconds_since_start) * 100)
                # Обмежуємо мінімум 1%, щоб не ділити на 0 в UI
                efficiency_percentage = max(1, min(100, efficiency_percentage))
                self.eff_val_lbl.configure(text=f"{efficiency_percentage}%")

            # Оновлення основного таймера зворотного відліку
            limit_total = self.cfg_m.config["work_duration"] * 60
            remaining = max(0, limit_total - self.accumulated_work_time)
            m, s = divmod(remaining, 60)
            self.time_left_lbl.configure(text=f"{m:02d}:{s:02d}")

            if self.accumulated_work_time >= limit_total:
                self.fire_overlay()

        self.after(1000, self.engine)

    def fire_overlay(self):
        self.is_break_screen_open = True
        FullscreenBreakOverlay(self, self.cfg_m.config["break_duration"], self.end_overlay)

    def end_overlay(self, success):
        self.is_break_screen_open = False
        self.accumulated_work_time = 0
        self.last_input_timestamp = time.time()
        if success: self.cfg_m.config["total_breaks_month"] += 1
        else: self.cfg_m.config["skipped_exercises"] += 1
        self.cfg_m.save_config()

    def open_settings(self): ExceptionsWindow(self, self.cfg_m)
    def open_progress(self): ProgressWindow(self, self.cfg_m)

    def destroy(self):
        self.listener.stop()
        super().destroy()

if __name__ == "__main__":
    app = SmartBreakReminderApp()
    app.mainloop()