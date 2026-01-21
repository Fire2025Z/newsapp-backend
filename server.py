# server.py - Using FREE Google Gemini API
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
import requests

print("🚀 AI News Assistant Server - Google Gemini (FREE)")

# Get Google Gemini API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not set!")
    print("Get FREE API key from: https://makersuite.google.com/app/apikey")
    print("Then set GEMINI_API_KEY in Railway environment variables")
    exit(1)

print(f"✅ Gemini API Key loaded")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__)

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def after_request(response):
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
1. Generate news in English first
2. Use this exact structure:
   HEADLINE: [Clear, factual headline]
   
   SUMMARY: [2-3 sentence summary]
   
   KEY DEVELOPMENTS:
   • [Bullet point 1]
   • [Bullet point 2]
   • [Bullet point 3]
   • [Bullet point 4]
   
   CONTEXT: [Relevant background]

3. Rules:
   - Focus on latest developments
   - Use neutral, factual tone
   - No sensationalism
   - If country info limited, provide regional context
   - Never invent facts

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
        
        print(f"📰 Request: {country} | {topic}")
        
        # Get news prompt
        prompt = get_news_prompt(country, topic)
        
        print("🤖 Calling Gemini API...")
        
        # Call Gemini API
        response = model.generate_content(prompt)
        
        if response.text:
            news_content = response.text
            print(f"✅ Gemini response received ({len(news_content)} chars)")
            
            result = {
                'description': news_content,
                'success': True,
                'language': 'en',
                'country': country,
                'topic': topic,
                'translated_description': None,
                'is_rtl': False,
                'ai_provider': 'Google Gemini (Free)'
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
            
            return jsonify(result)
        else:
            return jsonify({'error': 'No response from AI'}), 500
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch news',
            'details': str(e)
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'AI News Assistant',
        'ai_provider': 'Google Gemini (Free)',
        'message': 'Server is working'
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"\n🌍 Server starting on port {port}")
    print(f"🤖 Using: Google Gemini API (Free)")
    print(f"🔗 Get API key: https://makersuite.google.com/app/apikey")
    app.run(host='0.0.0.0', port=port, debug=False)