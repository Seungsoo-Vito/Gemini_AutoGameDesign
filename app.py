import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re
import os.path
import streamlit.components.v1 as components

# 1. Page Configuration (와이드 레이아웃 확보)
st.set_page_config(page_title="비토쨩 자동 기획서 연습", page_icon="🎮", layout="wide")

# --- 🎨 UI 스타일링 ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #f1f5f9; color: #1e293b; font-family: 'Pretendard', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    .main-title {
        font-size: calc(2.5rem + 1.8vw) !important; font-weight: 900 !important;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 0.5rem !important;
    }
    div.stButton > button {
        border-radius: 12px !important; font-weight: 700 !important;
        transition: all 0.2s; height: 3.8rem; font-size: 1.1rem !important;
    }
    .status-card { padding: 10px; border-radius: 8px; background: #f8fafc; border: 1px solid #e2e8f0; margin-bottom: 5px; font-size: 0.85rem; }
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
        API_KEY = st.text_input("Gemini API Key를 입력하세요", type="password")
    else:
        st.info("✅ API 키 로드 완료")

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 🎨 이미지 생성 엔진 (Imagen 4.0) ---
def generate_specialized_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    prompts = {
        "concept": f"Cinematic epic game key visual art, {genre}, theme: {key}, style: {art}. 8k, professional lighting.",
        "ui": f"Professional High-fidelity mobile game UI/UX design mockup, {genre} interface, style: {art}. HUD, buttons, dashboard, inspired by {key}.",
        "world": f"Environment concept art, immersive world of {genre}, location theme: {key}, style: {art}. Beautiful landscape.",
        "character": f"Character concept art portrait, {genre} game unit, motif: {key}, style: {art}. Professional digital asset."
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

# 세션 상태 관리
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'generated_images' not in st.session_state: st.session_state['generated_images'] = {}
if 'history' not in st.session_state: st.session_state['history'] = []

# 사이드바 히스토리
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
            st.markdown(f"<div class='status-card'>{k.upper()}: <b style='color:{color}'>{'준비됨' if v else '실패'}</b></div>", unsafe_allow_html=True)

# 메인 UI
st.markdown('<h1 class="main-title">비토쨩 자동 기획서 만들기 🎮</h1>', unsafe_allow_html=True)
st.write("제미나이를 활용한 연습.")
st.divider()

# 입력창
genres = ["방치형 RPG", "수집형 RPG", "액션 RPG", "MMORPG", "로그라이크", "전략 시뮬레이션"]
targets = ["글로벌", "한국", "일본", "중국", "북미", "유럽"]
styles = ["픽셀 아트 (Retro)", "2D 카툰/애니메이션", "실사풍", "3D 캐주얼", "사이버펑크"]

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
            with st.spinner("시니어 기획자가 기획서를 작성하고 이미지를 생성 중입니다..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"당신은 전설적인 기획자입니다. 장르={genre}, 국가={target}, 키워드={key}, 아트={art} 조건으로 전문적인 GDD를 작성하세요. 불필요한 '#' 기호 한 줄은 제거하세요. 섹션 제목은 반드시 '## 숫자. 제목' 형식을 유지하세요."
                gdd_res = model.generate_content(prompt)
                st.session_state['gdd_result'] = gdd_res.text
                
                imgs = {
                    "concept": generate_specialized_image("concept", genre, art, key),
                    "world": generate_specialized_image("world", genre, art, key),
                    "ui": generate_specialized_image("ui", genre, art, key),
                    "character": generate_specialized_image("character", genre, art, key)
                }
                st.session_state['generated_images'] = imgs
                st.session_state['history'].append({"key": key, "content": gdd_res.text, "images": imgs})

# --- 결과 출력 & 렌더링 엔진 (이미지 출력 보장 버전) ---
if st.session_state['gdd_result']:
    st.divider()
    
    export_payload = {
        "title": f"{key.upper()} 기획안",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['generated_images']
    }
    
    # f-string 에러를 방지하기 위해 replace 방식 사용
    html_template = """
    <div id="render-target"></div>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
        const data = ST_DATA_JSON;
        
        function cleanText(text) {
            return text
                .replace(/^#+ /gm, '') // ## 기호 제거
                .replace(/^#\s*$/gm, '') // 홀로 남은 # 제거
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/^\\* /gm, '<li style="margin-bottom:8px;">')
                .replace(/\\n/g, '<br>');
        }

        function buildHTML(data) {
            let html = `<div id="export-area" style="background:white; padding:80px; border-radius:24px; font-family:'Pretendard', sans-serif; color:#1e293b; line-height:1.9; max-width:1200px; margin:0 auto; border:1px solid #e2e8f0; box-shadow:0 15px 45px rgba(0,0,0,0.06);">`;
            html += `<h1 style="font-size:56px; font-weight:900; text-align:center; border-bottom:10px solid #4f46e5; padding-bottom:30px; margin-bottom:60px;">${data.title}</h1>`;
            
            // 1. [메인 비주얼]
            if(data.images.concept) {
                html += `<div style="text-align:center; margin-bottom:80px;"><img src="data:image/png;base64,${data.images.concept}" style="width:100%; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.12);"><div style="color:#64748b; font-size:16px; margin-top:15px; font-weight:600;">[Main Concept Visual]</div></div>`;
            }
            
            const sections = data.content.split('## ');
            const otherImgs = [
                {data: data.images.world, label: 'World Concept'},
                {data: data.images.ui, label: 'UI/UX Mockup'},
                {data: data.images.character, label: 'Character Design'}
            ].filter(x => x.data);

            sections.forEach((sec, i) => {
                if(!sec.trim()) return;
                
                // 제목과 본문 분리
                let lines = sec.split('\\n');
                let title = lines[0].trim();
                let body = lines.slice(1).join('\\n');

                // 섹션 제목 렌더링
                html += `<h2 style="font-size:32px; font-weight:800; color:#4f46e5; border-left:12px solid #4f46e5; padding:15px 30px; background:#f8fafc; margin-top:60px; border-radius:0 15px 15px 0;">${title.replace(/^#+/, '')}</h2>`;
                
                // 본문 렌더링
                html += `<div style="font-size:20px; margin-top:25px;">${cleanText(body)}</div>`;
                
                // 🚀 이미지 강제 분산 배치 (섹션이 넘어갈 때마다 하나씩)
                let imgIdx = i - 1; // 첫 섹션 이후부터 배치
                if(imgIdx >= 0 && imgIdx < otherImgs.length) {
                    html += `<div style="text-align:center; margin:60px 0;"><img src="data:image/png;base64,${otherImgs[imgIdx].data}" style="width:100%; border-radius:20px; box-shadow:0 8px 25px rgba(0,0,0,0.08);"><div style="color:#64748b; font-size:16px; margin-top:12px; font-weight:600;">[Visual Reference: ${otherImgs[imgIdx].label}]</div></div>`;
                }
            });
            
            html += `</div>`;
            return html;
        }

        const target = document.getElementById('render-target');
        target.innerHTML = `
            <div style="display:flex; gap:25px; margin-bottom:50px; max-width:1200px; margin-left:auto; margin-right:auto;">
                <button id="pdfBtn" style="flex:1; background:#4f46e5; color:white; border:none; padding:25px; border-radius:16px; font-weight:900; cursor:pointer; font-size:20px; box-shadow:0 10px 25px rgba(79,70,229,0.3);">📄 PDF로 저장</button>
                <button id="pngBtn" style="flex:1; background:#7c3aed; color:white; border:none; padding:25px; border-radius:16px; font-weight:900; cursor:pointer; font-size:20px; box-shadow:0 10px 25px rgba(124,58,237,0.3);">🖼️ 이미지 저장</button>
            </div>
            <div id="preview-box">${buildHTML(data)}</div>
        `;

        document.getElementById('pdfBtn').onclick = () => {
            const win = window.open('', '_blank');
            win.document.write('<html><head><meta charset="UTF-8"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css"></head><body style="margin:0; background:#f1f5f9;">' + document.getElementById('export-area').outerHTML + '</body></html>');
            win.document.close();
            win.onload = () => setTimeout(() => { win.focus(); win.print(); }, 1000);
        };

        document.getElementById('pngBtn').onclick = () => {
            const btn = document.getElementById('pngBtn');
            btn.innerText = "⏳ 렌더링 중...";
            html2canvas(document.getElementById('export-area'), { useCORS: true, scale: 2 }).then(canvas => {
                const a = document.createElement('a');
                a.download = `VitoGDD_${data.title}.png`;
                a.href = canvas.toDataURL('image/png');
                a.click();
                btn.innerText = "🖼️ 이미지 저장";
            });
        };
    </script>
    """
    
    final_html = html_template.replace("ST_DATA_JSON", json.dumps(export_payload))
    components.html(final_html, height=4500, scrolling=True)

st.caption("비토쨩 연습하기")