document.addEventListener('DOMContentLoaded', () => {
  const extensionToggle = document.getElementById('extension-toggle');
  const notionStatus = document.getElementById('notion-status');
  const btnOpenOptions = document.getElementById('btn-open-options');

  // Load cài đặt hiện tại
  chrome.storage.local.get(['extensionEnabled', 'notionEnabled'], (result) => {
    // Mặc định là true nếu chưa có cấu hình
    extensionToggle.checked = result.extensionEnabled !== false;
    
    if (result.notionEnabled) {
      notionStatus.textContent = 'Notion On';
      notionStatus.className = 'status-badge connected';
    } else {
      notionStatus.textContent = 'Notion Off';
      notionStatus.className = 'status-badge';
    }
  });

  // Lưu trạng thái bật/tắt extension
  extensionToggle.addEventListener('change', () => {
    chrome.storage.local.set({ extensionEnabled: extensionToggle.checked });
  });

  // Mở trang Options quản lý từ vựng
  btnOpenOptions.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
});
