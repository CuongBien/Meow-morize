import flet as ft
from ui.theme import *

class SpellingQuiz(ft.Column):
    def __init__(self, on_correct=None):
        super().__init__()
        self.on_correct = on_correct
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 15
        self.visible = False
        
        self.correct_word = ""
        self.hint_clicks = 0
        self.init_ui()

    def init_ui(self):
        # Ô nhập liệu từ vựng
        self.tf_answer = ft.TextField(
            label="Nhập từ vựng tiếng Anh...",
            width=380,
            autofocus=True,
            on_submit=self.on_submit_click
        )
        
        # Nhãn hiển thị gợi ý
        self.lbl_hint_text = ft.Text(
            value="",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=COLOR_WARNING,
            text_align=ft.TextAlign.CENTER
        )
        
        # Nút chức năng
        self.btn_hint = ft.Button(
            content=ft.Text("Gợi ý 💡"),
            bgcolor=COLOR_BG_CARD,
            color=COLOR_TEXT_MUTED,
            width=180,
            height=40,
            on_click=self.on_hint_click
        )
        
        self.btn_submit = ft.Button(
            content=ft.Text("Kiểm tra 📝"),
            bgcolor=COLOR_PRIMARY,
            color=COLOR_TEXT_PRIMARY,
            width=180,
            height=40,
            on_click=self.on_submit_click
        )
        
        buttons_row = ft.Row(
            controls=[self.btn_hint, self.btn_submit],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
        
        self.controls = [
            self.tf_answer,
            self.lbl_hint_text,
            buttons_row
        ]

    def set_quiz(self, correct_word):
        self.correct_word = correct_word.strip()
        self.hint_clicks = 0
        self.tf_answer.value = ""
        self.tf_answer.disabled = False
        self.tf_answer.border_color = None
        self.tf_answer.helper_text = ""
        self.lbl_hint_text.value = ""
        self.btn_submit.disabled = False
        self.btn_hint.disabled = False
        self.update()

    def on_hint_click(self, e):
        if not self.correct_word:
            return
            
        self.hint_clicks += 1
        n = len(self.correct_word)
        
        # Tăng dần số ký tự gợi ý mỗi lần click
        revealed_chars = min(self.hint_clicks, n)
        
        hint_parts = []
        for i in range(n):
            char = self.correct_word[i]
            if char.isspace() or char in ["-", "_"]:
                hint_parts.append(char)
            elif i < revealed_chars:
                hint_parts.append(char)
            else:
                hint_parts.append("_")
                
        self.lbl_hint_text.value = " ".join(hint_parts)
        self.update()

    def on_submit_click(self, e):
        user_input = self.tf_answer.value.strip().lower()
        target_lower = self.correct_word.lower()
        
        if user_input == target_lower:
            # Trả lời chính xác
            self.tf_answer.border_color = COLOR_SUCCESS
            self.tf_answer.disabled = True
            self.tf_answer.helper_text = "Chính xác! 🎉"
            self.btn_submit.disabled = True
            self.btn_hint.disabled = True
            self.update()
            
            if self.on_correct:
                self.on_correct()
        else:
            # Chưa chính xác
            self.tf_answer.border_color = COLOR_ERROR
            self.tf_answer.helper_text = "Chưa đúng, hãy thử lại hoặc nhấn lật thẻ bên trái!"
            self.update()
            
            # Vẫn hiển thị nút SRS để người dùng có thể tự bấm bỏ qua/đánh giá nếu quên
            if self.on_correct:
                self.on_correct()

    def show_quiz(self, visible=True):
        self.visible = visible
        self.update()
