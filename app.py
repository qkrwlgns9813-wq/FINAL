import json
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"user_profile": {}, "actual_records": [], "recommended_plans": []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(load_data())

@app.route('/api/data', methods=['POST'])
def update_data():
    data = request.json
    save_data(data)
    return jsonify({"status": "success"})

@app.route('/api/passed_data', methods=['GET'])
def get_passed_data():
    if not os.path.exists('passed_data.json'):
        return jsonify([])
    with open('passed_data.json', 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

import subprocess

scrapper_process = None

@app.route('/api/run_scrapper', methods=['POST'])
def run_scrapper_route():
    global scrapper_process
    data = request.json
    limit = data.get('limit', 5)
    
    try:
        # Run scrapper.py as a subprocess
        scrapper_process = subprocess.Popen(['python', 'scrapper.py', str(limit)])
        scrapper_process.wait() # Wait for completion (blocking for simplicity here)
        scrapper_process = None
        return get_passed_data()
    except Exception as e:
        scrapper_process = None
        return jsonify({"error": str(e)}), 500

@app.route('/api/cancel_scrapper', methods=['POST'])
def cancel_scrapper():
    global scrapper_process
    if scrapper_process:
        scrapper_process.terminate()
        scrapper_process = None
        return jsonify({"status": "cancelled"})
    return jsonify({"status": "no active process"})

from google import genai
from google.genai import types

# Setup Gemini Client (New google-genai style)
client = genai.Client(api_key="AIzaSyBIgr9gcgknRjEMV-l8wTS4M2G-BIqZ2Bo")

@app.route('/api/motivation', methods=['GET'])
def get_motivation():
    # Hardcoded or later could be scraped
    motivation_data = {
        "quotes": [
            {"text": "열정은 하늘의 선물이다. 그러나 끈기는 인간의 덕목이다.", "author": "요한 볼프강 폰 괴테"},
            {"text": "어제보다 나은 내일은 오늘의 노력에서 시작된다.", "author": "작자 미상"},
            {"text": "할 수 있다고 믿는 사람은 결국 해낸다.", "author": "헨리 포드"}
        ],
        "videos": [
            {"title": "순공시간 늘리는 법", "url": "https://www.youtube.com/results?search_query=공부자극"},
            {"title": "합격자의 멘탈 관리법", "url": "https://www.youtube.com/results?search_query=수험생+동기부여"}
        ]
    }
    return jsonify(motivation_data)

@app.route('/api/mentor_feedback', methods=['POST'])
def get_mentor_feedback():
    data = request.json
    records = data.get('records', [])
    plans = data.get('plans', [])
    
    prompt = f"""
    당신은 전설적인 수험 코치 '임용 멘토'입니다. 
    오늘 사용자의 학습 기록과 원래 세워진 계획을 바탕으로 하루를 총평해주세요.
    
    [오늘의 학습 기록]
    {json.dumps(records, ensure_ascii=False)}
    
    [오늘의 원래 계획]
    {json.dumps(plans, ensure_ascii=False)}
    
    [요청 사항]
    - 부족했던 점에 대해서는 따끔하지만 건설적인 피드백을 주세요.
    - 잘한 점에 대해서는 구체적으로 찬사를 보내주세요.
    - 내일을 위한 응원 한마디를 해주세요.
    - 말투는 친근하면서도 권위 있는 멘토처럼 해주세요. (예: ~했군, ~하게나, 잘했네!)
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return jsonify({"feedback": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from datetime import datetime
import pytz

@app.route('/api/generate_ai_plan', methods=['POST'])
def generate_ai_plan():
    try:
        kst = pytz.timezone('Asia/Seoul')
        now_kst = datetime.now(kst).strftime('%Y-%m-%d')
        
        data_content = load_data()
        profile = data_content.get('user_profile', {})
        
        passed_data = []
        if os.path.exists('passed_data.json'):
            with open('passed_data.json', 'r', encoding='utf-8') as f:
                passed_data = json.load(f)
        
        req_body = request.json
        period_type = req_body.get('period', 'weekly')

        # D-Day 계산
        target_date = datetime.strptime(profile.get('exam_date', now_kst), '%Y-%m-%d')
        today_date = datetime.strptime(now_kst, '%Y-%m-%d')
        d_day = (target_date - today_date).days

        # 기존 로드맵 정보 (있을 경우 반영)
        existing_roadmap = data_content.get('yearly_roadmap', "")

        # 프롬프트 구성 (디테일 강화)
        if period_type == 'yearly':
            # --- Call 1: Roadmap & Weekly Goals (Day 31 ~ Exam) ---
            prompt = f"""
            당신은 '합격 메이커' AI 코치입니다.
            **목표**: 연간 합격 로드맵과 시험 전까지의 주간 계획(Weekly Goals)을 수립하세요. (초기 30일 제외)

            [상황]
            - 오늘: {now_kst}
            - 시험: {profile.get('exam_type')} ({profile.get('exam_detail')})
            - 상태: {d_day}일 남음

            [권장 커리큘럼 (국어 임용 등 유사 시험 참고용)]
            1. **기초 이론 (1~2월)**: 문법론, 문학론 기초, 국어사, 화법/작문, 독서론 기초
            2. **심화 및 기출 (3~4월)**: 교육론, 기출 분석(최근 5년 -> 10년), 오답 노트
            3. **영역별 문제 풀이 (4~5월)**: 문법, 문학, 화작, 독서 영역별 집중 풀이
            4. **취약점 보완 및 심화 (5~6월)**: 취약 영역 집중 학습, 심화 이론, 백지 인출 연습
            5. **실전 모의고사 및 멘탈 관리 (7~8월)**: 모의고사 실시, 스터디/멘토링 활용, 멘탈/체력 관리
            6. **최종 마무리 (9~11월)**: 전체 회독(4회독 이상), 백지 인출 복습, 파이널 모의고사, 핵심 암기

            [요청 1: 로드맵 (Roadmap Text)]
            - **핵심 요구사항**: 오늘부터 시험일까지 **매 주차별로 한 줄씩** 작성하세요. 날짜를 뭉뚱그려(예: 1월~2월) 작성하면 **절대 안 됩니다.**
            - **형식**: `YYYY.MM.DD ~ YYYY.MM.DD (N주차) : [해당 주차의 학습목표]`
            - **작성 방법**:
                1. Start Date({now_kst})부터 7일 단위로 날짜를 끊으세요.
                2. 시험일({profile.get('exam_date')})까지 **모든 주차**가 한 줄씩 나와야 합니다.
                3. 예:
                   2026.01.22 ~ 2026.01.28 (1주차) : 국어 문법론 기초 1강~5강
                   2026.01.29 ~ 2026.02.04 (2주차) : 국어 문법론 기초 6강~10강
                   ... (시험일까지 약 40줄 이상 나와야 함) ...

            [요청 2: 주간 계획 (Weekly Goals JSON)]
            - **필수 조건**: 위 로드맵과 동일하게 **단 한 주도 빠뜨리지 말고** 모든 주차의 객체를 생성하세요.
            - **데이터 구조**: 리스트의 길이는 (시험일까지의 총 주차 수)와 같아야 합니다.

            [결과 형식 - JSON]
            {{
                "roadmap": "YYYY.MM.DD ~ YYYY.MM.DD (1주차) : [주간목표] ... \nYYYY.MM.DD ~ YYYY.MM.DD (2주차) : [주간목표] ... \n(위와 같이 매 주차별로 줄바꿈하여 작성, 뭉뚱그리기 금지)",
                "plans": [ 
                    {{ "date": "2026-01-22", "tasks": [ {{ "title": "[주간목표] 1월 4주차: ..." }} ] }},
                    {{ "date": "2026-01-29", "tasks": [ {{ "title": "[주간목표] 1월 5주차: ..." }} ] }},
                    ... (시험일까지 계속) ...
                ]
            }}
            """
        else:
            # 기존 로직 (Weekly, Monthly)
            prompt = f"""
            당신은 AI 코치입니다.
            목표: {period_type} 계획 수립. (시험: {profile.get('exam_type')}, D-{d_day})
            요청:
            1. roadmap: 해당 기간의 전략 요약 (yyyy.mm.dd 포맷 사용)
            2. plans: 상세 일일 계획 리스트 (JSON)
            
            Format: {{"roadmap": "...", "plans": [...]}}
            """

        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", max_output_tokens=8192)
        )

        try:
            parsed = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        except Exception:
            parsed = getattr(response, 'parsed', {})

        new_plans = parsed.get('plans', [])
        roadmap_text = parsed.get('roadmap', "")

        # [NEW] Parse roadmap text to ensure plans exist (Fallback/Enforce)
        try:
            if roadmap_text:
                import re
                # Regex to match: 2026.01.22 ~ 2026.01.28 (1주차) : [Goal] or similar
                # Support both YYYY.MM.DD and YYYY-MM-DD
                lines = roadmap_text.split('\n')
                parsed_plans_from_text = []
                
                for line in lines:
                    match = re.search(r'(\d{4}[\.\-]\d{2}[\.\-]\d{2})\s*~\s*(?:.*?)[:：]\s*(.*)', line)
                    if match:
                        start_date = match.group(1).replace('.', '-')
                        content = match.group(2).strip()
                        
                        # Create a plan object
                        plan_obj = {
                            "date": start_date,
                            "tasks": [
                                {
                                    "title": f"[주간목표] {content}",
                                    "time_target": 0, # Default
                                    "progress": 0
                                }
                            ]
                        }
                        parsed_plans_from_text.append(plan_obj)
                
                # Merge logic: If existing plans (from JSON) are few or we want to trust text more.
                # User request: "gemini가 텍스트로 생성한 주간 목표를 gemini 가 분석해서 주간 목표 goals ui 안에 탭 형태로 적어줘"
                # This implies the text is the source of truth.
                # We will merge them. Text-derived plans take precedence for the "Weekly Goal" slot.
                
                text_plan_map = {p['date']: p for p in parsed_plans_from_text}
                json_plan_map = {p.get('date'): p for p in new_plans if p.get('date')}
                
                # Merge: Use JSON plan details if available, but ensure Text goal is present as a task
                final_merged_plans = []
                all_dates = sorted(set(list(text_plan_map.keys()) + list(json_plan_map.keys())))
                
                for d in all_dates:
                    if d in text_plan_map:
                        base_plan = text_plan_map[d]
                        # If JSON also had this date, maybe append other tasks?
                        # But for now, let's stick to the text for the "Weekly Goal" requirement.
                        final_merged_plans.append(base_plan)
                    elif d in json_plan_map:
                        final_merged_plans.append(json_plan_map[d])
                        
                if final_merged_plans:
                    new_plans = final_merged_plans

        except Exception as e:
            print(f"Error parsing roadmap text: {e}")


        # 공통 처리 (결과 반환)
        # parsed = {"roadmap": roadmap_text, "plans": new_plans} (Unused)
        
        current_plans = data_content.get('recommended_plans', [])
        plan_map = {p['date']: p for p in current_plans}
        
        # Only merge in memory for preview, DO NOT SAVE
        for day in new_plans:
            if 'date' in day:
                plan_map[day['date']] = day
            
        return jsonify({
            "status": "success",
            "recommended_plans": list(plan_map.values()),
            "plans": new_plans, # Explicitly return new plans for frontend logic
            "yearly_roadmap": roadmap_text,
            "period_type": period_type
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_daily_detail', methods=['POST'])
def generate_daily_detail():
    data_content = load_data()
    profile = data_content.get('user_profile', {})
    
    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst).strftime('%Y-%m-%d')
    
    req_body = request.json
    weekly_goals_context = req_body.get('weekly_goals', [])
    
    # Format weekly goals for the prompt
    weekly_goals_str = ""
    if weekly_goals_context:
        weekly_goals_str = "\n[참고: 확정된 주간 목표]\n"
        for week in weekly_goals_context:
            title = "목표 없음"
            if week.get('tasks') and len(week['tasks']) > 0:
                title = week['tasks'][0].get('title', '목표 없음')
            weekly_goals_str += f"- {week.get('date')}: {title}\n"

    prompt = f"""
    당신은 AI 코치입니다.
    **목표**: 오늘부터 30일간의 **상세 일일 계획(Daily Plan)**을 수립하세요.
    해당 기간의 '주간 목표'를 반드시 참고하여, 그 목표를 달성하기 위한 구체적인 하루 실천 계획을 짜야 합니다.

    [상황]
    - 오늘: {now_kst}
    - 시험: {profile.get('exam_type')}
    {weekly_goals_str}

    [요청: 30일 일일 계획]
    - **기간**: 오늘({now_kst})부터 30일간 (하루도 빠짐없이)
    - **내용**: 하루당 핵심 Task 3개 생성 (구체적인 공부 내용, 분량, 강의 수강 등)
    - **제약**: Task Title은 15자 이내로 짧고 명확하게.

    [결과 형식 - JSON]
    {{
        "plans": [ {{ "date": "YYYY-MM-DD", "tasks": [ {{ "title": "...", "time_target": 2 }} ] }} ]
    }}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", max_output_tokens=8192)
        )
        parsed = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        return jsonify(parsed)
    except Exception as e:
        print(f"Error generating daily detail: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

@app.route('/api/expand_weekly_plans', methods=['POST'])
def expand_weekly_plans():
    try:
        req_body = request.json
        simple_plans = req_body.get('weekly_plans', [])
        
        expanded_plans = generate_expanded_weekly_plan(simple_plans)
        return jsonify({"plans": expanded_plans})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_expanded_weekly_plan(simple_plans):
    """
    Takes a list of simple weekly plans (title only) and asks Gemini to split them into 2-3 sub-tasks.
    """
    if not simple_plans:
        return []

    # Prepare context for prompt
    plan_text = ""
    for p in simple_plans:
        title = "목표 없음"
        if p.get('tasks') and len(p['tasks']) > 0:
            title = p['tasks'][0].get('title', '')
        plan_text += f"- {p.get('date')}: {title}\n"

    prompt = f"""
    당신은 AI 학습 코치입니다.
    다음은 사용자의 '주간 핵심 목표' 리스트입니다.
    각 주차의 목표가 너무 포괄적이므로, **실천 가능한 2~3개의 하위 목표(Sub-tasks)**로 구체화해주세요.

    [입력된 주간 목표]
    {plan_text}

    [요청사항]
    1. 각 주차별로 기존 목표를 유지하되, 이를 쪼개서 2~3개의 Task로 만드세요.
    2. 모든 Task의 Title 앞에 **`[주간]`** 태그를 반드시 붙이세요. (UI 식별용)
    3. 예: "[주간목표] 문법론 1회독" -> 
       - "[주간] 문법론 음운/형태소 개념 정리"
       - "[주간] 문법론 통사/의미론 개념 정리"
    4. 날짜는 입력된 날짜를 그대로 유지하세요.

    [결과 형식 - JSON]
    {{
        "plans": [ 
            {{ "date": "YYYY-MM-DD", "tasks": [ {{ "title": "[주간] ...", "time_target": 5, "progress": 0 }} ... ] }},
            ...
        ]
    }}
    """

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp', generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result.get('plans', [])
    except Exception as e:
        print(f"Expansion failed: {e}")
        return simple_plans # Fallback to original
