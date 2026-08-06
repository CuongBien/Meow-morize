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
