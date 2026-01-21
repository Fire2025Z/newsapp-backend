# server.py - Fixed version with compatible OpenAI SDK
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai  # Using older SDK version
import requests

print("🚀 AI News Assistant Server - OpenAI Version (Fixed)")

# Get OpenAI API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not set in Railway environment!")
    print("Please set OPENAI_API_KEY in Railway dashboard")
    exit(1)

print(f"✅ OpenAI API Key loaded")
print(f"📝 Key starts with: {OPENAI_API_KEY[:12]}...")

# Configure OpenAI with older SDK
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

# Enable CORS for all origins
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

def translate_text(text, target_language):
    """Translate text using Google Translate API"""
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        
        language_map = {
            'ar': 'ar',
            'ku': 'ckb',
            'en': 'en'
        }
        
        target_lang_code = language_map.get(target_language, 'en')
        
        params = {
            'client': 'gtx',
            'sl': 'en',
            'tl': target_lang_code,
            'dt': 't',
            'q': text
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
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
        return None
    except Exception as e:
        print(f"Translation error: {e}")
        return None

def get_news_prompt(country, topic):
    """Get AI prompt for news generation"""
    
    prompt = f"""You are a professional journalist and news assistant. Generate news about {topic} for {country}.

IMPORTANT INSTRUCTIONS:
1. Generate news in English first (for quality)
2. Use this exact structure:
   HEADLINE: [Clear, factual headline]
   
   SUMMARY: [2-3 sentence summary of main story]
   
   KEY DEVELOPMENTS:
   • [Bullet point 1 - important development]
   • [Bullet point 2 - important development]
   • [Bullet point 3 - important development]
   • [Bullet point 4 - important development]
   
   CONTEXT: [Relevant background information]
   
   ADDITIONAL INFO: [Any other important details]

3. Rules:
   - Focus on latest developments (last 24-48 hours)
   - Use neutral, factual tone
   - No sensationalism or bias
   - If specific country info is limited, provide regional context
   - Never invent facts or sources
   - For political topics, use balanced perspective
   - Make it sound like real news

Generate comprehensive news report about {topic} in {country}."""

    return prompt

@app.route('/get_news', methods=['POST', 'OPTIONS'])
def get_news():
    """Handle news requests - Main endpoint"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        country = data.get('country', 'Global')
        topic = data.get('topic', 'Breaking News')
        original_language = data.get('original_language', 'en')
        needs_translation = data.get('needs_translation', False)
        
        print(f"\n📰 NEW REQUEST: {country} | {topic} | Lang: {original_language}")
        
        # Get news prompt
        prompt = get_news_prompt(country, topic)
        
        print("🤖 Calling OpenAI API...")
        
        # Call OpenAI API using older SDK syntax
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Using 3.5 for faster/cheaper response
            messages=[
                {"role": "system", "content": "You are a professional journalist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.4
        )
        
        news_content = response.choices[0].message.content
        print(f"✅ OpenAI response received ({len(news_content)} chars)")
        
        result = {
            'description': news_content,
            'success': True,
            'language': 'en',
            'country': country,
            'topic': topic,
            'translated_description': None,
            'is_rtl': False
        }
        
        # Translate if needed
        if needs_translation and original_language != 'en':
            print(f"🌍 Translating to {original_language}...")
            translated_text = translate_text(news_content, original_language)
            if translated_text:
                result['translated_description'] = translated_text
                if original_language in ['ar', 'ku']:
                    result['is_rtl'] = True
                print(f"✅ Translation completed")
            else:
                print("⚠ Translation failed, keeping English")
        
        print(f"🎉 Request completed successfully")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in get_news: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch news',
            'details': str(e)
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint to check server status"""
    return jsonify({
        'status': 'running',
        'service': 'AI News Assistant',
        'ai_provider': 'OpenAI GPT-3.5-turbo',
        'sdk_version': '0.28.1',
        'endpoints': {
            '/get_news': 'POST - Get news by country, topic, language',
            '/test': 'GET - Server status',
            '/health': 'GET - Health check'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': 'Server is running'
    })

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'AI News Assistant API (OpenAI)',
        'status': 'active',
        'usage': 'Send POST requests to /get_news endpoint'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"\n{'='*60}")
    print("AI NEWS ASSISTANT SERVER - OPENAI (FIXED VERSION)")
    print(f"{'='*60}")
    print(f"🌍 Port: {port}")
    print(f"🔗 Health check: /health")
    print(f"📡 Main endpoint: /get_news")
    print(f"🤖 AI Model: GPT-3.5-turbo")
    print(f"📦 OpenAI SDK: 0.28.1")
    print(f"{'='*60}")
    print("Server starting...")
    app.run(host='0.0.0.0', port=port, debug=False)