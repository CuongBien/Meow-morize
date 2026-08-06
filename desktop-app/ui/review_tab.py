import datetime
import re
import flet as ft
from ui.theme import *
from srs import update_srs_item

class ReviewTab(ft.Column):
    def __init__(self, page: ft.Page, srs_data, save_srs_data_fn):
        super().__init__()
        self.page_ref = page
        self.srs_data = srs_data
        self.save_srs_data_fn = save_srs_data_fn
        self.vocab_list = []
        self.review_queue = []
        self.current_index = 0
        
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.alignment = ft.MainAxisAlignment.CENTER
        
        self.init_ui()

    def init_ui(self):
        # Review Cards Controls
        self.card_word = ft.Text(value="Ready", size=36, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        self.card_context = ft.Text(value="Context", italic=True, size=15, color=COLOR_TEXT_MUTED, text_align=ft.TextAlign.CENTER)
        self.card_translation = ft.Text(value="Translation", size=20, weight=ft.FontWeight.W_500, color=COLOR_INFO, text_align=ft.TextAlign.CENTER, visible=False)
        
        self.btn_reveal = ft.Button("Reveal Answer 🔓", width=250, height=45, color=COLOR_TEXT_PRIMARY, bgcolor=COLOR_PRIMARY, on_click=self.on_reveal_click)
        
        # Group nút đánh giá chất lượng ghi nhớ
        self.btn_again = ft.Button("Again ❌ (1d)", bgcolor=COLOR_ERROR_DARK, color=COLOR_TEXT_PRIMARY, visible=False, on_click=self.make_rate_handler(1))
        self.btn_hard = ft.Button("Hard ⚠️ (2d)", bgcolor=COLOR_WARNING_DARK, color=COLOR_TEXT_PRIMARY, visible=False, on_click=self.make_rate_handler(3))
        self.btn_good = ft.Button("Good 👍 (4d)", bgcolor=COLOR_INFO_DARK, color=COLOR_TEXT_PRIMARY, visible=False, on_click=self.make_rate_handler(4))
        self.btn_easy = ft.Button("Easy 🎉 (7d)", bgcolor=COLOR_SUCCESS_DARK, color=COLOR_TEXT_PRIMARY, visible=False, on_click=self.make_rate_handler(5))
        
        self.progress_bar = ft.ProgressBar(value=0, width=400, color=COLOR_PRIMARY_LIGHT, bgcolor=COLOR_BG_PROGRESS)
        self.lbl_progress = ft.Text(value="0/0 Words", size=13, color=COLOR_TEXT_MUTED)
        
        self.review_card = ft.Container(
            content=ft.Column(
                controls=[
                    self.card_word,
                    ft.Divider(color=COLOR_BORDER),
                    self.card_context,
                    ft.Container(height=10),
                    self.card_translation,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=30,
            width=550,
            height=280,
            border_radius=16,
            bgcolor=COLOR_BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, COLOR_BORDER),
                right=ft.BorderSide(1, COLOR_BORDER),
                bottom=ft.BorderSide(1, COLOR_BORDER),
                left=ft.BorderSide(1, COLOR_BORDER)
            ),
            alignment=ft.Alignment(0, 0),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=COLOR_SHADOW,
                offset=ft.Offset(0, 5)
            )
        )
        
        self.controls = [
            ft.Text("Meow-morize Daily Review 🐾", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Master your vocabulary using Spaced Repetition", size=14, color=COLOR_TEXT_SUBTITLE),
            ft.Container(height=15),
            self.review_card,
            ft.Container(height=15),
            self.btn_reveal,
            ft.Row(
                controls=[self.btn_again, self.btn_hard, self.btn_good, self.btn_easy],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            ),
            ft.Container(height=15),
            self.progress_bar,
            self.lbl_progress
        ]

    # Logic lọc danh sách từ cần ôn hôm nay
    def build_review_queue(self, vocab_list):
        self.vocab_list = vocab_list
        self.review_queue = []
        self.current_index = 0
        today = datetime.date.today().isoformat()
        
        for item in self.vocab_list:
            word = item["word"]
            # Nếu chưa từng ôn (chưa có trong srs_data) hoặc đến hạn ôn (next_review <= today)
            if word not in self.srs_data or self.srs_data[word]["next_review"] <= today:
                self.review_queue.append(item)
                
        # Cập nhật thanh tiến trình
        self.update_progress_ui()
        self.show_current_card()
        
    def update_progress_ui(self):
        total = len(self.review_queue)
        if total == 0:
            self.progress_bar.value = 0
            self.lbl_progress.value = "All caught up! 🎉 No words to review today."
        else:
            self.progress_bar.value = self.current_index / total
            self.lbl_progress.value = f"Reviewing: {self.current_index + 1}/{total} words"

    def show_current_card(self):
        # Ẩn đáp án đi
        self.card_translation.visible = False
        self.btn_reveal.visible = True
        self.btn_again.visible = False
        self.btn_hard.visible = False
        self.btn_good.visible = False
        self.btn_easy.visible = False
        
        if not self.review_queue or self.current_index >= len(self.review_queue):
            self.card_word.value = "All Done! 🐱"
            self.card_context.value = "You have finished all vocab reviews for today."
            self.btn_reveal.visible = False
            self.progress_bar.value = 1.0
            self.lbl_progress.value = "Completed!"
        else:
            item = self.review_queue[self.current_index]
            self.card_word.value = item["word"]
            
            # Làm mờ từ gốc trong câu ngữ cảnh để tăng hiệu quả nhớ từ
            hidden_context = item["context"]
            if item["word"].lower() in hidden_context.lower():
                insensitive_word = re.compile(re.escape(item["word"]), re.IGNORECASE)
                hidden_context = insensitive_word.sub("_______", hidden_context)
                
            self.card_context.value = hidden_context
            self.card_translation.value = item["translation"]
            
        self.page_ref.update()

    # Event click lật thẻ
    def on_reveal_click(self, e):
        if not self.review_queue or self.current_index >= len(self.review_queue):
            return
        self.btn_reveal.visible = False
        self.card_translation.visible = True
        
        # Lấy khoảng cách ngày từ SRS để hiển thị trên nút bấm
        word = self.review_queue[self.current_index]["word"]
        item_srs = self.srs_data.get(word, {"ease_factor": 2.5, "repetitions": 0, "interval": 1})
        
        # Ước lượng khoảng cách ôn tiếp theo để hiển thị trên nhãn nút
        ef = item_srs["ease_factor"]
        rep = item_srs["repetitions"]
        
        if rep == 0:
            day_easy = 4
        elif rep == 1:
            day_easy = 6
        else:
            day_easy = int(round(item_srs["interval"] * ef))
            
        self.btn_again.text = "Again ❌ (1d)"
        self.btn_hard.text = f"Hard ⚠️ ({max(1, int(day_easy*0.5))}d)"
        self.btn_good.text = f"Good 👍 ({max(2, int(day_easy*0.8))}d)"
        self.btn_easy.text = f"Easy 🎉 ({day_easy}d)"
        
        # Hiện các nút đánh giá
        self.btn_again.visible = True
        self.btn_hard.visible = True
        self.btn_good.visible = True
        self.btn_easy.visible = True
        self.page_ref.update()

    # Event click đánh giá chất lượng ghi nhớ (SRS)
    def make_rate_handler(self, quality):
        def handle_rate(e):
            if not self.review_queue or self.current_index >= len(self.review_queue):
                return
            word = self.review_queue[self.current_index]["word"]
            
            # Cập nhật thuật toán SRS
            self.srs_data = update_srs_item(self.srs_data, word, quality)
            self.save_srs_data_fn(self.srs_data)
            
            # Chuyển sang từ tiếp theo
            self.current_index += 1
            self.update_progress_ui()
            self.show_current_card()
        return handle_rate
