import datetime
import re
import random
import flet as ft
from ui.theme import *
from srs import update_srs_item
from config import save_synonyms_cache
from notion_api import fetch_synonyms_antonyms, fetch_notion_page_blocks_text
from ui.components import WordCard, SRSButtons, ChoiceButtons, MatchQuiz, SpellingQuiz, ScrambleQuiz

class ReviewTab(ft.Column):
    def __init__(self, page: ft.Page, srs_data, save_srs_data_fn, synonyms_cache, notion_token):
        super().__init__()
        self.scroll = ft.ScrollMode.AUTO
        self.page_ref = page
        self.srs_data = srs_data
        self.save_srs_data_fn = save_srs_data_fn
        self.synonyms_cache = synonyms_cache
        self.notion_token = notion_token
        self.vocab_list = []
        self.review_queue = []
        self.current_index = 0
        self.review_mode = "flashcard"
        
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.alignment = ft.MainAxisAlignment.CENTER
        
        self.init_ui()

    def init_ui(self):
        # 1. Word Card Component (Truyền callback click lật thẻ)
        self.word_card = WordCard(on_card_click=self.on_card_click)
        
        # 2. Dòng chữ hướng dẫn lật thẻ (Chỉ hiện trong chế độ Flashcard khi chưa lật)
        self.lbl_flashcard_instruction = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon=ft.Icons.LIGHTBULB_OUTLINED, color=COLOR_WARNING, size=40),
                    ft.Text("Nhấn vào thẻ bên trái\nde xem nghĩa câu 💡", size=16, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            width=400,
            alignment=ft.Alignment(0, 0),
            visible=False
        )
        
        # 3. Choice Buttons Component (Cho chế độ Trắc nghiệm dịch nghĩa & Đồng/Trái nghĩa Dạng 1)
        self.choice_buttons = ChoiceButtons(on_choice_click=self.handle_choice_selected)

        # 4. Match Quiz Component (Cho chế độ Đánh dấu Đồng/Trái nghĩa Dạng 2)
        self.match_quiz = MatchQuiz(on_verify=self.handle_match_verified)

        # 5. Spelling Quiz Component (Dạng tự viết từ vựng)
        self.spelling_quiz = SpellingQuiz(on_correct=self.handle_spelling_verified)

        # 6. Scramble Quiz Component (Dạng sắp xếp chữ cái)
        self.scramble_quiz = ScrambleQuiz(on_correct=self.handle_scramble_verified)

        # 7. SRS Buttons Component (Phản hồi chất lượng ghi nhớ)
        self.srs_buttons = SRSButtons(on_rate_click=self.handle_srs_rating)
        
        # 8. Khung tương tác bên tay phải (Interaction Panel)
        self.interaction_panel = ft.Column(
            controls=[
                self.lbl_flashcard_instruction,
                self.choice_buttons,
                self.match_quiz,
                self.spelling_quiz,
                self.scramble_quiz,
                ft.Container(height=10),
                self.srs_buttons
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            width=380,
            spacing=10
        )
        
        # 9. Giao diện Song song (Split Layout: Card bên trái, Tương tác bên phải)
        self.main_split_layout = ft.Row(
            controls=[
                self.word_card,
                ft.VerticalDivider(color=COLOR_BORDER, width=20),
                self.interaction_panel
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
        
        # 10. Progress UI Components
        self.progress_bar = ft.ProgressBar(value=0, width=500, color=COLOR_PRIMARY_LIGHT, bgcolor=COLOR_BG_PROGRESS)
        self.lbl_progress = ft.Text(value="Chưa kết nối dữ liệu. Vui lòng vào tab Settings và bấm Sync with Notion 🔄", size=13, color=COLOR_TEXT_MUTED)
        
        self.controls = [
            ft.Text("Meow-morize Daily Review 🐾", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Master your vocabulary using Spaced Repetition", size=14, color=COLOR_TEXT_SUBTITLE),
            ft.Container(height=20),
            self.main_split_layout,
            ft.Container(height=20),
            self.progress_bar,
            self.lbl_progress
        ]

    def on_card_click(self, e):
        # Cho phép click lật thẻ để xem nghĩa/từ gốc trong các chế độ ôn tập
        is_hidden = False
        if self.review_mode in ["flashcard"] and not self.word_card.lbl_translation.visible:
            is_hidden = True
        elif self.review_mode in ["spelling"] and self.word_card.lbl_word.value == "Spell this word 🔠":
            is_hidden = True
        elif self.review_mode in ["scramble"] and self.word_card.lbl_word.value == "Unscramble the letters! 🔄":
            is_hidden = True
            
        if is_hidden:
            if not self.review_queue or self.current_index >= len(self.review_queue):
                return
            
            current_item = self.review_queue[self.current_index]
            
            # Lật thẻ hiển thị nghĩa và từ gốc tiếng Anh
            self.word_card.lbl_word.value = current_item["word"] # Hiện từ gốc
            self.word_card.reveal_translation(True)
            self.lbl_flashcard_instruction.visible = False
            self.page_ref.update()
            
            # Kích hoạt hiện các nút đánh giá SRS
            self.setup_srs_ratings()

    def build_review_queue(self, vocab_list):
        self.vocab_list = vocab_list
        self.review_queue = []
        self.current_index = 0
        today = datetime.date.today().isoformat()
        
        due_words = []
        for item in self.vocab_list:
            word = item["word"]
            if word not in self.srs_data or self.srs_data[word]["next_review"] <= today:
                due_words.append(item)
                
        # Trộn ngẫu nhiên danh sách ôn tập hôm nay
        random.shuffle(due_words)
        
        # Giới hạn tối đa 50 từ mỗi ngày
        self.review_queue = due_words[:50]
        
        # Gán ngẫu nhiên chế độ câu hỏi cho từng từ
        for item in self.review_queue:
            word = item["word"]
            cached_data = self.synonyms_cache.get(word, {})
            syns = cached_data.get("synonyms", [])
            ants = cached_data.get("antonyms", [])
            
            # Gán ngẫu nhiên giữa 6 chế độ: flashcard, multiple_choice, spelling, scramble, synonym_antonym_choice, synonym_antonym_match
            if word not in self.synonyms_cache or "source" not in cached_data or syns or ants:
                item["quiz_type"] = random.choice([
                    "flashcard", 
                    "multiple_choice", 
                    "spelling",
                    "scramble",
                    "synonym_antonym_choice", 
                    "synonym_antonym_match"
                ])
            else:
                item["quiz_type"] = random.choice(["flashcard", "multiple_choice", "spelling", "scramble"])
                
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
        self.word_card.reveal_translation(False)
        self.srs_buttons.show_buttons(False)
        self.lbl_flashcard_instruction.visible = False
        self.choice_buttons.show_choices(False)
        self.match_quiz.show_quiz(False)
        self.spelling_quiz.show_quiz(False)
        self.scramble_quiz.show_quiz(False)
        
        if not self.review_queue or self.current_index >= len(self.review_queue):
            self.word_card.reset_card(
                word="All Done! 🐱", 
                context="You have finished all vocab reviews for today.", 
                translation=""
            )
            self.word_card.lbl_hint.visible = False
            self.progress_bar.value = 1.0
            self.lbl_progress.value = "Completed!"
            self.page_ref.update()
            return
            
        item = self.review_queue[self.current_index]
        word = item["word"]
        self.word_card.set_word(word)
        
        # Đọc chế độ câu hỏi được gán ngẫu nhiên cho từ này
        self.review_mode = item.get("quiz_type", "flashcard")
        
        # Kiểm tra nếu ở chế độ Đồng/Trái nghĩa, tiến hành lazy loading nếu chưa có hoặc có dữ liệu cũ trong cache
        if self.review_mode in ["synonym_antonym_choice", "synonym_antonym_match"]:
            cached_data = self.synonyms_cache.get(word, {})
            if word not in self.synonyms_cache or "source" not in cached_data:
                self.lbl_progress.value = f"⌛ Loading synonyms for '{word}' from Notion..."
                self.page_ref.update()
                
                syns = []
                ants = []
                # 1. Đầu tiên, cố gắng lấy từ trang Notion (do AI viết)
                if self.notion_token and item.get("id"):
                    page_text = fetch_notion_page_blocks_text(item["id"], self.notion_token)
                    if page_text:
                        syn_match = re.search(r"^\s*đồng\s+nghĩa\s*:\s*([^\n]+)", page_text, re.IGNORECASE | re.MULTILINE)
                        if syn_match:
                            syns = [s.strip() for s in syn_match.group(1).split(",") if s.strip()]
                        
                        ant_match = re.search(r"^\s*trái\s+nghĩa\s*:\s*([^\n]+)", page_text, re.IGNORECASE | re.MULTILINE)
                        if ant_match:
                            ants = [a.strip() for a in ant_match.group(1).split(",") if a.strip()]
                
                # 2. Nếu Notion rỗng, fallback sang gọi API Từ điển công cộng
                if not syns and not ants:
                    self.lbl_progress.value = f"⌛ Checked Notion, now fetching '{word}' from Dictionary API..."
                    self.page_ref.update()
                    syns, ants = fetch_synonyms_antonyms(word)
                
                # Lưu vào cache kèm đánh dấu source=notion để tự động phục hồi các bản cache cũ
                self.synonyms_cache[word] = {"synonyms": syns, "antonyms": ants, "source": "notion"}
                save_synonyms_cache(self.synonyms_cache)
                
            # Đọc lại từ cache
            cached_data = self.synonyms_cache.get(word, {})
            if not cached_data.get("synonyms") and not cached_data.get("antonyms"):
                # Nếu cả hai đều không tìm thấy gì, tự động chuyển về Flashcard hoặc Trắc nghiệm dịch
                self.review_mode = random.choice(["flashcard", "multiple_choice", "spelling", "scramble"])
        
        # Tiến hành kết xuất giao diện dựa trên chế độ thực tế
        if self.review_mode == "flashcard":
            # Che từ trong ngữ cảnh
            hidden_context = item["context"]
            if item["word"].lower() in hidden_context.lower():
                insensitive_word = re.compile(re.escape(item["word"]), re.IGNORECASE)
                hidden_context = insensitive_word.sub("_______", hidden_context)
            self.word_card.set_context(hidden_context)
            self.word_card.set_translation(item["translation"])
            self.word_card.lbl_hint.visible = True
            
            self.lbl_flashcard_instruction.visible = True
            self.choice_buttons.show_choices(False)
            self.match_quiz.show_quiz(False)
            
        elif self.review_mode == "multiple_choice":
            hidden_context = item["context"]
            if item["word"].lower() in hidden_context.lower():
                insensitive_word = re.compile(re.escape(item["word"]), re.IGNORECASE)
                hidden_context = insensitive_word.sub("_______", hidden_context)
            self.word_card.set_context(hidden_context)
            self.word_card.set_translation(item["translation"])
            self.word_card.lbl_hint.visible = False
            
            self.lbl_flashcard_instruction.visible = False
            self.choice_buttons.show_choices(True)
            self.match_quiz.show_quiz(False)
            self.setup_choices()
            
        elif self.review_mode == "synonym_antonym_choice":
            self.word_card.lbl_hint.visible = False
            self.lbl_flashcard_instruction.visible = False
            self.choice_buttons.show_choices(True)
            self.match_quiz.show_quiz(False)
            self.setup_synonym_antonym_choice()
            
        elif self.review_mode == "synonym_antonym_match":
            self.word_card.lbl_hint.visible = False
            self.lbl_flashcard_instruction.visible = False
            self.choice_buttons.show_choices(False)
            self.match_quiz.show_quiz(True)
            self.setup_synonym_antonym_match()

        elif self.review_mode == "spelling":
            # Ẩn từ gốc trên thẻ để bắt người dùng tự gõ
            self.word_card.lbl_word.value = "Spell this word 🔠"
            
            # Che từ trong ngữ cảnh
            hidden_context = item["context"]
            if item["word"].lower() in hidden_context.lower():
                insensitive_word = re.compile(re.escape(item["word"]), re.IGNORECASE)
                hidden_context = insensitive_word.sub("_______", hidden_context)
            self.word_card.set_context(hidden_context)
            self.word_card.set_translation(item["translation"])
            self.word_card.lbl_translation.visible = True
            self.word_card.lbl_hint.visible = True
            
            self.lbl_flashcard_instruction.visible = False
            self.choice_buttons.show_choices(False)
            self.match_quiz.show_quiz(False)
            
            self.spelling_quiz.show_quiz(True)
            self.spelling_quiz.set_quiz(item["word"])

        elif self.review_mode == "scramble":
            # Ẩn từ gốc trên thẻ để bắt người dùng tự ghép chữ cái
            self.word_card.lbl_word.value = "Unscramble the letters! 🔄"
            
            # Che từ trong ngữ cảnh
            hidden_context = item["context"]
            if item["word"].lower() in hidden_context.lower():
                insensitive_word = re.compile(re.escape(item["word"]), re.IGNORECASE)
                hidden_context = insensitive_word.sub("_______", hidden_context)
            self.word_card.set_context(hidden_context)
            self.word_card.set_translation(item["translation"])
            self.word_card.lbl_translation.visible = True
            self.word_card.lbl_hint.visible = True
            
            self.lbl_flashcard_instruction.visible = False
            self.choice_buttons.show_choices(False)
            self.match_quiz.show_quiz(False)
            self.spelling_quiz.show_quiz(False)
            
            self.scramble_quiz.show_quiz(True)
            self.scramble_quiz.set_quiz(item["word"])
        
        self.update_progress_ui()
        self.page_ref.update()

    def setup_choices(self):
        if not self.review_queue or self.current_index >= len(self.review_queue):
            return
        
        current_item = self.review_queue[self.current_index]
        correct_ans = current_item["translation"]
        
        # Gather distinct incorrect translation options
        other_translations = [
            item["translation"] for item in self.vocab_list 
            if item["word"].lower() != current_item["word"].lower() and item["translation"]
        ]
        other_translations = list(set(other_translations))
        
        while len(other_translations) < 3:
            other_translations.append("Nghĩa bổ trợ " + str(len(other_translations) + 1))
            
        distractors = random.sample(other_translations, 3)
        choices = [correct_ans] + distractors
        random.shuffle(choices)
        
        self.choice_buttons.set_choices(choices, correct_ans)

    def setup_synonym_antonym_choice(self):
        current_item = self.review_queue[self.current_index]
        word = current_item["word"]
        cached_data = self.synonyms_cache.get(word, {})
        syns = cached_data.get("synonyms", [])
        ants = cached_data.get("antonyms", [])
        
        # Chọn hỏi về đồng nghĩa hay trái nghĩa tùy vào dữ liệu có sẵn
        ask_type = "synonym"
        if syns and ants:
            ask_type = random.choice(["synonym", "antonym"])
        elif ants:
            ask_type = "antonym"
            
        if ask_type == "synonym":
            self.word_card.set_context("Tìm từ ĐỒNG NGHĨA (Synonym) của từ trên:")
            correct_ans = random.choice(syns)
        else:
            self.word_card.set_context("Tìm từ TRÁI NGHĨA (Antonym) của từ trên:")
            correct_ans = random.choice(ants)
            
        self.word_card.set_translation(f"Dịch nghĩa từ gốc: {current_item['translation']}")
        
        # Tạo distractors từ danh sách từ vựng thông thường
        distractors_pool = [
            item["word"] for item in self.vocab_list 
            if item["word"].lower() != word.lower() and item["word"] not in syns and item["word"] not in ants
        ]
        
        while len(distractors_pool) < 3:
            distractors_pool.append("fake_word_" + str(len(distractors_pool)))
            
        distractors = random.sample(distractors_pool, 3)
        choices = [correct_ans] + distractors
        random.shuffle(choices)
        
        self.choice_buttons.set_choices(choices, correct_ans)

    def setup_synonym_antonym_match(self):
        current_item = self.review_queue[self.current_index]
        word = current_item["word"]
        cached_data = self.synonyms_cache.get(word, {})
        syns = cached_data.get("synonyms", [])
        ants = cached_data.get("antonyms", [])
        
        self.word_card.set_context("Đánh dấu mỗi từ bên phải là Đồng nghĩa (Synonym) hay Trái nghĩa (Antonym) so với từ trên:")
        self.word_card.set_translation(f"Dịch nghĩa từ gốc: {current_item['translation']}")
        
        match_options = []
        correct_answers = {}
        
        # Chọn tối đa 2 từ đồng nghĩa
        selected_syns = random.sample(syns, min(2, len(syns))) if syns else []
        for s in selected_syns:
            match_options.append(s)
            correct_answers[s] = "synonym"
            
        # Chọn tối đa 2 từ trái nghĩa
        selected_ants = random.sample(ants, min(2, len(ants))) if ants else []
        for a in selected_ants:
            match_options.append(a)
            correct_answers[a] = "antonym"
            
        # Thêm các từ không liên quan để lấp đầy 4 vị trí
        unrelated_pool = [
            item["word"] for item in self.vocab_list 
            if item["word"].lower() != word.lower() and item["word"] not in syns and item["word"] not in ants
        ]
        needed = 4 - len(match_options)
        selected_unrelated = random.sample(unrelated_pool, min(needed, len(unrelated_pool))) if unrelated_pool else []
        for u in selected_unrelated:
            match_options.append(u)
            correct_answers[u] = "unrelated"
            
        # Dự phòng nếu không đủ từ
        while len(match_options) < 4:
            fake_w = "word_" + str(len(match_options))
            match_options.append(fake_w)
            correct_answers[fake_w] = "unrelated"
            
        random.shuffle(match_options)
        
        # Thiết lập match quiz
        self.match_quiz.set_quiz(match_options, correct_answers)

    def handle_choice_selected(self, selected_ans, is_correct):
        # Reveal card answer
        self.word_card.reveal_translation(True)
        # Display SRS rating options
        self.setup_srs_ratings()

    def handle_match_verified(self):
        # Reveal card answer
        self.word_card.reveal_translation(True)
        # Display SRS rating options
        self.setup_srs_ratings()

    def handle_spelling_verified(self):
        # Reveal target word and translation on card
        current_item = self.review_queue[self.current_index]
        self.word_card.lbl_word.value = current_item["word"]
        self.word_card.reveal_translation(True)
        # Display SRS rating options
        self.setup_srs_ratings()

    def handle_scramble_verified(self):
        # Reveal target word and translation on card
        current_item = self.review_queue[self.current_index]
        self.word_card.lbl_word.value = current_item["word"]
        self.word_card.reveal_translation(True)
        # Display SRS rating options
        self.setup_srs_ratings()

    def setup_srs_ratings(self):
        # Calculate intervals
        word = self.review_queue[self.current_index]["word"]
        item_srs = self.srs_data.get(word, {"ease_factor": 2.5, "repetitions": 0, "interval": 1})
        ef = item_srs["ease_factor"]
        rep = item_srs["repetitions"]
        
        if rep == 0:
            day_easy = 4
        elif rep == 1:
            day_easy = 6
        else:
            day_easy = int(round(item_srs["interval"] * ef))
            
        self.srs_buttons.set_ratings(day_easy)
        self.srs_buttons.show_buttons(True)
        self.page_ref.update()

    def handle_srs_rating(self, quality):
        if not self.review_queue or self.current_index >= len(self.review_queue):
            return
        word = self.review_queue[self.current_index]["word"]
        
        # Update spacing schedule
        self.srs_data = update_srs_item(self.srs_data, word, quality)
        self.save_srs_data_fn(self.srs_data)
        
        # Next card
        self.current_index += 1
        self.show_current_card()
