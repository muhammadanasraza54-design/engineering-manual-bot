import streamlit as st
import requests
import json
import base64
import re
from streamlit_mic_recorder import mic_recorder

st.set_page_config(layout="wide", page_title="TCF Engineering Manual AI")

st.title("🏗️ TCF Scanned Engineering Manual AI Assistant")
st.markdown("---")

# Streamlit Secrets se safe tareeqay se key uthana
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("🔑 API Key nahi mili! Please App Settings -> Secrets mein 'GEMINI_API_KEY' set karein.")
    st.stop()

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

def ask_gemini_scanned_pdf(query, pdf_bytes):
    # Pure scanned PDF ko base64 mein convert karna taake Gemini direct images parh sake
    encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    
    prompt = f"""
    Aap ek expert engineering structural engineer hain jo TCF (The Citizens Foundation) ke schools ke liye kaam kar rahe hain.
    Aap ke paas poora scanned engineering manual data niche inline_data mein attach hai.
    
    Instructions:
    1. User ke sawal ka jawab strictly is manual ko dekh kar dein. Scanned text/images ko dhyan se parhein.
    2. Agar user Urdu mein poochhe toh Urdu mein jawab dein, English mein poochhe toh English mein.
    3. Apne jawab ke aakhir mein exact page number zaroor likhein is format mein: [Page: X]
    
    User Question: {query}
    """
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": encoded_pdf
                    }
                }
            ]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=45)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 401:
            return "Error 401: Streamlit Secrets mein mojud API Key valid nahi hai. Dubara check karein."
        return f"Server Error: {response.status_code}"
    except Exception as e:
        return "Processing mein thoda zyada waqt lag raha hai. Meharbani farma kar thoda mukhtasar sawal dubara likhein."

# Sidebar upload
st.sidebar.header("📂 Manual Upload")
uploaded_file = st.sidebar.file_uploader("Upload Scanned Engineering Manual (PDF)", type="pdf")

if uploaded_file:
    # Read bytes once
    if "pdf_bytes" not in st.session_state:
        st.session_state.pdf_bytes = uploaded_file.read()
        
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "active_page" not in st.session_state:
        st.session_state.active_page = "N/A"

    col1, col2 = st.columns([4, 2])

    with col1:
        st.subheader("💬 Voice & Text Chat")
        
        audio = mic_recorder(start_prompt="🎤 Click to Speak (Urdu/English)", stop_prompt="🛑 Stop & Process", key='recorder')
        
        user_query = ""
        if audio:
            st.audio(audio['bytes'])
            st.info("Voice record ho chuki hai. Sync complete karne ke liye niche text bar mein 'gate' ya apna topic likh kar enter karein.")

        text_input = st.chat_input("Scanned manual se mutaliq kuch bhi poochhein (e.g., gate detail, boundary wall)...")
        if text_input:
            user_query = text_input

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if user_query:
            with st.chat_message("user"):
                st.write(user_query)
            st.session_state.messages.append({"role": "user", "content": user_query})
            
            with st.chat_message("assistant"):
                with st.spinner("Scanned PDF ke pages parakh raha hoon..."):
                    ai_response = ask_gemini_scanned_pdf(user_query, st.session_state.pdf_bytes)
                    st.write(ai_response)
            
            page_match = re.search(r"\[Page:\s*(\d+)\]", ai_response)
            if page_match:
                st.session_state.active_page = page_match.group(1)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.rerun()

    with col2:
        st.subheader("📍 Document Reference")
        st.metric(label="Last Identified Reference Page", value=f"Page {st.session_state.active_page}")
        st.info("Chunkay aap ka manual scanned image format mein hai, AI isay direct text ke bajaye vision se analyze kar raha hai. Bataye gaye page number ko local PDF par double-check kar lein.")
else:
    st.info("Meharbani farma kar sidebar se Engineering Manual upload karein.")
