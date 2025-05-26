import streamlit as st

# Import Claude integration
try:
    from utils.claude_integration import render_claude_sidebar
    claude_available = True
except ImportError:
    claude_available = False

st.set_page_config(page_title="Upload & Process", page_icon="📁", layout="wide")

# Set current page for Claude context
st.session_state.current_page = "Upload & Process - ePACT2 Data"

# Render Claude sidebar
if claude_available:
    render_claude_sidebar()
else:
    st.sidebar.error("Claude integration not available")

st.title("📁 Upload & Process ePACT2 Data")
st.subheader("Transform Your ePACT2 Exports with AI")

# [Rest of your existing upload page content]
st.info("🚧 Upload functionality coming soon!")