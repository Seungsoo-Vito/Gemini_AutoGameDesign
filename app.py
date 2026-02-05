import streamlit as st
import google.generativeai as genai
import base64
import json
import io
import re
import streamlit.components.v1 as components

# 1. 페이지 설정
st.set_page_config(page_title="비토쨩 GDD Pro (Strategic)", page_icon="📝", layout="wide")

# --- 🎨 프리미엄 스타일링 ---
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #f1f5f9; font-family: 'Pretendard', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    
    .main-title {
        font-size: 3.5rem; font-weight: 900;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 2rem;
        letter-spacing: -0.05em;
    }
    
    div.stButton > button {
        border-radius: 12px !important; font-weight: 700 !important;
        height: 4rem; width: 100%; font-size: 1.1rem !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(79, 70, 229, 0.2);
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
    
    st.divider()
    st.info("💡 **전략적 고도화 버전**\n\n각 시스템의 **기획 의도와 기대 효과(Why & Effect)**를 심층 분석한 리포트를 생성합니다.")

if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None

# --- 🏠 메인 화면 ---
st.markdown('<h1 class="main-title">비토쨩 전략 기획서 제작 🎮</h1>', unsafe_allow_html=True)

with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르 선택", ["방치형 RPG", "수집형 RPG", "MMORPG", "로그라이크", "전략 시뮬레이션", "서브컬처 수집형"])
    with c2: target = st.selectbox("타켓 시장", ["글로벌 (북미/유럽)", "한국 (하드코어/모바일)", "일본 (서브컬처)", "중국 (대중화권)"])
    
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("아트 스타일", ["픽셀 아트", "2D 카툰/애니메이션", "하이엔드 실사풍", "3D 캐주얼/로우폴리", "사이버펑크"])
    with c4: key = st.text_input("핵심 컨셉 키워드", placeholder="예: 타임루프 고양이, 지하철 서바이벌")
    
    if st.button("전략적 기획서 생성 시작 ✨", type="primary"):
        if not current_api_key: 
            st.error("사이드바에서 API 키를 설정해주세요.")
        elif not key: 
            st.warning("키워드를 입력해주세요.")
        else:
            with st.spinner("시니어 디렉터가 게임의 인과관계와 경제 모델을 설계 중입니다..."):
                model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
                # 고도화된 프롬프트: 기획 의도와 효과 강조
                prompt = f"""
                당신은 15년 경력의 시니어 게임 디렉터입니다. 
                장르: {genre}, 타겟: {target}, 스타일: {art}, 키워드: {key} 조건을 기반으로 전문 게임 디자인 문서(GDD)를 작성하세요.

                [핵심 요구사항]
                단순한 기능 설명이 아니라, 각 시스템이 왜 필요한지(기획 의도)와 그로 인한 유저 경험 변화(기대 효과)를 심도 있게 기술하세요.

                [필수 포함 항목]
                1. ## 프로젝트 비전 및 시장 경쟁력 (Vision & USP)
                   - 독창적인 핵심 컨셉(USP) 3가지와 타겟 유저가 선택해야만 하는 심리적 이유.
                2. ## 게임 시스템 및 상세 콘텐츠 (Detailed Systems & Contents)
                   - 주요 시스템(전투, 성장 등)을 설명하고, 각각 '기획 의도'와 '유저 경험 효과'를 분리하여 서술.
                   - 수치 산정 방식은 '$$ 공식 $$' 문법 사용.
                3. ## 핵심 게임 루프 및 콘텐츠 순환 (Core Loop)
                   - 초반/중반/후반 콘텐츠의 연결 구조 설계.
                4. ## 경제 모델 및 유료화 전략 (Economy & Monetization)
                   - 인플레이션 방지 설계 및 BM 구성. 데이터는 | 표 | 형식 활용.
                5. ## UI/UX 및 인터페이스 설계 (User Experience)
                   - ### UI/UX 목업 항목에서 메인 화면 구성을 텍스트로 상세 묘사.
                6. ## 향후 업데이트 로드맵 (Roadmap)
                   - 1년간의 시즌제 운영 계획.

                [작성 지침]
                - 제목 앞의 '#' 기호는 제거하십시오.
                - 핵심 단어는 **강조** 처리를 하십시오.
                - 이미지는 생성하지 마십시오.
                """
                res = model.generate_content(prompt)
                st.session_state['gdd_result'] = res.text

# --- 🚀 고도화 렌더링 엔진 (f-string 중괄호 보정 완료) ---
if st.session_state['gdd_result']:
    st.divider()
    
    payload_data = {
        "title": f"{key.upper()} STRATEGIC GDD",
        "content": st.session_state['gdd_result']
    }
    encoded_payload = base64.b64encode(json.dumps(payload_data).encode('utf-8')).decode('utf-8')

    html_template = f"""
    <div id="app-root"></div>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
        (function() {{
            const rawData = atob('{encoded_payload}');
            const data = JSON.parse(decodeURIComponent(escape(rawData)));
            const root = document.getElementById('app-root');
            
            function inline(t) {{
                return t.replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color:#4f46e5; font-weight:800;">$1</strong>');
            }}

            function parseContent(text) {{
                return text.split('\\n').map(line => {{
                    let l = line.trim();
                    if (!l || l === '#' || l === '##' || l === '###') return '';
                    
                    if (l.startsWith('$$')) {{
                        return `<div style="background:#f8faff; border:1px solid #c7d2fe; padding:30px; border-radius:12px; text-align:center; font-size:24px; font-weight:700; color:#3730a3; margin:40px 0; font-family:'Times New Roman', serif;">${{inline(l.replace(/\\$\\$/g, ''))}}</div>`;
                    }}
                    
                    if (l.startsWith('|')) {{
                        const cells = l.split('|').filter(c => c.trim() !== '' || l.indexOf('|') !== l.lastIndexOf('|')).map(c => c.trim());
                        if (cells.length === 0 || l.includes('---')) return '';
                        return `<tr>${{cells.map(c => `<td style="padding:15px; border:1px solid #f1f5f9; font-size:18px;">${{inline(c)}}</td>`).join('')}}</tr>`;
                    }}
                    
                    if (l.startsWith('## ')) {{
                        return `<h2 style="font-size:34px; color:#4f46e5; border-left:12px solid #4f46e5; padding-left:20px; margin-top:60px; background:#f8fafc; border-radius:0 12px 12px 0; font-weight:800;">${{l.replace(/^##\\s*/, '')}}</h2>`;
                    }}
                    
                    if (l.startsWith('### ')) {{
                        return `<h3 style="font-size:26px; color:#0891b2; margin-top:45px; border-bottom:2px solid #f1f5f9; padding-bottom:10px; font-weight:700;">${{l.replace(/^###\\s*/, '')}}</h3>`;
                    }}
                    
                    return `<p style="font-size:21px; color:#334155; margin-bottom:25px; line-height:1.9; text-align:justify;">${{inline(l)}}</p>`;
                }}).join('');
            }}

            let bodyHtml = parseContent(data.content).replace(/(<tr>.*?<\\/tr>)+/g, m => `<div style="overflow-x:auto;"><table style="width:100%; border-collapse:collapse; margin:30px 0; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden;">${{m}}</table></div>`);

            root.innerHTML = `
                <div class="no-print" style="display:flex; gap:15px; max-width:1200px; margin:0 auto 30px auto;">
                    <button onclick="window.print()" style="flex:1; padding:20px; border-radius:15px; background:#4f46e5; color:white; border:none; font-weight:900; font-size:18px; cursor:pointer;">📄 PDF 저장</button>
                    <button id="cap-btn" style="flex:1; padding:20px; border-radius:15px; background:#7c3aed; color:white; border:none; font-weight:900; font-size:18px; cursor:pointer;">🖼️ 이미지 저장</button>
                    <button id="copy-btn" style="flex:1; padding:20px; border-radius:15px; background:#f59e0b; color:white; border:none; font-weight:900; font-size:18px; cursor:pointer;">📋 텍스트 복사</button>
                </div>
                <div id="gdd-paper" style="background:white; max-width:1200px; margin:0 auto; padding:120px 100px; border-radius:40px; border:1px solid #e2e8f0; box-shadow:0 30px 60px rgba(0,0,0,0.05); color:#1e293b;">
                    <div style="text-align:center; margin-bottom:80px;">
                        <div style="color:#4f46e5; font-weight:800; font-size:20px; margin-bottom:15px; letter-spacing:4px; text-transform:uppercase;">Technical & Strategic Design Document</div>
                        <h1 style="font-size:72px; font-weight:900; margin:0; letter-spacing:-0.04em; line-height:1.1;">${{data.title}}</h1>
                    </div>
                    ${{bodyHtml}}
                    <div style="margin-top:100px; padding-top:40px; border-top:1px solid #e2e8f0; color:#94a3b8; text-align:center; font-size:16px;">
                        Copyright 2026 Vito GDD Pro. Designed for Industry Professionals.
                    </div>
                </div>
            `;

            // 이미지 저장 로직
            document.getElementById('cap-btn').onclick = function() {{
                const btn = this;
                btn.innerText = "⏳ 렌더링 중...";
                html2canvas(document.getElementById('gdd-paper'), {{ scale: 2, useCORS: true, backgroundColor: '#ffffff' }}).then(canvas => {{
                    const a = document.createElement('a');
                    a.download = 'Strategic_GDD_Report.png';
                    a.href = canvas.toDataURL('image/png');
                    a.click();
                    btn.innerText = "🖼️ 이미지 저장";
                }});
            }};

            // 텍스트 복사 로직
            document.getElementById('copy-btn').onclick = function() {{
                const btn = this;
                const textArea = document.createElement("textarea");
                textArea.value = data.content; 
                document.body.appendChild(textArea);
                textArea.select();
                try {{
                    document.execCommand('copy');
                    btn.innerText = "✅ 복사 완료!";
                    setTimeout(() => {{ btn.innerText = "📋 텍스트 복사"; }}, 2000);
                }} catch (err) {{}}
                document.body.removeChild(textArea);
            }};
        })();
    </script>
    <style> 
        @media print {{ 
            .no-print {{ display: none !important; }} 
            body {{ background: white !important; padding:0 !important; }} 
            #gdd-paper {{ box-shadow: none !important; border: none !important; margin:0 !important; width: 100% !important; border-radius: 0 !important; }} 
        }} 
    </style>
    """
    components.html(html_template, height=10000, scrolling=True)