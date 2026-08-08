import random
import flet as ft
from ui.theme import *

class ScrambleQuiz(ft.Column):
    def __init__(self, on_correct=None):
        super().__init__()
        self.on_correct = on_correct
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 8  # Giảm spacing dọc để tránh tràn màn hình
        self.visible = False
        
        self.correct_word = ""
        self.scrambled_letters = []
        self.user_selections = []
        
        # Các biến lưu kích cỡ động theo chiều dài của từ
        self.slot_size = 38
        self.slot_font = 18
        self.btn_size = 45
        self.btn_font = 16
        
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
            height=36,
            on_click=self.on_reset_click
        )
        
        self.controls = [
            ft.Text("Ghép các chữ cái bên dưới thành từ đúng:", size=13, color=COLOR_TEXT_MUTED),
            self.slots_row,
            self.letters_row,
            self.btn_reset
        ]

    def set_quiz(self, correct_word):
        self.correct_word = correct_word.strip()
        n = len(self.correct_word)
        
        # 1. Tính toán kích thước ô chữ (slots) và nút bấm (buttons) động theo độ dài từ để không bị xuống dòng tràn màn hình
        if n <= 7:
            self.slot_size = 38
            self.slot_font = 18
            slot_spacing = 8
            self.btn_size = 45
            self.btn_font = 16
            btn_spacing = 10
        elif n <= 11:
            self.slot_size = 28
            self.slot_font = 13
            slot_spacing = 5
            self.btn_size = 34
            self.btn_font = 12
            btn_spacing = 6
        else:
            # Cho các từ cực kỳ dài như 'recommendations'
            self.slot_size = 20
            self.slot_font = 10
            slot_spacing = 3
            self.btn_size = 26
            self.btn_font = 9
            btn_spacing = 4
            
        self.slots_row.spacing = slot_spacing
        self.letters_row.spacing = btn_spacing
        
        # Tạo danh sách các chữ cái kèm chỉ số gốc
        letters = list(self.correct_word)
        indices_letters = list(enumerate(letters))
        
        # Xáo trộn
        random.shuffle(indices_letters)
        self.scrambled_letters = indices_letters
        self.user_selections = []
        
        self.btn_reset.disabled = False
        
        # 2. Khởi tạo các ô trống Slots với kích thước động
        self.slots_row.controls.clear()
        for _ in range(n):
            slot = ft.Container(
                content=ft.Text("", size=self.slot_font, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT),
                alignment=ft.Alignment(0, 0),
                width=self.slot_size,
                height=self.slot_size,
                border_radius=6 if n > 7 else 8,
                bgcolor=COLOR_BG_CARD,
                border=ft.Border.all(1, COLOR_BORDER)
            )
            self.slots_row.controls.append(slot)
            
        # 3. Tạo các nút chữ cái lựa chọn với kích thước động
        self.letters_row.controls.clear()
        for idx, (orig_idx, char) in enumerate(self.scrambled_letters):
            btn = ft.Container(
                content=ft.Text(char, size=self.btn_font, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                alignment=ft.Alignment(0, 0),
                width=self.btn_size,
                height=self.btn_size,
                border_radius=self.btn_size / 2,
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
                orig_idx = self.user_selections[i]
                char = self.correct_word[orig_idx]
                slot.content.value = char
                slot.border = ft.Border.all(1.5, COLOR_PRIMARY_LIGHT)
            else:
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
            # Ghép đúng: Tô xanh lá nhẹ và đổi màu chữ thành màu xanh
            for slot in self.slots_row.controls:
                slot.bgcolor = COLOR_SUCCESS_DARK
                slot.border = ft.Border.all(1.5, COLOR_SUCCESS)
                slot.content.color = COLOR_SUCCESS
            
            self.btn_reset.disabled = True
            for btn in self.letters_row.controls:
                btn.disabled = True
            self.update()
            
            if self.on_correct:
                self.on_correct()
        else:
            # Ghép sai: Tô đỏ nhẹ và đổi màu chữ thành đỏ
            for slot in self.slots_row.controls:
                slot.bgcolor = COLOR_ERROR_DARK
                slot.border = ft.Border.all(1.5, COLOR_ERROR)
                slot.content.color = COLOR_ERROR
            self.update()

    def show_quiz(self, visible=True):
        self.visible = visible
        self.update()
