document.addEventListener('DOMContentLoaded', () => {
  // Navigation Tabs
  const tabDashboard = document.getElementById('tab-dashboard');
  const tabSettings = document.getElementById('tab-settings');
  const secDashboard = document.getElementById('section-dashboard');
  const secSettings = document.getElementById('section-settings');

  // Input & UI Elements
  const searchInput = document.getElementById('search-vocab');
  const vocabTotal = document.getElementById('vocab-total');
  const tbody = document.getElementById('vocab-list-tbody');
  const noVocabState = document.getElementById('no-vocab-state');

  // Notion Settings Elements
  const notionEnabled = document.getElementById('notion-enabled');
  const notionFields = document.getElementById('notion-fields');
  const notionToken = document.getElementById('notion-token');
  const notionDbId = document.getElementById('notion-db-id');
  const configForm = document.getElementById('notion-config-form');

  // Translation Settings Elements
  const translationProvider = document.getElementById('translation-provider');
  const deeplFields = document.getElementById('deepl-fields');
  const deeplToken = document.getElementById('deepl-token');
  const translationForm = document.getElementById('translation-config-form');
  const btnTestDeepl = document.getElementById('btn-test-deepl');
  const translationStatusMsg = document.getElementById('translation-status-msg');

  // Gemini AI Settings Elements
  const geminiEnabled = document.getElementById('gemini-enabled');
  const geminiFields = document.getElementById('gemini-fields');
  const geminiToken = document.getElementById('gemini-token');
  const geminiForm = document.getElementById('gemini-config-form');
  const btnTestGemini = document.getElementById('btn-test-gemini');
  const geminiStatusMsg = document.getElementById('gemini-status-msg');
  const aiEndpoint = document.getElementById('ai-endpoint');
  const aiModel = document.getElementById('ai-model');
  const debugLogsContainer = document.getElementById('debug-logs-container');
  const btnRefreshLogs = document.getElementById('btn-refresh-logs');

  // Action Buttons
  const btnExport = document.getElementById('btn-export-csv');
  const btnClearAll = document.getElementById('btn-clear-all');
  const btnTestConn = document.getElementById('btn-test-connection');
  const connectionStatusMsg = document.getElementById('connection-status-msg');

  let localVocabList = [];

  // ================= Navigation Routing (Hash-based) =================
  function switchTab(tabId) {
    if (tabId === 'settings') {
      tabDashboard.classList.remove('active');
      tabSettings.classList.add('active');
      secDashboard.classList.remove('active');
      secSettings.classList.add('active');
    } else {
      tabSettings.classList.remove('active');
      tabDashboard.classList.add('active');
      secSettings.classList.remove('active');
      secDashboard.classList.add('active');
      loadVocabList(); // Reload vocab when going to dashboard
    }
  }

  function handleHashRoute() {
    const hash = window.location.hash;
    if (hash === '#settings') {
      switchTab('settings');
    } else {
      switchTab('dashboard');
    }
  }

  // Listen to hash changes in the URL
  window.addEventListener('hashchange', handleHashRoute);

  // Run initial route checking
  handleHashRoute();

  // ================= Notion Configuration =================
  // Toggle Visibility of settings input fields based on Notion switch status
  notionEnabled.addEventListener('change', () => {
    toggleNotionFields(notionEnabled.checked);
  });

  function toggleNotionFields(enabled) {
    if (enabled) {
      notionFields.classList.add('visible');
      notionToken.required = true;
      notionDbId.required = true;
    } else {
      notionFields.classList.remove('visible');
      notionToken.required = false;
      notionDbId.required = false;
    }
  }

  // Load saved settings on load
  chrome.storage.local.get([
    'notionEnabled', 'notionToken', 'notionDbId',
    'geminiEnabled', 'geminiToken', 'aiEndpoint', 'aiModel',
    'translationProvider', 'deeplToken'
  ], (settings) => {
    // Translation Load
    translationProvider.value = settings.translationProvider || 'google';
    toggleDeeplFields(settings.translationProvider === 'deepl');
    deeplToken.value = settings.deeplToken || '';

    // Notion Load
    notionEnabled.checked = !!settings.notionEnabled;
    toggleNotionFields(!!settings.notionEnabled);
    notionToken.value = settings.notionToken || '';
    notionDbId.value = settings.notionDbId || '';

    // Gemini Load
    geminiEnabled.checked = !!settings.geminiEnabled;
    toggleGeminiFields(!!settings.geminiEnabled);
    geminiToken.value = settings.geminiToken || '';
    aiEndpoint.value = settings.aiEndpoint || 'https://openrouter.ai/api/v1';
    aiModel.value = settings.aiModel || 'nvidia/llama-3.1-nemotron-70b-instruct:free';
    
    // Load Logs
    loadDebugLogs();
  });

  // Toggle visibility of DeepL fields
  translationProvider.addEventListener('change', () => {
    toggleDeeplFields(translationProvider.value === 'deepl');
  });

  function toggleDeeplFields(visible) {
    if (visible) {
      deeplFields.classList.add('visible');
      deeplToken.required = true;
    } else {
      deeplFields.classList.remove('visible');
      deeplToken.required = false;
    }
  }

  // Save Translation settings
  translationForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const settings = {
      translationProvider: translationProvider.value,
      deeplToken: deeplToken.value.trim()
    };
    chrome.storage.local.set(settings, () => {
      showStatusMessage(translationStatusMsg, 'success', 'Translation settings saved successfully!');
    });
  });

  // Test DeepL Connection
  btnTestDeepl.addEventListener('click', () => {
    const token = deeplToken.value.trim();
    if (!token) {
      showStatusMessage(translationStatusMsg, 'error', 'Please enter DeepL Auth Key to test!');
      return;
    }

    btnTestDeepl.disabled = true;
    btnTestDeepl.textContent = 'Testing...';
    showStatusMessage(translationStatusMsg, '', '');

    chrome.runtime.sendMessage({
      action: 'test_deepl',
      token: token
    }, (response) => {
      btnTestDeepl.disabled = false;
      btnTestDeepl.textContent = 'Test Translation';

      if (response && response.success) {
        showStatusMessage(translationStatusMsg, 'success', 'DeepL connection successful! Ready to translate.');
      } else {
        const errMsg = response ? response.error : 'No response from background worker.';
        showStatusMessage(translationStatusMsg, 'error', `DeepL test failed: ${errMsg}`);
      }
    });
  });

  function loadDebugLogs() {
    chrome.storage.local.get('debugLogs', (data) => {
      const logs = data.debugLogs || [];
      if (logs.length === 0) {
        debugLogsContainer.textContent = 'No logs recorded yet. Try saving a word first.';
      } else {
        debugLogsContainer.textContent = logs.join('\n');
      }
    });
  }

  btnRefreshLogs.addEventListener('click', loadDebugLogs);

  // Save settings in local storage
  configForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const settings = {
      notionEnabled: notionEnabled.checked,
      notionToken: notionToken.value.trim(),
      notionDbId: notionDbId.value.trim()
    };

    chrome.storage.local.set(settings, () => {
      showStatusMessage(connectionStatusMsg, 'success', 'Notion settings saved successfully!');
    });
  });

  // Save Gemini settings in local storage
  geminiForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const settings = {
      geminiEnabled: geminiEnabled.checked,
      geminiToken: geminiToken.value.trim(),
      aiEndpoint: aiEndpoint.value.trim(),
      aiModel: aiModel.value.trim()
    };

    chrome.storage.local.set(settings, () => {
      showStatusMessage(geminiStatusMsg, 'success', 'AI settings saved successfully!');
    });
  });

  // Test integration connection to Notion
  btnTestConn.addEventListener('click', () => {
    const token = notionToken.value.trim();
    const dbId = notionDbId.value.trim();

    if (!token || !dbId) {
      showStatusMessage(connectionStatusMsg, 'error', 'Please fill in both Token and Database ID to test!');
      return;
    }

    btnTestConn.disabled = true;
    btnTestConn.textContent = 'Testing connection...';
    showStatusMessage(connectionStatusMsg, '', ''); // Clear previous status

    chrome.runtime.sendMessage({
      action: 'test_notion',
      token: token,
      dbId: dbId
    }, (response) => {
      btnTestConn.disabled = false;
      btnTestConn.textContent = 'Test Connection';

      if (response && response.success) {
        showStatusMessage(connectionStatusMsg, 'success', 'Connection successful! Database verified.');
      } else {
        const errMsg = response ? response.error : 'No response from extension background service worker.';
        showStatusMessage(connectionStatusMsg, 'error', `Connection failed: ${errMsg}`);
      }
    });
  });

  // Toggle Visibility of Gemini fields
  geminiEnabled.addEventListener('change', () => {
    toggleGeminiFields(geminiEnabled.checked);
  });

  function toggleGeminiFields(enabled) {
    if (enabled) {
      geminiFields.classList.add('visible');
      geminiToken.required = true;
      aiEndpoint.required = true;
      aiModel.required = true;
    } else {
      geminiFields.classList.remove('visible');
      geminiToken.required = false;
      aiEndpoint.required = false;
      aiModel.required = false;
    }
  }

  // Test connection to Gemini API
  btnTestGemini.addEventListener('click', () => {
    const token = geminiToken.value.trim();
    const endpoint = aiEndpoint.value.trim();
    const model = aiModel.value.trim();

    if (!token || !endpoint || !model) {
      showStatusMessage(geminiStatusMsg, 'error', 'Please enter API Key, Endpoint, and Model to test!');
      return;
    }

    btnTestGemini.disabled = true;
    btnTestGemini.textContent = 'Testing AI...';
    showStatusMessage(geminiStatusMsg, '', '');

    chrome.runtime.sendMessage({
      action: 'test_gemini',
      token: token,
      endpoint: endpoint,
      model: model
    }, (response) => {
      btnTestGemini.disabled = false;
      btnTestGemini.textContent = 'Test AI Connection';

      if (response && response.success) {
        showStatusMessage(geminiStatusMsg, 'success', 'AI connection successful! Gemini is ready.');
      } else {
        const errMsg = response ? response.error : 'No response from background service worker.';
        showStatusMessage(geminiStatusMsg, 'error', `AI connection failed: ${errMsg}`);
      }
    });
  });

  function showStatusMessage(element, type, message) {
    element.className = 'status-msg';
    if (!type) {
      element.style.display = 'none';
      return;
    }
    element.classList.add(type);
    element.textContent = message;
    element.style.display = 'block';
  }

  // ================= Vocabulary Management =================
  function loadVocabList() {
    chrome.storage.local.get(['localVocabList'], (result) => {
      localVocabList = result.localVocabList || [];
      renderVocabTable(localVocabList);
    });
  }

  function renderVocabTable(list) {
    tbody.innerHTML = '';
    vocabTotal.textContent = `${list.length} word${list.length !== 1 ? 's' : ''} saved`;

    if (list.length === 0) {
      noVocabState.style.display = 'flex';
      return;
    } else {
      noVocabState.style.display = 'none';
    }

    list.forEach(item => {
      const tr = document.createElement('tr');
      tr.id = `row-${item.id}`;

      // Source URL extraction
      let sourceLink = '';
      if (item.url) {
        try {
          const urlObj = new URL(item.url);
          sourceLink = `<a href="${item.url}" target="_blank" class="vocab-source" title="${item.url}">${urlObj.hostname}</a>`;
        } catch (e) {
          sourceLink = `<a href="${item.url}" target="_blank" class="vocab-source" title="${item.url}">Link</a>`;
        }
      } else {
        sourceLink = '<span class="text-secondary">-</span>';
      }

      tr.innerHTML = `
        <td class="vocab-word">${escapeHtml(item.word)}</td>
        <td class="vocab-trans">${escapeHtml(item.translation)}</td>
        <td class="vocab-context" title="${escapeHtml(item.context)}">${escapeHtml(item.context || '-')}</td>
        <td>${sourceLink}</td>
        <td>
          <button class="action-delete-btn" data-id="${item.id}" title="Delete word">
            <svg viewBox="0 0 24 24">
              <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
            </svg>
          </button>
        </td>
      `;

      tr.querySelector('.action-delete-btn').addEventListener('click', function() {
        const idToDelete = this.getAttribute('data-id');
        deleteVocabItem(idToDelete);
      });

      tbody.appendChild(tr);
    });
  }

  function deleteVocabItem(id) {
    localVocabList = localVocabList.filter(item => item.id !== id);
    chrome.storage.local.set({ localVocabList: localVocabList }, () => {
      const row = document.getElementById(`row-${id}`);
      if (row) {
        row.style.transition = 'all 0.2s ease-out';
        row.style.opacity = '0';
        row.style.transform = 'translateX(-12px)';
        setTimeout(() => {
          row.remove();
          vocabTotal.textContent = `${localVocabList.length} word${localVocabList.length !== 1 ? 's' : ''} saved`;
          if (localVocabList.length === 0) {
            noVocabState.style.display = 'flex';
          }
        }, 200);
      }
    });
  }

  // Filter word list based on search bar
  searchInput.addEventListener('input', () => {
    const query = searchInput.value.toLowerCase().trim();
    if (!query) {
      renderVocabTable(localVocabList);
      return;
    }

    const filtered = localVocabList.filter(item => {
      return item.word.toLowerCase().includes(query) || 
             item.translation.toLowerCase().includes(query) ||
             (item.context && item.context.toLowerCase().includes(query));
    });
    
    renderVocabTable(filtered);
    vocabTotal.textContent = `${filtered.length} result${filtered.length !== 1 ? 's' : ''} found`;
  });

  // Clear all words
  btnClearAll.addEventListener('click', () => {
    if (confirm('Are you sure you want to delete all saved vocabulary words? This action cannot be undone.')) {
      chrome.storage.local.set({ localVocabList: [] }, () => {
        localVocabList = [];
        renderVocabTable([]);
      });
    }
  });

  // Export to CSV format
  btnExport.addEventListener('click', () => {
    if (localVocabList.length === 0) {
      alert('Your word book is empty!');
      return;
    }

    let csvContent = '\uFEFF'; // UTF-8 BOM for Excel support
    csvContent += 'Word,Translation,Context,Source Link,Save Date\n';

    localVocabList.forEach(item => {
      const row = [
        item.word,
        item.translation,
        item.context || '',
        item.url || '',
        item.date ? new Date(item.date).toLocaleString() : ''
      ].map(field => `"${field.replace(/"/g, '""')}"`);

      csvContent += row.join(',') + '\n';
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `VocabSaver_WordBook_${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });

  function escapeHtml(text) {
    if (!text) return '';
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
  }

  // Load list initially
  loadVocabList();
});
