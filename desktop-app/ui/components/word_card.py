import flet as ft
from ui.theme import *

class WordCard(ft.Container):
    def __init__(self, on_card_click=None, on_speak_click=None):
        super().__init__()
        self.padding = 25
        self.width = 420
        self.height = 370
        self.border_radius = 20
        self.bgcolor = COLOR_BG_CARD
        self.border = ft.Border(
            top=ft.BorderSide(1.5, COLOR_BORDER),
            right=ft.BorderSide(1.5, COLOR_BORDER),
            bottom=ft.BorderSide(1.5, COLOR_BORDER),
            left=ft.BorderSide(1.5, COLOR_BORDER)
        )
        self.alignment = ft.Alignment(0, 0)
        self.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=18,
            color=COLOR_SHADOW,
            offset=ft.Offset(0, 6)
        )
        # Bật con trỏ chuột dạng bàn tay và gán sự kiện click để lật thẻ
        self.mouse_cursor = ft.MouseCursor.CLICK
        self.on_click = on_card_click
        self.on_speak_click = on_speak_click
        
        self.init_ui()

    def init_ui(self):
        self.lbl_word = ft.Text(
            value="Welcome! 🐾", 
            size=34, 
            weight=ft.FontWeight.BOLD, 
            text_align=ft.TextAlign.CENTER,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS
        )
        
        # Nút phát âm thanh từ vựng (Listening Mode)
        self.btn_speak = ft.IconButton(
            icon=ft.Icons.VOLUME_UP_ROUNDED,
            icon_size=48,
            icon_color=COLOR_PRIMARY,
            visible=False,
            on_click=self.on_speak_click
        )
        
        self.lbl_context = ft.Text(
            value="Hãy chọn tab Settings ⚙️ ở góc trên\nđể kết nối Notion và đồng bộ từ vựng nhé!", 
            italic=True, 
            size=14, 
            color=COLOR_TEXT_MUTED, 
            text_align=ft.TextAlign.CENTER
        )
        
        # Bọc context trong Column có thể tự động cuộn nếu câu dài
        self.context_container = ft.Column(
            controls=[self.lbl_context],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            height=130,
            scroll=ft.ScrollMode.AUTO
        )

        self.lbl_translation = ft.Text(
            value="", 
            size=22, 
            weight=ft.FontWeight.W_600, 
            color=COLOR_INFO, 
            text_align=ft.TextAlign.CENTER, 
            visible=False
        )
        
        self.lbl_hint = ft.Text(
            value="", 
            size=12, 
            color=COLOR_TEXT_SUBTITLE, 
            text_align=ft.TextAlign.CENTER
        )
        
        self.content = ft.Column(
            controls=[
                self.lbl_word,
                ft.Divider(color=COLOR_BORDER, height=15),
                self.btn_speak,
                self.context_container,
                ft.Container(height=5),
                self.lbl_translation,
                ft.Container(height=5),
                self.lbl_hint
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8
        )

    def set_word(self, word):
        self.lbl_word.value = word

    def set_context(self, context):
        self.lbl_context.value = context

    def set_translation(self, translation):
        self.lbl_translation.value = translation

    def reveal_translation(self, visible=True):
        self.lbl_translation.visible = visible
        self.lbl_hint.visible = not visible
        self.update()

    def reset_card(self, word="Ready", context="Context", translation="Translation"):
        self.lbl_word.value = word
        self.lbl_context.value = context
        self.lbl_translation.value = translation
        self.lbl_translation.visible = False
        self.lbl_hint.visible = True
        self.btn_speak.visible = False
        self.update()
