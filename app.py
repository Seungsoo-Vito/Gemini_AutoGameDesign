import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re
import os.path
import streamlit.components.v1 as components

# 1. Page Configuration (모바일 최적화 레이아웃)
st.set_page_config(page_title="비토쨩 GDD Pro", page_icon="🎮", layout="wide")

# --- 🎨 Responsive High-End UI Styling ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* 전체 앱 기본 스타일 */
    .stApp { 
        background-color: #f8fafc; 
        color: #1e293b; 
        font-family: 'Pretendard', sans-serif; 
    }
    
    .main-title {
        font-size: calc(1.8rem + 1.2vw) !important; 
        font-weight: 900 !important;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem !important;
    }
    
    /* 📸 기획서 캡처 영역 (모바일 대응) */
    #gdd-capture-area {
        background: #ffffff;
        padding: 40px 20px;
        border-radius: 12px; 
        color: #1e293b;
        line-height: 1.7;
        max-width: 900px;
        width: 100%;
        margin: 0 auto;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    /* 이미지 반응형 처리 */
    #gdd-capture-area img {
        max-width: 100% !important;
        height: auto !important;
        border-radius: 8px;
        display: block;
        margin: 20px auto;
    }

    /* PC에서 이미지가 너무 커지지 않게 제한 */
    .img-wrapper {
        max-width: 800px;
        margin: 0 auto;
    }
    
    #gdd-capture-area h1 { font-size: 2.2rem; text-align: center; margin-bottom: 25px; border-bottom: 5px solid #6366f1; padding-bottom: 15px; }
    #gdd-capture-area h2 { font-size: 1.6rem; color: #4f46e5; margin-top: 35px; border-left: 6px solid #6366f1; padding-left: 12px; background: #f8fafc; }
    #gdd-capture-area p, #gdd-capture-area li { font-size: 17px; margin-bottom: 10px; word-break: keep-all; }

    .img-caption {
        font-size: 0.85rem;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 35px;
    }

    /* 버튼 스타일 */
    div.stButton > button {
        width: 100%;
        border-radius: 12px !important;
        font-weight: 700 !important;
        height: 3.5rem;
    }

    @media (max-width: 768px) {
        #gdd-capture-area { padding: 25px 15px; }
        .main-title { font-size: 2rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔒 API Key Security ---
def load_api_key():
    for k in ["GEMINI_API_KEY", "gemini_api_key", "API_KEY"]:
        if k in st.secrets: return st.secrets[k]
    return ""

API_KEY = load_api_key()

with st.sidebar:
    st.header("🔑 보안 설정")
    if not API_KEY:
        API_KEY = st.text_input("Gemini API Key를 입력하세요", type="password")
    else:
        st.info("✅ 클라우드 설정에서 API 키를 불러왔습니다.")

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 🎨 Intelligent Image Engine ---
def generate_specialized_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    prompts = {
        "concept": f"Epic game key visual, {genre}, {key}, {art} style. Cinematic 8k.",
        "ui": f"Game UI/UX mockup, {genre} mobile game, {art} style. Clean layout.",
        "world": f"Environment concept art, {genre} game world, location: {key}, {art}.",
        "character": f"Character design or game asset, {genre}, {key}, {art} style."
    }
    selected_prompt = prompts.get(prompt_type, prompts["concept"])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {"instances": [{"prompt": selected_prompt}], "parameters": {"sampleCount": 1}}
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.json()["predictions"][0]["bytesBase64Encoded"]
    except: return None

# Session State
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'generated_images' not in st.session_state: st.session_state['generated_images'] = {}
if 'history' not in st.session_state: st.session_state['history'] = []

# --- 3. Sidebar History ---
with st.sidebar:
    st.divider()
    st.header("🕒 히스토리")
    if st.session_state['history']:
        for i, item in enumerate(st.session_state['history'][::-1]):
            if st.button(f"📄 {item['key'][:10]}", key=f"hist_{i}", use_container_width=True):
                st.session_state['gdd_result'] = item['content']
                st.session_state['generated_images'] = item.get('images', {})
                st.rerun()

# --- 4. UI Main ---
st.markdown('<h1 class="main-title">비토쨩 GDD Pro 🎮</h1>', unsafe_allow_html=True)
st.write("모바일 환경에서 이미지가 최적화되어 표시되는 버전입니다.")
st.divider()

# Input Section
with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르", ["방치형 RPG", "수집형 RPG", "오픈월드", "로그라이크", "액션"])
    with c2: target = st.selectbox("타겟 국가", ["글로벌", "한국", "일본", "북미/유럽"])
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼"])
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프")
    
    if st.button("전문 기획서 및 아트 생성 시작 ✨", type="primary", use_container_width=True):
        if not API_KEY: st.error("API 키를 입력해 주세요.")
        elif not key: st.warning("키워드를 입력해 주세요.")
        else:
            with st.spinner("AI가 기획서와 아트를 생성 중입니다..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"당신은 시니어 게임 기획자입니다. 장르={genre}, 국가={target}, 키워드={key}, 아트={art} 조건으로 전문 GDD를 작성하세요. 마크다운 형식을 지켜주세요."
                gdd_res = model.generate_content(prompt)
                st.session_state['gdd_result'] = gdd_res.text
                
                imgs = {
                    "concept": generate_specialized_image("concept", genre, art, key),
                    "ui": generate_specialized_image("ui", genre, art, key),
                    "world": generate_specialized_image("world", genre, art, key),
                    "asset": generate_specialized_image("character", genre, art, key)
                }
                st.session_state['generated_images'] = imgs
                st.session_state['history'].append({"key": key, "content": gdd_res.text, "images": imgs})

# Result Display
if st.session_state['gdd_result']:
    st.divider()
    
    # 📸 Responsive GDD Content Area
    st.markdown('<div id="gdd-capture-area">', unsafe_allow_html=True)
    st.markdown(f"<h1>{key.upper()} 기획안</h1>", unsafe_allow_html=True)
    
    imgs = st.session_state['generated_images']
    
    # 메인 이미지 (반응형 래퍼)
    if imgs.get("concept"):
        st.markdown('<div class="img-wrapper">', unsafe_allow_html=True)
        st.image(base64.b64decode(imgs["concept"]), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<p class="img-caption">[Main Visual Concept]</p>', unsafe_allow_html=True)

    content = st.session_state['gdd_result']
    sections = content.split("## ")
    for i, section in enumerate(sections):
        if not section.strip(): continue
        sec_text = "## " + section if i > 0 else section
        st.markdown(sec_text) 
        
        # 섹션별 이미지 삽입 (모바일 대응)
        if i == 1 and imgs.get("world"):
            st.markdown('<div class="img-wrapper">', unsafe_allow_html=True)
            st.image(base64.b64decode(imgs["world"]), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<p class="img-caption">[World Reference]</p>', unsafe_allow_html=True)
        elif i == 3 and imgs.get("ui"):
            st.markdown('<div class="img-wrapper">', unsafe_allow_html=True)
            st.image(base64.b64decode(imgs["ui"]), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<p class="img-caption">[UI/UX Design]</p>', unsafe_allow_html=True)
        elif i == 5 and imgs.get("asset"):
            st.markdown('<div class="img-wrapper">', unsafe_allow_html=True)
            st.image(base64.b64decode(imgs["asset"]), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<p class="img-caption">[Character Concept]</p>', unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

    # 📥 Download Logic
    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 PDF 저장 (새 창)", use_container_width=True):
            components.html(f"""
                <script>
                const content = window.parent.document.getElementById('gdd-capture-area').innerHTML;
                const win = window.open('', '_blank');
                win.document.write('<html><head><title>GDD_{key}</title>');
                win.document.write('<style>body{{font-family:sans-serif;padding:30px;}}img{{max-width:100%;height:auto;}}h1{{border-bottom:4px solid #6366f1;}}</style></head><body>');
                win.document.write(content);
                win.document.write('</body></html>');
                win.document.close();
                win.onload = () => win.print();
                </script>
            """, height=0)

    with col2:
        if st.button("🖼️ 이미지(PNG) 저장", use_container_width=True):
            components.html(f"""
                <script>
                const script = document.createElement('script');
                script.src = "https://html2canvas.hertzen.com/dist/html2canvas.min.js";
                script.onload = () => {{
                    const area = window.parent.document.getElementById('gdd-capture-area');
                    html2canvas(area, {{ useCORS: true, scale: 2 }}).then(canvas => {{
                        const link = document.createElement('a');
                        link.download = 'GDD_{key}.png';
                        link.href = canvas.toDataURL('image/png');
                        link.click();
                    }});
                }};
                document.head.appendChild(script);
                </script>
            """, height=0)

st.caption("비토쨩 GDD Pro | Optimized for Mobile & Desktop")