# server.py - UPDATED with new google-genai package
from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import datetime
import os
from google import genai
from google.genai import types
import requests

print("🚀 AI News Assistant Server - Updated Gemini API")

# Get Gemini API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize Gemini AI if API key is available
ai_enabled = False
client = None

if GEMINI_API_KEY:
    try:
        # Initialize with new client
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Test the connection with a simple call
        test_response = client.models.list()
        print(f"✅ Gemini API Key loaded successfully")
        print(f"📋 Available models: {[m.name for m in test_response.models][:3]}...")
        
        ai_enabled = True
        print("🤖 AI: ENABLED (Using Gemini 1.5 Flash)")
        
    except Exception as e:
        print(f"⚠️ Gemini initialization failed: {e}")
        print("💡 Using demo mode. Check your API key and region.")
        ai_enabled = False
else:
    print("⚠️ GEMINI_API_KEY not set. Using demo mode.")
    print("💡 Get FREE key: https://aistudio.google.com/app/apikey")

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
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# YOUR PROMPT FUNCTION - KEPT EXACTLY
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

def generate_demo_news(country, topic):
    """Generate demo news when AI is not available"""
    country_details = {
        'Iraq': {'capital': 'Baghdad', 'region': 'Middle East'},
        'Syria': {'capital': 'Damascus', 'region': 'Middle East'},
        'Kurdistan Region': {'capital': 'Erbil', 'region': 'Middle East'},
        'Iran': {'capital': 'Tehran', 'region': 'Middle East'},
        'Turkey': {'capital': 'Ankara', 'region': 'Europe/Asia'},
        'Germany': {'capital': 'Berlin', 'region': 'Europe'},
        'Sweden': {'capital': 'Stockholm', 'region': 'Scandinavia'},
        'United States': {'capital': 'Washington D.C.', 'region': 'North America'},
        'All Europe': {'capital': 'Various', 'region': 'Europe'},
        'Global': {'capital': 'Worldwide', 'region': 'Global'}
    }
    
    country_info = country_details.get(country, {'capital': 'the region', 'region': 'the area'})
    
    headlines = [
        f"Latest {topic} Updates from {country}",
        f"{country} Reports Progress in {topic}",
        f"{topic} Developments in {country} Show Positive Trends",
        f"International Community Observes {topic} Advancements in {country}",
        f"{country}'s {topic} Sector Experiences Growth"
    ]
    
    summaries = [
        f"Recent developments in {topic.lower()} across {country} indicate positive momentum, with experts noting improved conditions in {country_info['region']}.",
        f"As {country} continues to implement its {topic.lower()} strategies, observable progress has been reported by regional analysts and international observers.",
        f"New assessments of {topic.lower()} in {country} reveal ongoing developments and emerging opportunities for regional cooperation and economic advancement."
    ]
    
    points = [
        "Enhanced regional cooperation initiatives underway",
        "Economic indicators showing gradual improvement",
        "Infrastructure development projects making steady progress",
        "Educational and vocational training programs expanding",
        "Technology adoption increasing across multiple sectors",
        "Environmental conservation efforts gaining traction",
        "Cultural exchange programs strengthening international ties",
        "Healthcare system improvements being implemented"
    ]
    
    headline = random.choice(headlines)
    summary = random.choice(summaries)
    selected_points = random.sample(points, 4)
    
    news_content = f"""HEADLINE: {headline}

SUMMARY: {summary}

KEY DEVELOPMENTS:
• {selected_points[0]}
• {selected_points[1]}
• {selected_points[2]}
• {selected_points[3]}

CONTEXT: This report examines current {topic.lower()} conditions in {country}, providing insights into recent progress within {country_info['region']}.

REGIONAL PERSPECTIVE: Developments in {country} contribute to broader regional stability and cooperation efforts in {country_info['region']}.

SOURCES: Regional analysts, international observers, and local reports.

GENERATED: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
AI NEWS ASSISTANT | Demo Mode | Country: {country} | Topic: {topic}"""

    return news_content

@app.route('/get_news', methods=['POST', 'OPTIONS'])
def get_news():
    """Handle news requests - Works with AI or Demo"""
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
        
        print(f"📰 Request: {country} | {topic} | AI: {'Enabled' if ai_enabled else 'Demo'}")
        
        news_content = None
        ai_provider = "Demo Mode"
        
        # Try AI first if enabled
        if ai_enabled and client:
            try:
                prompt = get_news_prompt(country, topic)
                print("🤖 Calling Gemini AI (new API)...")
                
                # Use the new API format
                response = client.models.generate_content(
                    model="gemini-1.5-flash",  # Updated model name
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                        max_output_tokens=2000,
                    )
                )
                
                if response.text:
                    news_content = response.text
                    ai_provider = "Google Gemini AI 1.5"
                    print(f"✅ AI response received ({len(news_content)} chars)")
                else:
                    print("⚠️ AI returned empty response, using demo")
                    
            except Exception as ai_error:
                print(f"⚠️ AI error: {ai_error}")
                # Try alternative model
                try:
                    print("🔄 Trying alternative model...")
                    response = client.models.generate_content(
                        model="gemini-1.5-pro",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.4,
                            max_output_tokens=2000,
                        )
                    )
                    if response.text:
                        news_content = response.text
                        ai_provider = "Google Gemini AI 1.5 Pro"
                        print(f"✅ AI response received ({len(news_content)} chars)")
                except Exception as e2:
                    print(f"⚠️ Alternative model also failed: {e2}")
                    # Fall through to demo mode
        
        # Use demo if AI failed or not enabled
        if not news_content:
            news_content = generate_demo_news(country, topic)
            print(f"✅ Demo news generated ({len(news_content)} chars)")
        
        result = {
            'description': news_content,
            'success': True,
            'language': 'en',
            'country': country,
            'topic': topic,
            'translated_description': None,
            'is_rtl': False,
            'ai_provider': ai_provider,
            'ai_enabled': ai_enabled
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
        
        print(f"🎉 Request completed successfully")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            'error': 'Failed to process request',
            'details': str(e)
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'AI News Assistant',
        'ai_status': 'Enabled' if ai_enabled else 'Demo Mode',
        'ai_provider': 'Google Gemini 1.5' if ai_enabled else 'Demo',
        'gemini_api_version': 'google-genai (new)',
        'version': '2.0.0',
        'endpoints': {
            '/get_news': 'POST - Get AI-generated news',
            '/test': 'GET - Server status',
            '/health': 'GET - Health check'
        },
        'supported_countries': 10,
        'supported_topics': 24,
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ai_enabled': ai_enabled,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/debug', methods=['GET'])
def debug():
    """Debug endpoint"""
    return jsonify({
        'ai_enabled': ai_enabled,
        'gemini_key_set': bool(GEMINI_API_KEY),
        'gemini_key_length': len(GEMINI_API_KEY) if GEMINI_API_KEY else 0,
        'client_initialized': bool(client),
        'server_time': datetime.datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"\n{'='*60}")
    print("🤖 AI NEWS ASSISTANT - UPDATED GEMINI API")
    print(f"{'='*60}")
    print(f"🌍 Port: {port}")
    print(f"🤖 AI Status: {'ENABLED' if ai_enabled else 'DEMO MODE'}")
    if ai_enabled:
        print(f"🔑 API Key: Loaded successfully")
    else:
        print(f"🔑 API Key: {'Not set' if not GEMINI_API_KEY else 'Invalid/Error'}")
        print(f"💡 Get FREE key: https://aistudio.google.com/app/apikey")
    print(f"✅ Health check: /health")
    print(f"🐛 Debug: /debug")
    print(f"📡 Main endpoint: /get_news")
    print(f"{'='*60}")
    print("Server starting...")
    app.run(host='0.0.0.0', port=port, debug=False)