import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re
import os.path
import streamlit.components.v1 as components

# 1. 페이지 설정
st.set_page_config(page_title="비토쨩 GDD Pro", page_icon="🎮", layout="wide")

# --- 🎨 UI 스타일링 ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #fdfdfd; color: #2d3436; font-family: 'Pretendard', sans-serif; }
    
    [data-testid="stSidebar"] {
        background-color: #f1f3f5;
        border-right: 1px solid #e9ecef;
    }

    .main-title {
        font-size: 3.5rem !important; font-weight: 900 !important;
        background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 50%, #a1c4fd 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem !important;
    }
    
    /* 📸 캡처 영역 디자인 */
    #gdd-capture-area {
        background: #ffffff;
        padding: 60px;
        border-radius: 30px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 20px 50px rgba(0,0,0,0.05);
        color: #1e293b;
        margin-top: 20px;
    }
    
    .gdd-section {
        background: #f8fafc;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 25px;
        border: 1px solid #f1f5f9;
    }

    .gdd-section h2, .gdd-section h3 {
        color: #4f46e5 !important;
        margin-top: 0;
        border-left: 6px solid #6366f1;
        padding-left: 15px;
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
    
    .img-caption {
        font-size: 0.95rem;
        color: #94a3b8;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 30px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔒 API 키 보안 관리 ---
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

# --- 🎨 지능형 이미지 생성 엔진 ---
def generate_specialized_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    
    prompts = {
        "concept": f"Main key visual art for a {genre} game, theme of {key}, {art} style. Epic cinematic lighting.",
        "ui": f"High fidelity game UI/UX design for {genre} mobile game, {art} style. Dashboard and menus.",
        "world": f"Beautiful environment concept art for {genre} game, world of {key}, {art} style.",
        "character": f"Detailed character design sheet for {genre}, {art} style, {key} theme."
    }
    
    selected_prompt = prompts.get(prompt_type, prompts["concept"])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {"instances": [{"prompt": selected_prompt}], "parameters": {"sampleCount": 1}}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.json()["predictions"][0]["bytesBase64Encoded"]
    except:
        return None

# 세션 상태 관리
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'generated_images' not in st.session_state: st.session_state['generated_images'] = {}
if 'history' not in st.session_state: st.session_state['history'] = []
if 'editing_index' not in st.session_state: st.session_state['editing_index'] = -1

# --- 3. UI 사이드바 ---
with st.sidebar:
    st.divider()
    st.header("🕒 기획 히스토리")
    if not st.session_state['history']:
        st.write("기록이 없습니다.")
    else:
        for i in range(len(st.session_state['history']) - 1, -1, -1):
            item = st.session_state['history'][i]
            display_name = item.get('custom_name') or f"{item['key']}"
            st.markdown(f'<div class="history-item">', unsafe_allow_html=True)
            if st.button(f"📄 {display_name[:12]}", key=f"hist_load_{i}", use_container_width=True):
                st.session_state['gdd_result'] = item['content']
                st.session_state['generated_images'] = item.get('images', {})
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 4. UI 메인 ---
st.markdown('<h1 class="main-title">비토쨩 GDD Pro</h1>', unsafe_allow_html=True)
st.write("이미지 다운로드 기능이 강화된 고품격 AI 게임 기획 도구")
st.divider()

# 입력 섹션
with st.container():
    st.markdown('<div class="gdd-card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1: genre = st.selectbox("장르", ["방치형 RPG", "수집형 RPG", "오픈월드", "로그라이크", "액션"])
    with c2: target = st.selectbox("타겟 국가", ["글로벌", "한국", "일본", "북미/유럽"])
    with c3: art = st.selectbox("스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼"])
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프")
    
    st.write("")
    if st.button("전문 기획서 생성 및 아트 빌드 ✨", type="primary", use_container_width=True):
        if not API_KEY:
            st.error("API 키를 입력해 주세요.")
        elif not key:
            st.warning("키워드를 입력해 주세요.")
        else:
            with st.spinner("비토쨩이 최고의 기획서와 아트를 생성 중입니다..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                gdd_res = model.generate_content(f"장르: {genre}, 국가: {target}, 키워드: {key}, 아트: {art} 조건으로 시니어 게임 기획자로서 전문 GDD 작성.")
                st.session_state['gdd_result'] = gdd_res.text
                
                imgs = {}
                imgs["concept"] = generate_specialized_image("concept", genre, art, key)
                imgs["ui"] = generate_specialized_image("ui", genre, art, key)
                imgs["world"] = generate_specialized_image("world", genre, art, key)
                imgs["asset"] = generate_specialized_image("character", genre, art, key)
                st.session_state['generated_images'] = imgs
                st.session_state['history'].append({"key": key, "content": gdd_res.text, "images": imgs})

# 결과 출력
if st.session_state['gdd_result']:
    st.divider()
    
    # 📸 기획서 본문 영역 (캡처 대상)
    st.markdown('<div id="gdd-capture-area">', unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; font-size: 50px;'>GAME DESIGN DOCUMENT</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; color:#6366f1;'>{key.upper()}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#94a3b8;'>Produced by Vito-chan GDD Pro AI</p><br>", unsafe_allow_html=True)
    
    imgs = st.session_state['generated_images']
    if imgs.get("concept"):
        st.image(base64.b64decode(imgs["concept"]), use_container_width=True)
        st.markdown('<p class="img-caption">[Main Concept Art]</p>', unsafe_allow_html=True)

    parts = st.session_state['gdd_result'].split("\n\n")
    for i, part in enumerate(parts):
        st.markdown(f'<div class="gdd-section">{part}</div>', unsafe_allow_html=True)
        if i == 1 and imgs.get("world"):
            st.image(base64.b64decode(imgs["world"]), use_container_width=True)
            st.markdown('<p class="img-caption">[World & Environment]</p>', unsafe_allow_html=True)
        elif ("시스템" in part or "UI" in part) and imgs.get("ui"):
            st.image(base64.b64decode(imgs["ui"]), use_container_width=True)
            st.markdown('<p class="img-caption">[Game UI/UX Mockup]</p>', unsafe_allow_html=True)
        elif ("캐릭터" in part or "전투" in part) and imgs.get("asset"):
            st.image(base64.b64decode(imgs["asset"]), use_container_width=True)
            st.markdown('<p class="img-caption">[Hero & Asset Design]</p>', unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

    # 📥 이미지 다운로드 버튼
    st.write("---")
    if st.button("🖼️ 완성된 기획서를 이미지로 다운받기", use_container_width=True):
        # 자바스크립트 실행 (보안 및 로드 타이밍 강화)
        components.html(f"""
            <script>
            (function() {{
                const script = document.createElement('script');
                script.src = "https://html2canvas.hertzen.com/dist/html2canvas.min.js";
                script.onload = function() {{
                    const area = window.parent.document.getElementById('gdd-capture-area');
                    if (!area) {{
                        console.error("Capture area not found");
                        return;
                    }}
                    html2canvas(area, {{
                        useCORS: true,
                        allowTaint: false,
                        scale: 2,
                        logging: false,
                        backgroundColor: "#ffffff"
                    }}).then(canvas => {{
                        const link = document.createElement('a');
                        link.download = 'GDD_Report_{key}.png';
                        link.href = canvas.toDataURL('image/png');
                        link.click();
                    }}).catch(err => {{
                        console.error("Canvas capture error:", err);
                    }});
                }};
                document.head.appendChild(script);
            }})();
            </script>
        """, height=0)
        st.success("이미지 캡처를 시작했습니다. 완료될 때까지 잠시만 기다려 주세요!")

st.caption("비토쨩 GDD Pro | Reliable Image Export Engine")