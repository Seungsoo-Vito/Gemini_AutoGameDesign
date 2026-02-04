import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re
import os.path
import streamlit.components.v1 as components

# 1. Page Configuration (최대 너비 확보)
st.set_page_config(page_title="비토쨩 자동 기획서 연습", page_icon="🎮", layout="wide")

# --- 🎨 프리미엄 에디토리얼 UI 스타일링 (Ultra-Wide) ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    .stApp { 
        background-color: #f1f5f9; 
        color: #1e293b; 
        font-family: 'Pretendard', sans-serif; 
    }
    
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    .main-title {
        font-size: calc(2.5rem + 2vw) !important; 
        font-weight: 900 !important;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        text-align: center;
        letter-spacing: -0.05em;
        margin-bottom: 0.5rem !important;
    }
    
    div.stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: all 0.2s;
        height: 3.8rem;
        font-size: 1.1rem !important;
    }
    
    .status-card {
        padding: 10px;
        border-radius: 8px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        margin-bottom: 5px;
        font-size: 0.85rem;
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
    st.header("🔑 보안 및 설정")
    if not API_KEY:
        API_KEY = st.text_input("Gemini API Key를 입력하세요", type="password")
    else:
        st.info("✅ API 키 로드 완료")

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 🎨 Intelligent Image Engine ---
def generate_specialized_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    prompts = {
        "concept": f"Epic cinematic game key visual art, {genre}, theme: {key}, style: {art}. 8k, professional lighting.",
        "ui": f"High-fidelity mobile game UI design mockup, {genre} HUD, style: {art}. Dashboard, clean layout, inspired by {key}.",
        "world": f"Environment concept art, immersive game world, {genre}, location theme: {key}, style: {art}.",
        "character": f"Character concept portrait, {genre} hero unit, motif: {key}, style: {art}. Professional digital asset."
    }
    selected_prompt = prompts.get(prompt_type, prompts["concept"])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {"instances": [{"prompt": selected_prompt}], "parameters": {"sampleCount": 1}}
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()["predictions"][0]["bytesBase64Encoded"]
    except: pass
    return None

# Session State
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'generated_images' not in st.session_state: st.session_state['generated_images'] = {}
if 'history' not in st.session_state: st.session_state['history'] = []

# --- 3. Sidebar History & Status ---
with st.sidebar:
    st.divider()
    st.header("🕒 기획 히스토리")
    if st.session_state['history']:
        for i, item in enumerate(st.session_state['history'][::-1]):
            if st.button(f"📄 {item['key'][:12]}", key=f"hist_{i}", use_container_width=True):
                st.session_state['gdd_result'] = item['content']
                st.session_state['generated_images'] = item.get('images', {})
                st.rerun()
    
    if st.session_state['generated_images']:
        st.divider()
        st.header("🖼️ 이미지 준비 상태")
        for k, v in st.session_state['generated_images'].items():
            color = "#10b981" if v else "#ef4444"
            status = "준비됨" if v else "실패"
            st.markdown(f"""<div class='status-card'>{k.upper()}: <b style='color:{color}'>{status}</b></div>""", unsafe_allow_html=True)

# --- 4. UI Main ---
st.markdown('<h1 class="main-title">비토쨩 자동 기획서 만들기 🎮</h1>', unsafe_allow_html=True)
st.write("제미나이를 활용한 연습. (주요 카테고리 중심의 선택적 이미지 배치)")
st.divider()

# Input Options
genres = ["방치형 RPG", "수집형 RPG", "액션 RPG", "MMORPG", "로그라이크", "전략 시뮬레이션", "FPS/TPS"]
targets = ["글로벌", "한국", "일본", "중국", "북미", "유럽"]
styles = ["픽셀 아트 (Retro)", "2D 카툰/애니메이션", "실사풍", "3D 캐주얼", "사이버펑크", "다크 판타지"]

with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르 선택", genres)
    with c2: target = st.selectbox("타겟 국가", targets)
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("아트 스타일", styles)
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프, 지하철")
    
    if st.button("전문 기획서 생성 시작 ✨", type="primary", use_container_width=True):
        if not API_KEY: st.error("API 키를 입력해 주세요.")
        elif not key: st.warning("키워드를 입력해 주세요.")
        else:
            with st.spinner("시니어 기획자가 핵심 섹션을 설계하고 아트를 생성 중입니다..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"당신은 전설적인 기획자입니다. 장르={genre}, 국가={target}, 키워드={key}, 아트={art} 조건으로 상세 GDD를 작성하세요. 핵심 시스템, 콘텐츠 순환, UI/UX 전략을 매우 전문적으로 다루되 섹션 사이의 불필요한 '#' 기호는 제거하세요."
                gdd_res = model.generate_content(prompt)
                st.session_state['gdd_result'] = gdd_res.text
                
                # 이미지 생성
                imgs = {
                    "concept": generate_specialized_image("concept", genre, art, key),
                    "world": generate_specialized_image("world", genre, art, key),
                    "ui": generate_specialized_image("ui", genre, art, key),
                    "character": generate_specialized_image("character", genre, art, key)
                }
                st.session_state['generated_images'] = imgs
                st.session_state['history'].append({"key": key, "content": gdd_res.text, "images": imgs})

# --- 5. Result Display & Export Engine (정밀 렌더링 시스템) ---
if st.session_state['gdd_result']:
    st.divider()
    
    export_payload = {
        "title": f"{key.upper()} 기획안",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['generated_images']
    }
    
    components.html(f"""
        <div id="render-target"></div>
        <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
        <script>
            const data = {json.dumps(export_payload)};
            
            function cleanMd(md) {{
                return md
                    .replace(/^#\s*$/gm, '')
                    .replace(/^### (.*$)/gim, '<h3 style="font-size:26px; font-weight:700; color:#1e293b; margin-top:40px; border-bottom:2px solid #f1f5f9; padding-bottom:10px;">$1</h3>')
                    .replace(/^## (.*$)/gim, '<h2 style="font-size:34px; font-weight:800; color:#4f46e5; border-left:15px solid #4f46e5; padding:15px 30px; background:#f8fafc; margin-top:70px; border-radius:0 15px 15px 0;">$1</h2>')
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                    .replace(/^\\* (.*$)/gim, '<li style="margin-bottom:15px; font-size:20px; color:#475569;">$1</li>')
                    .replace(/\\n/g, '<br>')
                    .replace(/(<li>.*<\\/li>)/s, '<ul style="padding-left:40px; margin-bottom:40px;">$1</ul>');
            }}

            function buildHTML(data) {{
                let html = `<div id="export-area" style="background:white; padding:100px 80px; border-radius:24px; font-family:'Pretendard', sans-serif; color:#1e293b; line-height:1.9; max-width:1200px; margin:0 auto; border:1px solid #e2e8f0; box-shadow:0 20px 50px rgba(0,0,0,0.08);">`;
                html += `<h1 style="font-size:64px; font-weight:900; text-align:center; border-bottom:12px solid #4f46e5; padding-bottom:30px; margin-bottom:60px; letter-spacing:-0.04em;">${{data.title}}</h1>`;
                
                // 1. [메인] 최상단 배치
                if(data.images.concept) {{
                    html += `<div style="text-align:center; margin-bottom:80px;"><img src="data:image/png;base64,${{data.images.concept}}" style="max-width:1000px; width:100%; border-radius:20px; box-shadow:0 15px 40px rgba(0,0,0,0.15);"><div style="color:#64748b; font-size:18px; margin-top:20px; font-style:italic; font-weight:600;">[Key Concept Architecture]</div></div>`;
                }}
                
                const sections = data.content.split('## ');
                let usedKeys = new Set();

                // 섹션별 주요 이미지 매칭 테이블
                const imgMap = {{
                    "world": ["세계관", "배경", "아트", "분위기"],
                    "ui": ["시스템", "UI", "인터페이스", "화면", "메커니즘"],
                    "character": ["캐릭터", "에셋", "유닛", "영웅", "몬스터"]
                }};

                sections.forEach((sec, i) => {{
                    if(!sec.trim()) return;
                    let title = sec.split('\\n')[0];
                    html += cleanMd((i > 0 ? '## ' : '') + sec);
                    
                    // 해당 섹션이 주요 카테고리인 경우 이미지 삽입
                    for(let key in imgMap) {{
                        if(!usedKeys.has(key)) {{
                            if(imgMap[key].some(kw => title.includes(kw)) && data.images[key]) {{
                                const label = key === 'world' ? 'World View' : (key === 'ui' ? 'UI Mockup' : 'Character Asset');
                                html += `<div style="text-align:center; margin:60px 0;"><img src="data:image/png;base64,${{data.images[key]}}" style="max-width:1000px; width:100%; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.1);"><div style="color:#64748b; font-size:16px; margin-top:15px; font-weight:600;">[Design Reference: ${{label}}]</div></div>`;
                                usedKeys.add(key);
                                break;
                            }
                        }
                    }
                }});
                
                html += `</div>`;
                return html;
            }}

            const target = document.getElementById('render-target');
            target.innerHTML = `
                <div style="display:flex; gap:25px; margin-bottom:50px; max-width:1200px; margin-left:auto; margin-right:auto;">
                    <button id="pdfBtn" style="flex:1; background:#4f46e5; color:white; border:none; padding:25px; border-radius:16px; font-weight:900; cursor:pointer; font-size:20px; box-shadow:0 10px 25px rgba(79,70,229,0.3);">📄 PDF로 저장</button>
                    <button id="pngBtn" style="flex:1; background:#7c3aed; color:white; border:none; padding:25px; border-radius:16px; font-weight:900; cursor:pointer; font-size:20px; box-shadow:0 10px 25px rgba(124,58,237,0.3);">🖼️ 이미지 저장</button>
                </div>
                <div id="preview-box">${{buildHTML(data)}}</div>
            `;

            document.getElementById('pdfBtn').onclick = () => {{
                const win = window.open('', '_blank');
                win.document.write('<html><head><meta charset="UTF-8"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css"></head><body style="margin:0; background:#f1f5f9;">' + document.getElementById('export-area').outerHTML + '</body></html>');
                win.document.close();
                win.onload = () => setTimeout(() => {{ win.focus(); win.print(); }}, 1000);
            }};

            document.getElementById('pngBtn').onclick = () => {{
                const btn = document.getElementById('pngBtn');
                btn.innerText = "⏳ 렌더링 중...";
                html2canvas(document.getElementById('export-area'), {{ useCORS: true, scale: 2 }}).then(canvas => {{
                    const a = document.createElement('a');
                    a.download = `GDD_${{data.title}}.png`;
                    a.href = canvas.toDataURL('image/png');
                    a.click();
                    btn.innerText = "🖼️ 이미지 저장";
                }});
            }};
        </script>
    """, height=4000, scrolling=True)

st.caption("비토쨩 연습하기")