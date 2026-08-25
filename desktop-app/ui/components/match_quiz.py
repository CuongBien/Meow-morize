import flet as ft
from ui.theme import *

class MatchQuiz(ft.Column):
    def __init__(self, on_verify=None):
        super().__init__()
        self.on_verify = on_verify
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 10
        self.visible = False
        
        self.items = []
        self.correct_answers = {}
        self.init_ui()

    def init_ui(self):
        self.rows = []
        self.item_views = []
        
        for i in range(4):
            lbl_word = ft.Text("Word", size=13, weight=ft.FontWeight.W_500, width=110, overflow=ft.TextOverflow.ELLIPSIS)
            
            # Nút chọn Đồng nghĩa
            btn_syn = ft.Button(
                content=ft.Text("Synonym", size=11, weight=ft.FontWeight.W_500),
                bgcolor=COLOR_BG_CARD,
                color=COLOR_TEXT_MUTED,
                width=95,
                height=36,
                on_click=self.make_select_handler(i, "synonym")
            )
            
            # Nút chọn Trái nghĩa
            btn_ant = ft.Button(
                content=ft.Text("Antonym", size=11, weight=ft.FontWeight.W_500),
                bgcolor=COLOR_BG_CARD,
                color=COLOR_TEXT_MUTED,
                width=95,
                height=36,
                on_click=self.make_select_handler(i, "antonym")
            )

            # Nút chọn Không thuộc loại nào (Neither / Unrelated)
            btn_none = ft.Button(
                content=ft.Text("Neither", size=11, weight=ft.FontWeight.W_500),
                bgcolor=COLOR_BG_CARD,
                color=COLOR_TEXT_MUTED,
                width=95,
                height=36,
                on_click=self.make_select_handler(i, "unrelated")
            )
            
            row = ft.Row(
                controls=[lbl_word, btn_syn, btn_ant, btn_none],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            )
            self.rows.append(row)
            self.item_views.append({
                "lbl_word": lbl_word,
                "btn_syn": btn_syn,
                "btn_ant": btn_ant,
                "btn_none": btn_none,
                "selection": None
            })
            
        self.btn_verify = ft.Button(
            content=ft.Text("Verify 🔍", size=14, weight=ft.FontWeight.W_500),
            bgcolor=COLOR_PRIMARY,
            color="#ffffff",
            width=200,
            height=40,
            on_click=self.on_verify_click
        )
        
        self.controls = self.rows + [ft.Container(height=8), self.btn_verify]

    def make_select_handler(self, index, choice_type):
        def handle_select(e):
            view = self.item_views[index]
            if view["selection"] == choice_type:
                view["selection"] = None
            else:
                view["selection"] = choice_type
            
            self.render_item_state(index)
        return handle_select

    def render_item_state(self, index):
        view = self.item_views[index]
        sel = view["selection"]

        for ctype, btn_key in [("synonym", "btn_syn"), ("antonym", "btn_ant"), ("unrelated", "btn_none")]:
            btn = view[btn_key]
            if sel == ctype:
                btn.bgcolor = COLOR_PRIMARY
                btn.color = "#ffffff"
            else:
                btn.bgcolor = COLOR_BG_CARD
                btn.color = COLOR_TEXT_MUTED
        self.update()

    def set_quiz(self, words_list, correct_answers):
        self.correct_answers = correct_answers
        
        for i in range(4):
            word = words_list[i]
            view = self.item_views[i]
            view["lbl_word"].value = word
            view["selection"] = None
            
            for btn_key in ["btn_syn", "btn_ant", "btn_none"]:
                btn = view[btn_key]
                btn.bgcolor = COLOR_BG_CARD
                btn.color = COLOR_TEXT_MUTED
                btn.disabled = False
            
        self.btn_verify.disabled = False
        self.update()

    def on_verify_click(self, e):
        self.btn_verify.disabled = True
        
        for i in range(4):
            view = self.item_views[i]
            word = view["lbl_word"].value
            correct_rel = self.correct_answers.get(word, "unrelated")
            user_sel = view["selection"]
            
            view["btn_syn"].disabled = True
            view["btn_ant"].disabled = True
            view["btn_none"].disabled = True
            
            btn_map = {
                "synonym": view["btn_syn"],
                "antonym": view["btn_ant"],
                "unrelated": view["btn_none"]
            }

            for b in btn_map.values():
                b.bgcolor = COLOR_BG_CARD
                b.color = COLOR_TEXT_MUTED

            if correct_rel in btn_map:
                btn_map[correct_rel].bgcolor = COLOR_SUCCESS_DARK
                btn_map[correct_rel].color = COLOR_TEXT_PRIMARY

            if user_sel and user_sel != correct_rel:
                if user_sel in btn_map:
                    btn_map[user_sel].bgcolor = COLOR_ERROR_DARK
                    btn_map[user_sel].color = COLOR_TEXT_PRIMARY

        self.update()
        
        if self.on_verify:
            self.on_verify()

    def show_quiz(self, visible=True):
        self.visible = visible
        self.update()
