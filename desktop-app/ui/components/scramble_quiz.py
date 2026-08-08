import random
import flet as ft
from ui.theme import *

class ScrambleQuiz(ft.Column):
    def __init__(self, on_correct=None):
        super().__init__()
        self.on_correct = on_correct
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 15
        self.visible = False
        
        self.correct_word = ""
        self.scrambled_letters = []
        self.user_selections = []
        self.init_ui()

    def init_ui(self):
        # Ô hiển thị từ đang ghép
        self.lbl_constructed = ft.Text(
            value="",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=COLOR_PRIMARY_LIGHT,
            text_align=ft.TextAlign.CENTER
        )
        
        # Nhãn hiển thị hướng dẫn / gạch dưới đại diện số ký tự
        self.lbl_placeholders = ft.Text(
            value="",
            size=16,
            color=COLOR_TEXT_MUTED,
            text_align=ft.TextAlign.CENTER
        )
        
        # Khung chứa các chữ cái xáo trộn
        self.letters_row = ft.Row(
            wrap=True,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            width=380
        )
        
        # Nút Reset
        self.btn_reset = ft.Button(
            content=ft.Text("Reset 🔄"),
            bgcolor=COLOR_BG_CARD,
            color=COLOR_TEXT_MUTED,
            width=150,
            height=38,
            on_click=self.on_reset_click
        )
        
        self.controls = [
            self.lbl_constructed,
            self.lbl_placeholders,
            self.letters_row,
            ft.Container(height=5),
            self.btn_reset
        ]

    def set_quiz(self, correct_word):
        self.correct_word = correct_word.strip()
        
        # Tạo danh sách các chữ cái kèm chỉ số gốc để xử lý ký tự lặp
        letters = list(self.correct_word)
        indices_letters = list(enumerate(letters))
        
        # Xáo trộn
        random.shuffle(indices_letters)
        self.scrambled_letters = indices_letters
        self.user_selections = []
        
        self.btn_reset.disabled = False
        self.lbl_constructed.color = COLOR_PRIMARY_LIGHT
        self.update_ui_state()

    def update_ui_state(self):
        # 1. Cập nhật từ ghép được từ các chỉ số đã chọn
        selected_chars = [self.correct_word[idx] for idx in self.user_selections]
        self.lbl_constructed.value = " ".join(selected_chars)
        
        # 2. Cập nhật gạch dưới placeholders
        n = len(self.correct_word)
        placeholder_parts = []
        for i in range(n):
            if i < len(self.user_selections):
                placeholder_parts.append(" ")
            else:
                placeholder_parts.append("_")
        self.lbl_placeholders.value = " ".join(placeholder_parts)
        
        # 3. Tạo các nút chữ cái
        self.letters_row.controls.clear()
        for idx, (char, orig_idx) in enumerate(self.scrambled_letters):
            is_used = orig_idx in self.user_selections
            btn = ft.Button(
                content=ft.Text(char, size=16, weight=ft.FontWeight.BOLD),
                width=45,
                height=45,
                bgcolor=COLOR_BG_CARD if not is_used else COLOR_BORDER,
                color=COLOR_TEXT_PRIMARY if not is_used else COLOR_TEXT_MUTED,
                disabled=is_used,
                on_click=self.make_letter_click_handler(orig_idx)
            )
            self.letters_row.controls.append(btn)
            
        self.update()
        
        # 4. Tự động kiểm tra khi độ dài ghép bằng từ gốc
        if len(self.user_selections) == len(self.correct_word):
            self.check_answer()

    def make_letter_click_handler(self, orig_idx):
        def handle_click(e):
            if orig_idx not in self.user_selections:
                self.user_selections.append(orig_idx)
                self.update_ui_state()
        return handle_click

    def on_reset_click(self, e):
        self.user_selections = []
        self.lbl_constructed.color = COLOR_PRIMARY_LIGHT
        self.update_ui_state()

    def check_answer(self):
        constructed = "".join([self.correct_word[idx] for idx in self.user_selections])
        if constructed.lower() == self.correct_word.lower():
            # Trả lời chính xác
            self.lbl_constructed.color = COLOR_SUCCESS
            self.btn_reset.disabled = True
            for btn in self.letters_row.controls:
                btn.disabled = True
            self.update()
            
            if self.on_correct:
                self.on_correct()
        else:
            # Chưa chính xác
            self.lbl_constructed.color = COLOR_ERROR
            self.lbl_placeholders.value = "Chưa chính xác! Nhấn Reset để thử lại."
            self.update()

    def show_quiz(self, visible=True):
        self.visible = visible
        self.update()
