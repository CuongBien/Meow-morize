import datetime
import re
import random
import threading
import subprocess
import os
import json
import flet as ft
from ui.theme import *
from srs import update_srs_item, calculate_anki_previews
from config import save_synonyms_cache
from notion_api import fetch_synonyms_antonyms, fetch_notion_page_blocks_text
from ui.components import WordCard, SRSButtons, ChoiceButtons, MatchQuiz, SpellingQuiz, ScrambleQuiz

SESSION_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "review_session.json")

# Bộ phát âm thanh Text-To-Speech ngoại tuyến thông qua Windows Speech API (SAPI)
def play_tts(word):
    def run():
        # Làm sạch chuỗi từ tránh lỗi lệnh PowerShell
        clean_word = "".join([c for c in word if c.isalnum() or c.isspace() or c in ["-", "_", "'"]])
        ps_cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{clean_word}')"
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        subprocess.run(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=si)
    threading.Thread(target=run, daemon=True).start()

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
        self.settings_tab_ref = None  # Sẽ được gán từ main.py
        self.detail_open = False
        
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.alignment = ft.MainAxisAlignment.CENTER
        
        self.init_ui()

    def init_ui(self):
        # 1. Word Card Component (Truyền callback click lật thẻ và click nút phát âm)
        self.word_card = WordCard(on_card_click=self.on_card_click, on_speak_click=self.handle_speak_word)
        
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
        
        # 3. Choice Buttons Component (Cho chế độ Trắc nghiệm dịch nghĩa, Đồng/Trái nghĩa & Nghe chọn từ)
        self.choice_buttons = ChoiceButtons(on_choice_click=self.handle_choice_selected)

        # 4. Match Quiz Component (Cho chế độ Đánh dấu Đồng/Trái nghĩa Dạng 2)
        self.match_quiz = MatchQuiz(on_verify=self.handle_match_verified)

        # 5. Spelling Quiz Component (Dạng tự viết từ vựng)
        self.spelling_quiz = SpellingQuiz(on_correct=self.handle_spelling_verified)

        # 6. Scramble Quiz Component (Dạng sắp xếp chữ cái)
        self.scramble_quiz = ScrambleQuiz(on_correct=self.handle_scramble_verified)

        # 7. SRS Buttons Component (Phản hồi chất lượng ghi nhớ)
        self.srs_buttons = SRSButtons(on_rate_click=self.handle_srs_rating)

        # 7.5. Progress UI Components (Anki 3-Color Badge Bar + Progress Bar)
        self.badge_new = ft.Container(content=ft.Text("🔵 New: 0", size=12, weight=ft.FontWeight.BOLD, color="#1d4ed8"), bgcolor="#eff6ff", padding=ft.Padding(8, 3, 8, 3), border_radius=10, border=ft.Border.all(1, "#bfdbfe"))
        self.badge_learn = ft.Container(content=ft.Text("🟠 Learn: 0", size=12, weight=ft.FontWeight.BOLD, color="#b45309"), bgcolor="#fffbeb", padding=ft.Padding(8, 3, 8, 3), border_radius=10, border=ft.Border.all(1, "#fde68a"))
        self.badge_review = ft.Container(content=ft.Text("🟢 Review: 0", size=12, weight=ft.FontWeight.BOLD, color="#047857"), bgcolor="#ecfdf5", padding=ft.Padding(8, 3, 8, 3), border_radius=10, border=ft.Border.all(1, "#a7f3d0"))

        self.anki_counter_bar = ft.Row(
            controls=[self.badge_new, self.badge_learn, self.badge_review],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )

        self.progress_bar = ft.ProgressBar(value=0, width=500, color=COLOR_PRIMARY_LIGHT, bgcolor=COLOR_BG_PROGRESS)
        self.lbl_progress = ft.Text(value="Chưa kết nối dữ liệu. Bấm nút ⚙️ để cấu hình Notion 🔄", size=13, color=COLOR_TEXT_MUTED)
        
        # 8. Các nút tiện ích (Xem chi tiết Notion & Mở link Notion)
        self.btn_open_notion = ft.TextButton(
            content=ft.Text("Open in Notion 🔗"),
            on_click=self.handle_open_notion,
            visible=False
        )
        self.btn_view_details = ft.TextButton(
            content=ft.Text("Xem chi tiết 📄"),
            on_click=self.handle_view_details,
            visible=False
        )
        self.left_column = ft.Column(
            controls=[
                self.word_card,
                ft.Row(
                    controls=[self.btn_view_details, self.btn_open_notion],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=15
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

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

        # 9. Detail Panel bên phải (đóng/mở được, toàn bộ chiều cao cửa sổ)
        self.detail_markdown = ft.Markdown("", selectable=True)
        self.detail_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Chi tiết từ vựng 📄", size=16, weight=ft.FontWeight.BOLD),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=COLOR_TEXT_MUTED,
                                icon_size=20,
                                on_click=self.handle_close_detail
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(color=COLOR_BORDER, height=1),
                    ft.Column(
                        controls=[self.detail_markdown],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True
                    )
                ],
                spacing=8,
                expand=True
            ),
            width=420,
            border=ft.Border(
                left=ft.BorderSide(1, COLOR_BORDER),
                top=ft.BorderSide(0, "transparent"),
                right=ft.BorderSide(0, "transparent"),
                bottom=ft.BorderSide(0, "transparent")
            ),
            padding=ft.Padding(25, 20, 20, 20),
            visible=False
        )
        
        # 10. Khu vực ôn tập chính (Card + Interaction + Progress)
        self.center_area = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.left_column,
                        ft.VerticalDivider(color=COLOR_BORDER, width=20),
                        self.interaction_panel
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                ),
                ft.Container(height=15),
                self.anki_counter_bar,
                ft.Container(height=8),
                self.progress_bar,
                self.lbl_progress
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )

        # 11. Nút Settings
        self.btn_settings = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_color=COLOR_TEXT_MUTED,
            icon_size=22,
            on_click=self.handle_open_settings
        )

        # 12. Cột chính chứa Header + Content (sẽ bị đẩy sang trái khi mở detail panel)
        self.main_column = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Meow-morize Daily Review 🐾", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Master your vocabulary using Spaced Repetition", size=14, color=COLOR_TEXT_SUBTITLE),
                            ]
                        ),
                        self.btn_settings
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                ft.Divider(color=COLOR_BORDER, height=1),
                self.center_area
            ],
            expand=True
        )

        # 13. Bố cục tổng: [Main Column | Detail Panel] — detail panel đẩy toàn bộ main column
        self.controls = [
            ft.Row(
                controls=[
                    self.main_column,
                    self.detail_panel
                ],
                expand=True,
                spacing=0
            )
        ]
        self.expand = True
        self.scroll = None

    def on_card_click(self, e):
        # Cho phép click lật thẻ để xem nghĩa/từ gốc trong các chế độ ôn tập
        is_hidden = False
        if self.review_mode in ["flashcard"] and not self.word_card.lbl_translation.visible:
            is_hidden = True
        elif self.review_mode in ["spelling"] and self.word_card.lbl_word.value == "Spell this word 🔠":
            is_hidden = True
        elif self.review_mode in ["scramble"] and self.word_card.lbl_word.value == "Unscramble the letters! 🔄":
            is_hidden = True
        elif self.review_mode in ["listening"] and self.word_card.lbl_word.value == "Listen and choose! 🎧":
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
        today = datetime.date.today().isoformat()
        
        # Thử phục hồi session hôm nay (nếu restart app trong cùng ngày)
        restored = self.load_session(today)
        if restored:
            self.update_progress_ui()
            self.show_current_card()
            return
        
        # Tạo session mới
        self.review_queue = []
        self.current_index = 0
        
        due_review_words = []
        learning_words = []
        new_words = []
        
        for item in self.vocab_list:
            word = item["word"]
            srs_entry = self.srs_data.get(word, {})
            state = srs_entry.get("state", "new" if "repetitions" not in srs_entry else "review")
            next_rev = srs_entry.get("next_review", "")
            
            if word not in self.srs_data or state == "new":
                new_words.append(item)
            elif state == "learning":
                learning_words.append(item)
            elif next_rev <= today:
                due_review_words.append(item)
                
        # Trộn ngẫu nhiên từng nhóm
        random.shuffle(due_review_words)
        random.shuffle(learning_words)
        random.shuffle(new_words)
        
        # Không giới hạn 50 từ: đưa TOÀN BỘ từ cần học/ôn trong ngày vào danh sách (Review -> Learn -> New)
        self.review_queue = due_review_words + learning_words + new_words
        
        # Gán ngẫu nhiên chế độ câu hỏi cho từng từ
        for item in self.review_queue:
            word = item["word"]
            cached_data = self.synonyms_cache.get(word, {})
            syns = cached_data.get("synonyms", [])
            ants = cached_data.get("antonyms", [])
            
            if word not in self.synonyms_cache or "source" not in cached_data or syns or ants:
                item["quiz_type"] = random.choice([
                    "flashcard", 
                    "multiple_choice", 
                    "spelling",
                    "scramble",
                    "listening",
                    "synonym_antonym_choice", 
                    "synonym_antonym_match"
                ])
            else:
                item["quiz_type"] = random.choice(["flashcard", "multiple_choice", "spelling", "scramble", "listening"])
        
        self.save_session(today)
        self.update_progress_ui()
        self.show_current_card()

    def save_session(self, today):
        """Lưu session ôn tập hôm nay ra file để phục hồi khi restart."""
        try:
            session = {
                "date": today,
                "queue_words": [item["word"] for item in self.review_queue],
                "quiz_types": {item["word"]: item.get("quiz_type", "flashcard") for item in self.review_queue},
                "current_index": self.current_index
            }
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_session(self, today):
        """Phục hồi session nếu cùng ngày. Trả về True nếu thành công."""
        try:
            if not os.path.exists(SESSION_FILE):
                return False
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                session = json.load(f)
            
            if session.get("date") != today:
                return False
            
            queue_words = session.get("queue_words", [])
            quiz_types = session.get("quiz_types", {})
            
            if not queue_words:
                return False
            
            word_to_item = {item["word"]: item for item in self.vocab_list}
            self.review_queue = []
            for w in queue_words:
                if w in word_to_item:
                    item = word_to_item[w]
                    item["quiz_type"] = quiz_types.get(w, "flashcard")
                    self.review_queue.append(item)
            
            if not self.review_queue:
                return False
            
            self.current_index = session.get("current_index", 0)
            if self.current_index >= len(self.review_queue):
                self.current_index = len(self.review_queue)
            
            return True
        except Exception:
            return False
        
    def update_progress_ui(self):
        total = len(self.review_queue)
        
        # Đếm số từ còn lại cho 3 thẻ Anki: New, Learn, Review
        new_cnt = 0
        learn_cnt = 0
        review_cnt = 0
        
        for item in self.review_queue[self.current_index:]:
            w = item["word"]
            srs_entry = self.srs_data.get(w, {})
            state = srs_entry.get("state", "new" if "repetitions" not in srs_entry else "review")
            if w not in self.srs_data or state == "new":
                new_cnt += 1
            elif state == "learning":
                learn_cnt += 1
            else:
                review_cnt += 1
                
        self.badge_new.content.value = f"🔵 New: {new_cnt}"
        self.badge_learn.content.value = f"🟠 Learn: {learn_cnt}"
        self.badge_review.content.value = f"🟢 Review: {review_cnt}"
        
        if total == 0:
            self.progress_bar.value = 0
            self.lbl_progress.value = "All caught up! 🎉 No words to review today."
        else:
            self.progress_bar.value = min(1.0, self.current_index / total)
            self.lbl_progress.value = f"Progress: {self.current_index}/{total} cards reviewed today"

    def show_current_card(self):
        self.word_card.reveal_translation(False)
        self.srs_buttons.show_buttons(False)
        self.lbl_flashcard_instruction.visible = False
        self.choice_buttons.show_choices(False)
        self.match_quiz.show_quiz(False)
        self.spelling_quiz.show_quiz(False)
        self.scramble_quiz.show_quiz(False)
        self.word_card.btn_speak.visible = False
        self.btn_open_notion.visible = False
        self.btn_view_details.visible = False
        
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
                page_text = ""
                # 1. Đầu tiên, cố gắng lấy từ trang Notion (do AI viết)
                if self.notion_token and item.get("id"):
                    page_text = fetch_notion_page_blocks_text(item["id"], self.notion_token)
                    if page_text:
                        # Regex linh hoạt: cho phép dấu - , * , số thứ tự, khoảng trắng ở đầu dòng
                        syn_match = re.search(r"^[\s\-\*\d\.]*đồng\s+nghĩa\s*:\s*([^\n]+)", page_text, re.IGNORECASE | re.MULTILINE)
                        if syn_match:
                            syns = [s.strip().rstrip('.').strip() for s in syn_match.group(1).split(",") if s.strip().rstrip('.').strip()]
                        
                        ant_match = re.search(r"^[\s\-\*\d\.]*trái\s+nghĩa\s*:\s*([^\n]+)", page_text, re.IGNORECASE | re.MULTILINE)
                        if ant_match:
                            ants = [a.strip().rstrip('.').strip() for a in ant_match.group(1).split(",") if a.strip().rstrip('.').strip()]
                
                # 2. Nếu Notion rỗng, fallback sang gọi API Từ điển công cộng
                if not syns and not ants:
                    self.lbl_progress.value = f"⌛ Checked Notion, now fetching '{word}' from Dictionary API..."
                    self.page_ref.update()
                    syns, ants = fetch_synonyms_antonyms(word)
                
                # Lưu vào cache kèm đánh dấu source=notion để tự động phục hồi các bản cache cũ
                self.synonyms_cache[word] = {
                    "synonyms": syns, 
                    "antonyms": ants, 
                    "source": "notion",
                    "page_text": page_text
                }
                save_synonyms_cache(self.synonyms_cache)
                
            # Đọc lại từ cache
            cached_data = self.synonyms_cache.get(word, {})
            if not cached_data.get("synonyms") and not cached_data.get("antonyms"):
                # Nếu cả hai đều không tìm thấy gì, tự động chuyển về các chế độ thông thường
                self.review_mode = random.choice(["flashcard", "multiple_choice", "spelling", "scramble", "listening"])
        
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

        elif self.review_mode == "listening":
            # Ẩn từ gốc trên thẻ, hiện loa phóng thanh
            self.word_card.lbl_word.value = "Listen and choose! 🎧"
            self.word_card.btn_speak.visible = True
            
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
            self.choice_buttons.show_choices(True)
            self.match_quiz.show_quiz(False)
            self.spelling_quiz.show_quiz(False)
            self.scramble_quiz.show_quiz(False)
            
            self.setup_listening_choices()
            
            # Phát âm thanh tự động lần đầu cho thính giác nhận diện
            play_tts(item["word"])
        
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

    def setup_listening_choices(self):
        if not self.review_queue or self.current_index >= len(self.review_queue):
            return
            
        current_item = self.review_queue[self.current_index]
        correct_ans = current_item["word"]
        
        # Gather distinct incorrect English words from the database
        other_words = [
            item["word"] for item in self.vocab_list 
            if item["word"].lower() != correct_ans.lower()
        ]
        other_words = list(set(other_words))
        
        while len(other_words) < 3:
            other_words.append("word_" + str(len(other_words)))
            
        distractors = random.sample(other_words, 3)
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
        syns_lower = [s.lower() for s in syns]
        ants_lower = [a.lower() for a in ants]
        distractors_pool = [
            item["word"] for item in self.vocab_list 
            if item["word"].lower() != word.lower() and item["word"].lower() not in syns_lower and item["word"].lower() not in ants_lower
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
        syns_lower = [s.lower() for s in syns]
        ants_lower = [a.lower() for a in ants]
        unrelated_pool = [
            item["word"] for item in self.vocab_list 
            if item["word"].lower() != word.lower() and item["word"].lower() not in syns_lower and item["word"].lower() not in ants_lower
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
        self.word_card.lbl_word.value = self.review_queue[self.current_index]["word"]
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

    def handle_speak_word(self, e):
        if self.review_queue and self.current_index < len(self.review_queue):
            current_item = self.review_queue[self.current_index]
            play_tts(current_item["word"])

    def setup_srs_ratings(self):
        # Hiện các nút tiện ích xem chi tiết Notion khi đáp án đã lộ diện
        self.btn_open_notion.visible = True
        self.btn_view_details.visible = True
        
        # Calculate Anki interval previews
        word = self.review_queue[self.current_index]["word"]
        item_srs = self.srs_data.get(word, {})
        previews = calculate_anki_previews(item_srs)
            
        self.srs_buttons.set_ratings(previews)
        self.srs_buttons.show_buttons(True)
        self.page_ref.update()

    def handle_open_notion(self, e):
        try:
            if not self.review_queue or self.current_index >= len(self.review_queue):
                return
            current_item = self.review_queue[self.current_index]
            url = current_item.get("url")
            if url:
                import webbrowser
                webbrowser.open(url)
            else:
                self.page_ref.snack_bar = ft.SnackBar(content=ft.Text("Từ vựng này chưa có liên kết URL Notion. Vui lòng đồng bộ lại!"))
                self.page_ref.snack_bar.open = True
                self.page_ref.update()
        except Exception as ex:
            self.page_ref.snack_bar = ft.SnackBar(content=ft.Text(f"Lỗi mở link: {str(ex)}"))
            self.page_ref.snack_bar.open = True
            self.page_ref.update()

    def handle_open_settings(self, e):
        if self.settings_tab_ref:
            dlg = ft.AlertDialog(
                title=ft.Text("Notion Connection Settings ⚙️", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=self.settings_tab_ref,
                    width=550,
                    height=300
                )
            )
            def close_dlg(e):
                dlg.open = False
                self.page_ref.update()
            dlg.actions = [ft.TextButton(content=ft.Text("Đóng"), on_click=close_dlg)]
            self.page_ref.overlay.append(dlg)
            dlg.open = True
            self.page_ref.update()

    def handle_close_detail(self, e):
        self.detail_panel.visible = False
        self.detail_open = False
        self.page_ref.window_width = 950
        self.page_ref.update()

    def handle_view_details(self, e):
        try:
            if not self.review_queue or self.current_index >= len(self.review_queue):
                return
            current_item = self.review_queue[self.current_index]
            word = current_item["word"]
            page_id = current_item.get("id")
            
            if not page_id or not self.notion_token:
                self.page_ref.snack_bar = ft.SnackBar(content=ft.Text("Thiếu thông tin liên kết Notion hoặc Notion Token. Bấm nút ⚙️ để cấu hình!"))
                self.page_ref.snack_bar.open = True
                self.page_ref.update()
                return

            cached_data = self.synonyms_cache.get(word, {})
            page_text = cached_data.get("page_text", "")

            # Mở detail panel bên phải & mở rộng cửa sổ
            self.detail_panel.visible = True
            self.detail_open = True
            self.page_ref.window_width = 1400

            if page_text:
                self.detail_markdown.value = page_text
                self.page_ref.update()
            else:
                self.detail_markdown.value = "⌛ Đang tải dữ liệu trang từ Notion..."
                self.page_ref.update()

                def fetch_details():
                    try:
                        fetched_text = fetch_notion_page_blocks_text(page_id, self.notion_token)
                        if not fetched_text:
                            fetched_text = "Trang từ vựng rỗng hoặc không có dữ liệu chi tiết."
                        
                        cached = self.synonyms_cache.get(word, {})
                        self.synonyms_cache[word] = {
                            "synonyms": cached.get("synonyms", []),
                            "antonyms": cached.get("antonyms", []),
                            "source": "notion",
                            "page_text": fetched_text
                        }
                        save_synonyms_cache(self.synonyms_cache)
                        
                        self.detail_markdown.value = fetched_text
                    except Exception as ex:
                        self.detail_markdown.value = f"⚠️ Lỗi tải chi tiết: {str(ex)}"
                    self.page_ref.update()

                threading.Thread(target=fetch_details, daemon=True).start()

        except Exception as ex:
            self.page_ref.snack_bar = ft.SnackBar(content=ft.Text(f"Lỗi: {str(ex)}"))
            self.page_ref.snack_bar.open = True
            self.page_ref.update()

    def handle_srs_rating(self, quality):
        if not self.review_queue or self.current_index >= len(self.review_queue):
            return
        
        current_item = self.review_queue[self.current_index]
        word = current_item["word"]
        
        # Update spacing schedule (Anki steps + FSRS)
        self.srs_data, graduated = update_srs_item(self.srs_data, word, quality)
        self.save_srs_data_fn(self.srs_data)
        
        # Nếu thẻ chưa tốt nghiệp (bấm Again 1m hoặc Hard 10m trên từ mới/đang học hoặc Again trên review card):
        # Chèn lại từ này vào phía sau trong phiên học hôm nay để người học gặp lại trong phiên
        if not graduated:
            insert_pos = min(len(self.review_queue), self.current_index + 4)
            self.review_queue.insert(insert_pos, current_item)
        
        # Chuyển sang thẻ tiếp theo
        self.current_index += 1
        
        # Lưu tiến trình session
        today = datetime.date.today().isoformat()
        self.save_session(today)
        
        self.update_progress_ui()
        self.show_current_card()
