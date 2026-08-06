# Meow-morize 🐾 (VocabSaver & Daily Review App)

Hệ thống học từ vựng tiếng Anh cá nhân tích hợp, kết hợp giữa **Chrome Extension** (Dịch & Lưu nhanh từ trình duyệt vào Notion) và **Desktop App** (Ứng dụng ôn tập giãn cách chạy local cực nhẹ).

---

## 📁 Cấu trúc Thư mục Dự án

```text
meow-morize/
├── extension/                  # Chrome Extension source code
│   ├── manifest.json           # Extension metadata & permissions
│   ├── background.js           # Background service worker (Notion & AI API)
│   ├── content.js/css          # Floating cat translator injection UI
│   ├── popup.html/js           # Quick popup view
│   ├── options.html/css/js     # Wordbook & Settings page (Google/DeepL Translate)
│   └── icons/                  # Custom cat logo assets
│
├── desktop-app/                # Python Desktop App (Spaced Repetition)
│   ├── main.py                 # App entry point (bootstrap & tabs layout)
│   ├── config.py               # Local JSON database configuration (Notion tokens)
│   ├── srs.py                  # SuperMemo SM-2 spacing review algorithm
│   ├── notion_api.py           # Notion DB query client
│   └── ui/                     # UI Layout package
│       ├── theme.py            # Hex color style tokens
│       ├── review_tab.py       # Active Recall flashcards review panel
│       └── settings_tab.py     # Notion sync settings UI
│
├── .gitignore                  # Git untracked files definition
└── README.md                   # Project documentation
```

---

## 🚀 1. Hướng dẫn cài đặt Chrome Extension

1. Mở trình duyệt Chrome, truy cập: **`chrome://extensions/`**
2. Bật chế độ **Chế độ dành cho nhà phát triển (Developer mode)** ở góc trên bên phải.
3. Chọn **Tải thư mục đã giải nén (Load unpacked)** ở góc trên bên trái.
4. Trỏ đường dẫn đến thư mục: **`d:\vocab\extension`**
5. Click biểu tượng Tiện ích trên thanh công cụ để ghim **Meow-morize** ra ngoài.

*Để thiết lập API Dịch thuật (Google/DeepL) và tài khoản Notion, click chuột phải vào extension chọn **Options**.*

---

## 💻 2. Hướng dẫn chạy Python Desktop App

Ứng dụng ôn tập Desktop App chạy bằng Python độc lập với Chrome, tự động đồng bộ từ vựng từ Notion và lên lịch ôn tập hằng ngày theo thuật toán **Spaced Repetition (SM-2)**.

### Yêu cầu hệ thống:
- Đã cài đặt Python 3.8 trở lên.

### Cài đặt & Chạy ứng dụng:
1. Mở PowerShell/Terminal tại thư mục dự án và cài đặt thư viện cần thiết:
   ```bash
   pip install flet requests
   ```
2. Di chuyển vào thư mục ứng dụng và chạy:
   ```bash
   cd desktop-app
   python main.py
   ```

*Nhập Notion Token và Database ID tại tab Settings để đồng bộ danh sách từ của bạn.*
