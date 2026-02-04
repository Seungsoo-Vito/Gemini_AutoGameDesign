import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re
import streamlit.components.v1 as components

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

# --- 🔒 API 설정 ---
def get_api_key():
    if "GEMINI_API_KEY" in st.secrets: return st.secrets["GEMINI_API_KEY"]
    if "api_key" in st.session_state: return st.session_state["api_key"]
    return ""

current_api_key = get_api_key()

with st.sidebar:
    st.header("🔑 설정 및 상태")
    if current_api_key:
        st.success("✅ API 키 설정 완료")
        genai.configure(api_key=current_api_key)
    else:
        user_key = st.text_input("Gemini API Key 입력", type="password")
        if user_key:
            st.session_state["api_key"] = user_key
            st.rerun()

    # 이미지 로딩 상태 표시
    if 'images' in st.session_state and st.session_state['images']:
        st.divider()
        st.subheader("🖼️ 이미지 생성 현황")
        labels = {"concept": "메인 컨셉", "world": "세계관 아트", "ui": "UI/UX 목업", "character": "캐릭터 에셋"}
        for k, v in st.session_state['images'].items():
            status_text = "준비됨" if v else "실패"
            status_color = "#10b981" if v else "#ef4444"
            st.markdown(f'<div class="status-badge"><span>{labels.get(k, k)}</span><b style="color: {status_color};">{status_text}</b></div>', unsafe_allow_html=True)

if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'images' not in st.session_state: st.session_state['images'] = {}

# --- 🖼️ 이미지 생성 함수 (대화 초반 성공 규격 복구) ---
def generate_image(prompt_text):
    api_key = get_api_key()
    if not api_key: return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"
    
    # 초반에 성공했던 표준 리스트 형식을 다시 사용합니다.
    payload = {
        "instances": [{"prompt": prompt_text}],
        "parameters": {"sampleCount": 1}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            res_json = response.json()
            if "predictions" in res_json and len(res_json["predictions"]) > 0:
                return res_json["predictions"][0]["bytesBase64Encoded"]
    except:
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
        if not current_api_key: st.error("API 키를 설정해주세요.")
        elif not key: st.warning("키워드를 입력해주세요.")
        else:
            with st.spinner("전문 기획자가 문서를 작성하고 아트를 생성 중입니다..."):
                # 1. GDD 텍스트 생성
                model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
                prompt = f"장르:{genre}, 타겟:{target}, 스타일:{art}, 키워드:{key} 조건으로 전문 GDD를 작성하세요. ## 제목, ### 소제목, **강조**, $$ 공식 $$, | 표 | 형식을 포함하고 UI/UX 목업 섹션을 반드시 만드세요. 제목 기호 #가 노출되지 않게 하세요."
                res = model.generate_content(prompt)
                st.session_state['gdd_result'] = res.text
                
                # 2. 이미지 생성
                st.session_state['images'] = {
                    "concept": generate_image(f"Masterpiece game art visual, {genre}, theme:{key}, style:{art}, 8k, cinematic"),
                    "world": generate_image(f"Stunning environment concept, {genre} world, {art} style, high detail"),
                    "ui": generate_image(f"Mobile game UI HUD mockup, {genre}, professional layout, {art}"),
                    "character": generate_image(f"Game character concept art, {genre}, motif:{key}, {art} style")
                }

# --- 🚀 통합 렌더링 엔진 (데이터 전송 보강) ---
if st.session_state['gdd_result']:
    st.divider()
    
    # 데이터 깨짐 방지를 위해 전체 데이터를 Base64로 인코딩하여 전달
    payload_data = {
        "title": f"{key.upper()} PROJECT GDD",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['images']
    }
    encoded_payload = base64.b64encode(json.dumps(payload_data).encode('utf-8')).decode('utf-8')

    html_template = f"""
    <div id="app-root"></div>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
        (function() {{
            // 데이터를 안전하게 복호화 (한글 깨짐 방지 처리)
            const rawData = atob('{encoded_payload}');
            const data = JSON.parse(decodeURIComponent(escape(rawData)));
            
            const root = document.getElementById('app-root');
            
            function inline(t) {{
                return t.replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color:#4f46e5; font-weight:800;">$1</strong>');
            }}

            function createImgBox(b64, label) {{
                if(!b64) return '';
                return `<div style="text-align:center; margin:60px 0; padding:30px; background:#f8fafc; border-radius:24px; border:1px solid #e2e8f0;">
                    <img src="data:image/png;base64,${{b64}}" style="width:100%; border-radius:15px; box-shadow:0 15px 35px rgba(0,0,0,0.1);">
                    <div style="font-size:16px; color:#6366f1; font-weight:800; margin-top:20px; text-transform:uppercase; letter-spacing:1px;">[Reference: ${{label}}]</div>
                </div>`;
            }}

            function parseContent(text) {{
                return text.split('\\n').map(line => {{
                    let l = line.trim();
                    if (!l || l === '#' || l === '##' || l === '###') return '';
                    
                    // 수식 처리
                    if (l.startsWith('$$')) {{
                        return `<div style="background:#f8faff; border:1px solid #c7d2fe; padding:30px; border-radius:12px; text-align:center; font-size:24px; font-weight:700; color:#3730a3; margin:40px 0; font-family:'Times New Roman', serif;">${{inline(l.replace(/\\$\\$/g, ''))}}</div>`;
                    }}
                    
                    // 표 처리
                    if (l.startsWith('|')) {{
                        const cells = l.split('|').filter(c => c.trim() !== '' || l.indexOf('|') !== l.lastIndexOf('|')).map(c => c.trim());
                        if (cells.length === 0 || l.includes('---')) return '';
                        return `<tr>${{cells.map(c => `<td style="padding:15px; border:1px solid #f1f5f9; font-size:18px;">${{inline(c)}}</td>`).join('')}}</tr>`;
                    }}
                    
                    // 상위 제목 (##) - Indigo Blue + # 제거
                    if (l.startsWith('## ')) {{
                        return `<h2 style="font-size:34px; color:#4f46e5; border-left:12px solid #4f46e5; padding-left:20px; margin-top:60px; background:#f8fafc; padding:15px 20px; border-radius:0 12px 12px 0; font-weight:800;">${{l.replace(/^##\\s*/, '')}}</h2>`;
                    }}
                    
                    // 하위 제목 (###) - Teal Green + # 제거
                    if (l.startsWith('### ')) {{
                        const sub = l.replace(/^###\\s*/, '');
                        let h = `<h3 style="font-size:26px; color:#0891b2; margin-top:45px; border-bottom:2px solid #f1f5f9; padding-bottom:10px; font-weight:700;">${{sub}}</h3>`;
                        // UI 목업 섹션일 때 이미지 자동 삽입
                        if ((sub.includes('목업') || sub.includes('Mockup')) && data.images.ui) {{
                            h += createImgBox(data.images.ui, 'UI/UX Mockup');
                        }}
                        return h;
                    }}
                    
                    // 일반 본문
                    return `<p style="font-size:21px; color:#334155; margin-bottom:25px; line-height:1.9; text-align:justify;">${{inline(l)}}</p>`;
                }}).join('');
            }}

            let bodyHtml = parseContent(data.content).replace(/(<tr>.*?<\\/tr>)+/g, m => `<div style="overflow-x:auto;"><table style="width:100%; border-collapse:collapse; margin:30px 0; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden;">${{m}}</table></div>`);

            root.innerHTML = `
                <div class="no-print" style="display:flex; gap:20px; max-width:1200px; margin:0 auto 30px auto;">
                    <button onclick="window.print()" style="flex:1; padding:20px; border-radius:15px; background:#4f46e5; color:white; border:none; font-weight:900; font-size:18px; cursor:pointer; box-shadow:0 4px 15px rgba(0,0,0,0.1);">📄 PDF 저장</button>
                    <button id="cap-btn" style="flex:1; padding:20px; border-radius:15px; background:#7c3aed; color:white; border:none; font-weight:900; font-size:18px; cursor:pointer; box-shadow:0 4px 15px rgba(0,0,0,0.1);">🖼️ 이미지 저장</button>
                </div>
                <div id="gdd-paper" style="background:white; max-width:1200px; margin:0 auto; padding:100px 80px; border-radius:30px; border:1px solid #e2e8f0; box-shadow:0 30px 60px rgba(0,0,0,0.05); color:#1e293b;">
                    <h1 style="font-size:64px; font-weight:900; text-align:center; border-bottom:12px solid #4f46e5; padding-bottom:40px; margin-bottom:60px; letter-spacing:-0.03em;">${{data.title}}</h1>
                    ${{createImgBox(data.images.concept, 'Main Concept Art')}}
                    ${{bodyHtml}}
                    ${{createImgBox(data.images.world, 'World Environment Concept')}}
                    ${{createImgBox(data.images.character, 'Main Character Asset')}}
                </div>
            `;

            document.getElementById('cap-btn').onclick = function() {{
                const btn = this;
                btn.innerText = "⏳ 렌더링 중...";
                html2canvas(document.getElementById('gdd-paper'), {{ scale: 2, useCORS: true }}).then(canvas => {{
                    const a = document.createElement('a');
                    a.download = 'Vito_GDD_Final_Report.png';
                    a.href = canvas.toDataURL('image/png');
                    a.click();
                    btn.innerText = "🖼️ 이미지 저장";
                }});
            }};
        }})();
    </script>
    <style> 
        @media print {{ 
            .no-print {{ display: none !important; }} 
            body {{ background: white !important; padding:0 !important; }} 
            #gdd-paper {{ box-shadow: none !important; border: none !important; margin:0 !important; width:100% !important; }} 
        }} 
    </style>
    """
    components.html(html_template, height=9000, scrolling=True)