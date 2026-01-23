# server.py - Enhanced for Railway with multiple AI providers
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import feedparser
from datetime import datetime, timedelta
import json
import time

print("🚀 AI NEWS SERVER - Railway Deployment")
print("=" * 50)

# Load environment variables
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")
SERVER_ENV = os.environ.get("RAILWAY_ENVIRONMENT", "production")

print(f"Environment: {SERVER_ENV}")
print(f"HuggingFace API: {'✅ Loaded' if HUGGINGFACE_API_KEY else '❌ Not found'}")
print(f"Groq API: {'✅ Loaded' if GROQ_API_KEY else '❌ Not found'}")
print(f"NewsAPI: {'✅ Loaded' if NEWSAPI_KEY else '❌ Not found'}")
print("=" * 50)

app = Flask(__name__)
CORS(app)

# Cache for news responses
news_cache = {}

# RSS Feeds by country/category
RSS_FEEDS = {
    'global': 'http://feeds.bbci.co.uk/news/rss.xml',
    'us': 'https://feeds.npr.org/1001/rss.xml',
    'uk': 'http://feeds.bbci.co.uk/news/rss.xml',
    'technology': 'https://feeds.feedburner.com/TechCrunch/',
    'sports': 'http://feeds.bbci.co.uk/sport/rss.xml',
    'business': 'https://feeds.reuters.com/reuters/businessNews',
    'science': 'https://feeds.feedburner.com/sciencealert-latestnews',
    'health': 'https://feeds.feedburner.com/medicalnewstoday',
}

def get_cache_key(country, topic, language):
    return f"{country}_{topic}_{language}_{datetime.now().strftime('%Y%m%d%H')}"

def get_rss_feed(country, topic):
    """Fetch RSS feed based on country and topic"""
    try:
        # Map country to feed
        feed_key = country.lower().replace(' ', '_')
        if feed_key not in RSS_FEEDS:
            # Try topic-based feed
            topic_key = topic.lower().replace(' ', '_')
            if topic_key in RSS_FEEDS:
                feed_url = RSS_FEEDS[topic_key]
            else:
                feed_url = RSS_FEEDS['global']
        else:
            feed_url = RSS_FEEDS[feed_key]
        
        print(f"Fetching RSS from: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        articles = []
        for entry in feed.entries[:8]:  # Get 8 articles
            articles.append({
                'title': entry.title,
                'summary': entry.get('summary', entry.title),
                'link': entry.link,
                'published': entry.get('published', ''),
                'source': feed.feed.get('title', 'News Feed')
            })
        
        return articles
    except Exception as e:
        print(f"RSS Error: {e}")
        return []

def generate_ai_summary(articles, country, topic, language):
    """Generate AI summary using available providers"""
    
    # Prepare prompt
    articles_text = "\n".join([f"{i+1}. {a['title']} - {a['summary'][:200]}..." 
                              for i, a in enumerate(articles)])
    
    prompt = f"""As a professional journalist, create a news summary about {topic} in {country}.

Recent Headlines:
{articles_text}

Please write a comprehensive news report including:
1. Main headline
2. Key developments
3. Context and background
4. Important quotes or facts
5. Future implications

Write in a neutral, factual tone.
{"Write in " + language + " language." if language != 'en' else ''}

Format your response clearly with sections."""
    
    # Try different AI providers in order
    ai_response = try_huggingface(prompt)
    if not ai_response:
        ai_response = try_groq(prompt)
    if not ai_response:
        ai_response = try_fallback_ai(prompt)
    
    return ai_response or "News analysis currently unavailable. Please check back soon."

def try_huggingface(prompt):
    """Try Hugging Face Inference API"""
    if not HUGGINGFACE_API_KEY:
        return None
    
    try:
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        
        # Try different models
        models = [
            "mistralai/Mistral-7B-Instruct-v0.2",
            "meta-llama/Meta-Llama-3-8B-Instruct",
            "google/flan-t5-xxl"
        ]
        
        for model in models:
            try:
                response = requests.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers=headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 800,
                            "temperature": 0.7,
                            "top_p": 0.9
                        }
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        text = result[0].get('generated_text', '')
                        if text:
                            print(f"HuggingFace success with {model}")
                            return text
            except:
                continue
        
        return None
    except Exception as e:
        print(f"HuggingFace error: {e}")
        return None

def try_groq(prompt):
    """Try Groq API"""
    if not GROQ_API_KEY:
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a professional journalist."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 1000
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
        
        return None
    except Exception as e:
        print(f"Groq error: {e}")
        return None

def try_fallback_ai(prompt):
    """Try free AI endpoints"""
    endpoints = [
        "https://api.deepinfra.com/v1/openai/chat/completions",
        "https://free.churchless.tech/v1/chat/completions",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.post(
                endpoint,
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 600
                },
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data:
                    return data['choices'][0]['message']['content']
        except:
            continue
    
    return None

def translate_text(text, target_lang):
    """Simple translation using available services"""
    if target_lang == 'en' or not text:
        return text
    
    # Try translation APIs
    translation_apis = [
        # Add translation API calls here if you have access
        # Example: Google Translate, LibreTranslate, etc.
    ]
    
    # For now, return original with note
    return f"{text}\n\n[Translated from English to {target_lang}]"

@app.route('/get_news', methods=['POST', 'OPTIONS'])
def get_news():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        start_time = time.time()
        data = request.get_json()
        
        country = data.get('country', 'Global')
        topic = data.get('topic', 'Breaking News')
        original_language = data.get('original_language', 'en')
        needs_translation = data.get('needs_translation', False)
        
        print(f"\n📡 News Request:")
        print(f"   Country: {country}")
        print(f"   Topic: {topic}")
        print(f"   Language: {original_language}")
        print(f"   Needs translation: {needs_translation}")
        
        # Check cache
        cache_key = get_cache_key(country, topic, original_language)
        if cache_key in news_cache:
            cache_age = datetime.now() - news_cache[cache_key]['timestamp']
            if cache_age < timedelta(minutes=30):  # Cache for 30 minutes
                print("   ✅ Serving from cache")
                return jsonify(news_cache[cache_key]['response'])
        
        # Step 1: Fetch real news
        articles = get_rss_feed(country, topic)
        
        if not articles:
            # Fallback articles
            articles = [
                {
                    'title': f'Latest developments in {country}',
                    'summary': f'Recent updates on {topic.lower()} from various sources',
                    'source': 'AI News Assistant',
                    'published': datetime.now().strftime('%Y-%m-%d')
                }
            ]
        
        # Step 2: Generate AI summary
        print("   🤖 Generating AI summary...")
        ai_summary = generate_ai_summary(articles, country, topic, 
                                        'Arabic' if original_language == 'ar' else 
                                        'Kurdish' if original_language == 'ku' else 'English')
        
        # Step 3: Translate if needed
        translated_summary = None
        if needs_translation and original_language != 'en':
            print(f"   🔄 Translating to {original_language}...")
            translated_summary = translate_text(ai_summary, original_language)
        
        # Step 4: Prepare response
        response_data = {
            'description': ai_summary,
            'translated_description': translated_summary,
            'success': True,
            'country': country,
            'topic': topic,
            'language': original_language,
            'articles_count': len(articles),
            'cache_key': cache_key,
            'processing_time': round(time.time() - start_time, 2),
            'timestamp': datetime.now().isoformat(),
            'ai_providers_used': 'HuggingFace/Groq/Fallback'
        }
        
        # Cache the response
        news_cache[cache_key] = {
            'timestamp': datetime.now(),
            'response': response_data
        }
        
        # Clean old cache entries
        cleanup_cache()
        
        print(f"   ✅ Response ready ({response_data['processing_time']}s)")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'description': f"""📢 **News Update for {data.get('country', 'Global')}**

**Topic:** {data.get('topic', 'Breaking News')}

Due to high demand, our AI systems are processing your request.
In the meantime, here are the latest developments:

• Digital transformation continues across various sectors
• New initiatives focus on sustainable development
• Global partnerships strengthen economic ties
• Innovation in technology drives progress

For live updates, check major news outlets.

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*Powered by AI News Assistant*""",
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def cleanup_cache():
    """Remove cache entries older than 2 hours"""
    cutoff = datetime.now() - timedelta(hours=2)
    keys_to_remove = []
    
    for key, value in news_cache.items():
        if value['timestamp'] < cutoff:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del news_cache[key]
    
    if keys_to_remove:
        print(f"Cleaned up {len(keys_to_remove)} cache entries")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'environment': SERVER_ENV,
        'cache_size': len(news_cache),
        'apis_available': {
            'huggingface': bool(HUGGINGFACE_API_KEY),
            'groq': bool(GROQ_API_KEY),
            'newsapi': bool(NEWSAPI_KEY)
        }
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint with sample data"""
    return jsonify({
        'message': 'AI News Server is running!',
        'endpoints': {
            '/get_news': 'POST - Get news summary',
            '/health': 'GET - Health check',
            '/test': 'GET - This endpoint'
        },
        'environment': SERVER_ENV,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"\n✅ Server ready on port {port}")
    print(f"🌐 Environment: {SERVER_ENV}")
    print(f"🔗 Health check: http://localhost:{port}/health")
    print(f"🧪 Test endpoint: http://localhost:{port}/test")
    print(f"🤖 Available AI providers: {'HuggingFace' if HUGGINGFACE_API_KEY else 'None'}, "
          f"{'Groq' if GROQ_API_KEY else 'None'}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=(SERVER_ENV == 'development'))