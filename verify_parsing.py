
import json

def test_parse():
    try:
        with open('debug_gemini_response.txt', 'r', encoding='utf-8') as f:
            raw_text = f.read()
        
        clean_text = raw_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
            
        parsed = json.loads(clean_text)
        print(f"Roadmap key present: {'roadmap' in parsed}")
        print(f"Roadmap length: {len(parsed.get('roadmap', ''))}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_parse()
