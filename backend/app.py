# import os
# import string
# import joblib
# import pdfplumber
# import requests
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from datetime import datetime
# import nltk
# from nltk.corpus import stopwords

# # NLTK setup
# nltk.download('stopwords', quiet=True)
# STOPWORDS = set(stopwords.words('english'))

# app = Flask(__name__)
# CORS(app)

# # Configuration - Securely fetching from environment variables (Highly Recommended)
# # Tum apna original URL aur Key yahan waapas string mein likh sakte ho locally test karne ke liye,
# # lekin push karne se pehle inko hide zaroor kar dena!
# SUPABASE_URL = "https://bhthrqyvreuhafdpicol.supabase.co"
# SUPABASE_KEY = "sb_publishable_Thded3u-YcIifH-hjxr-FQ_IZ9kNLGZ"

# HEADERS = {
#     "apikey": SUPABASE_KEY, 
#     "Authorization": f"Bearer {SUPABASE_KEY}", 
#     "Content-Type": "application/json", 
#     "Prefer": "return=representation"
# }

# # Load Models
# try:
#     model = joblib.load('spam_model.pkl')
#     vectorizer = joblib.load('vectorizer.pkl')
# except Exception as e:
#     print(f"Error loading models: {e}")

# def clean_text(text):
#     text = text.lower()
#     text = "".join([char for char in text if char not in string.punctuation])
#     words = [w for w in text.split() if w not in STOPWORDS]
#     return " ".join(words)

# # ==========================================
# # OLD ROUTES (Predict, Feedback, History)
# # ==========================================

# @app.route('/predict', methods=['POST'])
# def predict():
#     try:
#         message = ""
#         # Handle file upload or text input
#         if 'file' in request.files:
#             file = request.files['file']
#             if file.filename.endswith('.pdf'):
#                 with pdfplumber.open(file) as pdf:
#                     message = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
#             else:
#                 message = file.read().decode('utf-8', errors='ignore')
#         else:
#             message = request.form.get('message', '')

#         if not message or not message.strip():
#             return jsonify({'error': 'No content provided'}), 400

#         # Processing
#         cleaned = clean_text(message)
#         vec = vectorizer.transform([cleaned])
#         prediction = model.predict(vec)[0]
#         probability = model.predict_proba(vec)[0]
        
#         result = "spam" if prediction == 1 else "ham"
#         conf = round(float(max(probability)) * 100, 1)

#         # Database Logging
#         payload = {
#             "message": message[:200], 
#             "nlp_text": cleaned[:200], 
#             "result": result, 
#             "confidence": conf, 
#             "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         }
#         res = requests.post(f"{SUPABASE_URL}/rest/v1/search_history", headers=HEADERS, json=payload)
        
#         return jsonify({
#             'result': result, 
#             'confidence': conf, 
#             'id': res.json()[0].get('id') if res.status_code in [200, 201] else None
#         })
    
#     except Exception as e:
#         print(f"Prediction Error: {e}")
#         return jsonify({'error': 'Internal Server Error'}), 500

# @app.route('/feedback', methods=['POST'])
# def feedback():
#     try:
#         data = request.json
#         res = requests.patch(f"{SUPABASE_URL}/rest/v1/search_history?id=eq.{data.get('id')}", 
#                              headers=HEADERS, json={"user_feedback": data.get('feedback')})
#         return jsonify({'success': res.status_code in [200, 204]})
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/history', methods=['GET'])
# def get_history():
#     try:
#         res = requests.get(f"{SUPABASE_URL}/rest/v1/search_history?select=*&order=id.desc&limit=5", headers=HEADERS)
#         return jsonify(res.json() if res.status_code == 200 else [])
#     except: 
#         return jsonify([])

# # ==========================================
# # NEW ROUTE: Fetch & Scan Live Gmail Inbox
# # ==========================================

# @app.route('/fetch-emails', methods=['POST'])
# def fetch_emails():
#     try:
#         data = request.json
#         access_token = data.get('access_token')

#         if not access_token:
#             return jsonify({'error': 'Access token missing'}), 400

#         headers = {'Authorization': f'Bearer {access_token}'}
        
#         # 1. Fetch latest 5 emails from Gmail API
#         list_url = 'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=5'
#         list_resp = requests.get(list_url, headers=headers)
        
#         if list_resp.status_code != 200:
#             print("GOOGLE API ERROR:", list_resp.json()) # Yeh line error ka asli kaaran bata degi
#             return jsonify({'error': 'Failed to fetch emails from Google'}), 400
            
#         messages = list_resp.json().get('messages', [])
#         results = []
        
#         for msg in messages:
#             msg_id = msg['id']
#             msg_url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full'
#             msg_resp = requests.get(msg_url, headers=headers).json()
            
#             # Extract Subject and Snippet
#             snippet = msg_resp.get('snippet', '')
#             headers_list = msg_resp.get('payload', {}).get('headers', [])
#             subject = next((h['value'] for h in headers_list if h['name'] == 'Subject'), 'No Subject')
            
#             # 2. Process through AI Model
#             combined_text = f"{subject} {snippet}"
#             cleaned_text = clean_text(combined_text) # Hum same old preprocessing method use kar rahe hain
#             vec_text = vectorizer.transform([cleaned_text])
#             prediction = model.predict(vec_text)[0]
            
#             # Prediction logic (1 = spam, 0 = ham)
#             result_label = 'spam' if prediction == 1 else 'ham'
            
#             results.append({
#                 'id': msg_id,
#                 'subject': subject,
#                 'snippet': snippet,
#                 'result': result_label
#             })
            
#         return jsonify(results)

#     except Exception as e:
#         print(f"Fetch Emails Error: {e}")
#         return jsonify({'error': 'Internal Server Error'}), 500

# if __name__ == '__main__':
#     app.run(port=5000, debug=True)
import os
import string
import joblib
import pdfplumber
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import nltk
from nltk.corpus import stopwords

# NLTK setup
nltk.download('stopwords', quiet=True)
STOPWORDS = set(stopwords.words('english'))

app = Flask(__name__)
CORS(app)

# Configuration - Supabase DB
SUPABASE_URL = "https://bhthrqyvreuhafdpicol.supabase.co"
SUPABASE_KEY = "sb_publishable_Thded3u-YcIifH-hjxr-FQ_IZ9kNLGZ"
HEADERS = {
    "apikey": SUPABASE_KEY, 
    "Authorization": f"Bearer {SUPABASE_KEY}", 
    "Content-Type": "application/json", 
    "Prefer": "return=representation"
}

# Load ML Models
try:
    model = joblib.load('spam_model.pkl')
    vectorizer = joblib.load('vectorizer.pkl')
except Exception as e:
    print(f"Error loading models: {e}")

def clean_text(text):
    text = text.lower()
    text = "".join([char for char in text if char not in string.punctuation])
    words = [w for w in text.split() if w not in STOPWORDS]
    return " ".join(words)

# ==========================================
# ROUTE 1: Manual Input & PDF Upload Scan
# ==========================================
@app.route('/predict', methods=['POST'])
def predict():
    try:
        message = ""
        if 'file' in request.files:
            file = request.files['file']
            if file.filename.endswith('.pdf'):
                with pdfplumber.open(file) as pdf:
                    message = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            else:
                message = file.read().decode('utf-8', errors='ignore')
        else:
            message = request.form.get('message', '')

        if not message or not message.strip():
            return jsonify({'error': 'No content provided'}), 400

        cleaned = clean_text(message)
        vec = vectorizer.transform([cleaned])
        prediction = model.predict(vec)[0]
        probability = model.predict_proba(vec)[0]
        
        result = "spam" if prediction == 1 else "ham"
        conf = round(float(max(probability)) * 100, 1)

        # Log to Supabase
        payload = {
            "message": message[:200], 
            "nlp_text": cleaned[:200], 
            "result": result, 
            "confidence": conf, 
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        res = requests.post(f"{SUPABASE_URL}/rest/v1/search_history", headers=HEADERS, json=payload)
        
        return jsonify({
            'result': result, 
            'confidence': conf, 
            'id': res.json()[0].get('id') if res.status_code in [200, 201] else None
        })
    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

# ==========================================
# ROUTE 2 & 3: Feedback & History (Database)
# ==========================================
@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.json
        res = requests.patch(f"{SUPABASE_URL}/rest/v1/search_history?id=eq.{data.get('id')}", 
                             headers=HEADERS, json={"user_feedback": data.get('feedback')})
        return jsonify({'success': res.status_code in [200, 204]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/search_history?select=*&order=id.desc&limit=5", headers=HEADERS)
        return jsonify(res.json() if res.status_code == 200 else [])
    except: 
        return jsonify([])

# ==========================================
# ROUTE 4: Live Gmail Fetch & Scan (V2 Feature)
# ==========================================
@app.route('/fetch-emails', methods=['POST'])
def fetch_emails():
    try:
        data = request.json
        access_token = data.get('access_token')

        if not access_token:
            return jsonify({'error': 'Access token missing'}), 400

        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Google API: Fetching latest 15 emails
        list_url = 'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=15'
        list_resp = requests.get(list_url, headers=headers)
        
        if list_resp.status_code != 200:
            print("GOOGLE API ERROR:", list_resp.json()) 
            return jsonify({'error': 'Failed to fetch emails from Google'}), 400
            
        messages = list_resp.json().get('messages', [])
        results = []
        
        for msg in messages:
            msg_id = msg['id']
            msg_url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full'
            msg_resp = requests.get(msg_url, headers=headers).json()
            
            snippet = msg_resp.get('snippet', '')
            headers_list = msg_resp.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers_list if h['name'] == 'Subject'), 'No Subject')
            
            combined_text = f"{subject} {snippet}"
            cleaned_text = clean_text(combined_text)
            vec_text = vectorizer.transform([cleaned_text])
            
            prediction = model.predict(vec_text)[0]
            probability = model.predict_proba(vec_text)[0]
            
            result_label = 'spam' if prediction == 1 else 'ham'
            conf_score = round(float(max(probability)) * 100, 1) # Calculation for Confidence %
            
            results.append({
                'id': msg_id,
                'subject': subject,
                'snippet': snippet,
                'result': result_label,
                'confidence': conf_score
            })
            
        return jsonify(results)

    except Exception as e:
        print(f"FETCH EMAILS ERROR: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)