# server.py - REAL AI NEWS APP - COMPLETE WORKING VERSION
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import datetime
import time

print("=" * 70)
print("🚀 AI NEWS ASSISTANT - REAL AI (GROQ API)")
print("=" * 70)

# ===== CONFIGURATION =====
# Get API Key from Railway Environment
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Validate API Key
if not GROQ_API_KEY:
    print("❌ CRITICAL ERROR: GROQ_API_KEY environment variable is NOT SET!")
    print("💡 Solution:")
    print("   1. Go to: https://console.groq.com/keys")
    print("   2. Sign up for FREE account")
    print("   3. Create API Key (starts with gsk_)")
    print("   4. In Railway Dashboard → Variables tab")
    print("   5. Add: GROQ_API_KEY = your-api-key-here")
    print("   6. Redeploy your server")
    print("=" * 70)
    exit(1)  # STOP if no API key

print(f"✅ API Key loaded successfully")
print(f"🔑 Key starts with: {GROQ_API_KEY[:12]}...")
print(f"🤖 AI Provider: Groq API")
print(f"🧠 Model: Llama 3.1 70B")
print("=" * 70)

# ===== FLASK APP =====
app = Flask(__name__)

# CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"]
    }
})

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# ===== AI FUNCTIONS =====
def get_news_prompt(country, topic):
    """Create optimized prompt for news generation"""
    
    prompt = f"""You are a professional journalist and news assistant. Generate news about {topic} for {country}.

CRITICAL INSTRUCTIONS:
1. Generate in English first
2. Use EXACTLY this structure (do not deviate):

HEADLINE: [Clear, factual headline about {topic} in {country}]

SUMMARY: [2-3 sentence summary of the main story. Focus on recent developments.]

KEY DEVELOPMENTS:
• [Bullet point 1 - specific, important development]
• [Bullet point 2 - specific, important development] 
• [Bullet point 3 - specific, important development]
• [Bullet point 4 - specific, important development]

CONTEXT: [Relevant background information about {country} and {topic}]

SOURCES: [Mention credible sources or reference reputable organizations]

JOURNALISTIC RULES:
- Focus on LATEST developments (last 24-48 hours)
- Use NEUTRAL, FACTUAL tone - NO sensationalism
- If specific info about {country} is limited, provide REGIONAL context
- NEVER invent facts, people, or sources
- For political topics, provide BALANCED perspective
- Include REALISTIC details that make it sound current

Generate a comprehensive, professional news report about {topic} in {country}.
Make it sound like REAL breaking news happening right now."""

    return prompt

def call_groq_api(prompt, max_retries=2):
    """Call Groq AI API with retry logic"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-70b-versatile",  # Best model for news
        "messages": [
            {
                "role": "system", 
                "content": "You are a professional journalist working for an international news agency. Generate factual, timely news reports."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4,      # Lower for factual content
        "max_tokens": 1200,      # Enough for detailed news
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    }
    
    for attempt in range(max_retries):
        try:
            print(f"🤖 Attempt {attempt + 1}: Calling Groq AI...")
            
            response = requests.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=45  # Increased timeout
            )
            
            print(f"📡 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                # Validate content
                if content and len(content) > 200:
                    print(f"✅ REAL AI Response Received: {len(content)} characters")
                    print(f"📝 Preview: {content[:150]}...")
                    return content
                else:
                    print("⚠️ AI returned insufficient content")
                    
            elif response.status_code == 401:
                print("❌ ERROR: Invalid API Key (401 Unauthorized)")
                print("💡 Get a new key from: https://console.groq.com/keys")
                return None
                
            elif response.status_code == 429:
                print("⚠️ Rate limit hit, waiting...")
                time.sleep(2)
                continue
                
            else:
                print(f"⚠️ API Error {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout on attempt {attempt + 1}")
            time.sleep(1)
            continue
        except Exception as e:
            print(f"❌ Request Error: {e}")
            break
    
    return None

def translate_text(text, target_language):
    """Translate text using Google Translate API"""
    if target_language == 'en':
        return text
        
    try:
        language_map = {
            'ar': 'ar',      # Arabic
            'ku': 'ckb'      # Sorani Kurdish
        }
        
        target_code = language_map.get(target_language, 'en')
        
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'en',
            'tl': target_code,
            'dt': 't',
            'q': text[:1500]  # Limit length
        }
        
        response = requests.get(url, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0 and data[0]:
                translated_parts = []
                for sentence in data[0]:
                    if sentence and len(sentence) > 0:
                        translated_text = sentence[0] if sentence[0] else ''
                        if translated_text:
                            translated_parts.append(translated_text)
                
                if translated_parts:
                    translated_text = ' '.join(translated_parts)
                    
                    # Add RTL mark for Arabic and Kurdish
                    if target_language in ['ar', 'ku']:
                        translated_text = '\u200F' + translated_text
                    
                    return translated_text
                    
    except Exception as e:
        print(f"⚠️ Translation error: {e}")
    
    return None

# ===== API ENDPOINTS =====
@app.route('/get_news', methods=['POST', 'OPTIONS'])
def get_news():
    """Main endpoint - Get AI-generated news"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        country = data.get('country', 'Global')
        topic = data.get('topic', 'Breaking News')
        original_language = data.get('original_language', 'en')
        needs_translation = data.get('needs_translation', False)
        
        print("\n" + "=" * 50)
        print(f"📰 NEW REQUEST: {country} | {topic}")
        print("=" * 50)
        
        # Generate prompt
        prompt = get_news_prompt(country, topic)
        
        # Call REAL AI
        print("🤖 Calling REAL Groq AI (Llama 3.1 70B)...")
        start_time = time.time()
        
        ai_content = call_groq_api(prompt)
        
        if not ai_content:
            print("❌ AI API FAILED - Check your API key!")
            return jsonify({
                'error': 'AI service unavailable',
                'message': 'Failed to connect to AI service. Please check your API key.',
                'solution': 'Get FREE API key from: https://console.groq.com/keys'
            }), 503
        
        response_time = time.time() - start_time
        print(f"⏱️ AI Response Time: {response_time:.2f} seconds")
        
        # Prepare result
        result = {
            'description': ai_content,
            'success': True,
            'language': 'en',
            'country': country,
            'topic': topic,
            'translated_description': None,
            'is_rtl': False,
            'ai_provider': 'Groq AI',
            'model': 'Llama 3.1 70B',
            'response_time': f"{response_time:.2f}s",
            'real_ai': True,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Translate if needed
        if needs_translation and original_language != 'en':
            print(f"🌍 Translating to {original_language}...")
            translated = translate_text(ai_content, original_language)
            if translated:
                result['translated_description'] = translated
                if original_language in ['ar', 'ku']:
                    result['is_rtl'] = True
                print(f"✅ Translation completed")
            else:
                print("⚠️ Translation failed")
        
        print(f"🎉 REQUEST COMPLETED SUCCESSFULLY")
        print("=" * 50)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ SERVER ERROR: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'details': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint - Verify server and AI status"""
    return jsonify({
        'status': 'running',
        'service': 'AI News Assistant',
        'ai_provider': 'Groq API',
        'model': 'Llama 3.1 70B',
        'api_key_status': 'Valid' if GROQ_API_KEY else 'Missing',
        'api_key_prefix': GROQ_API_KEY[:12] + '...' if GROQ_API_KEY else 'None',
        'real_ai': True,
        'version': '2.0.0',
        'features': [
            'Real AI news generation',
            '10 countries supported',
            '24 topics supported',
            '3 languages (English, Arabic, Kurdish)',
            'RTL support for Arabic/Kurdish'
        ],
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ai_service': 'active',
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/debug', methods=['GET'])
def debug():
    """Debug endpoint - Check API key status"""
    test_prompt = "Say 'AI is working' in one sentence."
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": test_prompt}],
        "max_tokens": 20
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
        
        return jsonify({
            'api_key_exists': bool(GROQ_API_KEY),
            'api_key_valid': response.status_code == 200,
            'api_response_code': response.status_code,
            'api_response_preview': response.text[:200] if response.text else 'No response',
            'server_time': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'api_key_exists': bool(GROQ_API_KEY),
            'api_key_valid': False,
            'error': str(e),
            'server_time': datetime.datetime.now().isoformat()
        })

# ===== MAIN =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    
    print("\n" + "=" * 70)
    print("🚀 SERVER STARTUP COMPLETE")
    print("=" * 70)
    print(f"🌍 Server URL: http://localhost:{port}")
    print(f"🔗 Health Check: /health")
    print(f"🔧 Debug Info: /debug")
    print(f"🧪 Test Endpoint: /test")
    print(f"📡 Main Endpoint: /get_news (POST)")
    print("\n✅ READY TO SERVE REAL AI NEWS REQUESTS!")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=port, debug=False)