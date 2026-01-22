import requests
from bs4 import BeautifulSoup
import json
import time
import os

import sys

def run_scrapper(limit=5):
    # 1. Load User Info
    if not os.path.exists('data.json'):
        print("[Error] data.json not found.")
        return
    
    # Load existing stories if they exist to append
    existing_stories = []
    if os.path.exists('passed_data.json'):
        with open('passed_data.json', 'r', encoding='utf-8') as f:
            existing_stories = json.load(f)
    seen_links = {s['link'] for s in existing_stories}

    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    exam_type = data['user_profile'].get('exam_type', '자격증')
    exam_detail = data['user_profile'].get('exam_detail', '')
    
    # Mapping for better search queries
    type_map = {
        'teacher': '임용고시',
        'csat': '수능',
        'civil': '공무원',
        'cert': '자격증'
    }
    exam_name = type_map.get(exam_type, exam_type)
    query = f"{exam_name} {exam_detail} 합격수기"
    
    print(f"SEARCH: '{query}' searching...")
    
    # 2. Naver Search (VIEW section)
    base_url = "https://search.naver.com/search.naver"
    params = {
        "where": "view",
        "query": query,
        "sm": "tab_nmw"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Broad Search: Find all <a> tags that might be titles
        all_links = soup.find_all('a')
        results = []
        count = 0
        
        for link_el in all_links:
            if count >= limit: break
            
            title_text = link_el.get_text(strip=True)
            href = link_el.get('href', '')
            
            # Simple heuristic: title should be long and contain keyword or '합격'
            if len(title_text) > 10 and ('합격' in title_text or '수기' in title_text):
                if href.startswith('http') and href not in seen_links:
                    print(f"FOUND: [{count+1}/5] {title_text[:30]}...")
                    
                    # Try to find a summary nearby (next sibling or parent sibling)
                    summary = "내용 요약 없음"
                    # Look at siblings or parent siblings for summary-like text
                    parent = link_el.parent
                    while parent and len(summary) < 20:
                        potential_desc = parent.get_text(strip=True)
                        if len(potential_desc) > len(title_text) + 20:
                            summary = potential_desc.replace(title_text, "")[:200] + "..."
                            break
                        parent = parent.parent

                    # Identify source (Blog or Cafe)
                    source = "블로그" # Default
                    if "cafe.naver.com" in href:
                        source = "네이버 카페"
                    elif "blog.naver.com" in href:
                        source = "네이버 블로그"
                    elif "tistory.com" in href:
                        source = "티스토리"

                    results.append({
                        "title": title_text,
                        "link": href,
                        "summary": summary,
                        "author": source,
                        "date": "최근"
                    })
                    seen_links.add(href)
                    count += 1
                    time.sleep(0.5)

        # 3. Append and Save
        final_data = existing_stories + results
        with open('passed_data.json', 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
        
        print(f"\nDONE: {len(results)} new items added to 'passed_data.json'.")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    limit_arg = 5
    if len(sys.argv) > 1:
        try:
            limit_arg = int(sys.argv[1])
        except ValueError:
            pass
    run_scrapper(limit_arg)
