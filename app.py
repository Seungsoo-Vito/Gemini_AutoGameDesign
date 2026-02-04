import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import zlib
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
    
    #gdd-capture-area {
        background: #ffffff;
        padding: 50px;
        border-radius: 24px;
        border: 1px solid #f1f3f5;
        box-shadow: 0 12px 24px rgba(0,0,0,0.05);
        color: #2d3436;
    }
    
    .gdd-card {
        background: #ffffff;
        padding: 20px;
        margin-bottom: 20px;
    }

    .gdd-card h1, .gdd-card h2, .gdd-card h3 {
        color: #1f2937 !important;
        border-bottom: 3px solid #e0e7ff;
        display: inline-block;
        padding-bottom: 4px;
        margin-top: 30px;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white; border: none; border-radius: 14px; font-weight: 700; height: 3.5rem;
        transition: all 0.3s;
    }
    
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(99, 102, 241, 0.3);
    }

    .history-item {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 14px;
        padding: 15px;
        margin-bottom: 12px;
    }
    
    .img-caption {
        font-size: 0.9rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 30px;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔒 API 키 보안 관리 ---
# 1순위: st.secrets에서 가져오기 (배포/설정용)
# 2순위: 사이드바에서 직접 입력받기
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("🔑 보안 설정")
    if not API_KEY:
        API_KEY = st.text_input("Gemini API Key를 입력하세요", type="password", help="키는 코드에 저장되지 않으며 세션 동안만 유지됩니다.")
        if API_KEY:
            st.success("API 키가 설정되었습니다.")
    else:
        st.info("✅ 보안 설정(Secrets)에서 API 키를 불러왔습니다.")

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 🎨 지능형 이미지 생성 엔진 ---
def generate_specialized_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    
    prompts = {
        "concept": f"Main key visual art for a {genre} game, theme of {key}, {art} style. Cinematic composition, high quality, epic scale.",
        "ui": f"Game UI and UX design for {genre} mobile game, {art} style. Inventory screen and HUD, clean layout, matching {key} theme. High fidelity mockup.",
        "world": f"Environment concept art, world map or background for {genre} game, {art} style, location: {key}. Immersive atmosphere, 8k resolution.",
        "character": f"Character design sheet or detailed game asset for {genre}, {art} style, based on {key}. Front view, professional game art."
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
            col_main, col_tools = st.columns([4, 1])
            if col_main.button(f"📄 {display_name[:12]}", key=f"hist_load_{i}", use_container_width=True):
                st.session_state['gdd_result'] = item['content']
                st.session_state['generated_images'] = item.get('images', {})
                st.session_state['editing_index'] = -1

            if col_tools.button("✏️", key=f"hist_edit_{i}", use_container_width=True):
                st.session_state['editing_index'] = i
            
            if st.session_state['editing_index'] == i:
                new_name = st.text_input("이름 변경", value=display_name, key=f"hist_name_{i}")
                if st.button("저장", key=f"hist_save_{i}", use_container_width=True):
                    st.session_state['history'][i]['custom_name'] = new_name
                    st.session_state['editing_index'] = -1
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    if st.button("전체 기록 삭제", use_container_width=True):
        st.session_state['history'] = []
        st.session_state['gdd_result'] = None
        st.rerun()

# --- 4. UI 메인 ---
st.markdown('<h1 class="main-title">비토쨩 GDD Pro</h1>', unsafe_allow_html=True)
st.write("안전한 API 관리 모드가 적용되었습니다. 기획서를 이미지로 다운로드하세요.")
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
            st.error("사이드바에 API 키를 입력해 주세요.")
        elif not key:
            st.warning("키워드를 입력해 주세요.")
        else:
            with st.spinner("비토쨩이 안전하게 데이터를 처리 중입니다..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                
                # 1. GDD 본문 생성
                gdd_res = model.generate_content(f"장르: {genre}, 국가: {target}, 키워드: {key}, 아트: {art} 전문 GDD 작성.")
                st.session_state['gdd_result'] = gdd_res.text
                
                # 2. 이미지 생성
                imgs = {}
                imgs["concept"] = generate_specialized_image("concept", genre, art, key)
                imgs["ui"] = generate_specialized_image("ui", genre, art, key)
                imgs["world"] = generate_specialized_image("world", genre, art, key)
                imgs["asset"] = generate_specialized_image("character", genre, art, key)
                st.session_state['generated_images'] = imgs

                # 3. 히스토리 저장
                st.session_state['history'].append({
                    "key": key, "content": gdd_res.text, "images": imgs, "custom_name": None
                })

# 결과 출력 및 이미지 다운로드 로직
if st.session_state['gdd_result']:
    st.divider()
    
    components.html("""
        <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
        <script>
        function downloadGDDImage() {
            const area = window.parent.document.getElementById('gdd-capture-area');
            html2canvas(area, {
                useCORS: true,
                scale: 2,
                backgroundColor: "#ffffff"
            }).then(canvas => {
                const link = document.createElement('a');
                link.download = 'Vito_GDD_Report.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            });
        }
        </script>
    """, height=0)

    # 📸 기획서 본문 영역
    st.markdown('<div id="gdd-capture-area">', unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center;'>GAME DESIGN DOCUMENT: {key}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#64748b;'>Powered by Vito-chan GDD Pro | Secure Mode</p><br>", unsafe_allow_html=True)
    
    imgs = st.session_state['generated_images']
    
    if imgs.get("concept"):
        st.image(base64.b64decode(imgs["concept"]), use_container_width=True)
        st.markdown('<p class="img-caption">[Main Concept Visual]</p>', unsafe_allow_html=True)

    parts = st.session_state['gdd_result'].split("\n\n")
    for i, part in enumerate(parts):
        st.markdown(f'<div class="gdd-card">{part}</div>', unsafe_allow_html=True)
        
        if i == 1 and imgs.get("world"):
            st.image(base64.b64decode(imgs["world"]), width=800)
            st.markdown('<p class="img-caption">[World Reference]</p>', unsafe_allow_html=True)
        elif ("시스템" in part or "UI" in part) and imgs.get("ui"):
            st.image(base64.b64decode(imgs["ui"]), width=800)
            st.markdown('<p class="img-caption">[UI/UX Mockup]</p>', unsafe_allow_html=True)
        elif ("캐릭터" in part or "전투" in part) and imgs.get("asset"):
            st.image(base64.b64decode(imgs["asset"]), width=800)
            st.markdown('<p class="img-caption">[Character & Asset Concept]</p>', unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")
    if st.button("🖼️ 완성된 기획서를 이미지로 다운받기", type="secondary", use_container_width=True):
        components.html("""
            <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
            <script>
                const area = window.parent.document.getElementById('gdd-capture-area');
                html2canvas(area, {
                    useCORS: true,
                    scale: 2,
                    backgroundColor: "#ffffff"
                }).then(canvas => {
                    const link = document.createElement('a');
                    link.download = 'Game_GDD_Report.png';
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                });
            </script>
        """, height=0)
        st.success("이미지 생성이 시작되었습니다.")

st.caption("비토쨩 GDD Pro | Secure API & Image Export Mode")