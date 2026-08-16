import json
import requests
import re
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    config = json.load(open('desktop-app/config.json'))
    token = config['notion_token']
    db_id = config['database_id']
    
    r = requests.post(
        f'https://api.notion.com/v1/databases/{db_id}/query', 
        headers={'Authorization': f'Bearer {token}', 'Notion-Version': '2022-06-28'}
    )
    pages = r.json().get('results', [])
    page_id = None
    for p in pages:
        title_prop = p['properties'].get('Từ vựng', {}).get('title', [])
        if title_prop:
            w = title_prop[0].get('text', {}).get('content', '')
            if w == 'testimonials':
                page_id = p['id']
                break
                
    if not page_id:
        print("Page testimonials not found in Notion database")
        return
        
    rb = requests.get(
        f'https://api.notion.com/v1/blocks/{page_id}/children', 
        headers={'Authorization': f'Bearer {token}', 'Notion-Version': '2022-06-28'}
    )
    blocks = rb.json().get('results', [])
    text_lines = []
    for b in blocks:
        b_type = b.get('type')
        if not b_type:
            continue
        rich_text = b.get(b_type, {}).get('rich_text', [])
        if rich_text:
            line = ''.join([t.get('plain_text', '') for t in rich_text])
            text_lines.append(line)
            
    page_text = '\n'.join(text_lines)
    print("--- RAW PAGE TEXT ---")
    print(page_text)
    print("----------------------")
    
    syns = []
    ants = []
    
    # Test Synonyms Regex
    syn_match = re.search(r"đồng\s+nghĩa\s*:\s*([^\n]+)", page_text, re.IGNORECASE)
    if syn_match:
        print("syn match group(0):", repr(syn_match.group(0)))
        syns = [s.strip() for s in syn_match.group(1).split(",") if s.strip()]
        
    # Test Antonyms Regex
    ant_match = re.search(r"trái\s+nghĩa\s*:\s*([^\n]+)", page_text, re.IGNORECASE)
    if ant_match:
        print("ant match group(0):", repr(ant_match.group(0)))
        ants = [a.strip() for a in ant_match.group(1).split(",") if a.strip()]
        
    print("parsed syns:", syns)
    print("parsed ants:", ants)

if __name__ == "__main__":
    main()
