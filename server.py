# server.py - UPDATED WITH REAL NEWS API
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from datetime import datetime, timedelta

print("🚀 ENHANCED AI NEWS SERVER")

# Get API keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")  # Get from https://newsapi.org

app = Flask(__name__)
CORS(app)

# Country to country code mapping
COUNTRY_CODES = {
    'Iraq': 'iq',
    'Syria': 'sy', 
    'Turkey': 'tr',
    'Iran': 'ir',
    'Germany': 'de',
    'Sweden': 'se',
    'United States': 'us',
    'Global': None
}

def get_real_news_from_api(country, topic):
    """Fetch real news from NewsAPI"""
    if not NEWS_API_KEY:
        return None
    
    try:
        # Build query
        query = topic.lower()
        country_code = COUNTRY_CODES.get(country)
        
        # Prepare URL
        if country_code and country != 'Global':
            url = f"https://newsapi.org/v2/top-headlines?country={country_code}&q={query}&apiKey={NEWS_API_KEY}"
        else:
            url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        
        print(f"📰 Fetching real news: {url}")
        
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['totalResults'] > 0:
                articles = data['articles'][:5]  # Get top 5 articles
                
                # Format articles
                news_text = ""
                for i, article in enumerate(articles, 1):
                    news_text += f"{i}. {article['title']}\n"
                    if article.get('description'):
                        news_text += f"   {article['description']}\n"
                    if article.get('source', {}).get('name'):
                        news_text += f"   Source: {article['source']['name']}\n"
                    news_text += "\n"
                
                return news_text[:2000]  # Limit length
        
        return None
        
    except Exception as e:
        print(f"❌ NewsAPI error: {e}")
        return None

def enhance_with_ai(news_text, country, topic):
    """Enhance real news with AI analysis"""
    
    if not GROQ_API_KEY:
        return news_text  # Return raw news if no AI key
    
    prompt = f"""You are a news analyst. Analyze and summarize these news articles about {topic} in {country}.

RAW NEWS ARTICLES:
{news_text}

Please provide:
1. **EXECUTIVE SUMMARY**: 2-3 sentence overview
2. **KEY POINTS**: Bulleted list of main developments
3. **CONTEXT**: Background information
4. **IMPACT**: Who is affected and how

Keep it factual, neutral, and informative."""

    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a professional news analyst."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            print(f"⚠️ AI enhancement failed: {response.status_code}")
            return news_text  # Fallback to raw news
            
    except Exception as e:
        print(f"⚠️ AI error: {e}")
        return news_text

@app.route('/get_news', methods=['POST', 'OPTIONS'])
def get_news():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json()
        country = data.get('country', 'Global')
        topic = data.get('topic', 'Breaking News')
        
        print(f"📡 Request: {country} | {topic}")
        
        # Step 1: Get real news
        raw_news = get_real_news_from_api(country, topic)
        
        if not raw_news:
            # Fallback: Generate AI news if no real news
            print("⚠️ No real news found, using AI generation")
            raw_news = f"Latest updates about {topic} in {country}. Recent developments show significant activity in this area."
        
        # Step 2: Enhance with AI
        enhanced_news = enhance_with_ai(raw_news, country, topic)
        
        # Step 3: Handle translation if needed
        needs_translation = data.get('needs_translation', False)
        original_language = data.get('original_language', 'en')
        
        translated_content = None
        if needs_translation and original_language != 'en':
            translated_content = translate_content(enhanced_news, original_language)
        
        return jsonify({
            'description': enhanced_news,
            'translated_description': translated_content,
            'success': True,
            'country': country,
            'topic': topic,
            'has_real_news': raw_news is not None,
            'ai_enhanced': True
        })
        
    except Exception as e:
        print(f"❌ Server error: {e}")
        return jsonify({
            'error': str(e),
            'fallback_news': f"Latest news about {data.get('topic', 'general')}. Please try again in a moment."
        }), 500

def translate_content(text, target_lang):
    """Simple translation using Groq"""
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        
        prompt = f"Translate this news summary to language code '{target_lang}':\n\n{text}"
        
        payload = {
            "model": "llama-3.1-8b-instant",  # Faster model for translation
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
            
    except Exception as e:
        print(f"⚠️ Translation error: {e}")
    
    return None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'news_api': bool(NEWS_API_KEY),
            'ai_service': bool(GROQ_API_KEY)
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"\n✅ Enhanced Server Ready")
    print(f"📰 News API: {'✅ Available' if NEWS_API_KEY else '❌ Not configured'}")
    print(f"🤖 Groq AI: {'✅ Available' if GROQ_API_KEY else '❌ Not configured'}")
    print(f"🌐 Port: {port}")
    app.run(host='0.0.0.0', port=port)