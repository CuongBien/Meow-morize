import datetime
import re
import random
import flet as ft
from ui.theme import *
from srs import update_srs_item
from ui.components import ModeSelector, WordCard, SRSButtons, ChoiceButtons

class ReviewTab(ft.Column):
    def __init__(self, page: ft.Page, srs_data, save_srs_data_fn):
        super().__init__()
        self.page_ref = page
        self.srs_data = srs_data
        self.save_srs_data_fn = save_srs_data_fn
        self.vocab_list = []
        self.review_queue = []
        self.current_index = 0
        self.review_mode = "flashcard"
        
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.alignment = ft.MainAxisAlignment.CENTER
        
        self.init_ui()

    def init_ui(self):
        # 1. Mode Selector Component
        self.mode_selector = ModeSelector(
            initial_mode=self.review_mode, 
            on_mode_change=self.handle_mode_change
        )

        # 2. Word Card Component
        self.word_card = WordCard()
        
        # 3. Reveal Button (for Flashcard mode)
        self.btn_reveal = ft.Button(
            "Reveal Answer 🔓", 
            width=250, 
            height=45, 
            color=COLOR_TEXT_PRIMARY, 
            bgcolor=COLOR_PRIMARY, 
            on_click=self.on_reveal_click
        )
        
        # 4. Choice Buttons Component (for Multiple Choice mode)
        self.choice_buttons = ChoiceButtons(on_choice_click=self.handle_choice_selected)

        # 5. SRS Buttons Component (Feedback ratings)
        self.srs_buttons = SRSButtons(on_rate_click=self.handle_srs_rating)
        
        # 6. Progress UI Components
        self.progress_bar = ft.ProgressBar(value=0, width=400, color=COLOR_PRIMARY_LIGHT, bgcolor=COLOR_BG_PROGRESS)
        self.lbl_progress = ft.Text(value="0/0 Words", size=13, color=COLOR_TEXT_MUTED)
        
        self.controls = [
            ft.Text("Meow-morize Daily Review 🐾", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Master your vocabulary using Spaced Repetition", size=14, color=COLOR_TEXT_SUBTITLE),
            ft.Container(height=10),
            self.mode_selector,
            ft.Container(height=15),
            self.word_card,
            ft.Container(height=15),
            self.btn_reveal,
            self.choice_buttons,
            self.srs_buttons,
            ft.Container(height=15),
            self.progress_bar,
            self.lbl_progress
        ]

    def handle_mode_change(self, new_mode):
        self.review_mode = new_mode
        self.show_current_card()

    def build_review_queue(self, vocab_list):
        self.vocab_list = vocab_list
        self.review_queue = []
        self.current_index = 0
        today = datetime.date.today().isoformat()
        
        for item in self.vocab_list:
            word = item["word"]
            if word not in self.srs_data or self.srs_data[word]["next_review"] <= today:
                self.review_queue.append(item)
                
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
        
        if not self.review_queue or self.current_index >= len(self.review_queue):
            self.word_card.reset_card(
                word="All Done! 🐱", 
                context="You have finished all vocab reviews for today.", 
                translation=""
            )
            self.btn_reveal.visible = False
            self.choice_buttons.show_choices(False)
            self.progress_bar.value = 1.0
            self.lbl_progress.value = "Completed!"
        else:
            item = self.review_queue[self.current_index]
            self.word_card.set_word(item["word"])
            
            # Mask the target word inside the example sentence
            hidden_context = item["context"]
            if item["word"].lower() in hidden_context.lower():
                insensitive_word = re.compile(re.escape(item["word"]), re.IGNORECASE)
                hidden_context = insensitive_word.sub("_______", hidden_context)
                
            self.word_card.set_context(hidden_context)
            self.word_card.set_translation(item["translation"])
            
            if self.review_mode == "flashcard":
                self.btn_reveal.visible = True
                self.choice_buttons.show_choices(False)
            else:
                self.btn_reveal.visible = False
                self.choice_buttons.show_choices(True)
                self.setup_choices()
            
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

    def handle_choice_selected(self, selected_ans, is_correct):
        # Reveal card answer
        self.word_card.reveal_translation(True)
        
        # Display SRS rating options
        self.setup_srs_ratings()

    def on_reveal_click(self, e):
        if not self.review_queue or self.current_index >= len(self.review_queue):
            return
        self.btn_reveal.visible = False
        self.word_card.reveal_translation(True)
        
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
        self.update_progress_ui()
        self.show_current_card()
