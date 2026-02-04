import feedparser
from datetime import datetime

# 1. 수집할 뉴스 소스 (RSS 주소)
NEWS_SOURCES = {
    "디스이즈게임": "https://www.thisisgame.com/rss/all.xml",
    "게임메카": "https://www.gamemeca.com/rss/news.xml",
    "인벤": "https://www.inven.co.kr/rss/news.xml"
}

def fetch_news():
    all_news = []
    for source_name, url in NEWS_SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:  # 매체당 최신 뉴스 5개씩
            all_news.append({
                "source": source_name,
                "title": entry.title,
                "link": entry.link,
                "date": entry.published if 'published' in entry else "최신"
            })
    return all_news

def generate_html(news_list):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>게임 업계 뉴스 브리핑</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 text-gray-900">
        <div class="max-w-4xl mx-auto py-10 px-4">
            <header class="mb-10 text-center">
                <h1 class="text-4xl font-bold text-blue-600 mb-2">🎮 게임 업계 뉴스 브리핑</h1>
                <p class="text-gray-500">업데이트 시간: {now}</p>
            </header>
            
            <div class="grid gap-6">
                {"".join([f'''
                <a href="{n['link']}" target="_blank" class="block p-6 bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow">
                    <span class="inline-block px-2 py-1 mb-2 text-xs font-semibold text-white bg-blue-500 rounded">
                        {n['source']}
                    </span>
                    <h2 class="text-xl font-bold mb-2">{n['title']}</h2>
                    <p class="text-sm text-gray-400">{n['date']}</p>
                </a>
                ''' for n in news_list])}
            </div>
            
            <footer class="mt-20 text-center text-gray-400 text-sm">
                이 페이지는 자동 생성되었습니다.
            </footer>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("성공! index.html 파일이 생성되었습니다.")

if __name__ == "__main__":
    news_data = fetch_news()
    generate_html(news_data)