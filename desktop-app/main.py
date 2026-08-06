import flet as ft
from config import load_config, save_config, load_srs_data, save_srs_data, load_synonyms_cache, save_synonyms_cache
from notion_api import fetch_notion_vocab, fetch_synonyms_antonyms
from ui.theme import *
from ui.review_tab import ReviewTab
from ui.settings_tab import SettingsTab

def main(page: ft.Page):
    page.title = "Meow-morize Desktop Review App 🐾"
    page.window_width = 950
    page.window_height = 680
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Tải cấu hình và dữ liệu ôn tập cục bộ
    config = load_config()
    srs_data = load_srs_data()
    synonyms_cache = load_synonyms_cache()
    vocab_list = []

    # Định nghĩa hàm callback lưu dữ liệu SRS
    def save_srs_data_fn(new_srs_data):
        save_srs_data(new_srs_data)

    # Hàm đồng bộ dữ liệu với Notion
    def sync_from_notion(token, db_id, status_label=None):
        nonlocal vocab_list, synonyms_cache
        try:
            vocab_list = fetch_notion_vocab(token, db_id)
            
            review_tab.synonyms_cache = synonyms_cache
            review_tab.notion_token = token
            review_tab.build_review_queue(vocab_list)
            
            if status_label:
                status_label.value = f"Success! Synced {len(vocab_list)} words from Notion."
                status_label.color = COLOR_SUCCESS
                page.update()
        except Exception as ex:
            if status_label:
                status_label.value = f"Sync failed: {str(ex)}"
                status_label.color = COLOR_ERROR
                page.update()
            raise ex

    # Khởi dựng các Tab UI (Truyền cache từ đồng nghĩa và notion_token vào)
    review_tab = ReviewTab(page, srs_data, save_srs_data_fn, synonyms_cache, config["notion_token"])
    settings_tab = SettingsTab(page, config, save_config, sync_from_notion)

    # Tự động tải từ Notion khi mở app nếu đã có sẵn Token & Database ID
    if config["notion_token"] and config["database_id"]:
        async def initial_load():
            try:
                sync_from_notion(config["notion_token"], config["database_id"])
            except Exception:
                settings_tab.lbl_status.value = "Initial auto-sync failed. Check your token/connection."
                settings_tab.lbl_status.color = COLOR_ERROR
                page.update()

        page.run_task(initial_load)

    # Dựng cấu trúc Tab giao diện lồng nhau
    tabs = ft.Tabs(
        length=2,
        selected_index=0,
        animation_duration=300,
        content=ft.Column(
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Review Panel 🧠"),
                        ft.Tab(label="Settings ⚙️")
                    ]
                ),
                ft.TabBarView(
                    controls=[
                        review_tab,
                        settings_tab
                    ],
                    expand=True
                )
            ],
            expand=True
        ),
        expand=True
    )

    page.add(tabs)

if __name__ == "__main__":
    ft.run(main)
