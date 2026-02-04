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
    .stApp { background-color: #f1f5f9; color: #1e293b; font-family: 'Pretendard', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    .main-title {
        font-size: calc(2.5rem + 2vw) !important; 
        font-weight: 900 !important;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        text-align: center; 
        margin-bottom: 0.5rem !important;
    }
    div.stButton > button {
        border-radius: 12px !important; 
        font-weight: 700 !important;
        transition: all 0.2s; 
        height: 3.8rem;
    }
    .status-card {
        padding: 12px; 
        border-radius: 10px; 
        background: #f8fafc; 
        border: 1px solid #e2e8f0; 
        margin-bottom: 8px; 
        font-size: 0.9rem;
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
        API_KEY = st.text_input("Gemini API Key를 입력하세요", type="password")
    else:
        st.info("✅ API 키 로드 완료")

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 🎨 고화질 이미지 엔진 (Imagen 4.0 규격 준수) ---
def generate_hd_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    prompts = {
        "concept": f"A high-quality masterpiece game key visual art, {genre}, theme: {key}, style: {art}. 8k resolution, cinematic lighting, professional digital art.",
        "ui": f"High-fidelity professional mobile game UI/UX design mockup, {genre} HUD interface, style: {art}. Dashboard, inventory, clean layout, inspired by {key}. Digital game design sheet, 4k."
    }
    if prompt_type not in prompts: return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {
        "instances": {"prompt": prompts[prompt_type]}, 
        "parameters": {"sampleCount": 1}
    }
    try:
        response = requests.post(url, json=payload, timeout=90)
        if response.status_code == 200:
            result = response.json()
            return result["predictions"][0]["bytesBase64Encoded"]
    except: pass
    return None

# 세션 상태
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'generated_images' not in st.session_state: st.session_state['generated_images'] = {}

# 사이드바 결과 분석
with st.sidebar:
    if st.session_state['generated_images']:
        st.divider()
        st.header("🖼️ 생성 이미지 분석")
        for k, v in st.session_state['generated_images'].items():
            color = "#10b981" if v else "#ef4444"
            status = "준비됨" if v else "실패"
            st.markdown(f"""<div class='status-card'>{k.upper()}: <b style='color:{color}'>{status}</b></div>""", unsafe_allow_html=True)

# 메인 UI
st.markdown('<h1 class="main-title">비토쨩 자동 기획서 만들기 🎮</h1>', unsafe_allow_html=True)
st.write("제미나이를 활용한 연습.")
st.divider()

# 입력 섹션
with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르 선택", ["방치형 RPG", "수집형 RPG", "MMORPG", "로그라이크", "FPS/TPS", "전략 시뮬레이션"])
    with c2: target = st.selectbox("타겟 시장", ["글로벌", "한국", "일본", "북미", "유럽", "중국"])
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("아트 스타일", ["픽셀 아트 (Retro)", "2D 카툰", "실사풍", "3D 캐주얼", "사이버펑크", "다크 판타지"])
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프")
    
    if st.button("고품격 기획서 빌드 시작 ✨", type="primary", use_container_width=True):
        if not API_KEY: st.error("API 키를 입력하세요.")
        elif not key: st.warning("키워드를 입력하세요.")
        else:
            with st.spinner("전문 기획자가 모든 텍스트와 UI 목업을 완벽하게 렌더링 중입니다 (최대 2분 소요)..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"""
                당신은 시니어 기획자입니다. 장르={genre}, 국가={target}, 키워드={key}, 아트={art} 조건으로 전문 GDD를 작성하세요.
                
                [중요 지침]
                1. 섹션 제목은 반드시 '## 제목' 형식을 사용하세요.
                2. 본문의 **강조 텍스트**를 적극적으로 활용하세요.
                3. 의미 없는 '#' 한 줄 구분선은 절대 넣지 마세요.
                4. 전투 공식, 시너지 시스템, 경제 구조를 매우 구체적으로 기술하세요.
                5. 복잡한 데이터는 반드시 | 헤더 | 마크다운 표 형식으로 작성하세요.
                6. '## UI/UX 전략 및 인터페이스 설계' 섹션을 반드시 포함하세요.
                7. 위 섹션 하위에 '### UI/UX 목업' 항목을 만들고 해당 화면의 구성 요소를 상세히 기술하세요.
                """
                gdd_res = model.generate_content(prompt)
                st.session_state['gdd_result'] = gdd_res.text
                
                # 이미지 생성 (메인 컨셉과 UI 목업에 집중)
                st.session_state['generated_images'] = {
                    "concept": generate_hd_image("concept", genre, art, key),
                    "ui": generate_hd_image("ui", genre, art, key)
                }

# --- 🚀 [핵심] 마크다운 정화 및 이미지 100% 출력 보장 엔진 ---
if st.session_state['gdd_result']:
    st.divider()
    
    # 데이터 안전 전송용 JSON (중괄호 충돌 방지)
    safe_data = json.dumps({
        "title": f"{key.upper()} 기획안",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['generated_images']
    }).replace("\\", "\\\\").replace("'", "\\'")

    html_code = """
    <style>
        /* 인쇄 시 버튼 영역 숨기기 전용 CSS */
        @media print {
            .no-print { display: none !important; }
            body { background: white !important; padding: 0 !important; }
            #capture-page { 
                box-shadow: none !important; 
                border: none !important; 
                margin: 0 !important; 
                padding: 0 !important; 
                width: 100% !important;
                max-width: none !important;
            }
        }
    </style>
    <div id="root-container"></div>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
        (function() {
            const data = JSON.parse('ST_DATA_JSON');
            
            // 🚀 기호 완전 박멸 및 고품격 태그 변환기
            function formatText(text, uiImg) {
                return text.split('\\n').map(line => {
                    let l = line.trim();
                    if (!l || l === '#' || l === '##' || l === '###') return '';
                    
                    // 1. 표(Table) 처리
                    if (l.startsWith('|')) {
                        const cells = l.split('|').filter(c => c.trim() !== '' || l.indexOf('|') !== l.lastIndexOf('|')).map(c => c.trim());
                        if (cells.length === 0 || l.includes('---')) return '';
                        return `<tr style="border-bottom:1px solid #f1f5f9;">${cells.map(c => `<td style="padding:15px; font-size:19px; color:#334155; border:1px solid #e2e8f0;">${processInline(c)}</td>`).join('')}</tr>`;
                    }

                    // 2. 제목 변환 (기호 삭제)
                    if (l.startsWith('##')) {
                        return `<h2 style="font-size:36px; font-weight:900; color:#4f46e5; border-left:12px solid #4f46e5; padding-left:25px; background:#f8fafc; margin-top:80px; margin-bottom:30px; border-radius:0 15px 15px 0;">${l.replace(/^##\s*/, '')}</h2>`;
                    }
                    if (l.startsWith('###')) {
                        const subTitle = l.replace(/^###\s*/, '');
                        let html = `<h3 style="font-size:24px; font-weight:700; color:#1e293b; margin-top:40px; border-bottom:2px solid #f1f5f9; padding-bottom:12px;">${subTitle}</h3>`;
                        
                        // 🌟 'UI/UX 목업' 항목 감지 시 이미지 바로 주입
                        if ((subTitle.includes('목업') || subTitle.includes('Mockup')) && uiImg) {
                            html += imgBox(uiImg, 'UI/UX SYSTEM MOCKUP');
                        }
                        return html;
                    }
                    
                    // 3. 구분선
                    if (l === '---' || l === '***') return '<hr style="border:none; border-top:1px solid #e2e8f0; margin:50px 0;">';

                    return `<p style="font-size:21px; color:#334155; line-height:1.9; text-align:justify; margin-bottom:25px;">${processInline(l)}</p>`;
                }).join('');
            }

            function processInline(t) {
                // 🌟 모든 ** 기호를 강력하게 제거하고 강조 적용
                return t.replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color:#4f46e5; font-weight:800;">$1</strong>');
            }

            function imgBox(b64, label) {
                if (!b64) return '';
                const src = b64.startsWith('data:') ? b64 : `data:image/png;base64,${b64}`;
                return `
                    <div style="text-align:center; margin:60px 0; padding:40px; background:#f8fafc; border-radius:32px; border:1px solid #e2e8f0;">
                        <img src="${src}" style="width:100%; max-width:1100px; border-radius:20px; box-shadow:0 25px 50px rgba(0,0,0,0.15);">
                        <div style="color:#64748b; font-size:18px; margin-top:25px; font-weight:700; font-style:italic;">[REFERENCE: ${label}]</div>
                    </div>`;
            }

            function renderAll() {
                const root = document.getElementById('root-container');
                
                // 🚀 버튼 영역 (no-print 클래스 추가로 인쇄 시 제외)
                let btns = `
                    <div class="no-print" style="display:flex; gap:30px; margin-bottom:60px; max-width:1200px; margin:0 auto;">
                        <button onclick="window.print()" style="flex:1; background:#4f46e5; color:white; border:none; padding:30px; border-radius:20px; font-weight:900; cursor:pointer; font-size:22px; box-shadow:0 12px 30px rgba(79,70,229,0.3);">📄 PDF 문서로 저장하기</button>
                        <button id="imgDown" style="flex:1; background:#7c3aed; color:white; border:none; padding:30px; border-radius:20px; font-weight:900; cursor:pointer; font-size:22px; box-shadow:0 12px 30px rgba(124,58,237,0.3);">🖼️ 리포트 이미지 저장</button>
                    </div>`;

                // 🚀 문서 본체 영역 (캡처 대상)
                let doc = `<div id="capture-page" style="background:white; padding:120px 100px; border-radius:40px; font-family:'Pretendard', sans-serif; color:#1e293b; max-width:1200px; margin:0 auto; border:1px solid #e2e8f0; box-shadow:0 40px 80px rgba(0,0,0,0.08);">`;
                
                doc += `<h1 style="font-size:80px; font-weight:900; text-align:center; border-bottom:15px solid #4f46e5; padding-bottom:50px; margin-bottom:100px; letter-spacing:-0.05em;">${data.title}</h1>`;
                
                // [1] 메인 비주얼
                doc += imgBox(data.images.concept, 'PROJECT CORE VISUAL');
                
                // [2] 본문 렌더링
                const sections = data.content.split('## ');
                sections.forEach((sec, i) => {
                    if (!sec.trim()) return;
                    doc += formatText((i > 0 ? '## ' : '') + sec, data.images.ui);
                });

                doc += `</div>`;
                
                // 버튼과 문서를 분리하여 root에 삽입
                root.innerHTML = btns + doc;

                // 이미지 저장 핸들러 (capture-page만 타겟팅)
                document.getElementById('imgDown').onclick = function() {
                    this.innerText = "⏳ 렌더링 중...";
                    html2canvas(document.getElementById('capture-page'), { scale: 2, useCORS: true }).then(canvas => {
                        const a = document.createElement('a');
                        a.download = `GDD_REPORT_${data.title}.png`;
                        a.href = canvas.toDataURL('image/png');
                        a.click();
                        this.innerText = "🖼️ 리포트 이미지 저장";
                    });
                };
            }

            renderAll();
        })();
    </script>
    """
    
    final_html = html_code.replace("ST_DATA_JSON", safe_data)
    components.html(final_html, height=6000, scrolling=True)

st.caption("비토쨩 연습하기")