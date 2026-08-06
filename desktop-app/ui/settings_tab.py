import flet as ft
from ui.theme import *

class SettingsTab(ft.Column):
    def __init__(self, page: ft.Page, config, save_config_fn, sync_fn):
        super().__init__()
        self.page = page
        self.config = config
        self.save_config_fn = save_config_fn
        self.sync_fn = sync_fn
        
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.alignment = ft.MainAxisAlignment.CENTER
        
        self.init_ui()

    def init_ui(self):
        self.txt_token = ft.TextField(label="Notion Token", password=True, can_reveal_password=True, value=self.config["notion_token"], width=500)
        self.txt_db_id = ft.TextField(label="Database ID", value=self.config["database_id"], width=500)
        self.lbl_status = ft.Text(value="", color=COLOR_SUCCESS)
        
        self.btn_sync = ft.Button("Sync with Notion 🔄", on_click=self.on_sync_click, bgcolor=COLOR_PRIMARY, color=COLOR_TEXT_PRIMARY)
        
        self.controls = [
            ft.Text("Notion Connection Settings ⚙️", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Link your local review app with your Notion vocabulary database", size=13, color=COLOR_TEXT_SUBTITLE),
            ft.Container(height=20),
            self.txt_token,
            self.txt_db_id,
            ft.Container(height=10),
            self.btn_sync,
            ft.Container(height=10),
            self.lbl_status
        ]

    def on_sync_click(self, e):
        self.lbl_status.value = "Fetching from Notion, please wait..."
        self.lbl_status.color = COLOR_WARNING
        self.page.update()
        
        token = self.txt_token.value.strip()
        db_id = self.txt_db_id.value.strip()
        
        if not token or not db_id:
            self.lbl_status.value = "Please fill in both Token and Database ID!"
            self.lbl_status.color = COLOR_ERROR
            self.page.update()
            return
            
        try:
            # Lưu cấu hình mới
            self.config["notion_token"] = token
            self.config["database_id"] = db_id
            self.save_config_fn(self.config)
            
            # Gọi callback đồng bộ từ Notion
            self.sync_fn(token, db_id, self.lbl_status)
        except Exception as ex:
            self.lbl_status.value = f"Error: {str(ex)}"
            self.lbl_status.color = COLOR_ERROR
            self.page.update()
