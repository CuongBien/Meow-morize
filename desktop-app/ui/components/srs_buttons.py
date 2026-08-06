import flet as ft
from ui.theme import *

class SRSButtons(ft.Column):
    def __init__(self, on_rate_click=None):
        super().__init__()
        self.on_rate_click = on_rate_click
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 10
        self.visible = False
        self.init_ui()

    def init_ui(self):
        self.btn_again = ft.Button(content=ft.Text("Again ❌ (1d)"), bgcolor=COLOR_ERROR_DARK, color=COLOR_TEXT_PRIMARY, on_click=lambda e: self.trigger_rate(1), width=180, height=40)
        self.btn_hard = ft.Button(content=ft.Text("Hard ⚠️ (2d)"), bgcolor=COLOR_WARNING_DARK, color=COLOR_TEXT_PRIMARY, on_click=lambda e: self.trigger_rate(3), width=180, height=40)
        self.btn_good = ft.Button(content=ft.Text("Good 👍 (4d)"), bgcolor=COLOR_INFO_DARK, color=COLOR_TEXT_PRIMARY, on_click=lambda e: self.trigger_rate(4), width=180, height=40)
        self.btn_easy = ft.Button(content=ft.Text("Easy 🎉 (7d)"), bgcolor=COLOR_SUCCESS_DARK, color=COLOR_TEXT_PRIMARY, on_click=lambda e: self.trigger_rate(5), width=180, height=40)
        
        self.controls = [
            ft.Row([self.btn_again, self.btn_hard], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Row([self.btn_good, self.btn_easy], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        ]

    def set_ratings(self, day_easy):
        self.btn_again.content.value = "Again ❌ (1d)"
        self.btn_hard.content.value = f"Hard ⚠️ ({max(1, int(day_easy*0.5))}d)"
        self.btn_good.content.value = f"Good 👍 ({max(2, int(day_easy*0.8))}d)"
        self.btn_easy.content.value = f"Easy 🎉 ({day_easy}d)"
        self.update()

    def trigger_rate(self, quality):
        if self.on_rate_click:
            self.on_rate_click(quality)

    def show_buttons(self, visible=True):
        self.visible = visible
        self.update()
