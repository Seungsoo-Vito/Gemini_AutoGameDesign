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

# --- 🎨 High-End Responsive UI Styling ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
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
    
    #gdd-capture-area img {
        max-width: 100% !important;
        height: auto !important;
        border-radius: 8px;
        display: block;
        margin: 20px auto;
    }

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
st.write("저장 기능이 강화된 고품격 게임 기획서 생성 도구입니다.")
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

# Result Display Logic
if st.session_state['gdd_result']:
    st.divider()
    
    # 📸 GDD 렌더링 (미리보기용)
    st.markdown('<div id="gdd-capture-area">', unsafe_allow_html=True)
    st.markdown(f"<h1>{key.upper()} 기획안</h1>", unsafe_allow_html=True)
    
    imgs = st.session_state['generated_images']
    
    if imgs.get("concept"):
        st.markdown('<div class="img-wrapper">', unsafe_allow_html=True)
        st.image(base64.b64decode(imgs["concept"]), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<p class="img-caption">[Main Visual Concept]</p>', unsafe_allow_html=True)

    content = st.session_state['gdd_result']
    # 마크다운 렌더링을 위해 간단한 HTML 변환 대신 st.markdown 사용
    sections = content.split("## ")
    for i, section in enumerate(sections):
        if not section.strip(): continue
        sec_text = "## " + section if i > 0 else section
        st.markdown(sec_text) 
        
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

    # --- 📥 저장 엔진 (보안 및 격리벽 해결) ---
    st.write("---")
    
    # 자바스크립트에 전달할 데이터 준비
    export_data = {
        "title": f"{key.upper()} 기획안",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['generated_images']
    }
    
    # 고도화된 export 컴포넌트
    components.html(f"""
        <div style="display: flex; gap: 10px; margin-bottom: 20px;">
            <button id="pdfBtn" style="flex:1; background: #6366f1; color: white; border: none; padding: 15px; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 16px;">
                📄 PDF 저장 (새 창)
            </button>
            <button id="pngBtn" style="flex:1; background: #a855f7; color: white; border: none; padding: 15px; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 16px;">
                🖼️ 이미지(PNG) 저장
            </button>
        </div>
        
        <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
        <script>
            const data = {json.dumps(export_data)};
            
            // 헬퍼: HTML 문서 생성
            function createPrintHTML(data) {{
                let html = `<html><head><title>${{data.title}}</title>`;
                html += `<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">`;
                html += `<style>
                    body {{ font-family: 'Pretendard', sans-serif; padding: 40px; color: #1e293b; max-width: 800px; margin: 0 auto; }}
                    h1 {{ font-size: 32px; border-bottom: 4px solid #6366f1; padding-bottom: 10px; text-align: center; }}
                    h2 {{ color: #4f46e5; margin-top: 30px; border-left: 5px solid #6366f1; padding-left: 10px; }}
                    img {{ max-width: 100%; border-radius: 8px; margin: 20px 0; }}
                    p, li {{ font-size: 16px; line-height: 1.6; margin-bottom: 10px; }}
                    .caption {{ text-align: center; color: #94a3b8; font-size: 14px; margin-bottom: 20px; }}
                </style></head><body>`;
                
                html += `<h1>${{data.title}}</h1>`;
                
                if(data.images.concept) {{
                    html += `<img src="data:image/png;base64,${{data.images.concept}}"><div class="caption">[Main Visual]</div>`;
                }}
                
                const sections = data.content.split('## ');
                sections.forEach((sec, i) => {{
                    if(!sec.trim()) return;
                    html += '<h2>' + (i > 0 ? '## ' : '') + sec.replace(/\\n/g, '<br>') + '</h2>';
                    
                    if(i === 1 && data.images.world) html += `<img src="data:image/png;base64,${{data.images.world}}"><div class="caption">[World]</div>`;
                    if(i === 3 && data.images.ui) html += `<img src="data:image/png;base64,${{data.images.ui}}"><div class="caption">[UI/UX]</div>`;
                    if(i === 5 && data.images.asset) html += `<img src="data:image/png;base64,${{data.images.asset}}"><div class="caption">[Asset]</div>`;
                }});
                
                html += `</body></html>`;
                return html;
            }}

            // PDF/인쇄 기능
            document.getElementById('pdfBtn').onclick = () => {{
                const win = window.open('', '_blank');
                win.document.write(createPrintHTML(data));
                win.document.close();
                win.onload = () => {{
                    win.focus();
                    win.print();
                }};
            }};

            // 이미지 저장 기능
            document.getElementById('pngBtn').onclick = () => {{
                const tempDiv = document.createElement('div');
                tempDiv.style.position = 'absolute';
                tempDiv.style.left = '-9999px';
                tempDiv.style.width = '800px';
                tempDiv.innerHTML = createPrintHTML(data);
                document.body.appendChild(tempDiv);

                const btn = document.getElementById('pngBtn');
                btn.innerText = "⏳ 처리 중...";
                btn.disabled = true;

                setTimeout(() => {{
                    html2canvas(tempDiv, {{ 
                        useCORS: true, 
                        scale: 2,
                        backgroundColor: "#ffffff"
                    }}).then(canvas => {{
                        const link = document.createElement('a');
                        link.download = `GDD_${{data.title}}.png`;
                        link.href = canvas.toDataURL('image/png');
                        link.click();
                        btn.innerText = "🖼️ 이미지(PNG) 저장";
                        btn.disabled = false;
                        document.body.removeChild(tempDiv);
                    }}).catch(err => {{
                        alert("이미지 생성 중 오류가 발생했습니다.");
                        console.error(err);
                        btn.disabled = false;
                    }});
                }}, 500);
            }};
        </script>
    """, height=100)

st.caption("비토쨩 GDD Pro | Secure Export System Active")