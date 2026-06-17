import streamlit as st
import re

st.set_page_config(layout="wide", page_title="TCF Engineering Manual Search")

st.title("🏗️ TCF Engineering Manual Smart Search Engine")
st.markdown("---")

# Text file loading logic (Super lightweight)
def parse_text_manual(uploaded_file):
    content = uploaded_file.read().decode("utf-8")
    # Pages ko split karna markers ke zariye
    pages_raw = content.split("--- PAGE ")
    manual_data = []
    
    for p in pages_raw:
        if p.strip():
            lines = p.split("---\n", 1)
            if len(lines) == 2:
                page_num = lines[0].strip()
                page_text = lines[1].lower()
                manual_data.append({"page": page_num, "content": page_text})
    return manual_data

def search_keyword(query, manual_data):
    keywords = [kw.strip() for kw in query.lower().split() if len(kw.strip()) > 2]
    if not keywords:
        return "Meharbani farma kar search bar mein kuch sahi topic likhein.", "N/A"
        
    page_scores = {}
    for data in manual_data:
        score = sum(data['content'].count(kw) for kw in keywords)
        if score > 0:
            page_scores[data['page']] = score
            
    if not page_scores:
        return f"Maazrat! Pure manual mein kahin bhi **'{query}'** ka zikr nahi mila.", "N/A"
        
    sorted_pages = sorted(page_scores.items(), key=lambda x: x[1], reverse=True)
    best_page = sorted_pages[0][0]
    
    result_text = f"🔍 **'{query}' ke liye behtareen matches mil gaye hain:**\n\n"
    result_text += f"✅ Sab se relevant data **Page {best_page}** par maujud hai (Keyword matched {sorted_pages[0][1]} times).\n\n"
    
    if len(sorted_pages) > 1:
        result_text += "📍 **Deegar relevant pages jahan yeh lafz aaya hai:**\n"
        for p, s in sorted_pages[1:6]:
            result_text += f"* **Page {p}** (Matched {s} times)\n"
            
    return result_text, best_page

# Sidebar setup
st.sidebar.header("📂 Data Upload")
uploaded_txt = st.sidebar.file_uploader("Upload Generated Text Manual (manual_text.txt)", type="txt")

if uploaded_txt:
    if "manual_data" not in st.session_state:
        st.session_state.manual_data = parse_text_manual(uploaded_txt)
        
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "active_page" not in st.session_state:
        st.session_state.active_page = "N/A"

    col1, col2 = st.columns([4, 2])

    with col1:
        st.subheader("💬 Search Portal")
        user_query = st.chat_input("Yahan search karein (e.g., gate, boundary, foundation)...")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if user_query:
            with st.chat_message("user"):
                st.write(user_query)
            st.session_state.messages.append({"role": "user", "content": user_query})
            
            with st.chat_message("assistant"):
                result_text, best_page = search_keyword(user_query, st.session_state.manual_data)
                st.write(result_text)
                st.session_state.active_page = best_page
                
            st.session_state.messages.append({"role": "assistant", "content": result_text})
            st.rerun()

    with col2:
        st.subheader("📍 Target Reference")
        st.metric(label="Target Document Page", value=f"Page {st.session_state.active_page}")
        st.success("App completely optimized hai aur memory safe chal rahi hai.")
else:
    st.info("Sidebar se local PC par bani hui 'manual_text.txt' file upload karein.")
