import flet as ft
from ui.theme import *

class ModeSelector(ft.Row):
    def __init__(self, initial_mode="flashcard", on_mode_change=None):
        super().__init__()
        self.current_mode = initial_mode
        self.on_mode_change = on_mode_change
        self.alignment = ft.MainAxisAlignment.CENTER
        self.spacing = 10
        self.init_ui()

    def init_ui(self):
        self.btn_flashcard = ft.Button(
            "📇 Flashcard",
            bgcolor=COLOR_PRIMARY if self.current_mode == "flashcard" else COLOR_BG_CARD,
            color=COLOR_TEXT_PRIMARY if self.current_mode == "flashcard" else COLOR_TEXT_MUTED,
            on_click=self.set_mode_flashcard
        )
        self.btn_quiz = ft.Button(
            "🧩 Multiple Choice",
            bgcolor=COLOR_PRIMARY if self.current_mode == "multiple_choice" else COLOR_BG_CARD,
            color=COLOR_TEXT_PRIMARY if self.current_mode == "multiple_choice" else COLOR_TEXT_MUTED,
            on_click=self.set_mode_quiz
        )
        self.controls = [self.btn_flashcard, self.btn_quiz]

    def set_mode_flashcard(self, e):
        self.current_mode = "flashcard"
        self.update_buttons()
        if self.on_mode_change:
            self.on_mode_change("flashcard")

    def set_mode_quiz(self, e):
        self.current_mode = "multiple_choice"
        self.update_buttons()
        if self.on_mode_change:
            self.on_mode_change("multiple_choice")

    def update_buttons(self):
        self.btn_flashcard.bgcolor = COLOR_PRIMARY if self.current_mode == "flashcard" else COLOR_BG_CARD
        self.btn_flashcard.color = COLOR_TEXT_PRIMARY if self.current_mode == "flashcard" else COLOR_TEXT_MUTED
        
        self.btn_quiz.bgcolor = COLOR_PRIMARY if self.current_mode == "multiple_choice" else COLOR_BG_CARD
        self.btn_quiz.color = COLOR_TEXT_PRIMARY if self.current_mode == "multiple_choice" else COLOR_TEXT_MUTED
        self.update()
