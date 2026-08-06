import flet as ft
from ui.theme import *

class ChoiceButtons(ft.Column):
    def __init__(self, on_choice_click=None):
        super().__init__()
        self.on_choice_click = on_choice_click
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 10
        self.visible = False
        self.choices = []
        self.correct_answer = ""
        self.init_ui()

    def init_ui(self):
        self.btns = []
        for i in range(4):
            btn = ft.Button(
                content=f"Choice {i+1}",
                width=450,
                height=45,
                bgcolor=COLOR_BG_CARD,
                color=COLOR_TEXT_PRIMARY,
                on_click=self.make_click_handler(i)
            )
            self.btns.append(btn)
        self.controls = self.btns

    def make_click_handler(self, index):
        def handle_click(e):
            selected_ans = self.choices[index]
            is_correct = (selected_ans == self.correct_answer)
            
            # Disable all buttons immediately
            for btn in self.btns:
                btn.disabled = True
                
            # Highlight selections
            if is_correct:
                self.btns[index].bgcolor = COLOR_SUCCESS_DARK
                self.btns[index].color = COLOR_TEXT_PRIMARY
            else:
                self.btns[index].bgcolor = COLOR_ERROR_DARK
                self.btns[index].color = COLOR_TEXT_PRIMARY
                
                # Show the correct answer in green
                for btn in self.btns:
                    if btn.content == self.correct_answer:
                        btn.bgcolor = COLOR_SUCCESS_DARK
                        btn.color = COLOR_TEXT_PRIMARY
            
            self.update()
            
            if self.on_choice_click:
                self.on_choice_click(selected_ans, is_correct)
        return handle_click

    def set_choices(self, choices, correct_answer):
        self.choices = choices
        self.correct_answer = correct_answer
        
        for i in range(4):
            self.btns[i].content = choices[i]
            self.btns[i].bgcolor = COLOR_BG_CARD
            self.btns[i].color = COLOR_TEXT_PRIMARY
            self.btns[i].disabled = False
        self.update()

    def show_choices(self, visible=True):
        self.visible = visible
        self.update()
