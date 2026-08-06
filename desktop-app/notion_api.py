import requests

def fetch_notion_vocab(token, db_id):
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json={})
    if not response.ok:
        raise Exception(f"Notion API Error: {response.status_code} - {response.text}")
        
    results = response.json().get("results", [])
    vocab_list = []
    
    for page in results:
        props = page.get("properties", {})
        
        # 1. Trích xuất Từ vựng (Title)
        word_title = props.get("Từ vựng", {}).get("title", [])
        word = word_title[0].get("text", {}).get("content", "") if word_title else ""
        
        # 2. Trích xuất Dịch nghĩa
        trans_rich = props.get("Dịch nghĩa", {}).get("rich_text", [])
        translation = trans_rich[0].get("text", {}).get("content", "") if trans_rich else ""
        
        # 3. Trích xuất Ngữ cảnh
        context_rich = props.get("Ngữ cảnh", {}).get("rich_text", [])
        context = context_rich[0].get("text", {}).get("content", "") if context_rich else ""
        
        # 4. Trích xuất Nguồn
        source = props.get("Nguồn", {}).get("url", "")
        
        if word:
            vocab_list.append({
                "id": page.get("id"),
                "word": word,
                "translation": translation,
                "context": context,
                "source": source
            })
            
    return vocab_list

def fetch_synonyms_antonyms(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    synonyms = []
    antonyms = []
    try:
        r = requests.get(url, timeout=5)
        if r.ok:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                meanings = data[0].get("meanings", [])
                for meaning in meanings:
                    for syn in meaning.get("synonyms", []):
                        if syn.strip() and syn.lower() != word.lower():
                            synonyms.append(syn.strip())
                    for ant in meaning.get("antonyms", []):
                        if ant.strip() and ant.lower() != word.lower():
                            antonyms.append(ant.strip())
        synonyms = list(set(synonyms))
        antonyms = list(set(antonyms))
    except Exception:
        pass
    return synonyms, antonyms

def fetch_notion_page_blocks_text(page_id, token):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.ok:
            results = response.json().get("results", [])
            text_lines = []
            for block in results:
                block_type = block.get("type")
                if not block_type:
                    continue
                block_content = block.get(block_type, {})
                rich_text = block_content.get("rich_text", [])
                if rich_text:
                    line = "".join([t.get("plain_text", "") for t in rich_text])
                    text_lines.append(line)
            return "\n".join(text_lines)
    except Exception:
        pass
    return ""


