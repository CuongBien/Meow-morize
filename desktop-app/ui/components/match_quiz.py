import flet as ft
from ui.theme import *

class MatchQuiz(ft.Column):
    def __init__(self, on_verify=None):
        super().__init__()
        self.on_verify = on_verify
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 12
        self.visible = False
        
        self.items = []
        self.correct_answers = {}
        self.init_ui()

    def init_ui(self):
        self.rows = []
        self.item_views = []
        
        for i in range(4):
            lbl_word = ft.Text("Word", size=15, weight=ft.FontWeight.W_500, width=130)
            
            # Nút chọn Đồng nghĩa (Không dùng emoji trong text để tránh xuống dòng)
            btn_syn = ft.Button(
                content=ft.Text("Synonym", size=12),
                bgcolor=COLOR_BG_CARD,
                color=COLOR_TEXT_MUTED,
                width=100,
                height=35,
                on_click=self.make_select_handler(i, "synonym")
            )
            
            # Nút chọn Trái nghĩa (Không dùng emoji trong text để tránh xuống dòng)
            btn_ant = ft.Button(
                content=ft.Text("Antonym", size=12),
                bgcolor=COLOR_BG_CARD,
                color=COLOR_TEXT_MUTED,
                width=100,
                height=35,
                on_click=self.make_select_handler(i, "antonym")
            )
            
            row = ft.Row(
                controls=[lbl_word, btn_syn, btn_ant],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12
            )
            self.rows.append(row)
            self.item_views.append({
                "lbl_word": lbl_word,
                "btn_syn": btn_syn,
                "btn_ant": btn_ant,
                "selection": None
            })
            
        self.btn_verify = ft.Button(
            content=ft.Text("Verify 🔍"),
            bgcolor=COLOR_PRIMARY,
            color=COLOR_TEXT_PRIMARY,
            width=180,
            height=40,
            on_click=self.on_verify_click
        )
        
        self.controls = self.rows + [ft.Container(height=5), self.btn_verify]

    def make_select_handler(self, index, choice_type):
        def handle_select(e):
            view = self.item_views[index]
            if view["selection"] == choice_type:
                # Bỏ chọn nếu nhấp lại cùng một nút
                view["selection"] = None
                view["btn_syn"].bgcolor = COLOR_BG_CARD
                view["btn_syn"].color = COLOR_TEXT_MUTED
                view["btn_ant"].bgcolor = COLOR_BG_CARD
                view["btn_ant"].color = COLOR_TEXT_MUTED
            else:
                view["selection"] = choice_type
                if choice_type == "synonym":
                    view["btn_syn"].bgcolor = COLOR_PRIMARY
                    view["btn_syn"].color = COLOR_TEXT_PRIMARY
                    view["btn_ant"].bgcolor = COLOR_BG_CARD
                    view["btn_ant"].color = COLOR_TEXT_MUTED
                else:
                    view["btn_ant"].bgcolor = COLOR_PRIMARY
                    view["btn_ant"].color = COLOR_TEXT_PRIMARY
                    view["btn_syn"].bgcolor = COLOR_BG_CARD
                    view["btn_syn"].color = COLOR_TEXT_MUTED
            self.update()
        return handle_select

    def set_quiz(self, words_list, correct_answers):
        self.correct_answers = correct_answers
        
        for i in range(4):
            word = words_list[i]
            view = self.item_views[i]
            view["lbl_word"].value = word
            view["selection"] = None
            
            # Reset trạng thái màu sắc
            view["btn_syn"].bgcolor = COLOR_BG_CARD
            view["btn_syn"].color = COLOR_TEXT_MUTED
            view["btn_syn"].disabled = False
            
            view["btn_ant"].bgcolor = COLOR_BG_CARD
            view["btn_ant"].color = COLOR_TEXT_MUTED
            view["btn_ant"].disabled = False
            
        self.btn_verify.disabled = False
        self.update()

    def on_verify_click(self, e):
        self.btn_verify.disabled = True
        
        # Kiểm tra và tô màu đúng/sai
        for i in range(4):
            view = self.item_views[i]
            word = view["lbl_word"].value
            correct_rel = self.correct_answers.get(word, "unrelated")
            user_sel = view["selection"]
            
            # Khóa nút
            view["btn_syn"].disabled = True
            view["btn_ant"].disabled = True
            
            # Nếu người dùng chọn đúng
            if user_sel == correct_rel:
                if correct_rel == "synonym":
                    view["btn_syn"].bgcolor = COLOR_SUCCESS_DARK
                    view["btn_syn"].color = COLOR_TEXT_PRIMARY
                elif correct_rel == "antonym":
                    view["btn_ant"].bgcolor = COLOR_SUCCESS_DARK
                    view["btn_ant"].color = COLOR_TEXT_PRIMARY
            else:
                # Nếu người dùng chọn sai, tô đỏ lựa chọn sai của họ
                if user_sel == "synonym":
                    view["btn_syn"].bgcolor = COLOR_ERROR_DARK
                    view["btn_syn"].color = COLOR_TEXT_PRIMARY
                elif user_sel == "antonym":
                    view["btn_ant"].bgcolor = COLOR_ERROR_DARK
                    view["btn_ant"].color = COLOR_TEXT_PRIMARY
                    
                # Đồng thời tô xanh lá cây đáp án ĐÚNG (nếu có) để người dùng học
                if correct_rel == "synonym":
                    view["btn_syn"].bgcolor = COLOR_SUCCESS_DARK
                    view["btn_syn"].color = COLOR_TEXT_PRIMARY
                elif correct_rel == "antonym":
                    view["btn_ant"].bgcolor = COLOR_SUCCESS_DARK
                    view["btn_ant"].color = COLOR_TEXT_PRIMARY
                    
        self.update()
        
        if self.on_verify:
            self.on_verify()

    def show_quiz(self, visible=True):
        self.visible = visible
        self.update()
