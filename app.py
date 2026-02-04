import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re

# 1. 페이지 설정
st.set_page_config(page_title="비토쨩 GDD Pro", page_icon="🎮", layout="wide")

# --- 🎨 스타일링 ---
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #f1f5f9; font-family: 'Pretendard', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    
    .main-title {
        font-size: 3rem; font-weight: 900;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 2rem;
    }
    
    div.stButton > button {
        border-radius: 12px !important; font-weight: 700 !important;
        height: 3.5rem; width: 100%;
    }
    
    .status-badge {
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 5px;
        font-size: 0.85rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# --- 🔒 API 설정 및 사이드바 제어 ---
def get_api_key():
    if "GEMINI_API_KEY" in st.secrets: return st.secrets["GEMINI_API_KEY"]
    if "api_key" in st.session_state: return st.session_state["api_key"]
    return ""

current_api_key = get_api_key()

with st.sidebar:
    st.header("🔑 설정 및 상태")
    
    # API 키 섹션
    if current_api_key:
        st.success("✅ API 키 설정 완료")
        genai.configure(api_key=current_api_key)
    else:
        user_key = st.text_input("Gemini API Key 입력", type="password")
        if user_key:
            st.session_state["api_key"] = user_key
            st.rerun()

    # 이미지 로딩 상태 표시 섹션 (추가됨)
    if 'images' in st.session_state and st.session_state['images']:
        st.divider()
        st.subheader("🖼️ 이미지 생성 현황")
        labels = {"concept": "메인 컨셉", "world": "세계관 아트", "ui": "UI/UX 목업", "character": "캐릭터 에셋"}
        for key, img_data in st.session_state['images'].items():
            status_text = "성공" if img_data else "실패"
            status_color = "#10b981" if img_data else "#ef4444"
            st.markdown(f"""
                <div class="status-badge">
                    <span>{labels.get(key, key)}</span>
                    <b style="color: {status_color};">{status_text}</b>
                </div>
            """, unsafe_allow_html=True)

# 세션 상태 관리
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'images' not in st.session_state: st.session_state['images'] = {}

# --- 🖼️ 이미지 생성 함수 ---
def generate_image(prompt_type, genre, art, key):
    api_key = get_api_key()
    if not api_key: return None
    
    prompts = {
        "concept": f"High-quality masterpiece game key visual art, {genre}, theme: {key}, style: {art}. Cinematic lighting, 8k resolution.",
        "ui": f"High-fidelity mobile game UI/UX design mockup, {genre} HUD interface, style: {art}. Clean layout, inspired by {key}. 4k.",
        "world": f"Stunning environment concept art, {genre} game world island, theme: {key}, style: {art}. Masterpiece landscape.",
        "character": f"High-quality character portrait, {genre} hero unit, motif: {key}, style: {art}. Professional character sheet."
    }
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"
    payload = {
        "instances": { "prompt": prompts.get(prompt_type, "") },
        "parameters": { "sampleCount": 1 }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=90)
        if response.status_code == 200:
            res_json = response.json()
            return res_json["predictions"][0]["bytesBase64Encoded"]
    except Exception:
        pass
    return None

# --- 🏠 메인 화면 ---
st.markdown('<h1 class="main-title">비토쨩 자동 기획서 만들기 🎮</h1>', unsafe_allow_html=True)

with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르 선택", ["방치형 RPG", "수집형 RPG", "MMORPG", "로그라이크", "전략 시뮬레이션"])
    with c2: target = st.selectbox("타겟 시장", ["글로벌", "한국", "일본", "북미", "유럽", "중국"])
    
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("아트 스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼", "사이버펑크"])
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 지하철, 타임루프")
    
    if st.button("고품격 통합 기획서 생성 시작 ✨", type="primary"):
        if not get_api_key():
            st.error("사이드바에서 API 키를 먼저 설정해주세요.")
        elif not key:
            st.warning("키워드를 입력해주세요.")
        else:
            with st.spinner("전문 기획자가 텍스트와 아트를 하나로 엮는 중입니다 (최대 2분 소요)..."):
                # 1. GDD 텍스트 생성
                model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
                prompt = f"""
                당신은 전설적인 게임 기획자입니다. 
                장르: {genre}, 타겟: {target}, 스타일: {art}, 키워드: {key} 조건으로 전문 GDD를 작성하세요.
                
                [필수 구조]
                1. ## 제목 (상위 카테고리)
                2. ### 소제목 (하위 카테고리)
                3. **강조 텍스트** 적극 활용
                4. 전투/성장 공식은 '$$ 공식 $$' 형태로 작성
                5. 복잡한 시스템은 | 표 | 형식 활용
                6. '## UI/UX 전략 및 인터페이스 설계' 섹션 하위에 '### UI/UX 목업' 항목을 무조건 포함하세요.
                """
                res = model.generate_content(prompt)
                st.session_state['gdd_result'] = res.text
                
                # 2. 이미지 생성
                st.session_state['images'] = {
                    "concept": generate_image("concept", genre, art, key),
                    "world": generate_image("world", genre, art, key),
                    "ui": generate_image("ui", genre, art, key),
                    "character": generate_image("character", genre, art, key)
                }

# --- 🚀 통합 렌더링 엔진 ---
if st.session_state['gdd_result']:
    st.divider()
    
    payload = json.dumps({
        "title": f"{key.upper()} PROJECT GDD",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['images']
    }).replace("\\", "\\\\").replace("'", "\\'")

    import streamlit.components.v1 as components
    
    html_template = f"""
    <style>
        @media print {{
            .btn-bar {{ display: none !important; }}
            body {{ background: white !important; padding: 0 !important; }}
            #gdd-paper {{ box-shadow: none !important; border: none !important; margin: 0 !important; width: 100% !important; }}
        }}
        
        body {{ background: #f1f5f9; padding: 20px; font-family: 'Pretendard', sans-serif; }}
        
        .btn-bar {{ max-width: 1200px; margin: 0 auto 30px auto; display: flex; gap: 20px; }}
        .btn {{ flex: 1; padding: 22px; border-radius: 15px; border: none; font-weight: 900; font-size: 18px; cursor: pointer; color: white; transition: 0.3s; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .btn-pdf {{ background: #4f46e5; }}
        .btn-img {{ background: #7c3aed; }}

        /* 통합 기획서 종이 디자인 */
        #gdd-paper {{
            background: white; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 100px 80px; 
            border-radius: 30px; 
            border: 1px solid #e2e8f0; 
            box-shadow: 0 30px 60px rgba(0,0,0,0.05);
            line-height: 1.9;
            color: #1e293b;
        }}

        /* 텍스트 요소 스타일 */
        h1.main-title-text {{ font-size: 64px; font-weight: 900; text-align: center; border-bottom: 12px solid #4f46e5; padding-bottom: 40px; margin-bottom: 60px; }}
        h2 {{ font-size: 34px; color: #4f46e5; border-left: 10px solid #4f46e5; padding-left: 20px; margin-top: 60px; margin-bottom: 30px; background: #f8fafc; padding-top: 15px; padding-bottom: 15px; border-radius: 0 12px 12px 0; font-weight: 800; }}
        h3 {{ font-size: 26px; color: #0891b2; margin-top: 45px; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; font-weight: 700; }}
        p {{ font-size: 21px; color: #334155; margin-bottom: 25px; text-align: justify; }}
        
        /* 특수 블록 */
        .math-block {{ background: #f8faff; border: 1px solid #c7d2fe; padding: 30px; border-radius: 12px; text-align: center; font-size: 24px; font-weight: 700; color: #3730a3; margin: 40px 0; font-family: 'Times New Roman', serif; }}
        table {{ width: 100%; border-collapse: collapse; margin: 30px 0; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; }}
        td {{ padding: 15px; border: 1px solid #f1f5f9; font-size: 18px; }}
        
        /* 이미지 카드 디자인 */
        .img-container {{ text-align: center; margin: 60px 0; padding: 30px; background: #f8fafc; border-radius: 24px; border: 1px solid #e2e8f0; }}
        .img-container img {{ width: 100%; max-width: 1000px; border-radius: 15px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); }}
        .img-label {{ font-size: 16px; color: #6366f1; font-weight: 800; margin-top: 20px; text-transform: uppercase; letter-spacing: 1px; }}
    </style>

    <div class="btn-bar">
        <button class="btn btn-pdf" onclick="window.print()">📄 PDF 문서 저장</button>
        <button class="btn btn-img" id="capture-btn">🖼️ 기획서 이미지 저장</button>
    </div>

    <div id="gdd-paper">
        <h1 id="title-area" class="main-title-text"></h1>
        <div id="main-visual"></div>
        <div id="body-content"></div>
    </div>

    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
        (function() {{
            const data = JSON.parse('{payload}');
            
            // 1. 타이틀 주입
            document.getElementById('title-area').innerText = data.title;
            
            // 2. 메인 비주얼 주입 (최상단)
            if(data.images.concept) {{
                document.getElementById('main-visual').innerHTML = createImgBox(data.images.concept, 'Project Core Visual Art');
            }}

            // 3. 본문 텍스트 및 하위 이미지 파싱
            function parseContent(text) {{
                return text.split('\\n').map(line => {{
                    let l = line.trim();
                    if (!l || l === '#' || l === '##') return '';
                    
                    // 수식 처리
                    if (l.startsWith('$$') && l.endsWith('$$')) {{
                        return '<div class="math-block">' + inline(l.replace(/\\$\\$/g, '')) + '</div>';
                    }}
                    // 표 처리
                    if (l.startsWith('|')) {{
                        const cells = l.split('|').filter(c => c.trim() !== '' || l.indexOf('|') !== l.lastIndexOf('|')).map(c => c.trim());
                        if (cells.length === 0 || l.includes('---')) return '';
                        return '<tr>' + cells.map(c => '<td>' + inline(c) + '</td>').join('') + '</tr>';
                    }}
                    // 제목 처리 및 UI 이미지 삽입
                    if (l.startsWith('##')) {{
                        return '<h2>' + l.replace(/^##\s*/, '') + '</h2>';
                    }}
                    if (l.startsWith('###')) {{
                        const sub = l.replace(/^###\s*/, '');
                        let html = '<h3>' + sub + '</h3>';
                        // UI/UX 목업 섹션일 경우 이미지 강제 삽입
                        if ((sub.includes('목업') || sub.includes('Mockup')) && data.images.ui) {{
                            html += createImgBox(data.images.ui, 'UI/UX Interface Mockup');
                        }}
                        return html;
                    }}
                    
                    return '<p>' + inline(l) + '</p>';
                }}).join('');
            }}

            function inline(t) {{
                return t.replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color:#4f46e5; font-weight:800;">$1</strong>');
            }}

            function createImgBox(b64, label) {{
                return '<div class="img-container"><img src="data:image/png;base64,' + b64 + '"><div class="img-label">[Reference: ' + label + ']</div></div>';
            }}

            const bodyRoot = document.getElementById('body-content');
            let bodyHtml = parseContent(data.content);
            // 표를 table 태그로 감싸기
            bodyHtml = bodyHtml.replace(/(<tr>.*?<\\/tr>)+/g, m => '<div style="overflow-x:auto;"><table>' + m + '</table></div>');
            bodyRoot.innerHTML = bodyHtml;

            // 4. 이미지 저장
            document.getElementById('capture-btn').onclick = function() {{
                this.innerText = "⏳ 렌더링 중...";
                html2canvas(document.getElementById('gdd-paper'), {{ scale: 2, useCORS: true }}).then(canvas => {{
                    const a = document.createElement('a');
                    a.download = 'Vito_GDD_Unified_Report.png';
                    a.href = canvas.toDataURL('image/png');
                    a.click();
                    this.innerText = "🖼️ 기획서 이미지 저장";
                }});
            }};
        }})();
    </script>
    """
    components.html(html_template, height=8000, scrolling=True)