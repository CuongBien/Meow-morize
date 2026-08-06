import flet as ft
from ui.theme import *

class SRSButtons(ft.Row):
    def __init__(self, on_rate_click=None):
        super().__init__()
        self.on_rate_click = on_rate_click
        self.alignment = ft.MainAxisAlignment.CENTER
        self.spacing = 10
        self.visible = False
        self.init_ui()

    def init_ui(self):
        self.btn_again = ft.Button("Again ❌ (1d)", bgcolor=COLOR_ERROR_DARK, color=COLOR_TEXT_PRIMARY, on_click=lambda e: self.trigger_rate(1))
        self.btn_hard = ft.Button("Hard ⚠️ (2d)", bgcolor=COLOR_WARNING_DARK, color=COLOR_TEXT_PRIMARY, on_click=lambda e: self.trigger_rate(3))
        self.btn_good = ft.Button("Good 👍 (4d)", bgcolor=COLOR_INFO_DARK, color=COLOR_TEXT_PRIMARY, on_click=lambda e: self.trigger_rate(4))
        self.btn_easy = ft.Button("Easy 🎉 (7d)", bgcolor=COLOR_SUCCESS_DARK, color=COLOR_TEXT_PRIMARY, on_click=lambda e: self.trigger_rate(5))
        self.controls = [self.btn_again, self.btn_hard, self.btn_good, self.btn_easy]

    def set_ratings(self, day_easy):
        self.btn_again.content = "Again ❌ (1d)"
        self.btn_hard.content = f"Hard ⚠️ ({max(1, int(day_easy*0.5))}d)"
        self.btn_good.content = f"Good 👍 ({max(2, int(day_easy*0.8))}d)"
        self.btn_easy.content = f"Easy 🎉 ({day_easy}d)"
        self.update()

    def trigger_rate(self, quality):
        if self.on_rate_click:
            self.on_rate_click(quality)

    def show_buttons(self, visible=True):
        self.visible = visible
        self.update()
