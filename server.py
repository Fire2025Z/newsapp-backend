# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import os
# from anthropic import Anthropic
# import requests

# print("AI News Assistant Server - Full Version")

# # Get API key
# ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# if not ANTHROPIC_API_KEY:
#     print("ERROR: ANTHROPIC_API_KEY not set!")
#     # For local testing, you can set it here (remove in production)
#     ANTHROPIC_API_KEY = "your-anthropic-api-key-here"
#     print("Using placeholder API key - replace with your actual key")
# else:
#     print(f"API Key loaded successfully")

# # Initialize Anthropic client
# client = Anthropic(api_key=ANTHROPIC_API_KEY)

# app = Flask(__name__)

# # Enable CORS for all routes with proper configuration
# CORS(app, resources={
#     r"/*": {
#         "origins": "*",
#         "methods": ["GET", "POST", "OPTIONS"],
#         "allow_headers": ["Content-Type", "Accept", "Authorization"]
#     }
# })

# @app.after_request
# def after_request(response):
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
#     return response

# def translate_text(text, target_language):
#     """Translate text using Google Translate API"""
#     try:
#         # Google Translate API endpoint
#         url = "https://translate.googleapis.com/translate_a/single"
        
#         # Map language codes for translation with Sorani Kurdish
#         language_map = {
#             'ar': 'ar',  # Arabic
#             'ku': 'ckb', # Sorani Kurdish (Central Kurdish) code
#             'en': 'en'   # English
#         }
        
#         target_lang_code = language_map.get(target_language, 'en')
        
#         params = {
#             'client': 'gtx',
#             'sl': 'en',  # source language (always English)
#             'tl': target_lang_code,  # target language
#             'dt': 't',
#             'q': text
#         }
        
#         response = requests.get(url, params=params, timeout=30)
        
#         if response.status_code == 200:
#             data = response.json()
#             translated_parts = []
#             for sentence in data[0]:
#                 if sentence and len(sentence) > 0:
#                     translated_text = sentence[0] if sentence[0] else ''
#                     if translated_text:
#                         translated_parts.append(translated_text)
            
#             if translated_parts:
#                 translated_text = ' '.join(translated_parts)
#                 print(f"✓ Translation successful to {target_language} ({target_lang_code})")
                
#                 # Add RTL mark for Arabic and Kurdish
#                 if target_language in ['ar', 'ku']:
#                     translated_text = '\u200F' + translated_text
                
#                 return translated_text
#             else:
#                 print("✗ Translation returned empty result")
#                 return None
#         else:
#             print(f"✗ Translation API error: {response.status_code}")
#             return None
#     except Exception as e:
#         print(f"✗ Translation error: {e}")
#         return None

# def get_news_prompt(country, topic):
#     """Get AI prompt for news generation"""
    
#     prompt = f"""You are a professional journalist and news assistant. Generate news about {topic} for {country}.

# IMPORTANT INSTRUCTIONS:
# 1. Always generate in English first (for quality)
# 2. Use this exact structure:
#    HEADLINE: [Clear, factual headline]
   
#    SUMMARY: [2-3 sentence summary of main story]
   
#    KEY DEVELOPMENTS:
#    • [Bullet point 1]
#    • [Bullet point 2]
#    • [Bullet point 3]
#    • [Bullet point 4]
   
#    CONTEXT: [Relevant background information]
   
#    SOURCES: [Mention credible sources if applicable]

# 3. Rules:
#    - Focus on latest developments (last 24-48 hours)
#    - Use neutral, factual tone
#    - No sensationalism or bias
#    - If specific country info is limited, provide regional context
#    - Never invent facts or sources
#    - For political topics, use balanced perspective

# Generate comprehensive news report about {topic} in {country}."""

#     return prompt

# @app.route('/get_news', methods=['POST', 'OPTIONS'])
# def get_news():
#     """Handle news requests - Main endpoint"""
#     if request.method == 'OPTIONS':
#         # Handle preflight
#         return jsonify({'status': 'ok'}), 200
    
#     try:
#         # Log request
#         print("\n" + "="*50)
#         print("NEW NEWS REQUEST RECEIVED")
        
#         data = request.json
#         if not data:
#             print("✗ No data provided")
#             return jsonify({'error': 'No data provided'}), 400

#         country = data.get('country', 'Global')
#         topic = data.get('topic', 'Breaking News')
#         original_language = data.get('original_language', 'en')
#         needs_translation = data.get('needs_translation', False)
        
#         print(f"✓ Parameters received:")
#         print(f"  Country: {country}")
#         print(f"  Topic: {topic}")
#         print(f"  Language: {original_language}")
#         print(f"  Needs translation: {needs_translation}")
        
#         # Get news prompt
#         prompt = get_news_prompt(country, topic)
#         print(f"✓ Prompt generated ({len(prompt)} chars)")
        
#         # Call Anthropic API for news generation
#         print("⏳ Calling Claude API...")
#         message = client.messages.create(
#             model="claude-3-haiku-20240307",
#             max_tokens=2000,
#             temperature=0.4,
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": prompt
#                         }
#                     ]
#                 }
#             ]
#         )
        
#         if message.content and len(message.content) > 0:
#             response_text = message.content[0].text
#             print(f"✓ Claude response received ({len(response_text)} chars)")
            
#             result = {
#                 'description': response_text,
#                 'success': True,
#                 'language': 'en',
#                 'country': country,
#                 'topic': topic,
#                 'translated_description': None,
#                 'is_rtl': False
#             }
            
#             # Translate if needed
#             if needs_translation and original_language != 'en':
#                 print(f"⏳ Translating to {original_language}...")
#                 translated_text = translate_text(response_text, original_language)
#                 if translated_text:
#                     result['translated_description'] = translated_text
#                     if original_language in ['ar', 'ku']:
#                         result['is_rtl'] = True
#                     print(f"✓ Translation completed")
#                 else:
#                     print("⚠ Translation failed, returning English")
            
#             print(f"✓ Request completed successfully")
#             print("="*50)
            
#             return jsonify(result)
#         else:
#             print("✗ No content from Claude API")
#             return jsonify({'error': 'No news generated by AI'}), 500

#     except Exception as e:
#         print(f"✗ Error in get_news: {str(e)}")
#         print("="*50)
#         return jsonify({
#             'error': 'Failed to fetch news',
#             'details': str(e)
#         }), 500

# @app.route('/test', methods=['GET'])
# def test_endpoint():
#     """Test endpoint to check server status"""
#     return jsonify({
#         'status': 'running',
#         'service': 'AI News Assistant',
#         'version': '1.0',
#         'endpoints': {
#             '/get_news': 'POST - Get news by country, topic, language',
#             '/test': 'GET - Server status'
#         },
#         'supported_countries': 10,
#         'supported_topics': 24,
#         'supported_languages': 3
#     })

# @app.route('/', methods=['GET'])
# def index():
#     """Root endpoint"""
#     return jsonify({
#         'message': 'AI News Assistant API',
#         'status': 'active',
#         'usage': 'Send POST requests to /get_news endpoint'
#     })

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     print(f"\n{'='*60}")
#     print("AI NEWS ASSISTANT SERVER")
#     print(f"{'='*60}")
#     print(f"Port: {port}")
#     print(f"Endpoint: http://localhost:{port}/get_news")
#     print(f"Test: http://localhost:{port}/test")
#     print(f"{'='*60}")
#     print("Server starting...")
#     app.run(host='0.0.0.0', port=port, debug=True)

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from anthropic import Anthropic
import requests

print("🚀 AI News Assistant Server - Railway Edition")

# Get API key from Railway environment
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    print("❌ ERROR: ANTHROPIC_API_KEY not set in Railway environment!")
    print("Please set ANTHROPIC_API_KEY in Railway dashboard")
    exit(1)
else:
    print("✅ API Key loaded successfully from Railway environment")

# Initialize Anthropic client
client = Anthropic(api_key=ANTHROPIC_API_KEY)

app = Flask(__name__)

# Enable CORS for all origins - Railway handles this well
CORS(app, resources={r"/*": {"origins": "*"}})

# Handle OPTIONS preflight requests
@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
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
            else:
                return None
        else:
            print(f"Translation API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Translation error: {e}")
        return None

def get_news_prompt(country, topic):
    prompt = f"""You are a professional journalist and news assistant. Generate news about {topic} for {country}.

IMPORTANT INSTRUCTIONS:
1. Always generate in English first (for quality)
2. Use this exact structure:
   HEADLINE: [Clear, factual headline]
   
   SUMMARY: [2-3 sentence summary of main story]
   
   KEY DEVELOPMENTS:
   • [Bullet point 1]
   • [Bullet point 2]
   • [Bullet point 3]
   • [Bullet point 4]
   
   CONTEXT: [Relevant background information]
   
   SOURCES: [Mention credible sources if applicable]

3. Rules:
   - Focus on latest developments (last 24-48 hours)
   - Use neutral, factual tone
   - No sensationalism or bias
   - If specific country info is limited, provide regional context
   - Never invent facts or sources
   - For political topics, use balanced perspective

Generate comprehensive news report about {topic} in {country}."""

    return prompt

@app.route('/get_news', methods=['POST', 'OPTIONS'])
def get_news():
    """Handle news requests - Main endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        country = data.get('country', 'Global')
        topic = data.get('topic', 'Breaking News')
        original_language = data.get('original_language', 'en')
        needs_translation = data.get('needs_translation', False)
        
        print(f"📰 News request: {country}, {topic}, {original_language}")
        
        # Get news prompt
        prompt = get_news_prompt(country, topic)
        
        # Call Anthropic API
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            temperature=0.4,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        if message.content and len(message.content) > 0:
            response_text = message.content[0].text
            
            result = {
                'description': response_text,
                'success': True,
                'language': 'en',
                'country': country,
                'topic': topic,
                'translated_description': None,
                'is_rtl': False
            }
            
            # Translate if needed
            if needs_translation and original_language != 'en':
                translated_text = translate_text(response_text, original_language)
                if translated_text:
                    result['translated_description'] = translated_text
                    if original_language in ['ar', 'ku']:
                        result['is_rtl'] = True
            
            return jsonify(result)
        else:
            return jsonify({'error': 'No news generated by AI'}), 500

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch news',
            'details': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI News Assistant',
        'version': '1.0'
    })

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'status': 'running',
        'endpoint': '/get_news',
        'method': 'POST',
        'parameters': ['country', 'topic', 'original_language', 'needs_translation']
    })

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'AI News Assistant API',
        'endpoints': {
            '/get_news': 'POST - Fetch AI-generated news',
            '/health': 'GET - Health check',
            '/test': 'GET - Test endpoint'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"\n🌍 Server starting on port {port}")
    print(f"🔗 Health check: /health")
    print(f"📡 Main endpoint: /get_news")
    app.run(host='0.0.0.0', port=port, debug=False)