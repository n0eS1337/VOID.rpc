import customtkinter as ctk
from pypresence import Presence
import time
import os
import threading
import requests
import pystray
import ctypes  
from PIL import Image, ImageDraw
from pystray import MenuItem as item
from customtkinter import filedialog

# Фикс для панели задач Windows, чтобы она подтягивала кастомную иконку процесса
try:
    myappid = 'void.rpc.system.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

ctk.set_appearance_mode("Dark")

# --- СЛОВАРЬ ДЛЯ ДВУХ ЯЗЫКОВ ---
LANGS = {
    "RU": {
        "title": "VOID.rpc | SYSTEM",
        "header": "ПАНЕЛЬ УПРАВЛЕНИЯ DISCORD RPC",
        "id_label": "ID Приложения (меняет название игры):",
        "id_ph": "Вставь Application ID",
        "det_ph": "Верхняя строка (Details)",
        "state_ph": "Нижняя строка (State)",
        "timer": "Включить таймер",
        "modes": ["Минуты назад", "Unix Секунды"],
        "btn_browse": "Обзор...",
        "btn_update": "ПРИМЕНИТЬ ИЗМЕНЕНИЯ",
        "no_file": "Файл не выбран",
        "uploading": "Загрузка картинки на хостинг...",
        "img_ready": "Картинка успешно подготовлена!",
        "img_err": "Ошибка загрузки фото",
        "net_err": "Ошибка сети: ",
        "id_err": "Ошибка: Введите ID приложения!",
        "sync": "Синхронизация с Discord...",
        "discord_err": "Ошибка подключения к Discord: ",
        "api_err": "Ошибка Discord API: ",
        "success": "Всё успешно обновлено в Discord!",
        "status_wait": "Статус: Ожидание действий",
        "tray_open": "Развернуть",
        "tray_exit": "Выход",
        "notify_title": "VOID.rpc | SYSTEM",
        "notify_msg": "Приложение свернуто в трей и продолжает работать в фоне."
    },
    "EN": {
        "title": "VOID.rpc | SYSTEM",
        "header": "DISCORD RPC CONTROL PANEL",
        "id_label": "Application ID (changes game title):",
        "id_ph": "Insert Application ID",
        "det_ph": "Top line (Details)",
        "state_ph": "Bottom line (State)",
        "timer": "Enable timer",
        "modes": ["Minutes ago", "Unix Seconds"],
        "btn_browse": "Browse...",
        "btn_update": "APPLY CHANGES",
        "no_file": "No file selected",
        "uploading": "Uploading image to hosting...",
        "img_ready": "Image uploaded successfully!",
        "img_err": "Failed to upload image",
        "net_err": "Network error: ",
        "id_err": "Error: Enter Application ID!",
        "sync": "Synchronizing with Discord...",
        "discord_err": "Discord connection error: ",
        "api_err": "Discord API error: ",
        "success": "Successfully updated in Discord!",
        "status_wait": "Status: Waiting for action",
        "tray_open": "Open",
        "tray_exit": "Exit",
        "notify_title": "VOID.rpc | SYSTEM",
        "notify_msg": "The application is minimized to tray and continues running in the background."
    }
}

class UltimateRPCMenu(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.lang = "RU"
        self.title("VOID.rpc")
        self.geometry("550x660") 
        self.resizable(False, False)
        self.configure(fg_color="#111214")  

        self.rpc = None
        self.uploaded_image_url = None
        self.tray_icon = None

        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        # --- КОРРЕКТНАЯ ПРИВЯЗКА ИКОНКИ ДЛЯ ОКНА И ТАСКБАРА ---
        self.raw_logo = None
        
        # 1. Сначала пытаемся сохранить logo.png как logo.ico, если его еще нет
        if os.path.exists("logo.png") and not os.path.exists("logo.ico"):
            try:
                img = Image.open("logo.png")
                img.save("logo.ico", format="ICO", sizes=[(64, 64)])
            except Exception:
                pass

        # 2. Устанавливаем .ico файл для панели задач Windows намертво
        if os.path.exists("logo.ico"):
            try:
                self.iconbitmap("logo.ico")
            except Exception:
                pass

        # 3. Подгружаем картинку для интерфейса и трея
        try:
            self.raw_logo = Image.open("logo.png")
            self.logo_image = ctk.CTkImage(light_image=self.raw_logo, dark_image=self.raw_logo, size=(45, 45))
            self.logo_label = ctk.CTkLabel(self, image=self.logo_image, text="")
            self.logo_label.place(x=20, y=10) 
        except Exception:
            pass

        # Кнопка быстрой смены языка в правом верхнем углу
        self.lang_btn = ctk.CTkButton(self, text="RU / EN", width=60, height=25, fg_color="#2B2D31", hover_color="#3A3D42", command=self.toggle_lang)
        self.lang_btn.place(x=470, y=10)

        # --- Интерфейс ---
        self.label = ctk.CTkLabel(self, text="VOID.rpc | SYSTEM", font=ctk.CTkFont(size=18, weight="bold"), text_color="#ED4245")
        self.label.pack(pady=15)

        # 1. Поле для ID Приложения
        self.id_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.id_label.pack(pady=(5, 2))
        self.id_entry = ctk.CTkEntry(self, placeholder_text="", width=420, fg_color="#1E1F22", border_width=0)
        self.id_entry.pack(pady=5)
        self.id_entry.insert(0, "1517958796587176117") 

        # 2. Поле "Details"
        self.details_entry = ctk.CTkEntry(self, placeholder_text="", width=420, fg_color="#1E1F22", border_width=0)
        self.details_entry.pack(pady=10)
        self.details_entry.insert(0, "Тестирую кастомное меню")

        # 3. Поле "State"
        self.state_entry = ctk.CTkEntry(self, placeholder_text="", width=420, fg_color="#1E1F22", border_width=0)
        self.state_entry.pack(pady=10)
        self.state_entry.insert(0, "⸺⸺⸺⸺⸺ˢᵈᵏ⸺⸺⸺⸺⸺⸺⸺⸺")

        # --- НАСТРОЙКА ВРЕМЕНИ ---
        self.time_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.time_frame.pack(pady=10)

        self.time_checkbox = ctk.CTkCheckBox(self.time_frame, text="", width=140, fg_color="#ED4245", hover_color="#C03033")
        self.time_checkbox.pack(side="left", padx=5)
        self.time_checkbox.select()

        self.mode_switch = ctk.CTkOptionMenu(self.time_frame, values=["", ""], width=130, fg_color="#1E1F22", button_color="#2B2D31", button_hover_color="#3A3D42")
        self.mode_switch.pack(side="left", padx=5)

        self.time_entry = ctk.CTkEntry(self.time_frame, placeholder_text="", width=140, fg_color="#1E1F22", border_width=0)
        self.time_entry.pack(side="left", padx=5)
        self.time_entry.insert(0, "21") 

        # 4. Выбор картинки с ПК
        self.file_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.file_frame.pack(pady=10)
        
        self.file_label = ctk.CTkLabel(self.file_frame, text="", width=280, anchor="w", text_color="gray")
        self.file_label.pack(side="left", padx=5)
        
        self.btn_browse = ctk.CTkButton(self.file_frame, text="", command=self.browse_file, width=120, fg_color="#2B2D31", hover_color="#3A3D42")
        self.btn_browse.pack(side="right", padx=5)

        # 5. Кнопка «Применить»
        self.btn_update = ctk.CTkButton(
            self, 
            text="", 
            command=self.start_apply_thread, 
            width=220, 
            height=45,
            fg_color="#ED4245", 
            hover_color="#C03033"
        )
        self.btn_update.pack(pady=20)

        # Статус-бар
        self.status_bar = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_bar.pack(side="bottom", pady=10)

        self.update_ui_text()

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
        
        curr_mode = self.mode_switch.get()
        self.mode_switch.configure(values=l["modes"])
        if curr_mode == "" or curr_mode not in l["modes"]:
            self.mode_switch.set(l["modes"][0])
            
        self.btn_browse.configure(text=l["btn_browse"])
        self.btn_update.configure(text=l["btn_update"])
        if not self.uploaded_image_url:
            self.file_label.configure(text=l["no_file"])
        self.status_bar.configure(text=l["status_wait"])

    def browse_file(self):
        l = LANGS[self.lang]
        file_path = filedialog.askopenfilename(
            title="VOID.rpc | Image Select",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.webp")]
        )
        if file_path:
            self.file_label.configure(text=os.path.basename(file_path), text_color="white")
            self.status_bar.configure(text=l["uploading"], text_color="yellow")
            threading.Thread(target=self.upload_image_worker, args=(file_path,), daemon=True).start()

    def upload_image_worker(self, file_path):
        l = LANGS[self.lang]
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    "https://api.imgbb.com/1/upload",
                    params={"key": "6ac4e142b35147753eb20802e644a0a6"}, 
                    files={"image": f}
                )
            res_json = response.json()
            if res_json.get("success"):
                self.uploaded_image_url = res_json["data"]["url"]
                self.status_bar.configure(text=l["img_ready"], text_color="green")
            else:
                self.status_bar.configure(text=l["img_err"], text_color="#ED4245")
        except Exception as e:
            self.status_bar.configure(text=f"{l['net_err']}{str(e)}", text_color="#ED4245")

    def start_apply_thread(self):
        threading.Thread(target=self.apply_changes, daemon=True).start()

    def apply_changes(self):
        l = LANGS[self.lang]
        current_id = self.id_entry.get().strip()
        if not current_id:
            self.status_bar.configure(text=l["id_err"], text_color="#ED4245")
            return

        self.status_bar.configure(text=l["sync"], text_color="yellow")

        try:
            if self.rpc:
                try: self.rpc.close()
                except: pass
            self.rpc = Presence(current_id)
            self.rpc.connect()
        except Exception as e:
            self.status_bar.configure(text=f"{l['discord_err']}{str(e)}", text_color="#ED4245")
            return

        d_text = self.details_entry.get().strip() or None
        s_text = self.state_entry.get().strip() or None

        final_start_time = None
        if self.time_checkbox.get() == 1:
            try:
                val = self.time_entry.get().strip()
                mode = self.mode_switch.get()
                
                if val and val.isdigit():
                    if mode in ["Минуты назад", "Minutes ago"]:
                        final_start_time = int(time.time() - (int(val) * 60))
                    else:
                        final_start_time = int(val)
                else:
                    final_start_time = int(time.time())
            except Exception:
                final_start_time = int(time.time())

        try:
            self.rpc.update(
                details=d_text,
                state=s_text,
                large_image=self.uploaded_image_url, 
                start=final_start_time
            )
            self.status_bar.configure(text=l["success"], text_color="green")
        except Exception as e:
            self.status_bar.configure(text=f"{l['api_err']}{str(e)}", text_color="#ED4245")

    def tray_open_window(self, icon):
        icon.stop()  
        self.after(0, self.deiconify)  

    def tray_exit_program(self, icon):
        icon.stop()
        if self.rpc:
            try: self.rpc.close()
            except: pass
        self.destroy()  

    def minimize_to_tray(self):
        l = LANGS[self.lang]
        self.withdraw()  
        
        if self.raw_logo:
            tray_img = self.raw_logo
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
            icon.notify(
                message=l["notify_msg"],
                title=l["notify_title"]
            )

        threading.Thread(target=self.tray_icon.run, args=(on_tray_ready,), daemon=True).start()

if __name__ == "__main__":
    app = UltimateRPCMenu()
    app.mainloop()
