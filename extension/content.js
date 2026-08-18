(function() {
  // Tránh khai báo lại nếu script bị inject nhiều lần
  if (window.vocabSaverInitialized) return;
  window.vocabSaverInitialized = true;

  // CSS dành cho Shadow DOM để cô lập hoàn toàn giao diện, tránh bị ảnh hưởng bởi CSS của trang web
  const shadowStyles = `
    :host {
      --primary: #4f46e5;
      --primary-hover: #4338ca;
      --bg: #ffffff;
      --text: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --success: #10b981;
      --error: #ef4444;
      --shadow: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.08);
      
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 14px;
      line-height: 1.5;
      color: var(--text);
    }

    /* Floating Trigger Button */
    .vocab-trigger {
      position: fixed;
      z-index: 2147483647;
      pointer-events: auto;
      background: #ffffff;
      border: 2px solid var(--primary);
      border-radius: 50%;
      width: 38px;
      height: 38px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 4px 10px rgba(79, 70, 229, 0.2);
      transition: transform 0.2s, border-color 0.2s;
      padding: 0;
      overflow: hidden;
    }
    
    .vocab-trigger:hover {
      transform: scale(1.15);
      border-color: var(--primary-hover);
    }
    
    .vocab-trigger img {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      object-fit: cover;
      display: block;
    }

    /* Tooltip Panel */
    .vocab-tooltip {
      position: fixed;
      z-index: 2147483647;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      width: 280px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: 10px;
      box-sizing: border-box;
      opacity: 0;
      transform: translateY(10px) scale(0.95);
      transition: opacity 0.2s, transform 0.2s;
      pointer-events: none;
    }

    .vocab-tooltip.active {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: auto;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      padding-bottom: 6px;
    }

    .title {
      font-weight: 600;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--primary);
    }

    .close-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 2px;
      display: flex;
      align-items: center;
      border-radius: 4px;
    }

    .close-btn:hover {
      background: var(--border);
      color: var(--text);
    }

    .close-btn svg {
      width: 14px;
      height: 14px;
      fill: currentColor;
    }

    .content-body {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .word-row {
      font-weight: bold;
      font-size: 16px;
      color: var(--text);
    }

    .translation-row {
      font-size: 14px;
      color: var(--primary);
      background: rgba(79, 70, 229, 0.06);
      padding: 8px 12px;
      border-radius: 6px;
      border-left: 3px solid var(--primary);
      font-weight: 500;
    }

    .context-row {
      font-size: 12px;
      color: var(--text-muted);
      font-style: italic;
      background: #f8fafc;
      padding: 8px;
      border-radius: 6px;
      max-height: 60px;
      overflow-y: auto;
      border: 1px solid var(--border);
      outline: none;
    }

    .context-row:focus {
      border-color: var(--primary);
      background: #f1f5f9;
    }

    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 4px;
    }

    .btn {
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .btn-save {
      background: var(--primary);
      color: white;
      width: 100%;
      justify-content: center;
    }

    .btn-save:hover {
      background: var(--primary-hover);
    }

    .btn-save:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .btn-save.success {
      background: var(--success);
    }

    .btn-save.error {
      background: var(--error);
    }

    /* Spinner Loading */
    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top-color: white;
      animation: spin 0.8s linear infinite;
      display: inline-block;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `;

  // Tạo thẻ chứa extension và đưa vào body của trang web
  const container = document.createElement('div');
  container.id = 'vocabsaver-root';
  container.style.position = 'fixed';
  container.style.top = '0';
  container.style.left = '0';
  container.style.width = '0';
  container.style.height = '0';
  container.style.overflow = 'visible';
  container.style.zIndex = '2147483647';
  container.style.pointerEvents = 'none';
  // Append to documentElement (luôn tồn tại) thay vì body (có thể chưa sẵn sàng)
  (document.body || document.documentElement).appendChild(container);

  // Tạo Shadow DOM
  const shadow = container.attachShadow({ mode: 'open' });

  // Inject CSS style
  const styleEl = document.createElement('style');
  styleEl.textContent = shadowStyles;
  shadow.appendChild(styleEl);

  // Tạo nút Trigger (sử dụng icon hình mèo mũ nồi của người dùng làm logo to hơn)
  const trigger = document.createElement('button');
  trigger.className = 'vocab-trigger';
  trigger.style.display = 'none';
  trigger.innerHTML = `
    <img src="${chrome.runtime.getURL('icons/icon48.png')}" alt="VocabSaver Logo">
  `;
  shadow.appendChild(trigger);

  // Tạo bảng Tooltip Dịch
  const tooltip = document.createElement('div');
  tooltip.className = 'vocab-tooltip';
  tooltip.innerHTML = `
    <div class="header">
      <span class="title">VocabSaver</span>
      <button class="close-btn">
        <svg viewBox="0 0 24 24">
          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
      </button>
    </div>
    <div class="content-body">
      <div class="word-row" id="vocab-word">Word</div>
      <div class="translation-row" id="vocab-translation">Translating...</div>
      <div class="context-row" id="vocab-context" contenteditable="true" title="Click to edit context before saving">Context</div>
      <button class="btn btn-save" id="vocab-save-btn">Save word</button>
    </div>
  `;
  shadow.appendChild(tooltip);

  // Selector các element trong Shadow DOM
  const wordEl = shadow.querySelector('#vocab-word');
  const translationEl = shadow.querySelector('#vocab-translation');
  const contextEl = shadow.querySelector('#vocab-context');
  const saveBtn = shadow.querySelector('#vocab-save-btn');
  const closeBtn = shadow.querySelector('.close-btn');

  let currentSelectionInfo = null;

  // Lắng nghe sự kiện bôi đen chữ
  // Dùng capture phase (true) để chạy TRƯỚC khi trang web có thể chặn sự kiện
  document.addEventListener('mouseup', handleTextSelection, true);
  // Fallback: pointerup hoạt động trên một số trang chặn mouseup
  document.addEventListener('pointerup', handleTextSelection, true);

  // Lắng nghe sự kiện click ngoài để ẩn các bảng điều khiển
  document.addEventListener('mousedown', function(e) {
    // Nếu click ra ngoài container chứa root
    if (e.target !== container) {
      // Đợi một chút để xem có click trúng nút trigger không
      setTimeout(() => {
        if (trigger.style.display !== 'none' && !isClickInsideShadow(e)) {
          hideTrigger();
        }
        if (tooltip.classList.contains('active') && !isClickInsideShadow(e)) {
          hideTooltip();
        }
      }, 100);
    }
  }, true);

  // Kiểm tra click có nằm trong Shadow DOM không
  function isClickInsideShadow(e) {
    return e.target === container || (e.composedPath && e.composedPath().includes(container));
  }

  function handleTextSelection(e) {
    // Kiểm tra xem extension có đang được bật hay không
    chrome.storage.local.get(['extensionEnabled'], function(result) {
      if (result.extensionEnabled === false) {
        // Vẫn cho phép ẩn trigger nếu đang hiển thị và người dùng click ngoài
        if (trigger.style.display !== 'none' && !isClickInsideShadow(e)) {
          hideTrigger();
        }
        return;
      }

      const selection = window.getSelection();
      const selectedText = selection.toString().trim();

      // Chỉ dịch từ có độ dài hợp lý (từ 1 đến 150 ký tự) để tránh đoạn văn dài
      if (selectedText.length > 0 && selectedText.length <= 150) {
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        // Nếu rect có kích thước thực tế
        if (rect.width > 0 && rect.height > 0) {
          // Tự động nhận diện xem có đủ chỗ hiển thị ở phía dưới không
          const tooltipHeight = 220; // Chiều cao ước lượng của tooltip
          const fitsBelow = (rect.bottom + tooltipHeight) < window.innerHeight;
          
          // Dùng viewport coords trực tiếp (fixed positioning không cần scrollY/scrollX)
          let triggerY;
          if (fitsBelow) {
            triggerY = rect.bottom + 5;
          } else {
            triggerY = rect.top - 44;
          }

          // Lưu thông tin từ vựng tạm thời
          currentSelectionInfo = {
            word: selectedText,
            context: getContextSentence(selection),
            url: window.location.href,
            fitsBelow: fitsBelow,
            rect: {
              left: rect.left,
              right: rect.right,
              top: rect.top,
              bottom: rect.bottom,
              width: rect.width,
              height: rect.height
            }
          };

          showTrigger(rect.left + rect.width / 2, triggerY);
        }
      } else {
        // Nếu click nơi khác hoặc bỏ chọn, ẩn nút trigger (nhưng không ẩn tooltip nếu đang mở)
        if (trigger.style.display !== 'none' && !isClickInsideShadow(e)) {
          hideTrigger();
        }
      }
    });
  }

  function showTrigger(x, y) {
    trigger.style.left = `${x - 19}px`; // Căn giữa theo trục x (chiều rộng nút mèo 38px)
    trigger.style.top = `${y}px`;
    trigger.style.display = 'flex';
  }

  function hideTrigger() {
    trigger.style.display = 'none';
  }

  function showTooltip(rect, fitsBelow) {
    // Dùng viewport coords trực tiếp (fixed positioning)
    const width = 280;
    let left = (rect.left + rect.width / 2) - width / 2;
    if (left < 10) left = 10;
    if (left + width > window.innerWidth - 10) {
      left = window.innerWidth - width - 10;
    }

    let top;
    if (fitsBelow) {
      top = rect.bottom + 5;
    } else {
      top = rect.top - 215;
      if (top < 10) {
        top = 10;
      }
    }

    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
    tooltip.classList.add('active');
  }

  function hideTooltip() {
    tooltip.classList.remove('active');
    // Trả lại trạng thái nút save
    saveBtn.className = 'btn btn-save';
    saveBtn.innerHTML = 'Save word';
    saveBtn.disabled = false;
  }

  // Click nút Trigger để thực hiện dịch
  trigger.addEventListener('click', function(e) {
    e.stopPropagation();
    if (!currentSelectionInfo) return;

    hideTrigger();
    showTooltip(currentSelectionInfo.rect, currentSelectionInfo.fitsBelow);

    // Điền dữ liệu tạm thời
    wordEl.textContent = currentSelectionInfo.word;
    translationEl.innerHTML = '<span class="spinner"></span> Translating...';
    contextEl.textContent = currentSelectionInfo.context || 'Context not found';
    
    saveBtn.disabled = true;

    // Gửi tin nhắn đến background service worker để gọi API dịch
    chrome.runtime.sendMessage({
      action: 'translate',
      text: currentSelectionInfo.word
    }, function(response) {
      if (response && response.success) {
        translationEl.textContent = response.translation;
        currentSelectionInfo.translation = response.translation;
        saveBtn.disabled = false;
      } else {
        translationEl.textContent = 'Translation failed!';
        saveBtn.disabled = true;
        console.error('Translation error:', response ? response.error : 'No response');
      }
    });
  });

  // Click lưu từ vựng
  saveBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    if (!currentSelectionInfo || !currentSelectionInfo.translation) return;

    // Cập nhật ngữ cảnh nếu người dùng sửa đổi trực tiếp trên tooltip
    currentSelectionInfo.context = contextEl.textContent.trim();

    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner"></span> Saving...';

    chrome.runtime.sendMessage({
      action: 'save_vocab',
      data: currentSelectionInfo
    }, function(response) {
      if (response && response.success) {
        saveBtn.className = 'btn btn-save success';
        saveBtn.textContent = response.result.notion ? 'Saved to Notion & Local!' : 'Saved locally!';
        
        // Tự động đóng tooltip sau 1.5 giây
        setTimeout(() => {
          hideTooltip();
        }, 1500);
      } else {
        saveBtn.className = 'btn btn-save error';
        saveBtn.textContent = 'Retry (Error)';
        saveBtn.disabled = false;
        alert(response ? response.error : 'Connection error with background script!');
      }
    });
  });

  // Click đóng tooltip
  closeBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    hideTooltip();
  });

  // Hàm trích xuất câu chứa từ bôi đen để làm ngữ cảnh
  function getContextSentence(selection) {
    if (!selection.rangeCount) return '';
    const range = selection.getRangeAt(0);
    const container = range.startContainer;
    
    // Tìm thẻ cha gần nhất (p, span, div, li, etc.)
    let parent = container.parentElement;
    if (!parent) return '';
    
    const text = parent.innerText || parent.textContent || '';
    const selectedText = selection.toString().trim();
    
    // Tách văn bản thành các câu dựa vào các dấu . ! ?
    const sentences = text.split(/(?<=[.!?])\s+/);
    for (let sentence of sentences) {
      if (sentence.includes(selectedText)) {
        return sentence.trim();
      }
    }
    
    // Trả về trích dẫn ngắn xung quanh từ vựng nếu không tách được câu
    const fullText = container.textContent || '';
    const startPos = Math.max(0, range.startOffset - 80);
    const endPos = Math.min(fullText.length, range.endOffset + 80);
    let excerpt = fullText.slice(startPos, endPos).trim();
    if (startPos > 0) excerpt = '...' + excerpt;
    if (endPos < fullText.length) excerpt = excerpt + '...';
    return excerpt;
  }

})();
