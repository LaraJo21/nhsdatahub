import streamlit as st

# Import Claude integration
try:
    from utils.claude_integration import render_claude_sidebar
    claude_available = True
except ImportError:
    claude_available = False

st.set_page_config(page_title="Export Results", page_icon="💾", layout="wide")

# Set current page for Claude context
st.session_state.current_page = "Export Results"

# Render Claude sidebar
if claude_available:
    render_claude_sidebar()
else:
    st.sidebar.error("Claude integration not available")

st.title("💾 Export Your Results")
st.subheader("Get Insights in Your Preferred Format")

st.info("🚧 Export functionality coming soon!")