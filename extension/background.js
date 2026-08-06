// Logger debug lưu vào storage để theo dõi lỗi chạy ngầm
async function logDebug(message) {
  console.log(message);
  try {
    const data = await chrome.storage.local.get('debugLogs');
    const logs = data.debugLogs || [];
    logs.unshift(`[${new Date().toLocaleTimeString()}] ${message}`);
    if (logs.length > 50) logs.pop();
    await chrome.storage.local.set({ debugLogs: logs });
  } catch (e) {}
}

// Lắng nghe các tin nhắn gửi từ Content Script hoặc Options Page
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'translate') {
    translateText(message.text)
      .then(translatedText => sendResponse({ success: true, translation: translatedText }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Giữ kết nối async cho sendResponse
  }

  if (message.action === 'save_vocab') {
    saveVocabulary(message.data)
      .then(result => sendResponse({ success: true, result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (message.action === 'test_notion') {
    testNotionConnection(message.token, message.dbId)
      .then(() => sendResponse({ success: true }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (message.action === 'test_gemini') {
    testGeminiConnection(message.token, message.endpoint, message.model)
      .then(() => sendResponse({ success: true }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (message.action === 'test_deepl') {
    testDeepLConnection(message.token)
      .then(() => sendResponse({ success: true }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
});

// Hàm dịch từ vựng (Google hoặc DeepL)
async function translateText(text) {
  const settings = await chrome.storage.local.get(['translationProvider', 'deeplToken']);
  const provider = settings.translationProvider || 'google';
  const deeplToken = settings.deeplToken || '';

  if (provider === 'deepl' && deeplToken) {
    try {
      const hasVietnameseAccents = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]/i.test(text);
      if (hasVietnameseAccents) {
        const res = await fetchDeepLTranslation(text, deeplToken, 'EN');
        return res.text;
      }
      
      // Giả định dịch sang VI trước
      const res = await fetchDeepLTranslation(text, deeplToken, 'VI');
      
      // Nếu DeepL phát hiện đây là tiếng Việt (kể cả không dấu)
      if (res.detectedSource === 'vi') {
        const fallbackRes = await fetchDeepLTranslation(text, deeplToken, 'EN');
        return fallbackRes.text;
      }
      
      return res.text;
    } catch (e) {
      console.error('DeepL translation failed, falling back to Google Translate:', e);
      // Fallback sang Google Translate nếu DeepL bị lỗi
    }
  }

  // Mặc định: Dịch bằng Google Translate
  const hasVietnameseAccents = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]/.test(text);
  
  if (hasVietnameseAccents) {
    return await fetchTranslation(text, 'vi', 'en');
  }

  const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=vi&dt=t&q=${encodeURIComponent(text)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to connect to Google Translate API');
  }
  
  const data = await response.json();
  const detectedLang = data[2]; // Ngôn ngữ mà Google phát hiện được

  // Nếu Google phát hiện đây là tiếng Việt (kể cả không dấu)
  if (detectedLang === 'vi') {
    return await fetchTranslation(text, 'vi', 'en');
  }

  // Trả về kết quả dịch sang tiếng Việt
  let translatedText = '';
  if (data && data[0]) {
    for (let i = 0; i < data[0].length; i++) {
      if (data[0][i][0]) {
        translatedText += data[0][i][0];
      }
    }
  }
  return translatedText.trim() || 'Translation empty';
}

// Hàm phụ thực hiện gọi dịch theo ngôn ngữ chỉ định của Google Translate
async function fetchTranslation(text, sourceLang, targetLang) {
  const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sourceLang}&tl=${targetLang}&dt=t&q=${encodeURIComponent(text)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to connect to Google Translate API');
  }
  
  const data = await response.json();
  let translatedText = '';
  if (data && data[0]) {
    for (let i = 0; i < data[0].length; i++) {
      if (data[0][i][0]) {
        translatedText += data[0][i][0];
      }
    }
  }
  return translatedText.trim() || 'Translation empty';
}

// Hàm dịch bằng DeepL API
async function fetchDeepLTranslation(text, apiKey, targetLang) {
  const isFreeKey = apiKey.endsWith(':fx');
  const url = isFreeKey ? 'https://api-free.deepl.com/v2/translate' : 'https://api.deepl.com/v2/translate';
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `DeepL-Auth-Key ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text: [text],
      target_lang: targetLang.toUpperCase()
    })
  });
  
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || `DeepL API HTTP ${response.status}`);
  }
  
  const data = await response.json();
  if (data.translations && data.translations.length > 0) {
    return {
      text: data.translations[0].text,
      detectedSource: data.translations[0].detected_source_language.toLowerCase()
    };
  }
  throw new Error('Empty translation from DeepL');
}

// Hàm kiểm tra kết nối tới DeepL API
async function testDeepLConnection(apiKey) {
  const isFreeKey = apiKey.endsWith(':fx');
  const url = isFreeKey ? 'https://api-free.deepl.com/v2/translate' : 'https://api.deepl.com/v2/translate';
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `DeepL-Auth-Key ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text: ['Hello'],
      target_lang: 'DE'
    })
  });
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || `DeepL API HTTP ${response.status}`);
  }
  return true;
}

// Hàm lưu từ vựng (Notion hoặc Cục bộ)
async function saveVocabulary(vocabData) {
  await logDebug(`[LƯU] Bắt đầu lưu từ: "${vocabData.word}"`);
  // Lấy cấu hình lưu trữ bao gồm cấu hình AI
  const settings = await chrome.storage.local.get([
    'notionEnabled', 'notionToken', 'notionDbId', 
    'geminiEnabled', 'geminiToken', 'aiEndpoint', 'aiModel', 'localVocabList'
  ]);
  
  const { notionEnabled, notionToken, notionDbId, geminiEnabled, geminiToken, aiEndpoint, aiModel } = settings;
  await logDebug(`[CÀI ĐẶT] Tải được: notionEnabled=${notionEnabled}, geminiEnabled=${geminiEnabled}, geminiToken=${geminiToken ? 'Có' : 'Không'}, endpoint=${aiEndpoint}, model=${aiModel}`);

  const vocabItem = {
    id: Date.now().toString(),
    word: vocabData.word.trim(),
    translation: vocabData.translation.trim(),
    context: (vocabData.context || '').trim(),
    url: vocabData.url || '',
    date: new Date().toISOString()
  };

  let savedStatus = { notion: false, local: false };
  let notionPageId = null;

  // 1. Lưu vào Notion (tạo trang nhanh trước, KHÔNG truyền key AI để tránh delay)
  if (notionEnabled && notionToken && notionDbId) {
    try {
      const hasAIBackground = !!(geminiEnabled && geminiToken);
      await logDebug(`[NOTION] Đang gọi saveToNotion (hasAIBackground=${hasAIBackground})...`);
      const notionPage = await saveToNotion(vocabItem, notionToken, notionDbId, hasAIBackground);
      savedStatus.notion = true;
      notionPageId = notionPage.id;
      await logDebug(`[NOTION] Đã tạo thành công trang Notion. PageID = ${notionPageId}`);
    } catch (error) {
      await logDebug(`[LỖI] Tạo trang Notion thất bại: ${error.message}`);
      throw new Error(`Lỗi lưu Notion: ${error.message}`);
    }
  } else {
    await logDebug(`[NOTION] Notion Sync đang TẮT hoặc thiếu cấu hình.`);
  }

  // 2. Luôn lưu một bản sao cục bộ để dự phòng hoặc làm kho lưu trữ chính
  let localList = settings.localVocabList || [];
  localList.unshift(vocabItem); // Đưa lên đầu danh sách
  
  // Giới hạn lưu trữ cục bộ tối đa 1000 từ để tránh tràn bộ nhớ storage
  if (localList.length > 1000) {
    localList = localList.slice(0, 1000);
  }
  
  await chrome.storage.local.set({ localVocabList: localList });
  savedStatus.local = true;
  await logDebug(`[CỤC BỘ] Đã lưu cục bộ thành công.`);

  // 3. CHẠY BẤT ĐỒNG BỘ: Gọi AI phân tích và chèn nội dung vào Notion sau khi đã đóng tooltip
  if (notionEnabled && notionPageId && geminiEnabled && geminiToken) {
    await logDebug(`[AI] Kích hoạt tiến trình chạy ngầm runBackgroundAIAnalysis...`);
    runBackgroundAIAnalysis(notionPageId, vocabItem.word, notionToken, geminiToken, aiEndpoint, aiModel)
      .catch(async err => {
        await logDebug(`[LỖI PROGRESS] Chạy ngầm AI lỗi: ${err.message}`);
      });
  } else {
    await logDebug(`[AI] Bỏ qua chạy ngầm AI (notionPageId=${notionPageId}, geminiEnabled=${geminiEnabled}, geminiToken=${geminiToken ? 'Có' : 'Không'})`);
  }

  return savedStatus;
}

// Hàm thực hiện POST API lên Notion để tạo trang trống nhanh (0.1s)
async function saveToNotion(item, token, databaseId, hasAIBackground) {
  const url = 'https://api.notion.com/v1/pages';

  const requestBody = {
    parent: { database_id: databaseId },
    properties: {
      'Từ vựng': {
        title: [
          {
            text: {
              content: item.word
            }
          }
        ]
      },
      'Dịch nghĩa': {
        rich_text: [
          {
            text: {
              content: item.translation
            }
          }
        ]
      },
      'Ngữ cảnh': {
        rich_text: [
          {
            text: {
              content: item.context
            }
          }
        ]
      },
      'Nguồn': {
        url: item.url
      }
    }
  };

  // Nếu KHÔNG sử dụng AI của extension, bảo Notion áp dụng template mặc định
  if (!hasAIBackground) {
    requestBody.template = {
      type: "default"
    };
  }

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Notion-Version': '2022-06-28'
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || `HTTP ${response.status}`);
  }

  return await response.json();
}

// Hàm kiểm tra kết nối tới Notion Database
async function testNotionConnection(token, databaseId) {
  const url = `https://api.notion.com/v1/databases/${databaseId}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Notion-Version': '2022-06-28'
    }
  });

  if (!response.ok) {
    let errorMsg = `HTTP ${response.status}`;
    try {
      const errorData = await response.json();
      errorMsg = errorData.message || errorMsg;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  return true;
}

// Hàm kiểm tra kết nối tới Gemini hoặc OpenRouter API
async function testGeminiConnection(apiKey, endpoint, model) {
  const apiEndpoint = (endpoint || 'https://openrouter.ai/api/v1').replace(/\/$/, '');
  const url = `${apiEndpoint}/chat/completions`;
  const modelName = model || 'nvidia/llama-3.1-nemotron-70b-instruct:free';
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: modelName,
      messages: [{ role: 'user', content: 'Respond with OK.' }]
    })
  });
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || `HTTP ${response.status}`);
  }
  return true;
}

// Hàm gọi API AI để phân tích từ vựng nâng cao (hỗ trợ OpenRouter / OpenAI format)
async function getGeminiAnalysis(word, apiKey, endpoint, model) {
  const apiEndpoint = (endpoint || 'https://openrouter.ai/api/v1').replace(/\/$/, '');
  const url = `${apiEndpoint}/chat/completions`;
  const modelName = model || 'nvidia/llama-3.1-nemotron-70b-instruct:free';
  
  await logDebug(`[AI API] Gọi API: ${url}, Model: ${modelName}`);

  const prompt = `Hãy đóng vai một chuyên gia ngôn ngữ học. Phân tích chi tiết từ vựng: "${word}".
Mục đích của tôi là lưu kết quả này vào ứng dụng Ghi chú (Notes), nên nội dung cần được trình bày thật đẹp, trực quan, ngắt dòng rõ ràng, KHÔNG để dòng trống thừa thãi (không chèn 2 dấu xuống dòng liên tiếp) và sử dụng emoji phù hợp.
Yêu cầu chi tiết:
1. Ở phần Ví dụ thực tế, viết câu tiếng Anh và câu dịch tiếng Việt ngay sát nhau (Không chèn dòng trống ở giữa), sử dụng ký hiệu 👉 ở đầu câu dịch.
2. Ở mục Biến thể, hãy liệt kê đầy đủ TẤT CẢ các biến thể từ loại liên quan thông dụng của từ đó (Ví dụ: Noun của "watch" gồm "watch", "watcher", "watchfulness"...). Hãy liệt kê chi tiết từng từ kèm nghĩa, tránh việc chỉ ghi một từ ngắn ngủi.
3. Các mục biến thể phải bắt đầu bằng dấu cộng "+" ở đầu dòng để thụt lề (Ví dụ: + Danh từ (Noun): từ_1 - nghĩa 1 / từ_2 - nghĩa 2...).
4. Đảm bảo các cụm từ, thành ngữ phải đúng ngữ pháp tiếng Anh.

Bạn BẮT BUỘC phải trả về kết quả thuần túy dưới định dạng JSON sau (không sử dụng markdown backticks hay bất kỳ chữ nào khác ngoài chuỗi JSON này):
{
  "header": "🏷️ TỪ VỰNG: ${word} (Phiên âm IPA)",
  "definitions": "📚 ĐỊNH NGHĨA & BIẾN THỂ:\\n- [Từ gốc - Từ loại]: Nghĩa tiếng Việt.\\n- Biến thể liên quan nếu có:\\n  + Động từ (Verb): từ_1 - nghĩa / từ_2 - nghĩa...\\n  + Danh từ (Noun): từ_1 - nghĩa / từ_2 - nghĩa...\\n  + Tính từ (Adj): từ_1 - nghĩa / từ_2 - nghĩa...\\n  + Trạng từ (Adv): từ_1 - nghĩa / từ_2 - nghĩa...",
  "synonyms_antonyms": "🔄 ĐỒNG / TRÁI NGHĨA:\\n- Đồng nghĩa: từ 1, từ 2...\\n- Trái nghĩa: từ 1, từ 2...",
  "examples": "📝 VÍ DỤ THỰC TẾ:\\n1. Câu tiếng Anh 1\\n👉 Bản dịch tiếng Việt.\\n2. Câu tiếng Anh 2\\n👉 Bản dịch tiếng Việt.",
  "idioms_phrases": "🔥 CỤM TỪ, THÀNH NGỮ & SLANG:\\n- Cụm từ 1: Nghĩa tiếng Việt.\\n- Cụm từ 2: Nghĩa tiếng Việt."
}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, 25000); // 25 seconds timeout (Chrome service worker lives for 30s max per request)

  try {
    await logDebug(`[AI API] Đang gửi yêu cầu fetch (Timeout đặt là 25s)...`);
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: modelName,
        messages: [{ role: 'user', content: prompt }]
      }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    await logDebug(`[AI API] Nhận được phản hồi HTTP ${response.status}`);

    if (!response.ok) {
      const errText = await response.text();
      await logDebug(`[AI API LỖI] Lỗi từ API (HTTP ${response.status}): ${errText}`);
      throw new Error(errText || `HTTP ${response.status}`);
    }

    const data = await response.json();
    if (!data.choices || data.choices.length === 0) {
      await logDebug(`[AI API LỖI] Không có choices trong phản hồi: ${JSON.stringify(data)}`);
      throw new Error('No choices in API response');
    }

    const textResponse = data.choices[0].message.content.trim();
    await logDebug(`[AI API] Nhận text thành công (độ dài: ${textResponse.length})`);
    
    // Xóa các ký tự markdown backticks ```json ... ``` nếu AI tự thêm vào
    const jsonMatch = textResponse.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      await logDebug(`[AI API LỖI] Không tìm thấy JSON trong text: ${textResponse}`);
      throw new Error('No JSON object found in AI response');
    }
    
    try {
      return JSON.parse(jsonMatch[0]);
    } catch (e) {
      await logDebug(`[AI API LỖI] Phân tích cú pháp JSON thất bại: ${e.message}`);
      throw e;
    }
  } catch (e) {
    clearTimeout(timeoutId);
    if (e.name === 'AbortError') {
      await logDebug(`[AI API LỖI] Yêu cầu gọi AI bị quá thời gian (Timeout 25s)`);
      throw new Error('AI request timeout (25 seconds limit)');
    }
    await logDebug(`[AI API LỖI] Gọi fetch xảy ra ngoại lệ: ${e.message}`);
    throw e;
  }
}


// Hàm chuyển đổi kết quả AI thành các Block trong Notion Page Content
function buildNotionBlocks(aiData) {
  const blocks = [];

  // 1. Header (Heading 2)
  if (aiData.header) {
    blocks.push({
      object: 'block',
      type: 'heading_2',
      heading_2: {
        rich_text: [{ type: 'text', text: { content: aiData.header } }]
      }
    });
  }

  // Hàm helper phân tích các dòng văn bản có ngắt dòng (\n) thành blocks tương ứng của Notion
  function parseAndAppendSection(text) {
    if (!text) return;
    const lines = text.split('\n');
    let isTitle = true;

    lines.forEach(line => {
      const trimmed = line.trim();
      if (!trimmed) return;

      // Tiêu đề của phần (Dòng đầu tiên thường có emoji và viết hoa)
      if (isTitle) {
        blocks.push({
          object: 'block',
          type: 'heading_3',
          heading_3: {
            rich_text: [{ type: 'text', text: { content: trimmed } }]
          }
        });
        isTitle = false;
      }
      // Dòng gạch đầu dòng '-' hoặc '+'
      else if (trimmed.startsWith('-') || trimmed.startsWith('+')) {
        blocks.push({
          object: 'block',
          type: 'bulleted_list_item',
          bulleted_list_item: {
            rich_text: [{ type: 'text', text: { content: trimmed.replace(/^[-+]\s*/, '') } }]
          }
        });
      }
      // Dòng đánh số thứ tự như '1.', '2.'
      else if (/^\d+\./.test(trimmed)) {
        blocks.push({
          object: 'block',
          type: 'numbered_list_item',
          numbered_list_item: {
            rich_text: [{ type: 'text', text: { content: trimmed.replace(/^\d+\.\s*/, '') } }]
          }
        });
      }
      // Dòng paragraph bình thường
      else {
        // Nếu là dòng dịch nghĩa thụt lề (bắt đầu bằng 👉)
        if (trimmed.startsWith('👉')) {
          blocks.push({
            object: 'block',
            type: 'paragraph',
            paragraph: {
              rich_text: [{ 
                type: 'text', 
                text: { content: '      ' + trimmed } // Thụt lề nhẹ cho bản dịch
              }]
            }
          });
        } else {
          blocks.push({
            object: 'block',
            type: 'paragraph',
            paragraph: {
              rich_text: [{ type: 'text', text: { content: trimmed } }]
            }
          });
        }
      }
    });
  }

  // 2. Định nghĩa & Dạng từ
  if (aiData.definitions) {
    parseAndAppendSection(aiData.definitions);
  }

  // 3. Đồng / Trái nghĩa
  if (aiData.synonyms_antonyms) {
    parseAndAppendSection(aiData.synonyms_antonyms);
  }

  // 4. Ví dụ
  if (aiData.examples) {
    parseAndAppendSection(aiData.examples);
  }

  // 5. Cụm từ, thành ngữ & Slang
  if (aiData.idioms_phrases) {
    parseAndAppendSection(aiData.idioms_phrases);
  }

  return blocks;
}

// Hàm chạy phân tích từ bằng AI trong background
async function runBackgroundAIAnalysis(pageId, word, notionToken, geminiToken, aiEndpoint, aiModel) {
  await logDebug(`[AI BACKGROUND] Bắt đầu chạy ngầm cho từ: "${word}"`);
  try {
    await logDebug(`[AI BACKGROUND] Đang gọi getGeminiAnalysis...`);
    const aiData = await getGeminiAnalysis(word, geminiToken, aiEndpoint, aiModel);
    await logDebug(`[AI BACKGROUND] Gọi AI thành công. Đang dựng blocks...`);
    const blocks = buildNotionBlocks(aiData);
    if (blocks.length > 0) {
      await logDebug(`[AI BACKGROUND] Đang chèn ${blocks.length} blocks nội dung vào trang Notion...`);
      await appendBlocksToNotionPage(pageId, notionToken, blocks);
      await logDebug(`[AI BACKGROUND] Hoàn thành chèn blocks vào trang Notion thành công!`);
    } else {
      await logDebug(`[AI BACKGROUND] Không tạo được blocks nào từ dữ liệu AI.`);
    }
  } catch (e) {
    await logDebug(`[AI LỖI CHẠY NGẦM] Xử lý AI thất bại: ${e.message}`);
    // Ghi nhận lỗi trực tiếp vào trang trong Notion để người dùng biết
    try {
      const errorBlock = [{
        object: 'block',
        type: 'paragraph',
        paragraph: {
          rich_text: [{ type: 'text', text: { content: `⚠️ AI word analysis failed: ${e.message}` } }]
        }
      }];
      await appendBlocksToNotionPage(pageId, notionToken, errorBlock);
      await logDebug(`[AI LỖI CHẠY NGẦM] Đã ghi block lỗi thành công lên Notion.`);
    } catch (ex) {
      await logDebug(`[AI LỖI CHẠY NGẦM] Không thể ghi block lỗi lên Notion: ${ex.message}`);
    }
  }
}

// Hàm phụ để đẩy (append) các block nội dung vào Notion Page
async function appendBlocksToNotionPage(pageId, token, blocks) {
  const url = `https://api.notion.com/v1/blocks/${pageId}/children`;
  
  const response = await fetch(url, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Notion-Version': '2022-06-28'
    },
    body: JSON.stringify({ children: blocks })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || `HTTP ${response.status}`);
  }

  return await response.json();
}
