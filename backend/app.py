import os
import requests
import pdfplumber
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import string
import nltk
from nltk.corpus import stopwords
from datetime import datetime

nltk.download('stopwords', quiet=True)

app = Flask(__name__)
CORS(app)

SUPABASE_URL = "https://bhthrqyvreuhafdpicol.supabase.co"
SUPABASE_KEY = "sb_publishable_Thded3u-YcIifH-hjxr-FQ_IZ9kNLGZ"
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

model = joblib.load('spam_model.pkl')
vectorizer = joblib.load('vectorizer.pkl')

def clean_text(text):
    text = text.lower()
    text = "".join([char for char in text if char not in string.punctuation])
    words = [w for w in text.split() if w not in set(stopwords.words('english'))]
    return " ".join(words)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        message = ""
        # PDF ya text file ko handle karne ka safe tarika
        if 'file' in request.files:
            file = request.files['file']
            if file.filename.endswith('.pdf'):
                with pdfplumber.open(file) as pdf:
                    message = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            else:
                # Agar CSV ya TXT hai, toh seedha read karo
                message = file.read().decode('utf-8', errors='ignore')
        else:
            message = request.form.get('message', '')

        if not message or not message.strip():
            return jsonify({'error': 'No text could be extracted'}), 400

        cleaned = clean_text(message)
        vec = vectorizer.transform([cleaned])
        result = "spam" if model.predict(vec)[0] == 1 else "ham"
        conf = round(max(model.predict_proba(vec)[0]) * 100, 1)

        payload = {"message": message[:200], "nlp_text": cleaned[:200], "result": result, "confidence": conf, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        res = requests.post(f"{SUPABASE_URL}/rest/v1/search_history", headers=HEADERS, json=payload)
        
        return jsonify({
            'result': result, 
            'confidence': conf, 
            'nlp_text': cleaned[:50], 
            'id': res.json()[0].get('id') if res.status_code in [200, 201] else None
        })
    
    except Exception as e:
        print(f"Backend Error: {e}") # Terminal mein error dikhega
        return jsonify({'error': str(e)}), 500

@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.json
        res = requests.patch(f"{SUPABASE_URL}/rest/v1/search_history?id=eq.{data['id']}", headers=HEADERS, json={"user_feedback": data['feedback']})
        return jsonify({'success': res.status_code == 200})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/search_history?select=*&order=id.desc&limit=5", headers=HEADERS)
        return jsonify(res.json() if res.status_code == 200 else [])
    except: return jsonify([])

if __name__ == '__main__':
    app.run(port=5000, debug=True)