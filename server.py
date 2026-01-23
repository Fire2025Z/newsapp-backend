# server.py - AI with Web Search
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json

print("🚀 AI NEWS SEARCHER SERVER")

# API Keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")  # https://tavily.com (free tier available)
# # OR
# SERPER_API_KEY = os.environ.get("SERPER_API_KEY")  # https://serper.dev (free tier)

app = Flask(__name__)
CORS(app)

def search_web_news(country, topic):
    """Search real news from the web"""
    search_query = f"{topic} news {country} today latest"
    
    # Option A: Using Tavily (recommended for AI agents)
    if TAVILY_API_KEY:
        try:
            print(f"🔍 Searching web with Tavily: {search_query}")
            
            tavily_response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": search_query,
                    "search_depth": "advanced",
                    "include_answer": False,
                    "include_raw_content": True,
                    "max_results": 8,
                    "include_domains": [
                        "bbc.com", "reuters.com", "apnews.com", 
                        "aljazeera.com", "dw.com", "cnn.com",
                        "nytimes.com", "theguardian.com"
                    ]
                },
                timeout=30
            )
            
            if tavily_response.status_code == 200:
                data = tavily_response.json()
                
                # Format search results
                news_sources = []
                for result in data.get('results', []):
                    source = {
                        'title': result.get('title', ''),
                        'content': result.get('content', ''),
                        'url': result.get('url', ''),
                        'source': result.get('source', '')
                    }
                    news_sources.append(source)
                
                print(f"✅ Found {len(news_sources)} sources")
                return news_sources
                
        except Exception as e:
            print(f"⚠️ Tavily error: {e}")
    
    # Option B: Using Serper (Google search)
    elif SERPER_API_KEY:
        try:
            print(f"🔍 Searching with Serper: {search_query}")
            
            serper_response = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_API_KEY},
                json={"q": search_query, "num": 10},
                timeout=30
            )
            
            if serper_response.status_code == 200:
                data = serper_response.json()
                news_sources = []
                
                for result in data.get('organic', []):
                    source = {
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'url': result.get('link', ''),
                        'source': result.get('source', '')
                    }
                    news_sources.append(source)
                
                print(f"✅ Found {len(news_sources)} sources via Serper")
                return news_sources
                
        except Exception as e:
            print(f"⚠️ Serper error: {e}")
    
    return []

def ai_process_news(news_sources, country, topic, language):
    """Let AI analyze and summarize found news"""
    
    # Prepare context for AI
    context_text = "Here are recent news sources I found:\n\n"
    
    for i, source in enumerate(news_sources[:6], 1):
        context_text += f"SOURCE {i}:\n"
        context_text += f"Title: {source.get('title', 'N/A')}\n"
        
        if source.get('content'):
            content_preview = source['content'][:300] + "..." if len(source['content']) > 300 else source['content']
            context_text += f"Content: {content_preview}\n"
        elif source.get('snippet'):
            context_text += f"Snippet: {source['snippet']}\n"
            
        context_text += f"URL: {source.get('url', 'N/A')}\n"
        context_text += f"Source: {source.get('source', 'Unknown')}\n"
        context_text += "-" * 50 + "\n"
    
    # AI prompt
    prompt = f"""You are a news journalist. Based on these recent sources about {topic} in {country}, create a comprehensive news report.

{context_text}

IMPORTANT: ONLY use information from the sources above. Do not make up news.

Please provide in this exact format:
📰 **HEADLINE**: [Main headline based on sources]

📋 **EXECUTIVE SUMMARY**: [2-3 paragraph summary]

🔑 **KEY DEVELOPMENTS**:
• [Point 1 with source reference]
• [Point 2 with source reference]
• [Point 3 with source reference]

🌍 **CONTEXT & BACKGROUND**: [Why this matters]

📊 **ANALYSIS**: [Expert analysis based on sources]

🔗 **SOURCES CITED**:
- [Source 1: website.com]
- [Source 2: website.com]

Write in {language} language."""

    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        
        payload = {
            "model": "mixtral-8x7b-32768",  # Groq model with large context
            "messages": [
                {"role": "system", "content": "You are a factual journalist. Only report what you see in sources."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,  # Low temperature for factual reporting
            "max_tokens": 1500,
            "top_p": 0.9
        }
        
        print(f"🤖 AI processing {len(news_sources)} sources...")
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data['choices'][0]['message']['content']
            print(f"✅ AI generated {len(ai_response)} chars")
            return ai_response
            
        else:
            print(f"❌ AI error: {response.status_code}")
            return f"Latest {topic} news in {country}. AI processing unavailable."
            
    except Exception as e:
        print(f"❌ AI processing failed: {e}")
        return f"Recent developments in {topic} for {country}. Sources found: {len(news_sources)}."

@app.route('/get_news', methods=['POST', 'OPTIONS'])
def get_news():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json()
        country = data.get('country', 'Global')
        topic = data.get('topic', 'Breaking News')
        language = data.get('language', 'English')
        
        print(f"📡 Request: {country} | {topic} | {language}")
        
        # Step 1: Search the web for real news
        print("🔍 Step 1: Searching web for news...")
        news_sources = search_web_news(country, topic)
        
        if not news_sources:
            print("⚠️ No sources found, using AI fallback")
            # Fallback to AI-generated summary
            prompt = f"Generate a factual news report about {topic} in {country} based on general knowledge up to 2024."
            news_sources = [{'title': f'{topic} in {country}', 'content': 'Recent developments', 'source': 'AI Analysis'}]
        
        # Step 2: Let AI process and summarize
        print("🤖 Step 2: AI processing news...")
        ai_news = ai_process_news(news_sources, country, topic, language)
        
        # Step 3: Handle translation if needed
        needs_translation = data.get('needs_translation', False)
        original_language = data.get('original_language', 'en')
        
        translated_content = None
        if needs_translation and original_language != 'en':
            translated_content = translate_with_ai(ai_news, original_language)
        
        return jsonify({
            'description': ai_news,
            'translated_description': translated_content,
            'success': True,
            'country': country,
            'topic': topic,
            'sources_found': len(news_sources),
            'ai_processed': True,
            'timestamp': 'Just now'
        })
        
    except Exception as e:
        print(f"❌ Server error: {e}")
        return jsonify({
            'error': str(e),
            'fallback': f"News about {data.get('topic', 'current events')}. Try again soon."
        }), 500

def translate_with_ai(text, target_lang):
    """Translate using AI"""
    try:
        if not GROQ_API_KEY:
            return None
            
        prompt = f"Translate this news report to {target_lang} language. Keep journalistic tone:\n\n{text}"
        
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2000
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
            
    except Exception as e:
        print(f"⚠️ Translation error: {e}")
    
    return None

@app.route('/test_search', methods=['GET'])
def test_search():
    """Test endpoint to verify search works"""
    test_sources = search_web_news("Global", "Technology")
    
    return jsonify({
        'search_working': len(test_sources) > 0,
        'sources_found': len(test_sources),
        'sample_sources': test_sources[:2] if test_sources else []
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    
    print(f"\n" + "="*50)
    print("🤖 AI NEWS SEARCHER SERVER")
    print("="*50)
    print(f"🔍 Web Search: {'✅ Tavily' if TAVILY_API_KEY else '✅ Serper' if SERPER_API_KEY else '❌ Not configured'}")
    print(f"🤖 Groq AI: {'✅ Available' if GROQ_API_KEY else '❌ Not configured'}")
    print(f"🌐 Port: {port}")
    print("\nEndpoints:")
    print(f"  POST /get_news     - Get AI-searched news")
    print(f"  GET  /test_search  - Test search function")
    print("="*50)
    
    app.run(host='0.0.0.0', port=port)