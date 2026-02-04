import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re
import os.path
import streamlit.components.v1 as components

# 1. Page Configuration (와이드 모드)
st.set_page_config(page_title="비토쨩 자동 기획서 연습", page_icon="🎮", layout="wide")

# --- 🎨 프리미엄 에디토리얼 UI 스타일링 ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #f1f5f9; color: #1e293b; font-family: 'Pretendard', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    .main-title {
        font-size: calc(2.5rem + 2vw) !important; font-weight: 900 !important;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 0.5rem !important;
    }
    div.stButton > button {
        border-radius: 12px !important; font-weight: 700 !important;
        transition: all 0.2s; height: 3.8rem;
    }
    .status-badge {
        padding: 10px; border-radius: 8px; background: #f8fafc; border: 1px solid #e2e8f0; margin-bottom: 5px; font-size: 0.85rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔒 API 키 설정 ---
def load_api_key():
    for k in ["GEMINI_API_KEY", "gemini_api_key", "API_KEY"]:
        if k in st.secrets: return st.secrets[k]
    return ""

API_KEY = load_api_key()
with st.sidebar:
    st.header("🔑 보안 및 설정")
    if not API_KEY:
        API_KEY = st.text_input("Gemini API Key", type="password")
    else:
        st.info("✅ API Key Ready")

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 🎨 고화질 이미지 엔진 (Imagen 4.0) ---
def generate_hd_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    prompts = {
        "concept": f"Masterpiece cinematic game key visual, {genre}, theme: {key}, style: {art}. 8k, professional game art.",
        "ui": f"Professional High-fidelity mobile game UI design mockup, {genre}, style: {art}. Clean layout, menu, HUD, inspired by {key}.",
        "world": f"Stunning detailed environment concept art, {genre} game world, location: {key}, style: {art}. Atmospheric landscape.",
        "character": f"High-quality character asset sheet, {genre} hero, motif: {key}, style: {art}. Professional character design portrait."
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {"instances": [{"prompt": prompts.get(prompt_type, prompts["concept"])}], "parameters": {"sampleCount": 1}}
    try:
        response = requests.post(url, json=payload, timeout=90)
        if response.status_code == 200:
            return response.json()["predictions"][0]["bytesBase64Encoded"]
    except: pass
    return None

# 세션 상태
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'generated_images' not in st.session_state: st.session_state['generated_images'] = {}

# 메인 UI
st.markdown('<h1 class="main-title">비토쨩 자동 기획서 만들기 🎮</h1>', unsafe_allow_html=True)
st.write("제미나이를 활용한 연습. (이미지 출력 안정성이 대폭 강화되었습니다.)")
st.divider()

# 입력 섹션
with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르", ["방치형 RPG", "수집형 RPG", "MMORPG", "로그라이크", "FPS/TPS"])
    with c2: target = st.selectbox("타겟", ["글로벌", "한국", "일본", "북미", "유럽"])
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("스타일", ["픽셀 아트 (Retro)", "2D 카툰", "실사풍", "3D 캐주얼", "사이버펑크"])
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 우주항해")
    
    if st.button("고품격 기획서 생성 시작 ✨", type="primary", use_container_width=True):
        if not API_KEY: st.error("API 키를 입력하세요.")
        elif not key: st.warning("키워드를 입력하세요.")
        else:
            with st.spinner("이미지를 포함한 전문 기획서를 작성 중입니다 (약 1분 소요)..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"당신은 시니어 기획자입니다. 장르={genre}, 국가={target}, 키워드={key}, 아트={art} 조건으로 전문 GDD를 작성하세요. 핵심 시스템, 콘텐츠 순환, UI 전략을 상세히 포함하세요. 섹션 제목은 반드시 '## 제목' 형식을 사용하고 불필요한 '#' 기호 한 줄은 넣지 마세요."
                gdd_res = model.generate_content(prompt)
                st.session_state['gdd_result'] = gdd_res.text
                
                # 이미지 생성
                st.session_state['generated_images'] = {
                    "concept": generate_hd_image("concept", genre, art, key),
                    "world": generate_hd_image("world", genre, art, key),
                    "ui": generate_hd_image("ui", genre, art, key),
                    "character": generate_hd_image("character", genre, art, key)
                }

# --- 🚀 고도화된 하이엔드 렌더링 엔진 ---
if st.session_state['gdd_result']:
    st.divider()
    
    # 데이터 직렬화
    payload = {
        "title": f"{key.upper()} 기획안",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['generated_images']
    }
    
    # f-string 에러 방지를 위한 템플릿 방식
    html_template = """
    <div id="render-target"></div>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
        const rawData = ST_DATA_JSON;
        
        function clean(md) {
            return md.split('\\n').map(line => {
                let l = line.trim();
                if (!l || l === '#' || l === '##') return '';
                if (l.startsWith('###')) return `<h3 style="font-size:24px; font-weight:700; color:#1e293b; margin-top:40px; border-bottom:2px solid #f1f5f9; padding-bottom:8px;">${l.replace(/^###\s*/, '')}</h3>`;
                if (l.startsWith('##')) return `<h2 style="font-size:32px; font-weight:800; color:#4f46e5; border-left:12px solid #4f46e5; padding-left:25px; background:#f8fafc; margin-top:60px; border-radius:0 12px 12px 0;">${l.replace(/^##\s*/, '')}</h2>`;
                if (l.startsWith('* ') || l.startsWith('- ')) return `<li style="font-size:20px; color:#334155; margin-bottom:10px; margin-left:20px;">${l.replace(/^[*|-]\s*/, '')}</li>`;
                if (l.includes('**')) l = l.replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color:#4f46e5;">$1</strong>');
                return `<p style="font-size:20px; color:#334155; line-height:1.9; text-align:justify; margin-bottom:20px;">${l}</p>`;
            }).join('');
        }

        function buildDoc() {
            let html = `<div id="paper" style="background:white; padding:100px 80px; border-radius:32px; font-family:'Pretendard', sans-serif; color:#1e293b; max-width:1200px; margin:0 auto; border:1px solid #e2e8f0; box-shadow:0 30px 60px rgba(0,0,0,0.08);">`;
            html += `<h1 style="font-size:68px; font-weight:900; text-align:center; border-bottom:12px solid #4f46e5; padding-bottom:40px; margin-bottom:80px; letter-spacing:-0.05em;">${rawData.title}</h1>`;
            
            // 1. 메인 이미지 (상단 고정)
            if(rawData.images.concept) {
                html += `<div style="text-align:center; margin-bottom:80px;"><img src="data:image/png;base64,${rawData.images.concept}" style="width:100%; max-width:1000px; border-radius:24px; box-shadow:0 15px 40px rgba(0,0,0,0.1);"><div style="color:#64748b; font-size:16px; margin-top:15px; font-weight:600;">[Key Visual Concept]</div></div>`;
            }
            
            const sections = rawData.content.split('## ');
            const imgSlots = [
                { data: rawData.images.world, label: 'WORLD CONCEPT' },
                { data: rawData.images.ui, label: 'UI/UX MOCKUP' },
                { data: rawData.images.character, label: 'CHARACTER ASSET' }
            ].filter(s => s.data);

            sections.forEach((sec, i) => {
                if(!sec.trim()) return;
                html += clean((i > 0 ? '## ' : '') + sec);
                
                // 섹션 2개마다 하나씩 이미지를 강제 배치 (누락 방지)
                if(i % 2 === 1 && imgSlots.length > 0) {
                    let slot = imgSlots.shift();
                    html += `<div style="text-align:center; margin:80px 0; padding:40px; background:#f8fafc; border-radius:24px;"><img src="data:image/png;base64,${slot.data}" style="width:100%; max-width:1000px; border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,0.08);"><div style="color:#64748b; font-size:16px; margin-top:15px; font-weight:600;">[Visual Reference: ${slot.label}]</div></div>`;
                }
            });
            
            html += `</div>`;
            return html;
        }

        const target = document.getElementById('render-target');
        target.innerHTML = `
            <div style="display:flex; gap:25px; margin-bottom:50px; max-width:1200px; margin:0 auto;">
                <button id="pdf" style="flex:1; background:#4f46e5; color:white; border:none; padding:25px; border-radius:16px; font-weight:900; cursor:pointer; font-size:20px; box-shadow:0 10px 25px rgba(79,70,229,0.3);">📄 PDF로 저장</button>
                <button id="png" style="flex:1; background:#7c3aed; color:white; border:none; padding:25px; border-radius:16px; font-weight:900; cursor:pointer; font-size:20px; box-shadow:0 10px 25px rgba(124,58,237,0.3);">🖼️ 이미지 저장</button>
            </div>
            <div id="preview-area">${buildDoc()}</div>
        `;

        document.getElementById('pdf').onclick = () => {
            const win = window.open('', '_blank');
            win.document.write('<html><head><meta charset="UTF-8"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css"></head><body style="margin:0; background:#f1f5f9; padding:50px;">' + document.getElementById('paper').outerHTML + '</body></html>');
            win.document.close();
            win.onload = () => setTimeout(() => { win.focus(); win.print(); }, 1000);
        };

        document.getElementById('png').onclick = () => {
            const btn = document.getElementById('png');
            btn.innerText = "⏳ 렌더링 중...";
            html2canvas(document.getElementById('paper'), { useCORS: true, scale: 2 }).then(canvas => {
                const a = document.createElement('a');
                a.download = `VitoGDD_${rawData.title}.png`;
                a.href = canvas.toDataURL('image/png');
                a.click();
                btn.innerText = "🖼️ 이미지 저장";
            });
        };
    </script>
    """
    
    final_html = html_template.replace("ST_DATA_JSON", json.dumps(payload))
    components.html(final_html, height=5000, scrolling=True)

st.caption("비토쨩 연습하기")