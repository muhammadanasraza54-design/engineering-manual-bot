import streamlit as st
import requests
import json
import pypdf
import base64
import re
from streamlit_mic_recorder import mic_recorder

st.set_page_config(layout="wide", page_title="Engineering Manual AI")

st.title("🏗️ TCF Engineering Manual AI Assistant")
st.markdown("---")

API_KEY = "AQ.Ab8RN6IuNtJeIQ_NzjIWHvHXspbj2CahUJKeHuMo5n7aNDIAAw"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

@st.cache_data
def extract_pdf_content(uploaded_file):
    viewer_context = []
    reader = pypdf.PdfReader(uploaded_file)
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            viewer_context.append({"page": page_num + 1, "content": text})
    return viewer_context

def ask_manual_direct(query, manual_data):
    # Filter content to avoid heavy payload
    keywords = query.lower().split()
    relevant_chunks = []
    for data in manual_data:
        if any(kw in data['content'].lower() for kw in keywords) or len(relevant_chunks) < 5:
            relevant_chunks.append(data)
            
    context = ""
    for data in relevant_chunks[:8]:
        context += f"\n--- PAGE {data['page']} ---\n{data['content']}\n"
        
    prompt = f"""
    You are an expert engineering assistant. Use the following manual context to answer the user's question.
    Instructions:
    1. Answer strictly from the provided context. Do not invent technical details.
    2. If the user asks or speaks in Urdu, reply in clear Urdu. If in English, reply in English.
    3. You MUST include the exact page reference inside brackets at the end of your response like this: [Page: X]
    
    Context:
    {context}
    Question: {query}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        return f"Error: {response.status_code}"
    except:
        return "Connection Timeout/Error."

# Sidebar for PDF Upload
st.sidebar.header("📂 Manual Upload")
uploaded_file = st.sidebar.file_uploader("Upload Engineering Manual (PDF)", type="pdf")

if uploaded_file:
    if "manual_data" not in st.session_state:
        with st.spinner("Processing Manual..."):
            st.session_state.manual_data = extract_pdf_content(uploaded_file)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "active_page" not in st.session_state:
        st.session_state.active_page = 1

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("💬 Voice & Text Chat")
        
        # 🎙️ Voice Recorder Button Component
        st.write("🎤 Bol kar sawal poochhein:")
        audio = mic_recorder(start_prompt="Record Voice (Urdu/English)", stop_prompt="Stop", key='recorder')
        
        user_query = ""
        if audio:
            # Note: Transcription logic can be connected here via Gemini Audio API if needed,
            # For now, it captures audio input directly.
            st.audio(audio['bytes'])
            st.info("Audio captured! Processing text input below while voice sync connects...")

        # Standard text fallback input
        text_input = st.chat_input("Ya phir yahan type karein...")
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
                with st.spinner("Manual se dhoond raha hoon..."):
                    ai_response = ask_manual_direct(user_query, st.session_state.manual_data)
                    st.write(ai_response)
            
            page_match = re.search(r"\[Page:\s*(\d+)\]", ai_response)
            if page_match:
                st.session_state.active_page = int(page_match.group(1))
            
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.rerun()

    with col2:
        st.subheader("📄 Dynamic PDF Viewer")
        uploaded_file.seek(0)
        base64_pdf = base64.b64encode(uploaded_file.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#page={st.session_state.active_page}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
else:
    st.info("Meharbani farma kar sidebar se Engineering Manual upload karein.")
