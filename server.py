# server.py - PURE GROQ NEWS SERVER
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
from datetime import datetime

print("🚀 PURE GROQ NEWS SERVER")

# Groq API Key
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("❌ ERROR: GROQ_API_KEY not found!")
    print("💡 Get one at: https://console.groq.com")
    exit(1)

app = Flask(__name__)
CORS(app)

# Country-specific prompts
COUNTRY_PROMPTS = {
    'Iraq': {
        'sources': ['Reuters', 'Al Jazeera', 'BBC Arabic', 'Iraqi News Agency', 'Rudaw'],
        'context': 'Focus on political developments, security, oil industry, and reconstruction.'
    },
    'Syria': {
        'sources': ['Reuters', 'AP News', 'Al Jazeera', 'Syrian Arab News Agency'],
        'context': 'Cover humanitarian situation, political developments, and regional diplomacy.'
    },
    'Kurdistan Region': {
        'sources': ['Rudaw', 'BasNews', 'Kurdistan 24', 'BBC Kurdish'],
        'context': 'Focus on regional government, Peshmerga, oil exports, and Turkey relations.'
    },
    'Iran': {
        'sources': ['Reuters', 'AP', 'BBC Persian', 'Iran International'],
        'context': 'Nuclear program, protests, economy, and regional influence.'
    },
    'Turkey': {
        'sources': ['Reuters', 'AP', 'BBC Turkish', 'Daily Sabah', 'Hurriyet'],
        'context': 'Economy, politics, Syrian refugees, and NATO relations.'
    },
    'Germany': {
        'sources': ['Reuters', 'AP', 'DW', 'Spiegel', 'FAZ'],
        'context': 'Economy, EU politics, energy transition, and technology.'
    },
    'Sweden': {
        'sources': ['Reuters', 'AP', 'SVT', 'DN', 'TT News Agency'],
        'context': 'NATO membership, innovation, climate policy, and social welfare.'
    },
    'United States': {
        'sources': ['Reuters', 'AP', 'CNN', 'NY Times', 'Washington Post'],
        'context': 'Politics, economy, technology, and foreign policy.'
    },
    'Global': {
        'sources': ['Reuters', 'AP', 'BBC', 'AFP', 'Bloomberg'],
        'context': 'Major international developments and global trends.'
    }
}

def generate_groq_news(country, topic, language):
    """Generate news report using Groq's knowledge"""
    
    country_info = COUNTRY_PROMPTS.get(country, COUNTRY_PROMPTS['Global'])
    
    # Get current date for realism
    current_date = datetime.now().strftime("%B %d, %Y")
    
    prompt = f"""You are a professional journalist for an international news agency.
Today's date: {current_date}

GENERATE A REALISTIC NEWS REPORT about: {topic.upper()} in {country.upper()}

USE THIS EXACT STRUCTURE:

📰 **BREAKING NEWS REPORT** - {current_date}

🌍 **LOCATION**: {country}
📊 **TOPIC**: {topic}

🎯 **EXECUTIVE SUMMARY**: [2-3 paragraphs summarizing key developments]

🔴 **LATEST DEVELOPMENTS**:
• [Development 1 with specific details]
• [Development 2 with specific details]
• [Development 3 with specific details]
• [Development 4 with specific details]

📈 **KEY FACTS & FIGURES**:
- [Fact 1 with numbers if available]
- [Fact 2 with numbers if available]
- [Fact 3 with numbers if available]

🤝 **STAKEHOLDERS INVOLVED**:
- [Who is involved]
- [Their positions/interests]

💡 **ANALYSIS & IMPLICATIONS**:
[2 paragraphs of expert analysis]

🎙️ **EXPERT QUOTES**:
"[Realistic quote from expert]"
- [Expert name], [Title]

📅 **BACKGROUND CONTEXT**:
{country_info['context']}

📋 **NEXT STEPS TO WATCH**:
• [What might happen next]
• [Key dates/deadlines]

🔗 **REPORTING SOURCES** (as if researched):
- {', '.join(country_info['sources'])}

⚠️ **IMPORTANT INSTRUCTIONS**:
1. Make it sound CURRENT and TIMELY
2. Include realistic details (names, places, numbers)
3. Be factual and neutral
4. Use journalistic tone
5. If about future, use words like "expected", "planned", "proposed"
6. Write in {language} language
7. Format with clear sections as shown above

BEGIN YOUR NEWS REPORT:"""

    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        
        # Use Mixtral for best news generation
        payload = {
            "model": "mixtral-8x7b-32768",  # Good for long, detailed content
            "messages": [
                {
                    "role": "system", 
                    "content": """You are a top international journalist. Generate realistic, detailed news reports that sound current and timely. Include specific details, names, places, and numbers where appropriate. Be factual and neutral in tone."""
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,  # Balanced creativity/factuality
            "max_tokens": 2000,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
        
        print(f"🤖 Generating {topic} news for {country} in {language}...")
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            news_report = data['choices'][0]['message']['content']
            
            print(f"✅ Generated {len(news_report)} characters")
            print(f"📝 Preview: {news_report[:150]}...")
            
            return news_report
            
        else:
            error_msg = response.text[:200] if response.text else 'No response'
            print(f"❌ Groq API error {response.status_code}: {error_msg}")
            
            # Try fallback model
            return generate_fallback_news(country, topic, language)
            
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return generate_fallback_news(country, topic, language)

def generate_fallback_news(country, topic, language):
    """Simple fallback if Groq fails"""
    fallback_text = f"""
📰 **NEWS UPDATE: {topic.upper()} IN {country.upper()}**

Key developments are underway regarding {topic.lower()} in {country}. 

Recent reports indicate significant activity in this area, with stakeholders closely monitoring the situation.

**Latest Information:**
• Important discussions are taking place
• Several key factors are being considered
• The situation continues to evolve

**Context:** This development aligns with broader regional and global trends.

**Next Steps:** Further updates are expected as more information becomes available.

*Report generated by AI News Assistant*
"""
    return fallback_text

def translate_with_groq(text, target_lang_code, target_lang_name):
    """Translate using Groq"""
    try:
        prompt = f"""Translate this news report to {target_lang_name} language.
Keep the journalistic tone, formatting, and section headers exactly as they are.
Only translate the content, not the emojis or formatting markers.

News report to translate:
{text}"""

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        
        payload = {
            "model": "llama-3.1-8b-instant",  # Fast for translation
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,  # Low temperature for accurate translation
            "max_tokens": 2500
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

@app.route('/get_news', methods=['POST', 'OPTIONS'])
def get_news():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json()
        country = data.get('country', 'Global')
        topic = data.get('topic', 'Breaking News')
        original_language = data.get('original_language', 'en')
        needs_translation = data.get('needs_translation', False)
        
        print(f"📡 Request: {country} | {topic}")
        
        # Determine language name from code
        language_names = {'en': 'English', 'ar': 'Arabic', 'ku': 'Kurdish'}
        language = language_names.get(original_language, 'English')
        
        # Step 1: Generate news with Groq
        print("🤖 Generating news report...")
        english_news = generate_groq_news(country, topic, 'English')
        
        # Step 2: Translate if needed
        translated_news = None
        if needs_translation and original_language != 'en':
            print(f"🌍 Translating to {language}...")
            translated_news = translate_with_groq(english_news, original_language, language)
        
        return jsonify({
            'description': english_news,
            'translated_description': translated_news,
            'success': True,
            'country': country,
            'topic': topic,
            'language': language,
            'ai_provider': 'Groq AI',
            'model': 'mixtral-8x7b-32768',
            'timestamp': datetime.now().isoformat(),
            'note': 'AI-generated news report based on training data'
        })
        
    except Exception as e:
        print(f"❌ Server error: {e}")
        return jsonify({
            'error': str(e),
            'fallback_news': f"Latest developments in {data.get('topic', 'news')} for {data.get('country', 'the region')}. More updates to follow.",
            'success': False
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'status': 'running',
        'ai_provider': 'Groq',
        'api_key_configured': bool(GROQ_API_KEY),
        'endpoints': {
            'POST /get_news': 'Get AI-generated news',
            'GET /test': 'This test endpoint',
            'GET /demo': 'Demo news generation'
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/demo', methods=['GET'])
def demo():
    """Generate a demo news report"""
    try:
        demo_news = generate_groq_news('Global', 'Technology', 'English')
        
        return jsonify({
            'demo': True,
            'country': 'Global',
            'topic': 'Technology',
            'news': demo_news[:500] + "..." if len(demo_news) > 500 else demo_news,
            'full_length': len(demo_news)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    
    print(f"\n" + "="*60)
    print("🤖 PURE GROQ NEWS SERVER")
    print("="*60)
    print(f"🔑 API Key: {'✅ Loaded' if GROQ_API_KEY else '❌ Missing'}")
    print(f"🌐 Port: {port}")
    print(f"📰 Countries supported: {len(COUNTRY_PROMPTS)}")
    print(f"📊 Topics: Comprehensive coverage")
    print("\n📋 Endpoints:")
    print(f"  POST /get_news - Main news endpoint")
    print(f"  GET  /test     - Server status")
    print(f"  GET  /demo     - Demo news")
    print("\n💡 Note: This generates realistic news reports using Groq AI.")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=False)