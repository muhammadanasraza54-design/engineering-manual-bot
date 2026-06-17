import streamlit as st
import pypdf
import re
from collections import Counter
from streamlit_mic_recorder import mic_recorder

st.set_page_config(layout="wide", page_title="Engineering Manual AI")

st.title("🏗️ TCF Engineering Manual Search Assistant (No-Key Version)")
st.markdown("---")

# Super lightweight text extraction
@st.cache_data(show_spinner=False)
def extract_pdf_text(uploaded_file):
    viewer_context = []
    reader = pypdf.PdfReader(uploaded_file)
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            viewer_context.append({"page": page_num + 1, "content": text.lower()})
    return viewer_context

# Fast local keyword matching instead of AI API
def search_manual_local(query, manual_data):
    keywords = [kw.strip() for kw in query.lower().split() if len(kw.strip()) > 2]
    if not keywords:
        return "Meharbani farma kar sahi se search term likhein ya bolein.", "N/A"
        
    page_scores = {}
    for data in manual_data:
        score = sum(data['content'].count(kw) for kw in keywords)
        if score > 0:
            page_scores[data['page']] = score
            
    if not page_scores:
        return f"Maazrat! Pure manual mein kahin bhi **'{query}'** nahi mila.", "N/A"
        
    # Sort pages by best keyword match match count
    sorted_pages = sorted(page_scores.items(), key=lambda x: x[1], reverse=True)
    best_page = sorted_pages[0][0]
    
    top_matches_text = f"🔍 **Search Results for '{query}':**\n\n"
    top_matches_text += f"✅ Sab se relevant data **Page {best_page}** par mila hai (Keywords matched: {sorted_pages[0][1]} times).\n\n"
    top_matches_text += "📍 **Deegar relevant pages:** " + ", ".join([f"Page {p}" for p, s in sorted_pages[1:6]])
    
    return top_matches_text, best_page

# Sidebar
st.sidebar.header("📂 Manual Upload")
uploaded_file = st.sidebar.file_uploader("Upload Engineering Manual (PDF)", type="pdf")

if uploaded_file:
    if "manual_data" not in st.session_state:
        with st.spinner("Manual scan ho raha hai... (Sirf ek baar waqt lagega)"):
            st.session_state.manual_data = extract_pdf_text(uploaded_file)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "active_page" not in st.session_state:
        st.session_state.active_page = "N/A"

    col1, col2 = st.columns([4, 2])

    with col1:
        st.subheader("💬 Voice & Text Search")
        
        # Voice Button
        audio = mic_recorder(start_prompt="🎤 Click to Speak (Urdu/English)", stop_prompt="🛑 Stop & Search", key='recorder')
        
        user_query = ""
        if audio:
            st.audio(audio['bytes'])
            st.info("Aap ki voice record ho gayi hai! Neeche chat bar mein us topic ka naam (jaise 'gate') type kar ke enter karein taake sync complete ho jaye.")

        text_input = st.chat_input("Kiske baare mein dhoondna hai? (e.g., gate, boundary, concrete)...")
        if text_input:
            user_query = text_input

        # Conversation History Display
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if user_query:
            with st.chat_message("user"):
                st.write(user_query)
            st.session_state.messages.append({"role": "user", "content": user_query})
            
            with st.chat_message("assistant"):
                with st.spinner("Manual dhoond raha hoon..."):
                    result_text, best_page = search_manual_local(user_query, st.session_state.manual_data)
                    st.write(result_text)
                    st.session_state.active_page = best_page
            
            st.session_state.messages.append({"role": "assistant", "content": result_text})
            st.rerun()

    with col2:
        st.subheader("📍 Document Reference")
        st.metric(label="Best Match Page", value=f"Page {st.session_state.active_page}")
        st.info("Yeh tool Bina kisi API Key ke 100% free chal raha hai. Chatbot jo page number bataye, aap usay apne computer par open PDF mein check kar sakte hain.")
else:
    st.info("Meharbani farma kar sidebar se Engineering Manual upload karein.")
