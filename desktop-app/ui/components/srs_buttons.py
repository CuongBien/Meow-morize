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
        self.btn_again = ft.Button(content=ft.Text("Again ❌ (1d)"), bgcolor=COLOR_ERROR, color="#ffffff", on_click=lambda e: self.trigger_rate(1), width=180, height=40)
        self.btn_hard = ft.Button(content=ft.Text("Hard ⚠️ (2d)"), bgcolor=COLOR_WARNING, color="#ffffff", on_click=lambda e: self.trigger_rate(3), width=180, height=40)
        self.btn_good = ft.Button(content=ft.Text("Good 👍 (4d)"), bgcolor=COLOR_INFO, color="#ffffff", on_click=lambda e: self.trigger_rate(4), width=180, height=40)
        self.btn_easy = ft.Button(content=ft.Text("Easy 🎉 (7d)"), bgcolor=COLOR_SUCCESS, color="#ffffff", on_click=lambda e: self.trigger_rate(5), width=180, height=40)
        
        self.controls = [
            ft.Row([self.btn_again, self.btn_hard], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Row([self.btn_good, self.btn_easy], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        ]

    def set_ratings(self, previews):
        if isinstance(previews, dict):
            again_val = str(previews.get(1, "1m"))
            hard_val = str(previews.get(3, "10m"))
            good_val = str(previews.get(4, "1d"))
            easy_val = str(previews.get(5, "4d"))
        else:
            again_val = "1d"
            hard_val = f"{max(1, int(previews * 0.5))}d"
            good_val = f"{max(2, int(previews * 0.8))}d"
            easy_val = f"{previews}d"

        again_str = again_val if any(again_val.endswith(x) for x in ['m', 'd']) else f"{again_val}d"
        hard_str = hard_val if any(hard_val.endswith(x) for x in ['m', 'd']) else f"{hard_val}d"
        good_str = good_val if any(good_val.endswith(x) for x in ['m', 'd']) else f"{good_val}d"
        easy_str = easy_val if any(easy_val.endswith(x) for x in ['m', 'd']) else f"{easy_val}d"

        self.btn_again.content.value = f"Again ❌ ({again_str})"
        self.btn_hard.content.value = f"Hard ⚠️ ({hard_str})"
        self.btn_good.content.value = f"Good 👍 ({good_str})"
        self.btn_easy.content.value = f"Easy 🎉 ({easy_str})"
        self.update()

    def trigger_rate(self, quality):
        if self.on_rate_click:
            self.on_rate_click(quality)

    def show_buttons(self, visible=True):
        self.visible = visible
        self.update()
