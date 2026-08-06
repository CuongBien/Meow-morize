import flet as ft
from ui.theme import *

class WordCard(ft.Container):
    def __init__(self, on_card_click=None):
        super().__init__()
        self.padding = 30
        self.width = 380
        self.height = 320
        self.border_radius = 16
        self.bgcolor = COLOR_BG_CARD
        self.border = ft.Border(
            top=ft.BorderSide(1, COLOR_BORDER),
            right=ft.BorderSide(1, COLOR_BORDER),
            bottom=ft.BorderSide(1, COLOR_BORDER),
            left=ft.BorderSide(1, COLOR_BORDER)
        )
        self.alignment = ft.Alignment(0, 0)
        self.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=COLOR_SHADOW,
            offset=ft.Offset(0, 5)
        )
        # Bật con trỏ chuột dạng bàn tay và gán sự kiện click để lật thẻ
        self.mouse_cursor = ft.MouseCursor.CLICK
        self.on_click = on_card_click
        
        self.init_ui()

    def init_ui(self):
        self.lbl_word = ft.Text(value="Ready", size=36, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        self.lbl_context = ft.Text(value="Context", italic=True, size=15, color=COLOR_TEXT_MUTED, text_align=ft.TextAlign.CENTER)
        self.lbl_translation = ft.Text(value="Translation", size=20, weight=ft.FontWeight.W_500, color=COLOR_INFO, text_align=ft.TextAlign.CENTER, visible=False)
        self.lbl_hint = ft.Text(value="(Nhấp vào thẻ để xem nghĩa 💡)", size=12, color=COLOR_TEXT_SUBTITLE, text_align=ft.TextAlign.CENTER)
        
        self.content = ft.Column(
            controls=[
                self.lbl_word,
                ft.Divider(color=COLOR_BORDER),
                self.lbl_context,
                ft.Container(height=10),
                self.lbl_translation,
                ft.Container(height=10),
                self.lbl_hint
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )

    def set_word(self, word):
        self.lbl_word.value = word

    def set_context(self, context):
        self.lbl_context.value = context

    def set_translation(self, translation):
        self.lbl_translation.value = translation

    def reveal_translation(self, visible=True):
        self.lbl_translation.visible = visible
        # Ẩn dòng chữ gợi ý click khi đã lộ đáp án
        self.lbl_hint.visible = not visible
        self.update()

    def reset_card(self, word="Ready", context="Context", translation="Translation"):
        self.lbl_word.value = word
        self.lbl_context.value = context
        self.lbl_translation.value = translation
        self.lbl_translation.visible = False
        self.lbl_hint.visible = True
        self.update()
