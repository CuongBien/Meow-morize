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
        # Hàng chứa các ô chữ cái ghép được (Letter Slots)
        self.slots_row = ft.Row(
            wrap=True,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            width=380
        )
        
        # Khung chứa các chữ cái xáo trộn bên dưới để chọn
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
            ft.Text("Ghép các chữ cái bên dưới thành từ đúng:", size=13, color=COLOR_TEXT_MUTED),
            self.slots_row,
            ft.Container(height=5),
            self.letters_row,
            ft.Container(height=10),
            self.btn_reset
        ]

    def set_quiz(self, correct_word):
        self.correct_word = correct_word.strip()
        
        # Tạo danh sách các chữ cái kèm chỉ số gốc
        letters = list(self.correct_word)
        indices_letters = list(enumerate(letters))
        
        # Xáo trộn các chữ cái
        random.shuffle(indices_letters)
        self.scrambled_letters = indices_letters
        self.user_selections = []
        
        self.btn_reset.disabled = False
        
        # 1. Khởi tạo hàng ô trống (Slots) đại diện cho độ dài từ
        self.slots_row.controls.clear()
        for _ in range(len(self.correct_word)):
            slot = ft.Container(
                content=ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT),
                alignment=ft.Alignment(0, 0),
                width=38,
                height=38,
                border_radius=8,
                bgcolor=COLOR_BG_CARD,
                border=ft.Border.all(1, COLOR_BORDER)
            )
            self.slots_row.controls.append(slot)
            
        # 2. Tạo các nút chữ cái lựa chọn (Sử dụng Container để căn chỉnh chính giữa tuyệt đối)
        self.letters_row.controls.clear()
        for idx, (orig_idx, char) in enumerate(self.scrambled_letters):
            btn = ft.Container(
                content=ft.Text(char, size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                alignment=ft.Alignment(0, 0),
                width=45,
                height=45,
                border_radius=22.5, # Bo tròn thành hình tròn hoàn hảo
                bgcolor=COLOR_BG_CARD,
                data=orig_idx,
                on_click=self.make_letter_click_handler(orig_idx)
            )
            self.letters_row.controls.append(btn)
            
        self.update_ui_state()

    def update_ui_state(self):
        # 1. Cập nhật các ô Slots
        n = len(self.correct_word)
        for i in range(n):
            slot = self.slots_row.controls[i]
            if i < len(self.user_selections):
                # Ô đã được điền chữ
                orig_idx = self.user_selections[i]
                char = self.correct_word[orig_idx]
                slot.content.value = char
                slot.border = ft.Border.all(1.5, COLOR_PRIMARY_LIGHT)
            else:
                # Ô trống
                slot.content.value = ""
                slot.bgcolor = COLOR_BG_CARD
                slot.border = ft.Border.all(1, COLOR_BORDER)
        
        # 2. Cập nhật trạng thái các nút lựa chọn
        for btn in self.letters_row.controls:
            orig_idx = btn.data
            is_used = orig_idx in self.user_selections
            btn.disabled = is_used
            btn.bgcolor = COLOR_BORDER if is_used else COLOR_BG_CARD
            btn.content.color = COLOR_TEXT_MUTED if is_used else COLOR_TEXT_PRIMARY
            
        self.update()
        
        # 3. Tự động kiểm tra kết quả khi đã điền đủ các ô
        if len(self.user_selections) == len(self.correct_word):
            self.check_answer()

    def make_letter_click_handler(self, orig_idx):
        def handle_click(e):
            # Kiểm tra trạng thái disabled thủ công cho Container
            btn = e.control
            if btn.disabled:
                return
            if orig_idx not in self.user_selections:
                self.user_selections.append(orig_idx)
                self.update_ui_state()
        return handle_click

    def on_reset_click(self, e):
        self.user_selections = []
        self.update_ui_state()

    def check_answer(self):
        constructed = "".join([self.correct_word[idx] for idx in self.user_selections])
        if constructed.lower() == self.correct_word.lower():
            # Ghép đúng: Tô xanh lá các ô Slots
            for slot in self.slots_row.controls:
                slot.bgcolor = COLOR_SUCCESS_DARK
                slot.border = ft.Border.all(1.5, COLOR_SUCCESS)
            
            self.btn_reset.disabled = True
            for btn in self.letters_row.controls:
                btn.disabled = True
            self.update()
            
            if self.on_correct:
                self.on_correct()
        else:
            # Ghép sai: Tô đỏ các ô Slots
            for slot in self.slots_row.controls:
                slot.bgcolor = COLOR_ERROR_DARK
                slot.border = ft.Border.all(1.5, COLOR_ERROR)
            self.update()

    def show_quiz(self, visible=True):
        self.visible = visible
        self.update()
