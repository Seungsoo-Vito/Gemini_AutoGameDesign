import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re

# 1. 페이지 설정
st.set_page_config(page_title="비토쨩 GDD Pro B", page_icon="🎮", layout="wide")

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
</style>
""", unsafe_allow_html=True)

# --- 🔒 API 설정 (사이드바) ---
def get_api_key():
    if "GEMINI_API_KEY" in st.secrets: return st.secrets["GEMINI_API_KEY"]
    if "api_key" in st.session_state: return st.session_state["api_key"]
    return ""

with st.sidebar:
    st.header("🔑 API 설정")
    user_key = st.text_input("Gemini API Key", type="password", value=get_api_key())
    if user_key:
        st.session_state["api_key"] = user_key
        genai.configure(api_key=user_key)
        st.success("API 키 설정 완료")

# 세션 상태 관리
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'images' not in st.session_state: st.session_state['images'] = {}

# --- 🖼️ 이미지 생성 함수 (규격 엄수) ---
def generate_image(prompt_type, genre, art, key):
    api_key = st.session_state.get("api_key", "")
    if not api_key: return None
    
    prompts = {
        "concept": f"High-quality masterpiece game key visual art, {genre}, theme: {key}, style: {art}. 8k resolution, cinematic lighting.",
        "ui": f"High-fidelity professional mobile game UI/UX design mockup, {genre} HUD, style: {art}. Dashboard, inspired by {key}. 4k.",
        "world": f"Environment concept art, immersive game world of {genre}, theme: {key}, style: {art}. Beautiful landscape.",
        "character": f"High-quality character concept art, {genre} hero unit, motif: {key}, style: {art}. Professional asset."
    }
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"
    # 시스템 가이드라인에 따른 정확한 Payload 구조
    payload = {
        "instances": { "prompt": prompts.get(prompt_type, "") },
        "parameters": { "sampleCount": 1 }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            res_json = response.json()
            return res_json["predictions"][0]["bytesBase64Encoded"]
    except Exception:
        pass
    return None

# --- 🏠 메인 화면 ---
st.markdown('<h1 class="main-title">비토쨩 GDD Pro B-Ver 🎮</h1>', unsafe_allow_html=True)

# 입력 영역
with st.container():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: genre = st.selectbox("장르", ["방치형 RPG", "수집형 RPG", "MMORPG", "로그라이크", "전략 시뮬레이션"])
    with c2: art = st.selectbox("스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼", "사이버펑크"])
    with c3: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 차원이동")
    
    if st.button("고품격 기획서 & 이미지 생성 시작 ✨", type="primary"):
        if not st.session_state.get("api_key"):
            st.error("사이드바에서 API 키를 먼저 입력해주세요.")
        elif not key:
            st.warning("키워드를 입력해주세요.")
        else:
            with st.spinner("전문 기획자가 텍스트와 아트를 독립적으로 구성 중입니다..."):
                # 1. 텍스트 생성
                model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
                prompt = f"당신은 전설적인 기획자입니다. {genre}, {art}, {key} 조건으로 전문 GDD를 작성하세요. ## 제목, **강조**, $$ 공식 $$, | 표 | 형식을 반드시 포함하세요. UI/UX 전략 섹션도 필수입니다."
                res = model.generate_content(prompt)
                st.session_state['gdd_result'] = res.text
                
                # 2. 이미지 생성 (4종)
                st.session_state['images'] = {
                    "concept": generate_image("concept", genre, art, key),
                    "world": generate_image("world", genre, art, key),
                    "ui": generate_image("ui", genre, art, key),
                    "character": generate_image("character", genre, art, key)
                }

# --- 🚀 [B-Ver] 분리형 렌더링 엔진 ---
if st.session_state['gdd_result']:
    st.divider()
    
    # 데이터 이스케이프 및 전송 준비
    payload = json.dumps({
        "title": f"{key.upper()} PROJECT GDD",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['images']
    }).replace("\\", "\\\\").replace("'", "\\'")

    import streamlit.components.v1 as components
    
    html_template = f"""
    <div id="btn-bar" style="display:flex; gap:20px; max-width:1400px; margin:0 auto 30px auto;">
        <button onclick="window.print()" style="flex:1; padding:20px; border-radius:15px; background:#4f46e5; color:white; border:none; font-weight:900; font-size:18px; cursor:pointer; box-shadow:0 4px 15px rgba(0,0,0,0.1);">📄 PDF 저장</button>
        <button id="save-img" style="flex:1; padding:20px; border-radius:15px; background:#7c3aed; color:white; border:none; font-weight:900; font-size:18px; cursor:pointer; box-shadow:0 4px 15px rgba(0,0,0,0.1);">🖼️ 리포트 이미지 저장</button>
    </div>

    <div id="workspace" style="display:flex; gap:40px; max-width:1400px; margin:0 auto; align-items:flex-start;">
        <!-- 좌측: 기획서 영역 -->
        <div id="gdd-doc" style="flex:0 0 65%; background:white; padding:80px 60px; border-radius:30px; border:1px solid #e2e8f0; box-shadow:0 20px 50px rgba(0,0,0,0.05); min-height:1000px;">
            <h1 id="doc-title" style="font-size:54px; font-weight:900; text-align:center; border-bottom:10px solid #4f46e5; padding-bottom:30px; margin-bottom:60px;"></h1>
            <div id="doc-body"></div>
        </div>
        
        <!-- 우측: 이미지 갤러리 영역 -->
        <div id="gallery" style="flex:1; position:sticky; top:20px; display:flex; flex-direction:column; gap:30px;"></div>
    </div>

    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
        (function() {{
            const data = JSON.parse('{payload}');
            
            // 타이틀 주입
            document.getElementById('doc-title').innerText = data.title;
            
            // 텍스트 파싱 로직 (A버전 엔진)
            function parseText(text) {{
                return text.split('\\n').map(line => {{
                    let l = line.trim();
                    if (!l || l === '#' || l === '##') return '';
                    
                    // 수식
                    if (l.startsWith('$$') && l.endsWith('$$')) {{
                        return '<div style="background:#f8faff; border:1px solid #c7d2fe; padding:25px; border-radius:10px; text-align:center; font-size:22px; font-weight:700; color:#3730a3; margin:30px 0;">' + l.replace(/\\$\\$/g, '') + '</div>';
                    }}
                    // 표
                    if (l.startsWith('|')) {{
                        const cells = l.split('|').filter(c => c.trim() !== '' || l.indexOf('|') !== l.lastIndexOf('|')).map(c => c.trim());
                        if (cells.length === 0 || l.includes('---')) return '';
                        return '<tr>' + cells.map(c => '<td style="padding:12px; border:1px solid #f1f5f9; font-size:17px;">' + inline(c) + '</td>').join('') + '</tr>';
                    }}
                    // 제목
                    if (l.startsWith('##')) {{
                        return '<h2 style="font-size:32px; color:#4f46e5; border-left:8px solid #4f46e5; padding-left:15px; margin-top:50px; background:#f8fafc; padding-top:10px; padding-bottom:10px;">' + l.replace(/^##\s*/, '') + '</h2>';
                    }}
                    if (l.startsWith('###')) {{
                        return '<h3 style="font-size:24px; color:#1e293b; margin-top:30px; border-bottom:2px solid #f1f5f9; padding-bottom:8px;">' + l.replace(/^###\s*/, '') + '</h3>';
                    }}
                    // 일반 텍스트 및 별표 제거
                    return '<p style="font-size:20px; line-height:1.8; color:#334155; margin-bottom:20px;">' + inline(l) + '</p>';
                }}).join('');
            }}

            function inline(t) {{
                return t.replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color:#4f46e5;">$1</strong>');
            }}

            // 문서 본문 렌더링
            let body = parseText(data.content);
            body = body.replace(/(<tr>.*?<\\/tr>)+/g, m => '<table style="width:100%; border-collapse:collapse; margin:20px 0;">' + m + '</table>');
            document.getElementById('doc-body').innerHTML = body;

            // 갤러리 렌더링 (우측)
            const gallery = document.getElementById('gallery');
            const imgLabels = {{ "concept": "Concept Art", "world": "Environment", "ui": "UI Mockup", "character": "Character" }};
            
            Object.keys(data.images).forEach(k => {{
                if (data.images[k]) {{
                    const card = document.createElement('div');
                    card.style = "background:white; border:1px solid #e2e8f0; padding:15px; border-radius:20px; text-align:center; box-shadow:0 10px 25px rgba(0,0,0,0.05);";
                    card.innerHTML = '<img src="data:image/png;base64,' + data.images[k] + '" style="width:100%; border-radius:12px; margin-bottom:10px;">' +
                                     '<div style="font-weight:900; color:#6366f1; font-size:14px; text-transform:uppercase;">' + imgLabels[k] + '</div>';
                    gallery.appendChild(card);
                }}
            }});

            // 이미지 저장
            document.getElementById('save-img').onclick = function() {{
                const btn = this;
                btn.innerText = "⏳ 렌더링 중...";
                html2canvas(document.getElementById('workspace'), {{ scale: 2, useCORS: true }}).then(canvas => {{
                    const a = document.createElement('a');
                    a.download = 'Vito_GDD_Report.png';
                    a.href = canvas.toDataURL('image/png');
                    a.click();
                    btn.innerText = "🖼️ 리포트 이미지 저장";
                }});
            }};
        }})();
    </script>
    """
    components.html(html_template, height=8000, scrolling=True)