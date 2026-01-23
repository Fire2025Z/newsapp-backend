# server.py - UPDATED WITH CORRECT GROQ MODEL
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

print("🚀 REAL AI NEWS SERVER - UPDATED GROQ MODEL")

# Get API key
API_KEY = os.environ.get("GROQ_API_KEY")

if not API_KEY:
    print("❌ ERROR: GROQ_API_KEY not found!")
    exit(1)

print(f"✅ API Key loaded: {API_KEY[:10]}...")

app = Flask(__name__)
CORS(app)

def get_news_prompt(country, topic):
    return f"""You are a professional journalist. Generate news about {topic} for {country}.

Use this exact structure:
HEADLINE: [Factual headline]

SUMMARY: [2-3 sentence summary]

KEY DEVELOPMENTS:
• [Important point 1]
• [Important point 2]
• [Important point 3]
• [Important point 4]

CONTEXT: [Background information]

SOURCES: [Credible sources]

Focus on recent developments, be factual and neutral."""

@app.route('/get_news', methods=['POST', 'OPTIONS'])
def get_news():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json()
        country = data.get('country', 'Global')
        topic = data.get('topic', 'Breaking News')
        
        print(f"📡 Request: {country} | {topic}")
        
        # Call Groq API with CORRECT MODEL
        headers = {"Authorization": f"Bearer {API_KEY}"}
        prompt = get_news_prompt(country, topic)
        
        payload = {
            # ⚠️ UPDATED MODEL NAME - Use one of these:
            "model": "llama-3.1-70b-versatile",  # OR "llama-3.1-8b-instant"
            "messages": [
                {"role": "system", "content": "You are a professional journalist."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 1000
        }
        
        print(f"🤖 Calling Groq API with model: {payload['model']}")
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"API Status: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = response.text[:200] if response.text else 'No response'
            print(f"❌ API Error: {response.status_code} - {error_msg}")
            
            # Try alternative model if first fails
            if "decommissioned" in error_msg or "not found" in error_msg:
                print("🔄 Trying alternative model...")
                payload["model"] = "llama-3.1-8b-instant"  # Alternative
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                print(f"Alternative model status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            print(f"✅ REAL AI Response: {len(content)} chars")
            print(f"📝 Preview: {content[:150]}...")
            
            return jsonify({
                'description': content,
                'success': True,
                'country': country,
                'topic': topic,
                'real_ai': True,
                'ai_provider': 'Groq',
                'model': payload['model']
            })
        else:
            return jsonify({
                'error': 'AI API failed',
                'status_code': response.status_code,
                'message': response.text[:200] if response.text else 'No response',
                'solution': 'Check available models at: https://console.groq.com/docs/models'
            }), 500
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test', methods=['GET'])
def test():
    """Test available models"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        # Get available models
        response = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers=headers,
            timeout=10
        )
        
        available_models = []
        if response.status_code == 200:
            models_data = response.json()
            available_models = [m['id'] for m in models_data.get('data', [])]
        
        return jsonify({
            'status': 'running',
            'api_key': 'Valid',
            'available_models': available_models[:5],  # First 5 models
            'recommended_model': 'llama-3.1-70b-versatile',
            'timestamp': 'Server is ready'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/debug', methods=['GET'])
def debug():
    """Debug endpoint"""
    # Test with a simple prompt
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [{"role": "user", "content": "Say 'AI is working'"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        return jsonify({
            'api_key_exists': True,
            'api_key_valid': response.status_code == 200,
            'api_response_code': response.status_code,
            'api_response': response.text[:200] if response.text else 'No response',
            'model_tested': payload['model']
        })
        
    except Exception as e:
        return jsonify({
            'api_key_exists': True,
            'api_key_valid': False,
            'error': str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"\n✅ Server ready on port {port}")
    print(f"🤖 Using Groq API")
    print(f"🔗 Test: http://localhost:{port}/test")
    print(f"🔧 Debug: http://localhost:{port}/debug")
    app.run(host='0.0.0.0', port=port)