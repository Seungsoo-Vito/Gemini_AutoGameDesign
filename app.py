import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re
import os.path
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(page_title="비토쨩 GDD Pro", page_icon="🎮", layout="wide")

# --- 🎨 High-End UI & Font Styling ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* Global Font Settings */
    .stApp { 
        background-color: #f8fafc; 
        color: #1e293b; 
        font-family: 'Pretendard', -apple-system, sans-serif; 
    }
    
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    .main-title {
        font-size: 3.5rem !important; 
        font-weight: 900 !important;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.05rem;
        margin-bottom: 1rem !important;
    }
    
    /* 📸 Capture Area Design */
    #gdd-capture-area {
        background: #ffffff;
        padding: 80px 60px;
        border-radius: 0px; 
        color: #1e293b;
        line-height: 1.8;
        font-family: 'Pretendard', sans-serif;
        max-width: 1000px;
        margin: 0 auto;
    }
    
    #gdd-capture-area h1 {
        font-size: 54px;
        font-weight: 900;
        color: #1e293b;
        margin-bottom: 40px;
        text-align: center;
        border-bottom: 8px solid #6366f1;
        padding-bottom: 20px;
    }

    #gdd-capture-area h2 {
        font-size: 32px;
        font-weight: 800;
        color: #4f46e5;
        margin-top: 60px;
        margin-bottom: 25px;
        border-left: 10px solid #6366f1;
        padding-left: 20px;
        background: #f1f5f9;
        padding-top: 10px;
        padding-bottom: 10px;
    }

    #gdd-capture-area h3 {
        font-size: 24px;
        font-weight: 700;
        color: #1e293b;
        margin-top: 40px;
        margin-bottom: 15px;
        padding-bottom: 5px;
        border-bottom: 2px solid #e2e8f0;
    }

    #gdd-capture-area p, #gdd-capture-area li {
        font-size: 19px;
        font-weight: 400;
        color: #334155;
        margin-bottom: 15px;
        word-break: keep-all;
    }

    #gdd-capture-area ul, #gdd-capture-area ol {
        padding-left: 30px;
        margin-bottom: 30px;
    }

    #gdd-capture-area li {
        margin-bottom: 10px;
        list-style-type: disc;
    }

    #gdd-capture-area strong {
        color: #4f46e5;
        font-weight: 700;
    }

    /* Image Styling */
    .gdd-img-container {
        margin: 40px auto;
        text-align: center;
        width: 800px;
    }
    
    .img-caption {
        font-size: 0.9rem;
        color: #94a3b8;
        text-align: center;
        margin-top: 5px;
        margin-bottom: 40px;
        font-weight: 500;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white; border: none; border-radius: 16px; font-weight: 700; height: 3.8rem;
    }

    .history-item {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
    }

    /* 🖨️ Print Styles (Optimized for PDF) */
    @media print {
        /* 전체 숨김 처리 */
        body * {
            visibility: hidden;
        }
        /* 기획서 영역만 표시 */
        #gdd-capture-area, #gdd-capture-area * {
            visibility: visible;
        }
        #gdd-capture-area {
            position: absolute;
            left: 0;
            top: 0;
            width: 100% !important;
            max-width: 100% !important;
            padding: 20px !important;
            margin: 0 !important;
            box-shadow: none !important;
            border: none !important;
        }
        /* 페이지 끊김 방지 */
        h1, h2, h3, img, .stImage {
            page-break-inside: avoid;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔒 API Key Security Management ---
def load_api_key():
    possible_keys = ["GEMINI_API_KEY", "gemini_api_key", "API_KEY", "api_key"]
    for k in possible_keys:
        if k in st.secrets:
            return st.secrets[k]
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

# --- 🎨 Intelligent Image Generation Engine ---
def generate_specialized_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    
    prompts = {
        "concept": f"Epic high-quality game key visual, {genre}, {key} theme, {art} style. Professional digital art, 8k cinematic lighting.",
        "ui": f"Professional game UI design, mobile {genre} game HUD, inventory, {art} style. Clean layout, icons, inspired by {key}.",
        "world": f"Game environment background, world concept art for {genre}, location: {key}, {art} style. Atmospheric, high detail.",
        "character": f"Character portrait or item asset, {genre} game, {key} motif, {art} style. Detailed concept sheet."
    }
    
    selected_prompt = prompts.get(prompt_type, prompts["concept"])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {"instances": [{"prompt": selected_prompt}], "parameters": {"sampleCount": 1}}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.json()["predictions"][0]["bytesBase64Encoded"]
    except:
        return None

# Session State Management
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'generated_images' not in st.session_state: st.session_state['generated_images'] = {}
if 'history' not in st.session_state: st.session_state['history'] = []

# --- 3. UI Sidebar ---
with st.sidebar:
    st.divider()
    st.header("🕒 히스토리")
    if not st.session_state['history']:
        st.write("기록이 없습니다.")
    else:
        for i, item in enumerate(st.session_state['history'][::-1]):
            st.markdown(f'<div class="history-item">📄 {item["key"][:12]}</div>', unsafe_allow_html=True)
    if st.button("기록 삭제", use_container_width=True):
        st.session_state['history'] = []
        st.rerun()

# --- 4. UI Main ---
st.markdown('<h1 class="main-title">비토쨩 GDD Pro 🎮</h1>', unsafe_allow_html=True)
st.write("이미지 크기를 최적화하고 PDF 저장 기능을 개선한 버전입니다.")
st.divider()

# Input Section
with st.container():
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1: genre = st.selectbox("장르", ["방치형 RPG", "수집형 RPG", "오픈월드", "로그라이크", "액션"])
    with c2: target = st.selectbox("타겟 국가", ["글로벌", "한국", "일본", "북미/유럽"])
    with c3: art = st.selectbox("스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼"])
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프")
    
    st.write("")
    if st.button("전문 기획서 및 아트 생성 시작 ✨", type="primary", use_container_width=True):
        if not API_KEY:
            st.error("API 키를 입력해 주세요.")
        elif not key:
            st.warning("키워드를 입력해 주세요.")
        else:
            with st.spinner("AI가 기획서를 작성 중입니다..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"""
                당신은 전설적인 게임 기획자입니다.
                다음 조건으로 게임 디자인 문서(GDD)를 작성하세요: 장르={genre}, 국가={target}, 키워드={key}, 아트={art}.
                
                [중요 지시사항]
                1. 반드시 마크다운(Markdown) 형식을 사용하세요.
                2. 헤더(###)와 리스트(*) 사이에는 반드시 빈 줄을 하나 넣으세요.
                3. 한 문장이 끝날 때마다 명확하게 줄바꿈을 하세요.
                4. 리스트 항목은 한 줄에 하나씩만 작성하세요.
                """
                gdd_res = model.generate_content(prompt)
                st.session_state['gdd_result'] = gdd_res.text
                
                # Image Generation
                imgs = {}
                imgs["concept"] = generate_specialized_image("concept", genre, art, key)
                imgs["ui"] = generate_specialized_image("ui", genre, art, key)
                imgs["world"] = generate_specialized_image("world", genre, art, key)
                imgs["asset"] = generate_specialized_image("character", genre, art, key)
                st.session_state['generated_images'] = imgs
                st.session_state['history'].append({"key": key, "content": gdd_res.text})

# Result Display
if st.session_state['gdd_result']:
    st.divider()
    
    # 📸 GDD Content Area
    st.markdown('<div id="gdd-capture-area">', unsafe_allow_html=True)
    st.markdown(f"<h1>{key.upper()} 기획서</h1>", unsafe_allow_html=True)
    
    imgs = st.session_state['generated_images']
    
    # 이미지 너비를 800px로 고정
    if imgs.get("concept"):
        st.image(base64.b64decode(imgs["concept"]), width=800)
        st.markdown('<p class="img-caption">[Main Concept Art]</p>', unsafe_allow_html=True)

    content = st.session_state['gdd_result']
    sections = content.split("## ")
    for i, section in enumerate(sections):
        if not section.strip(): continue
        sec_text = "## " + section if i > 0 else section
        st.markdown(sec_text) 
        
        # 중간 이미지 삽입 (800px 고정)
        if i == 1 and imgs.get("world"):
            st.image(base64.b64decode(imgs["world"]), width=800)
            st.markdown('<p class="img-caption">[World & Environment]</p>', unsafe_allow_html=True)
        elif i == 3 and imgs.get("ui"):
            st.image(base64.b64decode(imgs["ui"]), width=800)
            st.markdown('<p class="img-caption">[UI/UX Mockup]</p>', unsafe_allow_html=True)
        elif i == 5 and imgs.get("asset"):
            st.image(base64.b64decode(imgs["asset"]), width=800)
            st.markdown('<p class="img-caption">[Character & Assets]</p>', unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

    # 📥 Download Buttons
    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 PDF로 저장 / 인쇄하기 (추천 - 빠름)", use_container_width=True):
            # window.parent.print()를 사용하여 부모창 전체(기획서 영역 포함)를 인쇄 대상으로 설정
            components.html("<script>window.parent.print();</script>", height=0)
            st.info("💡 인쇄창이 뜨면 'PDF로 저장'을 선택해 주세요.")

    with col2:
        if st.button("🖼️ 고화질 이미지(PNG)로 저장하기", use_container_width=True):
            components.html(f"""
                <script>
                (function() {{
                    const script = document.createElement('script');
                    script.src = "https://html2canvas.hertzen.com/dist/html2canvas.min.js";
                    script.onload = function() {{
                        const area = window.parent.document.getElementById('gdd-capture-area');
                        html2canvas(area, {{
                            useCORS: true,
                            scale: 2,
                            backgroundColor: "#ffffff",
                            windowWidth: area.scrollWidth,
                            windowHeight: area.scrollHeight
                        }}).then(canvas => {{
                            const link = document.createElement('a');
                            link.download = 'Vito_GDD_Report_{key}.png';
                            link.href = canvas.toDataURL('image/png');
                            link.click();
                        }});
                    }};
                    document.head.appendChild(script);
                }})();
                </script>
            """, height=0)
            st.success("이미지 생성을 시작했습니다. 완료 후 자동으로 다운로드됩니다!")

st.caption("비토쨩 GDD Pro | Reliable Multi-Format Export")