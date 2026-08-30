import customtkinter as ctk
from pypresence import Presence, ActivityType
import psutil
from datetime import datetime
import random
import time
import os
import sys
import json
import shutil
import winreg
import threading
import requests
import pystray
import ctypes  
import keyboard  
from PIL import Image, ImageDraw
from pystray import MenuItem as item
from customtkinter import filedialog

import sys
import os

# 1. Жестко фиксируем папку, где лежит .exe (или скрипт)
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
    # _MEIPASS используется ТОЛЬКО для чтения встроенных ресурсов (картинок)
    RESOURCE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    script_path = __file__ if "__file__" in globals() else sys.argv[0]
    APP_DIR = os.path.dirname(os.path.abspath(script_path))
    RESOURCE_DIR = APP_DIR

# 2. Меняем рабочую директорию ОС на папку с .exe
try:
    os.chdir(APP_DIR)
except Exception:
    pass

# 3. Рабочая папка для данных (конфиги, логи, пресеты) рядом с .exe или скриптом
CORE_DIR = os.path.join(APP_DIR, "core") if getattr(sys, "frozen", False) else APP_DIR

CONFIG_PATH = os.path.join(CORE_DIR, "config.json")
CONFIG_BACKUP_DIR = os.path.join(CORE_DIR, "config_backups")
LOG_DIR = os.path.join(CORE_DIR, "logs")
PRESET_DIR = os.path.join(CORE_DIR, "presets")

# 4. Для картинок делаем умный поиск (сначала рядом с .exe, если нет — внутри _MEIPASS)
external_logo_png = os.path.join(CORE_DIR, "logo.png")
external_logo_ico = os.path.join(CORE_DIR, "logo.ico")

if os.path.exists(external_logo_png):
    LOGO_PATH = external_logo_png
else:
    LOGO_PATH = os.path.join(RESOURCE_DIR, "core", "logo.png") if getattr(sys, "frozen", False) else os.path.join(RESOURCE_DIR, "logo.png")

if os.path.exists(external_logo_ico):
    ICON_PATH = external_logo_ico
else:
    ICON_PATH = os.path.join(RESOURCE_DIR, "core", "logo.ico") if getattr(sys, "frozen", False) else os.path.join(RESOURCE_DIR, "logo.ico")


def resolve_resource_paths():
    """Гарантирует существование папок для данных."""
    os.makedirs(CORE_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(PRESET_DIR, exist_ok=True)
    os.makedirs(CONFIG_BACKUP_DIR, exist_ok=True)
    return APP_DIR

# Автоматически вызываем при импорте
resolve_resource_paths()


resolve_resource_paths()
REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "VOID_RPC_SYSTEM"
LOG_FILE_TEMPLATE = "log_{date}.txt"

GAME_NAME_MAP = {
    "cs2.exe": "Counter-Strike 2",
    "valorant.exe": "VALORANT",
    "robloxplayerbeta.exe": "Roblox",
    "dota2.exe": "Dota 2",
    "leagueclient.exe": "League of Legends",
    "overwatch.exe": "Overwatch",
    "minecraft.exe": "Minecraft",
    "steam.exe": "Steam",
    "fortnite.exe": "Fortnite",
    "apex.exe": "Apex Legends",
    "battlefield.exe": "Battlefield",
    "callofduty.exe": "Call of Duty",
    "starfield.exe": "Starfield",
    "witcher3.exe": "The Witcher 3",
    "cyberpunk2077.exe": "Cyberpunk 2077",
}


def ensure_core_dirs():
    os.makedirs(CORE_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(PRESET_DIR, exist_ok=True)


def ensure_logs_folder():
    ensure_core_dirs()


LOG_COLORS = {
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m"
}
RESET_COLOR = "\033[0m"
ASCII_ART_PATH = os.path.join(CORE_DIR, "ascii-art.txt")
ASCII_REFERENCE_PATH = os.path.join(CORE_DIR, "ascii-art (2).png")


def _print_colored_ascii(ascii_lines, reference_image):
    image_width, image_height = reference_image.size
    columns = max((len(line) for line in ascii_lines), default=0)
    rows = len(ascii_lines)
    if not columns or not rows:
        return

    for row, line in enumerate(ascii_lines):
        for col, character in enumerate(line):
            if character == " ":
                print(" ", end="")
                continue
            pixel_x = min(image_width - 1, int((col + 0.5) * image_width / columns))
            pixel_y = min(image_height - 1, int((row + 0.5) * image_height / rows))
            red, green, blue = reference_image.getpixel((pixel_x, pixel_y))[:3]
            print(f"\033[38;2;{red};{green};{blue}m{character}{RESET_COLOR}", end="")
        print()


def set_console_visibility(show: bool):
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not hwnd:
            return
        ctypes.windll.user32.ShowWindow(hwnd, 9 if show else 0)
        if show:
            ctypes.windll.kernel32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def print_terminal_banner(launch_mode: str = "1"):
    if launch_mode == "2":
        return
    if sys.stdout is None or not sys.stdout.isatty():
        return

    print("""█   █  ███  ███ ████      ████  ████   ███
██  ███ ███  ████████     █████ █████ █ ███
██  ████  ██ ██ ██  ██    ████ █████ ███
 █ █ ███  ██ ██ ██  ██ █  █████ █████ ██
  █ █  ███ ████ ████ █ ██ ██  █ ██     ███
   █    ███  ███ ████   █  █   █ █      ███""", flush=True)
    time.sleep(3)

    try:
        with open(ASCII_ART_PATH, "r", encoding="utf-8", newline="") as ascii_file:
            ascii_lines = ascii_file.read().splitlines()
        with Image.open(ASCII_REFERENCE_PATH) as reference_image:
            _print_colored_ascii(ascii_lines, reference_image.convert("RGB"))
    except (FileNotFoundError, OSError, UnicodeError):
        print("""█   █  ███  ███ ████      ████  ████   ███
██  ███ ███  ████████     █████ █████ █ ███
██  ████  ██ ██ ██  ██    ████ █████ ███
 █ █ ███  ██ ██ ██  ██ █  █████ █████ ██
  █ █  ███ ████ ████ █ ██ ██  █ ██     ███
   █    ███  ███ ████   █  █   █ █      ███""")

    print("[VOID.rpc] Starting...")
    print("[VOID.rpc] Version: v1.4 Fix V2")
    print("[VOID.rpc] Initializing...")


def write_log(message: str, level: str = "INFO"):
    try:
        ensure_logs_folder()
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {level:<7} {message}"
        if sys.stdout.isatty():
            color = LOG_COLORS.get(level, "")
            print(f"{color}{line}{RESET_COLOR}")
        else:
            print(line)
        file_path = os.path.join(LOG_DIR, LOG_FILE_TEMPLATE.format(date=datetime.now().strftime("%Y-%m-%d")))
        with open(file_path, "a", encoding="utf-8") as log_file:
            log_file.write(line + "\n")
    except Exception:
        pass


class BaseUploadProvider:
    name = "base"

    def __init__(self, logger=None):
        self.logger = logger or write_log

    def _log(self, message, level="INFO"):
        try:
            self.logger(message, level)
        except Exception:
            pass

    def upload(self, file_path, config_data=None):
        raise NotImplementedError

    def _looks_like_error(self, text):
        if not text:
            return True
        lower = text.lower()
        return "error" in lower or "disabled" in lower or "failed" in lower or "denied" in lower or "timeout" in lower


class CatboxProvider(BaseUploadProvider):
    name = "catbox"

    def upload(self, file_path, config_data=None):
        self._log("Uploading image to Catbox...", "INFO")
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": f},
                    timeout=30
                )
            text = response.text.strip()
            if response.status_code >= 400:
                self._log(f"Catbox upload failed with HTTP {response.status_code}: {text}", "WARNING")
                return None
            if not text.startswith("https://") or self._looks_like_error(text):
                self._log(f"Catbox upload failed: {text}", "WARNING")
                return None
            return {"success": True, "url": text, "provider": self.name}
        except requests.Timeout as exc:
            self._log(f"Catbox upload timed out: {exc}", "WARNING")
            return None
        except Exception as exc:
            self._log(f"Catbox upload failed: {exc}", "WARNING")
            return None


class ImgBBProvider(BaseUploadProvider):
    name = "imgbb"

    def upload(self, file_path, config_data=None):
        self._log("Uploading image to ImgBB...", "INFO")
        api_key = (config_data or {}).get("imgbb_api_key", "") if config_data else ""
        if not api_key:
            self._log("ImgBB upload skipped because no API key is configured.", "WARNING")
            return None
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    "https://api.imgbb.com/1/upload",
                    data={"key": api_key},
                    files={"image": f},
                    timeout=30
                )
            if response.status_code >= 400:
                self._log(f"ImgBB upload failed with HTTP {response.status_code}: {response.text}", "WARNING")
                return None
            payload = response.json() if response.content else {}
            if not isinstance(payload, dict):
                self._log("ImgBB upload failed: invalid response payload.", "WARNING")
                return None
            if payload.get("success") is False:
                self._log(f"ImgBB upload failed: {payload}", "WARNING")
                return None
            data = payload.get("data", {}) if isinstance(payload.get("data"), dict) else {}
            url = data.get("url") or data.get("display_url") or data.get("thumb_url")
            if url:
                return {"success": True, "url": url, "provider": self.name}
            self._log(f"ImgBB upload failed: {response.text}", "WARNING")
            return None
        except requests.Timeout as exc:
            self._log(f"ImgBB upload timed out: {exc}", "WARNING")
            return None
        except ValueError as exc:
            self._log(f"ImgBB upload failed: invalid JSON response ({exc})", "WARNING")
            return None
        except Exception as exc:
            self._log(f"ImgBB upload failed: {exc}", "WARNING")
            return None


class UploadManager:
    def __init__(self, providers=None, logger=None):
        self.providers = list(providers or [])
        self.logger = logger or write_log

    def _log(self, message, level="INFO"):
        try:
            self.logger(message, level)
        except Exception:
            pass

    def upload(self, file_path, config_data=None):
        for index, provider in enumerate(self.providers):
            if index > 0:
                self._log(f"Switching to {provider.name}...", "INFO")
            result = provider.upload(file_path, config_data=config_data)
            if result and result.get("success"):
                self._log(f"Upload successful via {provider.name}.", "INFO")
                return result
            if index < len(self.providers) - 1:
                self._log(f"{provider.name} upload failed. Trying next provider...", "WARNING")
        self._log("All upload providers failed.", "ERROR")
        return {"success": False, "provider": None, "error": "All upload providers failed."}


PROVIDER_REGISTRY = {
    "catbox": CatboxProvider,
    "imgbb": ImgBBProvider,
}


def build_upload_providers(config_data=None):
    names = (config_data or {}).get("upload_providers", ["catbox", "imgbb"])
    if isinstance(names, str):
        names = [names]
    providers = []
    for name in names:
        provider_cls = PROVIDER_REGISTRY.get(name)
        if provider_cls:
            providers.append(provider_cls(logger=write_log))
    if not providers:
        providers = [CatboxProvider(logger=write_log), ImgBBProvider(logger=write_log)]
    return providers


class SafePresence:
    def __init__(self, client_id=None, logger=None):
        self.client_id = client_id
        self.logger = logger or (lambda msg, level="INFO": None)
        self.rpc = None
        self.last_payload = None
        self.lock = threading.RLock()
        self.connected = False
        self.stop_flag = False
        self._health_thread = None
        self._start_health_worker()

    def _log(self, message, level="INFO"):
        try:
            self.logger(message, level)
        except Exception:
            pass

    def _start_health_worker(self):
        if self._health_thread is None:
            self._health_thread = threading.Thread(target=self._health_worker, daemon=True)
            self._health_thread.start()

    def _health_worker(self):
        while not self.stop_flag:
            try:
                with self.lock:
                    if self.client_id and not self.connected:
                        self._connect_internal()
                        if self.connected and self.last_payload:
                            self._replay_last_payload()
            except Exception:
                pass
            time.sleep(random.uniform(1.0, 2.0))

    def _connect_internal(self):
        if self.rpc or not self.client_id:
            return
        self._log("Discord connecting...", "INFO")
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            self._log("Connected to Discord", "INFO")
        except Exception as exc:
            self.connected = False
            self.rpc = None
            self._log(f"ERROR: Discord IPC unavailable: {exc}", "ERROR")

    def _replay_last_payload(self):
        if self.rpc and self.last_payload:
            try:
                self.rpc.update(**self.last_payload)
                self._log("Reconnected successfully", "INFO")
            except Exception as exc:
                self._log(f"ERROR: Failed to replay presence: {exc}", "ERROR")
                self._close_internal()

    def _close_internal(self):
        if self.rpc:
            try:
                self.rpc.close()
            except Exception:
                pass
            self._log("Discord disconnected", "WARNING")
        self.rpc = None
        self.connected = False

    def update(self, client_id=None, **kwargs):
        if client_id:
            self.client_id = client_id
        self.last_payload = kwargs
        with self.lock:
            if not self.connected:
                self._connect_internal()
            if not self.rpc:
                raise ConnectionError("Discord RPC unavailable")
            try:
                self.rpc.update(**kwargs)
                self.connected = True
                self._log("Presence updated", "INFO")
            except Exception as exc:
                self._log(f"ERROR: Failed to update Presence: {exc}", "ERROR")
                self._close_internal()
                self._log("Reconnecting...", "WARNING")
                self._connect_internal()
                if self.rpc:
                    try:
                        self.rpc.update(**kwargs)
                        self.connected = True
                        self._log("Reconnected and updated presence", "INFO")
                    except Exception as exc2:
                        self._log(f"ERROR: Failed to update Presence: {exc2}", "ERROR")
                        raise

    def clear(self):
        with self.lock:
            if self.rpc:
                try:
                    self.rpc.clear()
                    self._log("Presence cleared", "INFO")
                except Exception as exc:
                    self._log(f"ERROR: Failed to clear Presence: {exc}", "ERROR")
                    self._close_internal()

    def close(self):
        self.stop_flag = True
        with self.lock:
            self._close_internal()
            self.connected = False
            self.last_payload = None
        self._log("Application closed", "INFO")

try:
    myappid = 'void.rpc.system.1.4.fix.t3.(v3)'
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
        "auto_update": "Автообновление статуса",
        "launch_gui": "Запускать в GUI",
        "launch_tray": "Запускать в Tray",
        "backup_label": "Резервные копии config.json:",
        "backup_restore": "Восстановить",
        "backup_none": "Копий нет",
        "time_system": "Использовать системное время",
        "time_format": "Формат:",
        "time_format_24": "24 часа",
        "time_format_12": "12 часов (AM/PM)",
        "time_precise_min": "Часы и минуты",
        "time_precise_sec": "Часы, минуты и секунды",
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
        "auto_update": "Auto-update status",
        "launch_gui": "Launch in GUI",
        "launch_tray": "Launch in Tray",
        "backup_label": "config.json backups:",
        "backup_restore": "Restore",
        "backup_none": "No backups",
        "time_system": "Use system time",
        "time_format": "Format:",
        "time_format_24": "24 hours",
        "time_format_12": "12 hours (AM/PM)",
        "time_precise_min": "Hours and minutes",
        "time_precise_sec": "Hours, minutes and seconds",
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
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.ui_scale = min(1.0, (screen_width - 20) / 560, (screen_height - 40) / 1100)
        self.ui_scale = max(0.55, self.ui_scale)
        ctk.set_widget_scaling(self.ui_scale)
        window_width = max(240, int(560 * self.ui_scale))
        window_height = min(int(1100 * self.ui_scale), max(420, screen_height - 40))
        self.geometry(f"{window_width}x{window_height}")
        self.resizable(False, False)
        self.configure(fg_color="#111214")  

        self.rpc = None
        self.uploaded_image_url = None
        self.uploaded_small_image_url = None # Для маленькой картинки
        self.uploaded_image_provider = ""
        self.uploaded_small_image_provider = ""
        self.tray_icon = None
        self.is_hidden = False  
        self.loop_running = False
        self.current_loop_index = 0
        self.pc_time_start = int(time.time())
        self.auto_update_tick = 0
        self.manual_updates_count = 0
        self.auto_updates_count = 0
        self.update_durations = []
        
        self.config_data = self.load_config()
        self.upload_manager = UploadManager(providers=build_upload_providers(self.config_data), logger=write_log)
        self.safe_presence = SafePresence(logger=write_log)
        self.config_lock = threading.Lock()  # Шлагбаум для синхронизации потоков
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        # --- ЛОГОТИП ---
        self.raw_logo = None
        ensure_core_dirs()
        logo_png_path = LOGO_PATH
        logo_ico_path = ICON_PATH

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
        self.lang_btn.place(relx=1.0, x=-20, y=10, anchor="ne")

        self.content_parent = self
        if screen_height < 760 or screen_width < 520:
            self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
            self.content_frame.pack(fill="both", expand=True, padx=8, pady=(48, 0))
            self.content_parent = self.content_frame

        # --- ИНТЕРФЕЙС ---
        self.label = ctk.CTkLabel(self.content_parent, text="VOID.rpc | SYSTEM", font=ctk.CTkFont(size=18, weight="bold"), text_color="#ED4245")
        self.label.pack(pady=10)

        self.id_label = ctk.CTkLabel(self.content_parent, text="", text_color="gray")
        self.id_label.pack(pady=(2, 2))
        
        self.id_frame = ctk.CTkFrame(self.content_parent, fg_color="transparent")
        self.id_frame.pack(pady=3)
        self.id_entry = ctk.CTkEntry(self.id_frame, placeholder_text="", width=400, fg_color="#1E1F22", border_width=0)
        self.id_entry.pack(side="left", padx=(0, 5))
        self.id_copy_btn = ctk.CTkButton(self.id_frame, text="📋", width=35, fg_color="#1E1F22", hover_color="#3A3D42", command=self.copy_id_to_clipboard)
        self.id_copy_btn.pack(side="right")

        # Поле Details
        self.det_frame = ctk.CTkFrame(self.content_parent, fg_color="transparent")
        self.det_frame.pack(pady=(5, 2))
        self.details_entry = ctk.CTkEntry(self.det_frame, placeholder_text="", width=400, fg_color="#1E1F22", border_width=0)
        self.details_entry.pack(side="left", padx=(0, 5))
        self.det_clear = ctk.CTkButton(self.det_frame, text="×", width=35, fg_color="#1E1F22", hover_color="#3A3D42", command=self.clear_details)
        self.det_clear.pack(side="right")
        
        self.det_counter = ctk.CTkLabel(self.content_parent, text="0 / 128", font=ctk.CTkFont(size=11), text_color="gray")
        self.det_counter.pack(anchor="e", padx=65, fill="x", pady=(0, 2))
        self.details_entry.bind("<KeyRelease>", self.update_counters)

        # Поле State
        self.state_frame = ctk.CTkFrame(self.content_parent, fg_color="transparent")
        self.state_frame.pack(pady=(3, 2))
        self.state_entry = ctk.CTkEntry(self.state_frame, placeholder_text="", width=400, fg_color="#1E1F22", border_width=0)
        self.state_entry.pack(side="left", padx=(0, 5))
        self.state_clear = ctk.CTkButton(self.state_frame, text="×", width=35, fg_color="#1E1F22", hover_color="#3A3D42", command=self.clear_state)
        self.state_clear.pack(side="right")
        
        self.state_counter = ctk.CTkLabel(self.content_parent, text="0 / 128", font=ctk.CTkFont(size=11), text_color="gray")
        self.state_counter.pack(anchor="e", padx=65, fill="x", pady=(0, 2))
        self.state_entry.bind("<KeyRelease>", self.update_counters)

        # --- НАСТРОЙКА ВРЕМЕНИ И АКТИВНОСТЕЙ ---
        self.time_frame = ctk.CTkFrame(self.content_parent, fg_color="transparent")
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
        self.btn_label = ctk.CTkLabel(self.content_parent, text="", text_color="gray")
        self.btn_label.pack(pady=(5, 2))
        
        self.custom_btn_frame = ctk.CTkFrame(self.content_parent, fg_color="transparent")
        self.custom_btn_frame.pack(pady=3)
        
        self.btn_text_entry = ctk.CTkEntry(self.custom_btn_frame, placeholder_text="", width=140, fg_color="#1E1F22", border_width=0)
        self.btn_text_entry.pack(side="left", padx=5)
        
        self.btn_url_entry = ctk.CTkEntry(self.custom_btn_frame, placeholder_text="https://...", width=290, fg_color="#1E1F22", border_width=0)
        self.btn_url_entry.pack(side="left", padx=5)

        # --- КНОПКА 2 ---
        self.btn2_label = ctk.CTkLabel(self.content_parent, text="", text_color="gray")
        self.btn2_label.pack(pady=(5, 2))

        self.custom_btn2_frame = ctk.CTkFrame(self.content_parent, fg_color="transparent")
        self.custom_btn2_frame.pack(pady=3)

        self.btn2_text_entry = ctk.CTkEntry(self.custom_btn2_frame, placeholder_text="", width=140, fg_color="#1E1F22", border_width=0)
        self.btn2_text_entry.pack(side="left", padx=5)

        self.btn2_url_entry = ctk.CTkEntry(self.custom_btn2_frame, placeholder_text="https://...", width=290, fg_color="#1E1F22", border_width=0)
        self.btn2_url_entry.pack(side="left", padx=5)

        # --- АВТОЗАГРУЗКА ---
        self.autostart_var = ctk.BooleanVar(value=self.check_autostart_registry())
        self.autostart_check = ctk.CTkCheckBox(self.content_parent, text="", variable=self.autostart_var, fg_color="#ED4245", hover_color="#C03033", command=self.toggle_autostart)
        self.autostart_check.pack(pady=(5, 0), padx=65, anchor="w")

        self.auto_update_var = ctk.BooleanVar(value=self.config_data.get("auto_update", True))
        self.auto_update_check = ctk.CTkCheckBox(self.content_parent, text="", variable=self.auto_update_var, fg_color="#ED4245", hover_color="#C03033", command=self.handle_auto_update_toggle)
        self.auto_update_check.pack(pady=(2, 0), padx=65, anchor="w")

        self.console_var = ctk.BooleanVar(value=self.config_data.get("show_console", False))
        self.console_check = ctk.CTkCheckBox(self.content_parent, text="Режим терминала (Отладка)" if self.lang == "RU" else "Terminal Mode (Debug)", variable=self.console_var, fg_color="#ED4245", hover_color="#C03033", command=self.toggle_console_mode)
        self.console_check.pack(pady=(2, 0), padx=65, anchor="w")

        self.launch_gui_var = ctk.BooleanVar(value=self.config_data.get("launch_gui", not self.config_data.get("launch_tray", False)))
        self.launch_tray_var = ctk.BooleanVar(value=self.config_data.get("launch_tray", False))
        self.launch_gui_check = ctk.CTkCheckBox(self.content_parent, text="", variable=self.launch_gui_var, fg_color="#ED4245", hover_color="#C03033", command=self.toggle_launch_mode)
        self.launch_gui_check.pack(pady=(2, 0), padx=65, anchor="w")
        self.launch_tray_check = ctk.CTkCheckBox(self.content_parent, text="", variable=self.launch_tray_var, fg_color="#ED4245", hover_color="#C03033", command=self.toggle_launch_mode)
        self.launch_tray_check.pack(pady=(2, 0), padx=65, anchor="w")

        self.backup_frame = ctk.CTkFrame(self.content_parent, fg_color="transparent")
        self.backup_frame.pack(pady=(4, 2), padx=65, anchor="w", fill="x")
        self.backup_label = ctk.CTkLabel(self.backup_frame, text="", text_color="gray")
        self.backup_label.pack(anchor="w")
        self.backup_select = ctk.CTkOptionMenu(self.backup_frame, values=self.get_backup_names(), width=230, fg_color="#1E1F22", button_color="#2B2D31", button_hover_color="#3A3D42")
        self.backup_select.pack(side="left", pady=(2, 0))
        self.backup_restore_btn = ctk.CTkButton(self.backup_frame, text="", width=105, fg_color="#2B2D31", hover_color="#3A3D42", command=self.restore_config_backup)
        self.backup_restore_btn.pack(side="left", padx=(6, 0), pady=(2, 0))

        # --- ПРЕСЕТЫ ---
        self.presets_label = ctk.CTkLabel(self.content_parent, text="", text_color="gray")
        self.presets_label.pack(pady=(5, 2))
        
        self.preset_mgmt_frame = ctk.CTkFrame(self.content_parent, fg_color="transparent")
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
        self.loop_frame = ctk.CTkFrame(self.content_parent, fg_color="transparent")
        self.loop_frame.pack(pady=3)
        self.loop_checkbox = ctk.CTkCheckBox(self.loop_frame, text="", fg_color="#ED4245", hover_color="#C03033", command=self.toggle_preset_loop)
        self.loop_checkbox.pack(side="left", padx=5)
        self.loop_time_entry = ctk.CTkEntry(self.loop_frame, placeholder_text="15", width=60, fg_color="#1E1F22", border_width=0)
        self.loop_time_entry.insert(0, "15")
        self.loop_time_entry.pack(side="left", padx=5)

        # --- БОЛЬШАЯ КАРТИНКА ---
        self.file_frame = ctk.CTkFrame(self.content_parent, fg_color="transparent")
        self.file_frame.pack(pady=5)
        self.file_label = ctk.CTkLabel(self.file_frame, text="", width=300, anchor="w", text_color="gray")
        self.file_label.pack(side="left", padx=5)
        self.image_history_menu = ctk.CTkOptionMenu(self.file_frame, values=["История" if self.lang == "RU" else "History"], width=110, fg_color="#1E1F22", button_color="#2B2D31", button_hover_color="#3A3D42")
        self.image_history_menu.pack(side="right", padx=(0, 5))
        self.image_history_menu.configure(command=lambda value: self.select_history_image("large", value))
        self.btn_browse = ctk.CTkButton(self.file_frame, text="", command=lambda: self.browse_file("large"), width=120, fg_color="#2B2D31", hover_color="#3A3D42")
        self.btn_browse.pack(side="right", padx=5)

        # --- МАНЕНЬКАЯ КАРТИНКА + ЧЕКБОКС ---
        self.small_img_frame = ctk.CTkFrame(self.content_parent, fg_color="transparent")
        self.small_img_frame.pack(pady=5)
        
        self.small_img_checkbox = ctk.CTkCheckBox(self.small_img_frame, text="", width=30, fg_color="#ED4245", hover_color="#C03033")
        self.small_img_checkbox.pack(side="left", padx=2)
        self.small_img_checkbox.select()

        self.small_file_label = ctk.CTkLabel(self.small_img_frame, text="Малая картинка не выбрана", width=265, anchor="w", text_color="gray")
        self.small_file_label.pack(side="left", padx=5)
        self.small_image_history_menu = ctk.CTkOptionMenu(self.small_img_frame, values=["История" if self.lang == "RU" else "History"], width=110, fg_color="#1E1F22", button_color="#2B2D31", button_hover_color="#3A3D42")
        self.small_image_history_menu.pack(side="right", padx=(0, 5))
        self.small_image_history_menu.configure(command=lambda value: self.select_history_image("small", value))
        self.btn_browse_small = ctk.CTkButton(self.small_img_frame, text="Обзор...", command=lambda: self.browse_file("small"), width=120, fg_color="#2B2D31", hover_color="#3A3D42")
        self.btn_browse_small.pack(side="right", padx=5)

        # --- КНОПКА ОБНОВЛЕНИЯ СТАТУСА ---
        self.btn_update = ctk.CTkButton(self.content_parent, text="", command=self.start_apply_thread, width=220, height=40, fg_color="#ED4245", hover_color="#C03033")
        self.btn_update.pack(pady=10)

        self.status_bar = ctk.CTkLabel(self.content_parent, text="", text_color="gray")
        self.status_bar.pack(side="bottom", pady=5)

        self.load_saved_data()
        self.update_ui_text()
        self.update_counters()
        self.update_launch_mode_state()
        self.started_from_windows = "--autostart" in sys.argv
        if self.config_data.get("launch_tray", False) and (not self.started_from_windows or self.autostart_var.get() == 1):
            self.after(100, self.minimize_to_tray)
        write_log("Configuration loaded", "INFO")

        threading.Thread(target=self.setup_global_hotkeys, daemon=True).start()
        threading.Thread(target=self.auto_update_worker, daemon=True).start()
        write_log("Application started")

    def update_counters(self, event=None):
        det_len = len(self.details_entry.get())
        state_len = len(self.state_entry.get())
        
        self.det_counter.configure(text=f"{det_len} / 128")
        if det_len > 128: self.det_counter.configure(text_color="#ED4245")
        else: self.det_counter.configure(text_color="gray")
            
        self.state_counter.configure(text=f"{state_len} / 128")
        if state_len > 128: self.state_counter.configure(text_color="#ED4245")
        else: self.state_counter.configure(text_color="gray")

    def get_backup_names(self):
        ensure_core_dirs()
        backups = [name for name in os.listdir(CONFIG_BACKUP_DIR) if name.endswith(".json")]
        return sorted(backups, reverse=True) or [LANGS[self.lang]["backup_none"]]

    def refresh_backup_list(self):
        names = self.get_backup_names()
        self.backup_select.configure(values=names)
        self.backup_select.set(names[0])

    def update_launch_mode_state(self):
        gui_enabled = self.launch_gui_var.get() == 1
        tray_enabled = self.launch_tray_var.get() == 1
        autostart_enabled = self.autostart_var.get() == 1
        self.launch_gui_check.configure(state="disabled" if tray_enabled or not autostart_enabled else "normal")
        self.launch_tray_check.configure(state="disabled" if gui_enabled or not autostart_enabled else "normal")

    def toggle_launch_mode(self):
        if self.launch_gui_var.get() == 1 and self.launch_tray_var.get() == 1:
            self.launch_tray_var.set(False)
        if not self.launch_gui_var.get() and not self.launch_tray_var.get():
            self.update_launch_mode_state()
            return
        self.update_launch_mode_state()
        self.save_config()

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
        try:
            self.safe_presence.clear()
            self.status_bar.configure(text="Статус в Discord очищен!" if self.lang == "RU" else "RPC Cleared!", text_color="yellow")
        except Exception:
            pass

    def handle_auto_update_toggle(self):
        self.config_data["auto_update"] = True if self.auto_update_var.get() == 1 else False
        self.save_config()
        write_log(f"Auto-update {'enabled' if self.auto_update_var.get() == 1 else 'disabled'}", "INFO")

    def toggle_console_mode(self):
        self.config_data["show_console"] = True if self.console_var.get() == 1 else False
        self.save_config()
        set_console_visibility(self.config_data.get("show_console", False))

        try:
            executable = sys.executable
            argv = [executable] + sys.argv[1:]
            os.execv(executable, argv)
        except Exception:
            try:
                os.execv(sys.executable, [sys.executable] + sys.argv[1:])
            except Exception:
                pass

    def get_current_time_strings(self):
        now = datetime.now()
        time24 = now.strftime("%H:%M")
        time24s = now.strftime("%H:%M:%S")
        time12 = now.strftime("%I:%M %p")
        time12s = now.strftime("%I:%M:%S %p")
        return {
            "time24": time24,
            "time24s": time24s,
            "time12": time12,
            "time12s": time12s,
            "time": time24s if self.config_data.get("time_precision", "seconds") == "seconds" else time24
        }

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
        self.auto_update_check.configure(text=l.get("auto_update", "Auto-update"))
        self.launch_gui_check.configure(text=l["launch_gui"])
        self.launch_tray_check.configure(text=l["launch_tray"])
        self.backup_label.configure(text=l["backup_label"])
        self.backup_restore_btn.configure(text=l["backup_restore"])
        self.refresh_backup_list()
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
        ensure_core_dirs()
        if os.path.exists(CONFIG_PATH):
            try:
                os.chmod(CONFIG_PATH, stat.S_IWRITE)
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "presets" not in data: data["presets"] = {}
                    data.setdefault("launch_tray", False)
                    data.setdefault("launch_gui", not data["launch_tray"])
                    if data["launch_tray"]:
                        data["launch_gui"] = False
                    elif not data["launch_gui"]:
                        data["launch_gui"] = True
                    data.setdefault("show_console", False)
                    data.setdefault("img_provider", "")
                    data.setdefault("imgbb_api_key", "")
                    data.setdefault("upload_providers", ["catbox", "imgbb"])
                    data.setdefault("image_history", [])
                    data.setdefault("small_image_history", [])
                    return data
            except: pass
        return {
            "client_id": "1517958796587176117",
            "details": "Тестирую кастомное меню",
            "state": "⸺⸺⸺⸺⸺ˢᵈᵏ⸺⸺⸺⸺⸺⸺⸺⸺",
            "time_val": "21", "source_idx": 0, "behavior_idx": 0, "activity_idx": 0,
            "time_enabled": True,
            "auto_update": True,
            "show_console": False,
            "launch_gui": True,
            "launch_tray": False,
            "time_format": "24",
            "time_precision": "seconds",
            "btn_text": "", "btn_url": "", "btn2_text": "", "btn2_url": "",
            "img_url": "", "img_name": "",
            "small_img_url": "", "small_img_name": "", "small_img_enabled": True,
            "img_provider": "",
            "imgbb_api_key": "",
            "upload_providers": ["catbox", "imgbb"],
            "image_history": [],
            "small_image_history": [],
            "presets": {}
        }

    def _get_history_menu_values(self, target):
        history_key = "image_history" if target == "large" else "small_image_history"
        history = self.config_data.get(history_key, []) or []
        if not history:
            return ["История" if self.lang == "RU" else "History"]
        values = []
        for item in history[:15]:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("url") or ("Image" if target == "large" else "Small image")
            values.append(name)
        return values

    def _refresh_history_menus(self):
        large_values = self._get_history_menu_values("large")
        small_values = self._get_history_menu_values("small")
        self.image_history_menu.configure(values=large_values)
        self.small_image_history_menu.configure(values=small_values)
        if large_values:
            self.image_history_menu.set(large_values[0])
        else:
            self.image_history_menu.set("История" if self.lang == "RU" else "History")
        if small_values:
            self.small_image_history_menu.set(small_values[0])
        else:
            self.small_image_history_menu.set("История" if self.lang == "RU" else "History")

    def _record_successful_image_history(self, url, name, provider, target):
        if not url:
            return
        history_key = "image_history" if target == "large" else "small_image_history"
        history = self.config_data.get(history_key, []) or []
        item = {"url": url, "name": name or ("Image" if target == "large" else "Small image"), "provider": provider or ""}
        filtered = [existing for existing in history if isinstance(existing, dict) and existing.get("url") != url]
        filtered.insert(0, item)
        self.config_data[history_key] = filtered[:15]
        self._refresh_history_menus()

    def _apply_history_image(self, target, selected_name):
        if not selected_name or selected_name in ["История", "History"]:
            return
        history_key = "image_history" if target == "large" else "small_image_history"
        history = self.config_data.get(history_key, []) or []
        entry = next((item for item in history if isinstance(item, dict) and item.get("name") == selected_name), None)
        if entry is None:
            return
        url = entry.get("url")
        if not url:
            return
        if target == "large":
            self.uploaded_image_url = url
            self.uploaded_image_provider = entry.get("provider", "")
            self.file_label.configure(text=entry.get("name", "Loaded from history"), text_color="white")
            self.config_data["img_url"] = url
            self.config_data["img_name"] = entry.get("name", "Loaded from history")
            self.config_data["img_provider"] = self.uploaded_image_provider
        else:
            self.uploaded_small_image_url = url
            self.uploaded_small_image_provider = entry.get("provider", "")
            self.small_file_label.configure(text=entry.get("name", "Loaded from history"), text_color="white")
            self.config_data["small_img_url"] = url
            self.config_data["small_img_name"] = entry.get("name", "Loaded from history")
            self.config_data["small_img_enabled"] = True
        self.save_config()
        self.status_bar.configure(text="Изображение выбрано из истории" if self.lang == "RU" else "Image selected from history", text_color="green")

    def select_history_image(self, target, value):
        if value in ["История", "History"]:
            return
        self._apply_history_image(target, value)

    def _config_snapshot(self, config):
        return json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _create_config_backup(self, reason="manual"):
        ensure_core_dirs()
        if not isinstance(self.config_data, dict):
            return False

        snapshot = self._config_snapshot(self.config_data)

        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    if f.read() == snapshot:
                        return False
            except Exception:
                pass

        for name in sorted(os.listdir(CONFIG_BACKUP_DIR), reverse=True):
            if not name.endswith(".json"):
                continue
            backup_path = os.path.join(CONFIG_BACKUP_DIR, name)
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    if f.read() == snapshot:
                        return False
            except Exception:
                continue

        backup_name = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{reason}.json"
        backup_path = os.path.join(CONFIG_BACKUP_DIR, backup_name)
        try:
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)

            backups = sorted(
                (os.path.join(CONFIG_BACKUP_DIR, name) for name in os.listdir(CONFIG_BACKUP_DIR) if name.endswith(".json")),
                key=os.path.getmtime,
                reverse=True
            )
            for old_backup in backups[10:]:
                try:
                    os.remove(old_backup)
                except Exception:
                    pass
            return True
        except Exception:
            return False

    def save_config(self):
        import stat
        self.config_data["client_id"] = self.id_entry.get()
        self.config_data["details"] = self.details_entry.get()
        self.config_data["state"] = self.state_entry.get()
        self.config_data["time_val"] = self.time_entry.get()
        self.config_data["time_enabled"] = True if self.time_checkbox.get() == 1 else False
        self.config_data["auto_update"] = True if self.auto_update_var.get() == 1 else False

        # Автоматические безопасные настройки формата (вместо удаленных кривых меню)
        self.config_data["time_format"] = "24"
        self.config_data["time_precision"] = "seconds"
        
        l = LANGS[self.lang]
        cur_act = self.activity_switch.get()
        if cur_act in l["activity_modes"]: self.config_data["activity_idx"] = l["activity_modes"].index(cur_act)

        cur_src = self.source_switch.get()
        if cur_src in l["source_modes"]: self.config_data["source_idx"] = l["source_modes"].index(cur_src)
            
        cur_beh = self.behavior_switch.get()
        if cur_beh in l["behavior_modes"]: self.config_data["behavior_idx"] = l["behavior_modes"].index(cur_beh)
            
        self.config_data["btn_text"] = self.btn_text_entry.get()
        self.config_data["btn_url"] = self.btn_url_entry.get()
        self.config_data["btn2_text"] = self.btn2_text_entry.get()
        self.config_data["btn2_url"] = self.btn2_url_entry.get()
        
        self.config_data["img_url"] = self.uploaded_image_url if self.uploaded_image_url else self.config_data.get("img_url", "")
        self.config_data["img_name"] = self.file_label.cget("text")
        self.config_data["img_provider"] = self.uploaded_image_provider if self.uploaded_image_provider else self.config_data.get("img_provider", "")
        
        self.config_data["small_img_url"] = self.uploaded_small_image_url if self.uploaded_small_image_url else self.config_data.get("small_img_url", "")
        self.config_data["small_img_name"] = self.small_file_label.cget("text")
        self.config_data["small_img_enabled"] = True if self.small_img_checkbox.get() == 1 else False
        self.config_data["show_console"] = True if self.console_var.get() == 1 else False
        self.config_data["launch_gui"] = self.launch_gui_var.get() == 1
        self.config_data["launch_tray"] = self.launch_tray_var.get() == 1
        self.config_data["image_history"] = self.config_data.get("image_history", [])[:15]
        self.config_data["small_image_history"] = self.config_data.get("small_image_history", [])[:15]

        if hasattr(self, "console_var"):
            set_console_visibility(self.config_data.get("show_console", False))

        try:
            ensure_core_dirs()
            if os.path.exists(CONFIG_PATH):
                try:
                    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                        saved_config = json.load(f)
                    if saved_config == self.config_data:
                        return
                except Exception:
                    pass
                os.chmod(CONFIG_PATH, stat.S_IWRITE)

            # Сравнение уже проверено выше: запись на диск и бэкап выполняются только при реальном изменении
            self._create_config_backup("before_save")

            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)
            self.refresh_backup_list()
        except Exception as e:
            self.status_bar.configure(text=f"Error writing config: {str(e)}", text_color="#ED4245")

    def restore_config_backup(self):
        backup_name = self.backup_select.get()
        if backup_name == LANGS[self.lang]["backup_none"]:
            return
        backup_path = os.path.join(CONFIG_BACKUP_DIR, backup_name)
        try:
            with open(backup_path, "r", encoding="utf-8") as backup_file:
                restored = json.load(backup_file)
            if not isinstance(restored, dict):
                raise ValueError("Backup must contain a JSON object")

            # Сначала безопасно сохраняем текущую конфигурацию, чтобы можно было откатиться назад
            self._create_config_backup("before_restore")

            restored.setdefault("presets", {})
            restored.setdefault("launch_tray", False)
            restored.setdefault("launch_gui", not restored["launch_tray"])
            if restored["launch_tray"]:
                restored["launch_gui"] = False
            elif not restored["launch_gui"]:
                restored["launch_gui"] = True
            self.config_data = restored
            self.upload_manager = UploadManager(providers=build_upload_providers(self.config_data), logger=write_log)
            self.load_saved_data()
            self.update_ui_text()
            self.update_launch_mode_state()
            self.status_bar.configure(text="Конфигурация восстановлена" if self.lang == "RU" else "Configuration restored", text_color="green")
        except Exception as exc:
            self.status_bar.configure(text=f"Restore error: {exc}", text_color="#ED4245")

    def load_saved_data(self):
        for entry in (self.id_entry, self.details_entry, self.state_entry, self.time_entry, self.btn_text_entry, self.btn_url_entry, self.btn2_text_entry, self.btn2_url_entry):
            entry.delete(0, ctk.END)
        self.id_entry.insert(0, self.config_data.get("client_id", ""))
        self.details_entry.insert(0, self.config_data.get("details", ""))
        self.state_entry.insert(0, self.config_data.get("state", ""))
        self.time_entry.insert(0, self.config_data.get("time_val", "21"))
        self.btn_text_entry.insert(0, self.config_data.get("btn_text", ""))
        self.btn_url_entry.insert(0, self.config_data.get("btn_url", ""))
        self.btn2_text_entry.insert(0, self.config_data.get("btn2_text", ""))
        self.btn2_url_entry.insert(0, self.config_data.get("btn2_url", ""))
        
        if self.config_data.get("time_enabled", True):
            self.time_checkbox.select()
        else:
            self.time_checkbox.deselect()

        if self.config_data.get("auto_update", True):
            self.auto_update_check.select()
        else:
            self.auto_update_check.deselect()

        if self.config_data.get("show_console", False):
            self.console_check.select()
        else:
            self.console_check.deselect()
        set_console_visibility(self.config_data.get("show_console", False))

        if self.config_data.get("launch_tray", False):
            self.launch_tray_var.set(True)
            self.launch_gui_var.set(False)
        else:
            self.launch_tray_var.set(False)
            self.launch_gui_var.set(True)

        l = LANGS[self.lang]
        act_idx = self.config_data.get("activity_idx", 0)
        if act_idx < len(l["activity_modes"]): self.activity_switch.set(l["activity_modes"][act_idx])

        src_idx = self.config_data.get("source_idx", 0)
        if src_idx < len(l["source_modes"]): self.source_switch.set(l["source_modes"][src_idx])
            
        beh_idx = self.config_data.get("behavior_idx", 0)
        if beh_idx < len(l["behavior_modes"]): self.behavior_switch.set(l["behavior_modes"][beh_idx])
            
        self.uploaded_image_provider = self.config_data.get("img_provider", "")
        if self.config_data.get("img_url"):
            self.uploaded_image_url = self.config_data.get("img_url")
            self.file_label.configure(text=self.config_data.get("img_name", "Loaded from config"), text_color="white")
            
        if self.config_data.get("small_img_url"):
            self.uploaded_small_image_url = self.config_data.get("small_img_url")
            self.small_file_label.configure(text=self.config_data.get("small_img_name", "Small loaded"), text_color="white")
            
        if not self.config_data.get("small_img_enabled", True):
            self.small_img_checkbox.deselect()

        self._refresh_history_menus()
        
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
            self.load_preset_into_ui(preset)
            self.status_bar.configure(text=LANGS[self.lang]["preset_loaded"], text_color="green")

    def load_preset_into_ui(self, preset):
        self.id_entry.delete(0, ctk.END)
        self.id_entry.insert(0, preset.get("client_id", self.config_data.get("client_id", "")))

        self.details_entry.delete(0, ctk.END)
        self.details_entry.insert(0, preset.get("details", ""))

        self.state_entry.delete(0, ctk.END)
        self.state_entry.insert(0, preset.get("state", ""))

        self.time_entry.delete(0, ctk.END)
        self.time_entry.insert(0, preset.get("time_val", self.config_data.get("time_val", "21")))
        if preset.get("time_enabled", self.config_data.get("time_enabled", True)):
            self.time_checkbox.select()
        else:
            self.time_checkbox.deselect()

        activity_idx = preset.get("activity_idx", self.config_data.get("activity_idx", 0))
        if activity_idx < len(LANGS[self.lang]["activity_modes"]):
            self.activity_switch.set(LANGS[self.lang]["activity_modes"][activity_idx])

        source_idx = preset.get("source_idx", self.config_data.get("source_idx", 0))
        if source_idx < len(LANGS[self.lang]["source_modes"]):
            self.source_switch.set(LANGS[self.lang]["source_modes"][source_idx])

        behavior_idx = preset.get("behavior_idx", self.config_data.get("behavior_idx", 0))
        if behavior_idx < len(LANGS[self.lang]["behavior_modes"]):
            self.behavior_switch.set(LANGS[self.lang]["behavior_modes"][behavior_idx])

        self.btn_text_entry.delete(0, ctk.END)
        self.btn_text_entry.insert(0, preset.get("btn_text", self.config_data.get("btn_text", "")))
        self.btn_url_entry.delete(0, ctk.END)
        self.btn_url_entry.insert(0, preset.get("btn_url", self.config_data.get("btn_url", "")))
        self.btn2_text_entry.delete(0, ctk.END)
        self.btn2_text_entry.insert(0, preset.get("btn2_text", self.config_data.get("btn2_text", "")))
        self.btn2_url_entry.delete(0, ctk.END)
        self.btn2_url_entry.insert(0, preset.get("btn2_url", self.config_data.get("btn2_url", "")))

        self.uploaded_image_url = preset.get("img_url", self.config_data.get("img_url", ""))
        self.uploaded_image_provider = preset.get("img_provider", self.config_data.get("img_provider", ""))
        self.file_label.configure(text=preset.get("img_name", self.config_data.get("img_name", "Выбрать")), text_color="white" if self.uploaded_image_url else "gray")

        self.uploaded_small_image_url = preset.get("small_img_url", self.config_data.get("small_img_url", ""))
        self.small_file_label.configure(text=preset.get("small_img_name", self.config_data.get("small_img_name", "Малая картинка не выбрана")), text_color="white" if self.uploaded_small_image_url else "gray")
        if preset.get("small_img_enabled", self.config_data.get("small_img_enabled", True)):
            self.small_img_checkbox.select()
        else:
            self.small_img_checkbox.deselect()

        self.update_counters()

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
            "client_id": self.id_entry.get(),
            "details": self.details_entry.get(),
            "state": self.state_entry.get(),
            "time_val": self.time_entry.get(),
            "time_enabled": True if self.time_checkbox.get() == 1 else False,
            "activity_idx": self.config_data.get("activity_idx", 0),
            "source_idx": self.config_data.get("source_idx", 0),
            "behavior_idx": self.config_data.get("behavior_idx", 0),
            "btn_text": self.btn_text_entry.get(),
            "btn_url": self.btn_url_entry.get(),
            "btn2_text": self.btn2_text_entry.get(),
            "btn2_url": self.btn2_url_entry.get(),
            "img_url": self.uploaded_image_url or self.config_data.get("img_url", ""),
            "img_name": self.file_label.cget("text"),
            "img_provider": self.uploaded_image_provider or self.config_data.get("img_provider", ""),
            "small_img_url": self.uploaded_small_image_url or self.config_data.get("small_img_url", ""),
            "small_img_name": self.small_file_label.cget("text"),
            "small_img_enabled": True if self.small_img_checkbox.get() == 1 else False
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
            if not self.winfo_exists():
                break

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
            except:
                delay = 15

            self.current_loop_index += 1
            time.sleep(delay)

    def apply_preset_directly(self, name):
        self.preset_dropdown.set(name)
        preset = self.config_data["presets"].get(name, {})
        if preset:
            self.load_preset_into_ui(preset)
            self.start_apply_thread()
            write_log(f"Preset applied: {name}")

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

    def handle_upload_result(self, result, target, l):
        if result.get("success"):
            url = result.get("url", "")
            provider_name = result.get("provider", "unknown")
            label_text = os.path.basename(result.get("file_path", "")) if isinstance(result, dict) and result.get("file_path") else ("Image" if target == "large" else "Small image")
            if target == "large":
                self.uploaded_image_url = url
                self.uploaded_image_provider = provider_name
                self.file_label.configure(text=label_text, text_color="white")
            else:
                self.uploaded_small_image_url = url
                self.uploaded_small_image_provider = provider_name
                self.small_file_label.configure(text=label_text, text_color="white")
            self._record_successful_image_history(url, label_text, provider_name, target)
            self.save_config()
            self.status_bar.configure(text=l["img_ready"], text_color="green")
        else:
            self.status_bar.configure(text=l["img_err"], text_color="#ED4245")

    def upload_image_worker(self, file_path, target):
        l = LANGS[self.lang]
        try:
            result = self.upload_manager.upload(file_path, config_data=self.config_data)
            if result and result.get("success"):
                result["file_path"] = file_path
        except Exception as exc:
            write_log(f"Upload manager raised an exception: {exc}", "ERROR")
            result = {"success": False, "provider": None, "error": str(exc), "file_path": file_path}
        self.after(0, lambda: self.handle_upload_result(result, target, l))

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

    def get_system_metrics(self):
        try:
            if not hasattr(self, "_cpu_initialized"):
                psutil.cpu_percent(interval=None)
                self._cpu_initialized = True

            cpu = int(psutil.cpu_percent(interval=None))
            cpu = max(0, min(100, cpu))

            mem = psutil.virtual_memory()
            ram = int(mem.percent)
            return cpu, ram
        except Exception:
            return 0, 0

    def detect_game(self):
        try:
            for proc in psutil.process_iter(["name"]):
                name = proc.info.get("name")
                if not name:
                    continue
                key = name.lower()
                if key in GAME_NAME_MAP:
                    detected = GAME_NAME_MAP[key]
                    if detected != getattr(self, "current_game", None):
                        self.current_game = detected
                        write_log(f"Game detected: {detected}")
                    return detected
            self.current_game = None
            return ""
        except Exception:
            return ""

    def make_progress_bar(self, percent, length=10):
        """Создает красивую полоску прогресса для Дискорда."""
        filled_length = int(length * percent // 100)
        # ■ - заполненный квадрат, □ - пустой
        bar = "■" * filled_length + "□" * (length - filled_length)
        return bar

    def format_text_templates(self, text):
        cpu, ram = self.get_system_metrics()
        game = self.detect_game()

        cpu_bar = self.make_progress_bar(cpu)
        ram_bar = self.make_progress_bar(ram)

        formatted = text.replace("{cpu}", str(cpu))
        formatted = formatted.replace("{ram}", str(ram))
        formatted = formatted.replace("{game}", game)

        formatted = formatted.replace("{cpu_bar}", cpu_bar)
        formatted = formatted.replace("{ram_bar}", ram_bar)

        if self.time_checkbox.get() == 1:
            times = self.get_current_time_strings()
            formatted = formatted.replace("{time24}", times["time24"])
            formatted = formatted.replace("{time24s}", times["time24s"])
            formatted = formatted.replace("{time12}", times["time12"])
            formatted = formatted.replace("{time12s}", times["time12s"])
            formatted = formatted.replace("{time}", times["time"])
        else:
            for t_tag in ["{time24}", "{time24s}", "{time12}", "{time12s}", "{time}"]:
                formatted = formatted.replace(t_tag, "")
        return formatted

    def _has_live_status_tags(self, text):
        if not text:
            return False
        live_tags = [
            "{cpu}", "{ram}", "{cpu_bar}", "{ram_bar}", "{game}",
            "{time24}", "{time24s}", "{time12}", "{time12s}", "{time}"
        ]
        return any(tag in text for tag in live_tags)

    def _should_skip_static_auto_update(self):
        try:
            if not os.path.exists(CONFIG_PATH):
                return False

            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved_config = json.load(f)
        except Exception:
            return False

        l = LANGS[self.lang]
        act_str = self.activity_switch.get()
        src_str = self.source_switch.get()
        beh_str = self.behavior_switch.get()
        act_idx = l["activity_modes"].index(act_str) if act_str in l["activity_modes"] else 0
        src_idx = l["source_modes"].index(src_str) if src_str in l["source_modes"] else 0
        beh_idx = l["behavior_modes"].index(beh_str) if beh_str in l["behavior_modes"] else 0

        current_snapshot = {
            "client_id": self.id_entry.get(),
            "details": self.details_entry.get(),
            "state": self.state_entry.get(),
            "time_val": self.time_entry.get(),
            "time_enabled": bool(self.time_checkbox.get()),
            "activity_idx": act_idx,
            "source_idx": src_idx,
            "behavior_idx": beh_idx,
            "btn_text": self.btn_text_entry.get(),
            "btn_url": self.btn_url_entry.get(),
            "btn2_text": self.btn2_text_entry.get(),
            "btn2_url": self.btn2_url_entry.get(),
            "small_img_enabled": bool(self.small_img_checkbox.get()),
            "launch_gui": bool(self.launch_gui_var.get()),
            "launch_tray": bool(self.launch_tray_var.get()),
            "auto_update": bool(self.auto_update_var.get()),
        }

        saved_subset = {
            key: saved_config.get(key)
            for key in current_snapshot.keys()
            if key in saved_config
        }

        if current_snapshot != saved_subset:
            return False

        if self._has_live_status_tags(self.details_entry.get()) or self._has_live_status_tags(self.state_entry.get()):
            return False

        return True

    def auto_update_worker(self):
        while True:
            if not self.winfo_exists():
                break

            try:
                if self.auto_update_var.get() == 1 and self.id_entry.get().strip():
                    detected_game = self.detect_game()
                    if detected_game:
                        time.sleep(1)
                        continue

                    self.auto_update_tick += 1
                    if self.auto_update_tick >= 15:
                        self.auto_update_tick = 0
                        if self._should_skip_static_auto_update():
                            raise RuntimeError("skip_static_rpc_update")
                        self.apply_changes(is_auto=True)
            except RuntimeError as e:
                if str(e) != "skip_static_rpc_update":
                    raise
            except Exception:
                pass

            precision = self.config_data.get("time_precision", "seconds")
            if self.time_checkbox.get() == 1 and precision == "minutes":
                time.sleep(60)
            elif self.time_checkbox.get() == 1 and precision == "seconds":
                time.sleep(1)
            else:
                time.sleep(random.uniform(1.0, 2.0))

    def apply_changes(self, is_auto=False):
        # Блокируем одновременный запуск из разных потоков
        start_time = time.perf_counter()
        if is_auto:
            self.auto_updates_count += 1
        else:
            self.manual_updates_count += 1

        with self.config_lock:
            l = LANGS[self.lang]
            current_id = self.id_entry.get().strip()
            if not current_id:
                self.status_bar.configure(text=l["id_err"], text_color="#ED4245")
                return

            raw_d_text = self.details_entry.get().strip()
            raw_s_text = self.state_entry.get().strip()

            d_text = self.format_text_templates(raw_d_text)
            s_text = self.format_text_templates(raw_s_text)

            buttons = []
            for raw_text in [self.details_entry.get(), self.state_entry.get()]:
                label, url, _ = self.parse_inline_button(raw_text)
                if label and url and url.startswith("http"):
                    buttons.append({"label": label[:32], "url": url})

            input_fields = [
                (self.btn_text_entry, self.btn_url_entry),
                (self.btn2_text_entry, self.btn2_url_entry)
            ]

            for text_entry, url_entry in input_fields:
                if len(buttons) >= 2:
                    break
                b_text = text_entry.get().strip()
                b_url = url_entry.get().strip()
                if b_text and b_url and b_url.startswith("http"):
                    buttons.append({"label": b_text[:32], "url": b_url})

            kwargs = {"pid": os.getpid()}
            if d_text:
                kwargs["details"] = d_text[:128]
            if s_text:
                kwargs["state"] = s_text[:128]
            if buttons:
                kwargs["buttons"] = buttons

            details_lower = d_text.lower() if d_text else ""
            large_key = "large_idle"
            for keyword, asset_key in {"coding": "large_coding", "gaming": "large_gaming"}.items():
                if keyword in details_lower:
                    large_key = asset_key
                    break

            if self.uploaded_image_url:
                kwargs["large_image"] = self.uploaded_image_url
            else:
                kwargs["large_image"] = large_key

            if self.small_img_checkbox.get() == 1:
                if self.uploaded_small_image_url:
                    kwargs["small_image"] = self.uploaded_small_image_url
                else:
                    kwargs["small_image"] = "small_working" if s_text else "small_offline"

            act_str = self.activity_switch.get()
            act_idx = l["activity_modes"].index(act_str) if act_str in l["activity_modes"] else 0
            type_mapping = {
                0: ActivityType.PLAYING,
                1: ActivityType.LISTENING,
                2: ActivityType.WATCHING,
                3: ActivityType.COMPETING
            }
            kwargs["activity_type"] = type_mapping.get(act_idx, ActivityType.PLAYING)

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
                    if final_start_time is not None:
                        kwargs["start"] = int(final_start_time)
                    if final_end_time is not None:
                        kwargs["end"] = int(final_end_time)
                except Exception:
                    kwargs["start"] = int(time.time())

            try:
                self.safe_presence.update(client_id=current_id, **kwargs)
                self.save_config()
                self.status_bar.configure(text=l["success"], text_color="green")
                write_log("Presence updated")
            except Exception as e:
                self.status_bar.configure(text=f"{l['api_err']}{str(e)}", text_color="#ED4245")
                write_log(f"Presence update failed: {e}")
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self.update_durations.append(duration_ms)
                write_log(f"Presence update finished in {duration_ms:.2f} ms", "INFO")

    def check_autostart_registry(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def toggle_autostart(self):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_WRITE)
        if self.autostart_var.get():
            app_path = os.path.realpath(sys.argv[0])
            if getattr(sys, "frozen", False):
                command = f'"{app_path}" --autostart'
            else:
                command = f'"{sys.executable}" "{app_path}" --autostart'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        else:
            try: winreg.DeleteValue(key, APP_NAME)
            except WindowsError: pass
        winreg.CloseKey(key)
        self.update_launch_mode_state()

    def tray_open_window(self, icon):
        icon.stop()  
        self.is_hidden = False
        self.after(0, self.deiconify)  

    def tray_exit_program(self, icon):
        icon.stop()
        self.loop_running = False
        self.auto_update_tick = 0

        avg_duration = 0.0
        if self.update_durations:
            avg_duration = sum(self.update_durations) / len(self.update_durations)

        total_updates = self.manual_updates_count + self.auto_updates_count
        write_log("=========================================", "INFO")
        write_log("   [VOID.rpc] СЕССИЯ УСПЕШНО ЗАВЕРШЕНА   ", "INFO")
        write_log("=========================================", "INFO")
        write_log(f" Ручных применений изменений: {self.manual_updates_count}", "INFO")
        write_log(f" Автообновлений (по 15 тикам): {self.auto_updates_count}", "INFO")
        write_log(f" Всего обновлений отправлено: {total_updates}", "INFO")
        write_log(f" Средняя скорость ответа сети/ПК: {avg_duration:.2f} мс", "INFO")
        write_log("=========================================", "INFO")

        try:
            self.safe_presence.close()
        except Exception:
            pass

        try:
            if self.winfo_exists():
                self.update()
        except Exception:
            pass

        try:
            self.destroy()
        except Exception:
            pass

    def minimize_to_tray(self):
        l = LANGS[self.lang]
        self.withdraw()  
        self.is_hidden = True
        
        if self.raw_logo: tray_img = self.raw_logo
        else:
            logo_png_path = LOGO_PATH
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
            try:
                icon.notify(message=l["notify_msg"], title=l["notify_title"])
            except Exception as exc:
                write_log(f"Tray notification failed: {exc}", "WARNING")

        threading.Thread(target=self.tray_icon.run, args=(on_tray_ready,), daemon=True).start()



if __name__ == "__main__":
    show_console = False
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
                config = json.load(config_file)
            show_console = bool(config.get("show_console", False))
        except Exception:
            show_console = False

    has_attached_console = (
        sys.stdin is not None and hasattr(sys.stdin, "isatty") and sys.stdin.isatty() and
        sys.stdout is not None and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    )

    if show_console:
        set_console_visibility(True)
        print_terminal_banner(launch_mode="1")
    elif has_attached_console:
        set_console_visibility(True)
        print_terminal_banner(launch_mode="2")
    else:
        set_console_visibility(False)
        print_terminal_banner(launch_mode="2")

    app = UltimateRPCMenu()
    app.mainloop()
