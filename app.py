import streamlit as st
import requests
import json
import pypdf
import re
from streamlit_mic_recorder import mic_recorder

st.set_page_config(layout="wide", page_title="Engineering Manual AI")

st.title("🏗️ TCF Engineering Manual AI Assistant")
st.markdown("---")

API_KEY = "AQ.Ab8RN6IuNtJeIQ_NzjIWHvHXspbj2CahUJKeHuMo5n7aNDIAAw"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# Optimization 1: Super lightweight text extraction
@st.cache_data(show_spinner=False)
def extract_pdf_text(uploaded_file):
    viewer_context = []
    reader = pypdf.PdfReader(uploaded_file)
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            viewer_context.append({"page": page_num + 1, "content": text})
    return viewer_context

def ask_manual_direct(query, manual_data):
    keywords = query.lower().split()
    relevant_chunks = []
    
    # Quick keyword filtering to save memory & payload size
    for data in manual_data:
        if any(kw in data['content'].lower() for kw in keywords):
            relevant_chunks.append(data)
    
    # Fallback to first few pages if no keyword matches perfectly
    if not relevant_chunks:
        relevant_chunks = manual_data[:5]
        
    context = ""
    for data in relevant_chunks[:5]: # Send fewer, highly relevant pages
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
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        return f"Server Error: {response.status_code}"
    except:
        return "Response timeout. Thoda mukhtasar sawal poochhein."

# Sidebar
st.sidebar.header("📂 Manual Upload")
uploaded_file = st.sidebar.file_uploader("Upload Engineering Manual (PDF)", type="pdf")

if uploaded_file:
    if "manual_data" not in st.session_state:
        with st.spinner("Parsing Manual (Processing text only)..."):
            st.session_state.manual_data = extract_pdf_text(uploaded_file)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "active_page" not in st.session_state:
        st.session_state.active_page = "N/A"

    col1, col2 = st.columns([4, 2])

    with col1:
        st.subheader("💬 Voice & Text Chat")
        
        # Voice Input Component
        audio = mic_recorder(start_prompt="🎤 Click to Speak (Urdu/English)", stop_prompt="🛑 Stop & Process", key='recorder')
        
        user_query = ""
        if audio:
            st.audio(audio['bytes'])
            st.info("Audio recorded. Please use the text chat bar or verify your prompt while speech sync initializes.")

        text_input = st.chat_input("Yahan apna sawal likhein...")
        if text_input:
            user_query = text_input

        # Display conversation history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if user_query:
            with st.chat_message("user"):
                st.write(user_query)
            st.session_state.messages.append({"role": "user", "content": user_query})
            
            with st.chat_message("assistant"):
                with st.spinner("Manual dhoond raha hoon..."):
                    ai_response = ask_manual_direct(user_query, st.session_state.manual_data)
                    st.write(ai_response)
            
            page_match = re.search(r"\[Page:\s*(\d+)\]", ai_response)
            if page_match:
                st.session_state.active_page = page_match.group(1)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.rerun()

    with col2:
        # Optimization 2: Removed heavy PDF dynamic iframe to prevent Out Of Memory crashes.
        # Instead, showing quick metadata reference.
        st.subheader("📍 Document Reference")
        st.metric(label="Last Identified Reference Page", value=f"Page {st.session_state.active_page}")
        st.info("RAM bachane aur crash se bachne ke liye direct PDF rendering ko off kiya hai. Aap chatbot ke bataye hue page number ko apne local PDF manual mein check kar sakte hain.")
else:
    st.info("Meharbani farma kar sidebar se Engineering Manual upload karein.")
