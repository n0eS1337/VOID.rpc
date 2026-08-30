import customtkinter as ctk
from pypresence import Presence, ActivityType
import time
import os
import sys
import json
import winreg
import threading
import requests
import pystray
import ctypes  
import keyboard  
from PIL import Image, ImageDraw
from pystray import MenuItem as item
from customtkinter import filedialog

# Фикс рабочих путей при автостарте
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "VOID_RPC_SYSTEM"

try:
    myappid = 'void.rpc.system.1.3'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

ctk.set_appearance_mode("Dark")

LANGS = {
    "RU": {
        "title": "VOID.rpc | SYSTEM",
        "header": "ПАНЕЛЬ УПРАВЛЕНИЯ DISCORD RPC",
        "id_label": "ID Приложения (меняет название игры):",
        "id_ph": "Вставь Application ID",
        "det_ph": "Details (можно: Текст | https://ссылка)",
        "state_ph": "State (можно: Текст | https://ссылка)",
        "timer": "Включить таймер",
        "source_modes": ["Минуты назад", "Unix Секунды", "Время от ПК 💻", "Время от времени 🔄"],
        "behavior_modes": ["Идет вперед ⏳", "Обратный отсчет ⏱️", "Заморожен 🟥"],
        "activity_modes": ["Играет 🎮", "Слушает 🎵", "Смотрит 📺", "Соревнуется 🏆"],
        "btn_browse": "Обзор...",
        "btn_update": "ПРИМЕНИТЬ ИЗМЕНЕНИЯ",
        "no_file": "Файл не выбран",
        "uploading": "Загрузка картинки...",
        "img_ready": "Картинка готова!",
        "img_err": "Ошибка загрузки фото",
        "net_err": "Ошибка сети: ",
        "id_err": "Ошибка: Введите ID приложения!",
        "sync": "Синхронизация с Discord...",
        "discord_err": "Ошибка подключения к Discord: ",
        "api_err": "Ошибка Discord API: ",
        "success": "Всё успешно обновлено!",
        "status_wait": "Статус: Ожидание действий",
        "tray_open": "Развернуть",
        "tray_exit": "Выход",
        "notify_title": "VOID.rpc | SYSTEM",
        "notify_msg": "Приложение работает в фоне.\nCtrl+Shift+H - Скрыть/Показать\nCtrl+Shift+X - Очистить статус",
        "btn_label": "Кастомная кнопка (Формат: Текст | Ссылка):",
        "btn_txt_ph": "Текст (н-р: GitHub)",
        "autostart": "Запускать при старте Windows",
        "presets_label": "Управление пресетами:",
        "preset_name_ph": "Имя нового пресета",
        "preset_loaded": "Пресет загружен!",
        "preset_saved": "Пресет создан/сохранен!",
        "preset_deleted": "Пресет удален!",
        "loop_timer": "Цикл пресетов (сек):",
        "copied": "ID скопирован в буфер обмена!",
        "small_img_label": "Маленькая картинка (Вкл/Выкл):",
        "btn2_label": "Кнопка 2 (Текст | Ссылка):",
        "btn2_txt_ph": "Текст кнопки 2",
        "time_preset_label": "Авто-пресет по времени суток:",
        "time_preset_none": "Выкл"
    },
    "EN": {
        "title": "VOID.rpc | SYSTEM",
        "header": "DISCORD RPC CONTROL PANEL",
        "id_label": "Application ID (changes game title):",
        "id_ph": "Insert Application ID",
        "det_ph": "Details (format: Text | https://link)",
        "state_ph": "State (format: Text | https://link)",
        "timer": "Enable timer",
        "source_modes": ["Minutes ago", "Unix Seconds", "PC Time 💻", "Interval Time 🔄"],
        "behavior_modes": ["Count up ⏳", "Count down ⏱️", "Frozen bar 🟥"],
        "activity_modes": ["Playing 🎮", "Listening 🎵", "Watching 📺", "Competing 🏆"],
        "btn_browse": "Browse...",
        "btn_update": "APPLY CHANGES",
        "no_file": "No file selected",
        "uploading": "Uploading image...",
        "img_ready": "Image uploaded successfully!",
        "img_err": "Failed to upload image",
        "net_err": "Network error: ",
        "id_err": "Error: Enter Application ID!",
        "sync": "Synchronizing with Discord...",
        "discord_err": "Discord connection error: ",
        "api_err": "Discord API error: ",
        "success": "Successfully updated!",
        "status_wait": "Status: Waiting for action",
        "tray_open": "Open",
        "tray_exit": "Exit",
        "notify_title": "VOID.rpc | SYSTEM",
        "notify_msg": "Running in background.\nCtrl+Shift+H - Toggle Hide\nCtrl+Shift+X - Clear RPC",
        "btn_label": "Custom profile button (Text | Link):",
        "btn_txt_ph": "Text (ex: GitHub)",
        "autostart": "Launch at Windows startup",
        "presets_label": "Preset Management:",
        "preset_name_ph": "New preset name",
        "preset_loaded": "Preset saved!",
        "preset_saved": "Preset saved!",
        "preset_deleted": "Preset deleted!",
        "loop_timer": "Preset Loop (sec):",
        "copied": "ID copied to clipboard!",
        "small_img_label": "Small Image (On/Off):",
        "btn2_label": "Button 2 (Text | Link):",
        "btn2_txt_ph": "Button 2 text",
        "time_preset_label": "Auto-preset by time of day:",
        "time_preset_none": "Off"
    }
}

class UltimateRPCMenu(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.lang = "RU"
        self.title("VOID.rpc")
        self.geometry("560x960")  # Немного увеличили высоту под новые элементы
        self.resizable(False, False)
        self.configure(fg_color="#111214")  

        self.rpc = None
        self.uploaded_image_url = None
        self.uploaded_small_image_url = None # Для маленькой картинки
        self.tray_icon = None
        self.is_hidden = False  
        self.loop_running = False
        self.current_loop_index = 0
        self.pc_time_start = int(time.time())
        
        self.config_data = self.load_config()
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        # --- ЛОГОТИП ---
        self.raw_logo = None
        logo_png_path = os.path.join(BASE_DIR, "logo.png")
        logo_ico_path = os.path.join(BASE_DIR, "logo.ico")

        if os.path.exists(logo_png_path) and not os.path.exists(logo_ico_path):
            try:
                img = Image.open(logo_png_path)
                img.save(logo_ico_path, format="ICO", sizes=[(64, 64)])
            except Exception:
                pass

        if os.path.exists(logo_ico_path):
            try: self.iconbitmap(logo_ico_path)
            except Exception: pass

        try:
            if os.path.exists(logo_png_path):
                self.raw_logo = Image.open(logo_png_path)
                self.logo_image = ctk.CTkImage(light_image=self.raw_logo, dark_image=self.raw_logo, size=(45, 45))
                self.logo_label = ctk.CTkLabel(self, image=self.logo_image, text="")
                self.logo_label.place(x=20, y=10) 
        except Exception:
            pass

        self.lang_btn = ctk.CTkButton(self, text="RU / EN", width=60, height=25, fg_color="#2B2D31", hover_color="#3A3D42", command=self.toggle_lang)
        self.lang_btn.place(x=480, y=10)

        # --- ИНТЕРФЕЙС ---
        self.label = ctk.CTkLabel(self, text="VOID.rpc | SYSTEM", font=ctk.CTkFont(size=18, weight="bold"), text_color="#ED4245")
        self.label.pack(pady=10)

        self.id_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.id_label.pack(pady=(2, 2))
        
        self.id_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.id_frame.pack(pady=3)
        self.id_entry = ctk.CTkEntry(self.id_frame, placeholder_text="", width=400, fg_color="#1E1F22", border_width=0)
        self.id_entry.pack(side="left", padx=(0, 5))
        self.id_copy_btn = ctk.CTkButton(self.id_frame, text="📋", width=35, fg_color="#1E1F22", hover_color="#3A3D42", command=self.copy_id_to_clipboard)
        self.id_copy_btn.pack(side="right")

        # Поле Details
        self.det_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.det_frame.pack(pady=(5, 2))
        self.details_entry = ctk.CTkEntry(self.det_frame, placeholder_text="", width=400, fg_color="#1E1F22", border_width=0)
        self.details_entry.pack(side="left", padx=(0, 5))
        self.det_clear = ctk.CTkButton(self.det_frame, text="×", width=35, fg_color="#1E1F22", hover_color="#3A3D42", command=self.clear_details)
        self.det_clear.pack(side="right")
        
        self.det_counter = ctk.CTkLabel(self, text="0 / 128", font=ctk.CTkFont(size=11), text_color="gray")
        self.det_counter.pack(anchor="e", padx=65, fill="x", pady=(0, 2))
        self.details_entry.bind("<KeyRelease>", self.update_counters)

        # Поле State
        self.state_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.state_frame.pack(pady=(3, 2))
        self.state_entry = ctk.CTkEntry(self.state_frame, placeholder_text="", width=400, fg_color="#1E1F22", border_width=0)
        self.state_entry.pack(side="left", padx=(0, 5))
        self.state_clear = ctk.CTkButton(self.state_frame, text="×", width=35, fg_color="#1E1F22", hover_color="#3A3D42", command=self.clear_state)
        self.state_clear.pack(side="right")
        
        self.state_counter = ctk.CTkLabel(self, text="0 / 128", font=ctk.CTkFont(size=11), text_color="gray")
        self.state_counter.pack(anchor="e", padx=65, fill="x", pady=(0, 2))
        self.state_entry.bind("<KeyRelease>", self.update_counters)

        # --- НАСТРОЙКА ВРЕМЕНИ И АКТИВНОСТЕЙ ---
        self.time_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.time_frame.pack(pady=10)

        self.time_checkbox = ctk.CTkCheckBox(self.time_frame, text="", width=90, fg_color="#ED4245", hover_color="#C03033")
        self.time_checkbox.pack(side="left", padx=2)
        self.time_checkbox.select()

        self.activity_switch = ctk.CTkOptionMenu(self.time_frame, values=LANGS["RU"]["activity_modes"], width=105, fg_color="#1E1F22", button_color="#2B2D31", button_hover_color="#3A3D42")
        self.activity_switch.pack(side="left", padx=2)

        self.source_switch = ctk.CTkOptionMenu(self.time_frame, values=LANGS["RU"]["source_modes"], width=120, fg_color="#1E1F22", button_color="#2B2D31", button_hover_color="#3A3D42")
        self.source_switch.pack(side="left", padx=2)

        self.behavior_switch = ctk.CTkOptionMenu(self.time_frame, values=LANGS["RU"]["behavior_modes"], width=115, fg_color="#1E1F22", button_color="#2B2D31", button_hover_color="#3A3D42")
        self.behavior_switch.pack(side="left", padx=2)

        self.time_entry = ctk.CTkEntry(self.time_frame, placeholder_text="Знач", width=55, fg_color="#1E1F22", border_width=0)
        self.time_entry.pack(side="left", padx=2)

        # --- КНОПКА ПРОФИЛЯ ---
        self.btn_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.btn_label.pack(pady=(5, 2))
        
        self.custom_btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.custom_btn_frame.pack(pady=3)
        
        self.btn_text_entry = ctk.CTkEntry(self.custom_btn_frame, placeholder_text="", width=140, fg_color="#1E1F22", border_width=0)
        self.btn_text_entry.pack(side="left", padx=5)
        
        self.btn_url_entry = ctk.CTkEntry(self.custom_btn_frame, placeholder_text="https://...", width=290, fg_color="#1E1F22", border_width=0)
        self.btn_url_entry.pack(side="left", padx=5)

        # --- КНОПКА 2 ---
        self.btn2_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.btn2_label.pack(pady=(5, 2))

        self.custom_btn2_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.custom_btn2_frame.pack(pady=3)

        self.btn2_text_entry = ctk.CTkEntry(self.custom_btn2_frame, placeholder_text="", width=140, fg_color="#1E1F22", border_width=0)
        self.btn2_text_entry.pack(side="left", padx=5)

        self.btn2_url_entry = ctk.CTkEntry(self.custom_btn2_frame, placeholder_text="https://...", width=290, fg_color="#1E1F22", border_width=0)
        self.btn2_url_entry.pack(side="left", padx=5)

        # --- АВТОЗАГРУЗКА ---
        self.autostart_var = ctk.BooleanVar(value=self.check_autostart_registry())
        self.autostart_check = ctk.CTkCheckBox(self, text="", variable=self.autostart_var, fg_color="#ED4245", hover_color="#C03033", command=self.toggle_autostart)
        self.autostart_check.pack(pady=5, padx=65, anchor="w")

        # --- ПРЕСЕТЫ ---
        self.presets_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.presets_label.pack(pady=(5, 2))
        
        self.preset_mgmt_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.preset_mgmt_frame.pack(pady=3)
        
        preset_list = list(self.config_data.get("presets", {}).keys())
        self.preset_dropdown = ctk.CTkOptionMenu(
            self.preset_mgmt_frame, 
            values=preset_list if preset_list else ["None"], 
            width=150, 
            text_color="white",
            fg_color="#1E1F22", 
            button_color="#2B2D31", 
            button_hover_color="#3A3D42",
            command=self.on_preset_dropdown_select
        )
        self.preset_dropdown.pack(side="left", padx=5)
        
        self.preset_name_entry = ctk.CTkEntry(self.preset_mgmt_frame, placeholder_text="", width=150, fg_color="#1E1F22", border_width=0)
        self.preset_name_entry.pack(side="left", padx=5)
        
        self.preset_add_btn = ctk.CTkButton(self.preset_mgmt_frame, text="+", width=55, fg_color="#ED4245", hover_color="#C03033", font=ctk.CTkFont(size=14, weight="bold"), command=self.add_new_preset)
        self.preset_add_btn.pack(side="left", padx=5)
        
        self.preset_del_btn = ctk.CTkButton(self.preset_mgmt_frame, text="-", width=55, fg_color="#2B2D31", hover_color="#3A3D42", font=ctk.CTkFont(size=14, weight="bold"), command=self.delete_selected_preset)
        self.preset_del_btn.pack(side="left", padx=5)

        # --- РОТАЦИЯ ПРЕСЕТОВ ---
        self.loop_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.loop_frame.pack(pady=3)
        self.loop_checkbox = ctk.CTkCheckBox(self.loop_frame, text="", fg_color="#ED4245", hover_color="#C03033", command=self.toggle_preset_loop)
        self.loop_checkbox.pack(side="left", padx=5)
        self.loop_time_entry = ctk.CTkEntry(self.loop_frame, placeholder_text="15", width=60, fg_color="#1E1F22", border_width=0)
        self.loop_time_entry.insert(0, "15")
        self.loop_time_entry.pack(side="left", padx=5)

        # --- БОЛЬШАЯ КАРТИНКА ---
        self.file_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.file_frame.pack(pady=5)
        self.file_label = ctk.CTkLabel(self.file_frame, text="", width=300, anchor="w", text_color="gray")
        self.file_label.pack(side="left", padx=5)
        self.btn_browse = ctk.CTkButton(self.file_frame, text="", command=lambda: self.browse_file("large"), width=120, fg_color="#2B2D31", hover_color="#3A3D42")
        self.btn_browse.pack(side="right", padx=5)

        # --- МАНЕНЬКАЯ КАРТИНКА + ЧЕКБОКС ---
        self.small_img_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.small_img_frame.pack(pady=5)
        
        self.small_img_checkbox = ctk.CTkCheckBox(self.small_img_frame, text="", width=30, fg_color="#ED4245", hover_color="#C03033")
        self.small_img_checkbox.pack(side="left", padx=2)
        self.small_img_checkbox.select()

        self.small_file_label = ctk.CTkLabel(self.small_img_frame, text="Малая картинка не выбрана", width=265, anchor="w", text_color="gray")
        self.small_file_label.pack(side="left", padx=5)
        
        self.btn_browse_small = ctk.CTkButton(self.small_img_frame, text="Обзор...", command=lambda: self.browse_file("small"), width=120, fg_color="#2B2D31", hover_color="#3A3D42")
        self.btn_browse_small.pack(side="right", padx=5)

        # --- КНОПКА ОБНОВЛЕНИЯ СТАТУСА ---
        self.btn_update = ctk.CTkButton(self, text="", command=self.start_apply_thread, width=220, height=40, fg_color="#ED4245", hover_color="#C03033")
        self.btn_update.pack(pady=10)

        self.status_bar = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_bar.pack(side="bottom", pady=5)

        self.load_saved_data()
        self.update_ui_text()
        self.update_counters()

        threading.Thread(target=self.setup_global_hotkeys, daemon=True).start()

    def update_counters(self, event=None):
        det_len = len(self.details_entry.get())
        state_len = len(self.state_entry.get())
        
        self.det_counter.configure(text=f"{det_len} / 128")
        if det_len > 128: self.det_counter.configure(text_color="#ED4245")
        else: self.det_counter.configure(text_color="gray")
            
        self.state_counter.configure(text=f"{state_len} / 128")
        if state_len > 128: self.state_counter.configure(text_color="#ED4245")
        else: self.state_counter.configure(text_color="gray")

    def clear_details(self):
        self.details_entry.delete(0, ctk.END)
        self.update_counters()

    def clear_state(self):
        self.state_entry.delete(0, ctk.END)
        self.update_counters()

    def copy_id_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.id_entry.get())
        l = LANGS[self.lang]
        self.status_bar.configure(text=l["copied"], text_color="green")

    def setup_global_hotkeys(self):
        keyboard.add_hotkey('ctrl+shift+h', lambda: self.after(0, self.toggle_window_visibility))
        keyboard.add_hotkey('ctrl+shift+x', lambda: self.after(0, self.clear_rpc_status))
        keyboard.wait()

    def toggle_window_visibility(self):
        if self.is_hidden:
            if self.tray_icon: self.tray_icon.stop()
            self.deiconify()
            self.is_hidden = False
        else:
            self.minimize_to_tray()

    def clear_rpc_status(self):
        if self.rpc:
            try:
                self.rpc.clear()
                self.status_bar.configure(text="Статус в Discord очищен!" if self.lang == "RU" else "RPC Cleared!", text_color="yellow")
            except Exception: pass

    def toggle_lang(self):
        self.lang = "EN" if self.lang == "RU" else "RU"
        self.update_ui_text()

    def update_ui_text(self):
        l = LANGS[self.lang]
        self.label.configure(text=l["header"])
        self.id_label.configure(text=l["id_label"])
        self.id_entry.configure(placeholder_text=l["id_ph"])
        self.details_entry.configure(placeholder_text=l["det_ph"])
        self.state_entry.configure(placeholder_text=l["state_ph"])
        self.time_checkbox.configure(text=l["timer"])
        self.btn_label.configure(text=l["btn_label"])
        self.btn_text_entry.configure(placeholder_text=l["btn_txt_ph"])
        self.autostart_check.configure(text=l["autostart"])
        self.presets_label.configure(text=l["presets_label"])
        self.preset_name_entry.configure(placeholder_text=l["preset_name_ph"])
        self.loop_checkbox.configure(text=l["loop_timer"])
        self.small_img_checkbox.configure(text="")
        
        act_idx = 0
        old_act = self.activity_switch.get()
        if old_act in LANGS["RU"]["activity_modes"]: act_idx = LANGS["RU"]["activity_modes"].index(old_act)
        elif old_act in LANGS["EN"]["activity_modes"]: act_idx = LANGS["EN"]["activity_modes"].index(old_act)
        self.activity_switch.configure(values=l["activity_modes"])
        self.activity_switch.set(l["activity_modes"][act_idx])

        src_idx = 0
        old_src = self.source_switch.get()
        if old_src in LANGS["RU"]["source_modes"]: src_idx = LANGS["RU"]["source_modes"].index(old_src)
        elif old_src in LANGS["EN"]["source_modes"]: src_idx = LANGS["EN"]["source_modes"].index(old_src)
        self.source_switch.configure(values=l["source_modes"])
        self.source_switch.set(l["source_modes"][src_idx])

        beh_idx = 0
        old_beh = self.behavior_switch.get()
        if old_beh in LANGS["RU"]["behavior_modes"]: beh_idx = LANGS["RU"]["behavior_modes"].index(old_beh)
        elif old_beh in LANGS["EN"]["behavior_modes"]: beh_idx = LANGS["EN"]["behavior_modes"].index(old_beh)
        self.behavior_switch.configure(values=l["behavior_modes"])
        self.behavior_switch.set(l["behavior_modes"][beh_idx])
            
        self.btn_browse.configure(text=l["btn_browse"])
        self.btn_browse_small.configure(text=l["btn_browse"])
        self.btn_update.configure(text=l["btn_update"])
        
        if not self.uploaded_image_url and not self.config_data.get("img_url"):
            self.file_label.configure(text=l["no_file"])
        if not self.uploaded_small_image_url and not self.config_data.get("small_img_url"):
            self.small_file_label.configure(text="Малая картинка не выбрана" if self.lang == "RU" else "No small image")
            
        self.status_bar.configure(text=l["status_wait"])

    def load_config(self):
        import stat
        if os.path.exists(CONFIG_FILE):
            try:
                os.chmod(CONFIG_FILE, stat.S_IWRITE)
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "presets" not in data: data["presets"] = {}
                    return data
            except: pass
        return {
            "client_id": "1517958796587176117", 
            "details": "Тестирую кастомное меню", 
            "state": "⸺⸺⸺⸺⸺ˢᵈᵏ⸺⸺⸺⸺⸺⸺⸺⸺", 
            "time_val": "21", "source_idx": 0, "behavior_idx": 0, "activity_idx": 0,
            "btn_text": "", "btn_url": "", "btn2_text": "", "btn2_url": "", "img_url": "", "img_name": "",
            "small_img_url": "", "small_img_name": "", "small_img_enabled": True,
            "presets": {}
        }

    def save_config(self):
        import stat
        self.config_data["client_id"] = self.id_entry.get()
        self.config_data["details"] = self.details_entry.get()
        self.config_data["state"] = self.state_entry.get()
        self.config_data["time_val"] = self.time_entry.get()
        
        l = LANGS[self.lang]
        cur_act = self.activity_switch.get()
        if cur_act in l["activity_modes"]: self.config_data["activity_idx"] = l["activity_modes"].index(cur_act)

        cur_src = self.source_switch.get()
        if cur_src in l["source_modes"]: self.config_data["source_idx"] = l["source_modes"].index(cur_src)
            
        cur_beh = self.behavior_switch.get()
        if cur_beh in l["behavior_modes"]: self.config_data["behavior_idx"] = l["behavior_modes"].index(cur_beh)
            
        print("SAVE BTN2:", self.btn2_text_entry.get(), self.btn2_url_entry.get())
        self.config_data["btn_text"] = self.btn_text_entry.get()
        self.config_data["btn_url"] = self.btn_url_entry.get()
        self.config_data["btn2_text"] = self.btn2_text_entry.get()
        self.config_data["btn2_url"] = self.btn2_url_entry.get()
        
        self.config_data["img_url"] = self.uploaded_image_url if self.uploaded_image_url else self.config_data.get("img_url", "")
        self.config_data["img_name"] = self.file_label.cget("text")
        
        self.config_data["small_img_url"] = self.uploaded_small_image_url if self.uploaded_small_image_url else self.config_data.get("small_img_url", "")
        self.config_data["small_img_name"] = self.small_file_label.cget("text")
        self.config_data["small_img_enabled"] = True if self.small_img_checkbox.get() == 1 else False
        
        try:
            if os.path.exists(CONFIG_FILE): os.chmod(CONFIG_FILE, stat.S_IWRITE)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.status_bar.configure(text=f"Error writing config: {str(e)}", text_color="#ED4245")

    def load_saved_data(self):
        self.id_entry.insert(0, self.config_data.get("client_id", ""))
        self.details_entry.insert(0, self.config_data.get("details", ""))
        self.state_entry.insert(0, self.config_data.get("state", ""))
        self.time_entry.insert(0, self.config_data.get("time_val", "21"))
        self.btn_text_entry.insert(0, self.config_data.get("btn_text", ""))
        self.btn_url_entry.insert(0, self.config_data.get("btn_url", ""))
        self.btn2_text_entry.insert(0, self.config_data.get("btn2_text", ""))
        self.btn2_url_entry.insert(0, self.config_data.get("btn2_url", ""))
        
        l = LANGS[self.lang]
        act_idx = self.config_data.get("activity_idx", 0)
        if act_idx < len(l["activity_modes"]): self.activity_switch.set(l["activity_modes"][act_idx])

        src_idx = self.config_data.get("source_idx", 0)
        if src_idx < len(l["source_modes"]): self.source_switch.set(l["source_modes"][src_idx])
            
        beh_idx = self.config_data.get("behavior_idx", 0)
        if beh_idx < len(l["behavior_modes"]): self.behavior_switch.set(l["behavior_modes"][beh_idx])
            
        if self.config_data.get("img_url"):
            self.uploaded_image_url = self.config_data.get("img_url")
            self.file_label.configure(text=self.config_data.get("img_name", "Loaded from config"), text_color="white")
            
        if self.config_data.get("small_img_url"):
            self.uploaded_small_image_url = self.config_data.get("small_img_url")
            self.small_file_label.configure(text=self.config_data.get("small_img_name", "Small loaded"), text_color="white")
            
        if not self.config_data.get("small_img_enabled", True):
            self.small_img_checkbox.deselect()
        
        presets = list(self.config_data.get("presets", {}).keys())
        if presets:
            self.preset_dropdown.configure(values=presets)
            self.preset_dropdown.set(presets[0])
        else:
            self.preset_dropdown.configure(values=["None"])
            self.preset_dropdown.set("None")

    def on_preset_dropdown_select(self, name):
        if name == "None": return
        preset = self.config_data["presets"].get(name, {})
        if preset:
            self.details_entry.delete(0, ctk.END)
            self.details_entry.insert(0, preset.get("details", ""))
            self.state_entry.delete(0, ctk.END)
            self.state_entry.insert(0, preset.get("state", ""))
            self.update_counters()
            self.status_bar.configure(text=LANGS[self.lang]["preset_loaded"], text_color="green")

    def update_all_preset_selectors(self):
        presets = list(self.config_data.get("presets", {}).keys())
        if presets:
            self.preset_dropdown.configure(values=presets)
        else:
            self.preset_dropdown.configure(values=["None"])
            self.preset_dropdown.set("None")

    def add_new_preset(self):
        name = self.preset_name_entry.get().strip()
        if not name: return  
            
        self.config_data["presets"][name] = {
            "details": self.details_entry.get(),
            "state": self.state_entry.get()
        }
        self.save_config()
        self.update_all_preset_selectors()
        
        preset_list = list(self.config_data["presets"].keys())
        self.preset_dropdown.configure(values=preset_list)
        self.preset_dropdown.set(name)
        self.preset_name_entry.delete(0, ctk.END)
        self.status_bar.configure(text=LANGS[self.lang]["preset_saved"], text_color="green")

    def delete_selected_preset(self):
        name = self.preset_dropdown.get()
        if name == "None" or name not in self.config_data["presets"]: return
            
        del self.config_data["presets"][name]
        self.save_config()
        
        preset_list = list(self.config_data["presets"].keys())
        if preset_list:
            self.preset_dropdown.configure(values=preset_list)
            self.preset_dropdown.set(preset_list[0])
            self.on_preset_dropdown_select(preset_list[0])
        else:
            self.preset_dropdown.configure(values=["None"])
            self.preset_dropdown.set("None")
        self.status_bar.configure(text=LANGS[self.lang]["preset_deleted"], text_color="yellow")

    def toggle_preset_loop(self):
        if self.loop_checkbox.get() == 1:
            self.loop_running = True
            threading.Thread(target=self.preset_loop_worker, daemon=True).start()
        else:
            self.loop_running = False

    def preset_loop_worker(self):
        while self.loop_running:
            presets = list(self.config_data.get("presets", {}).keys())
            if not presets:
                time.sleep(2)
                continue
                
            if self.current_loop_index >= len(presets): self.current_loop_index = 0
                
            preset_name = presets[self.current_loop_index]
            self.after(0, lambda p=preset_name: self.apply_preset_directly(p))
            
            try:
                delay = int(self.loop_time_entry.get().strip())
                if delay < 5: delay = 5  
            except: delay = 15
                
            self.current_loop_index += 1
            time.sleep(delay)

    def apply_preset_directly(self, name):
        self.preset_dropdown.set(name)
        preset = self.config_data["presets"].get(name, {})
        if preset:
            self.details_entry.delete(0, ctk.END)
            self.details_entry.insert(0, preset.get("details", ""))
            self.state_entry.delete(0, ctk.END)
            self.state_entry.insert(0, preset.get("state", ""))
            self.update_counters()
            self.start_apply_thread()

    def browse_file(self, target="large"):
        l = LANGS[self.lang]
        file_path = filedialog.askopenfilename(
            title="VOID.rpc | Image Select",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.webp")]
        )
        if file_path:
            if target == "large":
                self.file_label.configure(text=os.path.basename(file_path), text_color="white")
            else:
                self.small_file_label.configure(text=os.path.basename(file_path), text_color="white")
                
            self.status_bar.configure(text=l["uploading"], text_color="yellow")
            threading.Thread(target=self.upload_image_worker, args=(file_path, target), daemon=True).start()

    def upload_image_worker(self, file_path, target):
        l = LANGS[self.lang]
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": f}
                )
            url = response.text.strip()
            if url.startswith("https://"):
                if target == "large":
                    self.uploaded_image_url = url
                else:
                    self.uploaded_small_image_url = url
                self.save_config()
                self.status_bar.configure(text=l["img_ready"], text_color="green")
            else:
                self.status_bar.configure(text=l["img_err"], text_color="#ED4245")
        except Exception as e:
            self.status_bar.configure(text=f"{l['net_err']}{str(e)}", text_color="#ED4245")

    def start_apply_thread(self):
        threading.Thread(target=self.apply_changes, daemon=True).start()

    def get_base_time(self, src_idx, val, now):
        if src_idx == 0:  # Минуты назад
            minutes = int(val) if (val and val.isdigit()) else 0
            return now - (minutes * 60)
        elif src_idx == 1:  # Unix Секунды
            if val and val.isdigit(): return int(val)
            return now
        elif src_idx == 2:  # Время от ПК (Берем точный таймстемп запуска)
            return self.pc_time_start
        elif src_idx == 3:  # Время от времени (Интервальный таймер)
            try:
                interval_mins = int(val) if (val and val.isdigit()) else 10
                if interval_mins <= 0: interval_mins = 10
                # Сбрасывает таймер на ноль каждые X минут циклом
                return now - (now % (interval_mins * 60))
            except:
                return now
        return now

    def apply_time_mode(self, beh_idx, base_time, now):
        if beh_idx == 0: return base_time, None  # Идет вперед
        elif beh_idx == 1:                       # Обратный отсчет
            offset = now - base_time if base_time <= now else 0
            return None, now + offset
        elif beh_idx == 2: return base_time, now # Заморожен
        return None, None

    def parse_inline_button(self, text):
        if text and "|" in text:
            parts = text.split("|", 1)
            label = parts[0].strip()
            url = parts[1].strip()
            if url.startswith(("http://", "https://")):
                return label, url, label
        return None, None, text

    def apply_changes(self):
        l = LANGS[self.lang]
        current_id = self.id_entry.get().strip()
        if not current_id:
            self.status_bar.configure(text=l["id_err"], text_color="#ED4245")
            return

        try:
            if not self.rpc:
                self.rpc = Presence(current_id)
                self.rpc.connect()
            elif hasattr(self.rpc, "client_id") and self.rpc.client_id != current_id:
                try: self.rpc.close()
                except: pass
                self.rpc = Presence(current_id)
                self.rpc.connect()
        except Exception as e:
            self.status_bar.configure(text=f"{l['discord_err']}{str(e)}", text_color="#ED4245")
            self.rpc = None
            return

        raw_d_text = self.details_entry.get().strip()
        raw_s_text = self.state_entry.get().strip()
        d_text = raw_d_text
        s_text = raw_s_text

        buttons = []

        # 1. Парсим ссылки из Details и State (если есть)
        for raw_text in [self.details_entry.get(), self.state_entry.get()]:
            label, url, _ = self.parse_inline_button(raw_text)
            if label and url and url.startswith("http"):
                buttons.append({"label": label[:32], "url": url})
        
        # 2. Добавляем кнопки из полей ввода, если есть место (лимит Discord = 2)
        input_fields = [
            (self.btn_text_entry, self.btn_url_entry),   # Первая кнопка
            (self.btn2_text_entry, self.btn2_url_entry)  # Вторая кнопка
        ]

        for text_entry, url_entry in input_fields:
            if len(buttons) >= 2: break # Лимит достигнут
            
            b_text = text_entry.get().strip()
            b_url = url_entry.get().strip()
            if b_text and b_url and b_url.startswith("http"):
                buttons.append({"label": b_text[:32], "url": b_url})

        # 3. Отправляем в Discord
        kwargs = {}
        kwargs["pid"] = os.getpid()
        
        # 2. Добавляем детали и состояние (d_text и s_text должны быть определены выше)
        if d_text: kwargs["details"] = d_text[:128]
        if s_text: kwargs["state"] = s_text[:128]

        # 3. А теперь добавляем кнопки в уже существующий kwargs
        if buttons:
            kwargs["buttons"] = buttons
        
        # --- МАППИНГ ИКОНОК (Discord Developer Portal Asset Keys) ---
        # Large image: маппим по тексту из Details
        LARGE_IMAGE_MAP = {
            "coding": "large_coding",
            "gaming": "large_gaming",
        }
        LARGE_IMAGE_DEFAULT = "large_idle"

        # Small image: маппим по наличию текста в State
        SMALL_IMAGE_ACTIVE  = "small_working"
        SMALL_IMAGE_DEFAULT = "small_offline"

        details_lower = d_text.lower() if d_text else ""
        large_key = LARGE_IMAGE_DEFAULT
        for keyword, asset_key in LARGE_IMAGE_MAP.items():
            if keyword in details_lower:
                large_key = asset_key
                break

        # Если загружена своя картинка — она имеет приоритет над маппингом
        if self.uploaded_image_url:
            url = self.uploaded_image_url.strip()
            if url and url not in ["", "нет", "None", "Выбрать"]:
                kwargs["large_image"] = url
        else:
            kwargs["large_image"] = large_key

        # --- МАЛЕНЬКАЯ КАРТИНКА ---
        if self.small_img_checkbox.get() == 1:
            if self.uploaded_small_image_url:
                url_small = self.uploaded_small_image_url.strip()
                if url_small and url_small not in ["", "нет", "None", "Выбрать"]:
                    kwargs["small_image"] = url_small
            else:
                # Маппинг: если State не пустой — small_working, иначе small_offline
                kwargs["small_image"] = SMALL_IMAGE_ACTIVE if s_text else SMALL_IMAGE_DEFAULT
        if buttons: kwargs["buttons"] = buttons

        # Тип активности
        act_str = self.activity_switch.get()
        act_idx = l["activity_modes"].index(act_str) if act_str in l["activity_modes"] else 0
        
        type_mapping = {
            0: ActivityType.PLAYING,
            1: ActivityType.LISTENING,
            2: ActivityType.WATCHING,
            3: ActivityType.COMPETING
        }
        kwargs["activity_type"] = type_mapping.get(act_idx, ActivityType.PLAYING)

        # Высчитываем время и таймер
        if self.time_checkbox.get() == 1:
            try:
                val = self.time_entry.get().strip()
                now = int(time.time())
                src_str = self.source_switch.get()
                beh_str = self.behavior_switch.get()
                src_idx = l["source_modes"].index(src_str) if src_str in l["source_modes"] else 0
                beh_idx = l["behavior_modes"].index(beh_str) if beh_str in l["behavior_modes"] else 0

                calculated_base = self.get_base_time(src_idx, val, now)
                final_start_time, final_end_time = self.apply_time_mode(beh_idx, calculated_base, now)
                
                if final_start_time is not None: kwargs["start"] = int(final_start_time)
                if final_end_time is not None: kwargs["end"] = int(final_end_time)
            except Exception:
                kwargs["pid"] = os.getpid()
                kwargs["start"] = int(time.time())

        try:
            self.rpc.update(**kwargs)
            self.save_config()
            self.status_bar.configure(text=l["success"], text_color="green")
        except Exception as e:
            self.status_bar.configure(text=f"{l['api_err']}{str(e)}", text_color="#ED4245")

    def check_autostart_registry(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except WindowsError: return False

    def toggle_autostart(self):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_WRITE)
        if self.autostart_var.get():
            app_path = os.path.realpath(sys.argv[0])
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{app_path}"')
        else:
            try: winreg.DeleteValue(key, APP_NAME)
            except WindowsError: pass
        winreg.CloseKey(key)

    def tray_open_window(self, icon):
        icon.stop()  
        self.is_hidden = False
        self.after(0, self.deiconify)  

    def tray_exit_program(self, icon):
        icon.stop()
        self.loop_running = False
        if self.rpc:
            try: self.rpc.close()
            except: pass
        self.destroy()

    def minimize_to_tray(self):
        l = LANGS[self.lang]
        self.withdraw()  
        self.is_hidden = True
        
        if self.raw_logo: tray_img = self.raw_logo
        else:
            logo_png_path = os.path.join(BASE_DIR, "logo.png")
            if os.path.exists(logo_png_path):
                try:
                    self.raw_logo = Image.open(logo_png_path)
                    tray_img = self.raw_logo
                except Exception:
                    tray_img = Image.new('RGB', (64, 64), color="#111214")
            else:
                tray_img = Image.new('RGB', (64, 64), color="#111214")
                draw = ImageDraw.Draw(tray_img)
                draw.rectangle([16, 16, 48, 48], fill="#ED4245")
        
        menu = (
            item(l["tray_open"], self.tray_open_window), 
            item(l["tray_exit"], self.tray_exit_program)
        )
        self.tray_icon = pystray.Icon("VOID.rpc", tray_img, "VOID.rpc", menu)
        
        def on_tray_ready(icon):
            icon.visible = True
            icon.notify(message=l["notify_msg"], title=l["notify_title"])

        threading.Thread(target=self.tray_icon.run, args=(on_tray_ready,), daemon=True).start()



if __name__ == "__main__":
    app = UltimateRPCMenu()
    app.mainloop()
