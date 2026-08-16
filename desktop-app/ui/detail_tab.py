import flet as ft
from ui.theme import *

class DetailTab(ft.Column):
    def __init__(self, page: ft.Page, on_back_to_review=None):
        super().__init__()
        self.scroll = ft.ScrollMode.AUTO
        self.page_ref = page
        self.on_back_to_review = on_back_to_review
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.expand = True
        
        self.init_ui()
        
    def init_ui(self):
        # Tiêu đề từ vựng
        self.lbl_title = ft.Text("Chi tiết từ vựng 📄", size=24, weight=ft.FontWeight.BOLD)
        
        # Nút Quay lại ôn tập
        self.btn_back = ft.Button(
            content=ft.Text("Quay lại ôn tập 🧠"),
            bgcolor=COLOR_PRIMARY,
            color="#ffffff",
            width=200,
            height=40,
            on_click=self.on_back_click
        )
        
        # Khung hiển thị Markdown chi tiết từ Notion
        self.markdown_view = ft.Markdown(
            value="Chọn một từ vựng trong quá trình ôn tập và bấm 'Xem chi tiết' để hiển thị thông tin trang Notion tại đây! 🐾",
            selectable=True
        )
        
        # Vùng chứa chi tiết cuộn được, giao diện rộng lớn dễ đọc
        self.details_container = ft.Container(
            content=ft.Column(
                controls=[self.markdown_view],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=25,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=12,
            bgcolor=COLOR_BG_CARD,
            expand=True
        )
        
        self.controls = [
            self.lbl_title,
            self.btn_back,
            ft.Container(height=10),
            self.details_container
        ]
        
    def set_content(self, word, text):
        self.lbl_title.value = f"Chi tiết từ vựng: {word} 📄"
        self.markdown_view.value = text
        self.update()
        
    def on_back_click(self, e):
        if self.on_back_to_review:
            self.on_back_to_review()
