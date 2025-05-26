import streamlit as st

# Import Claude integration
try:
    from utils.claude_integration import render_claude_sidebar
    claude_available = True
except ImportError:
    claude_available = False

st.set_page_config(page_title="Analytics Dashboard", page_icon="📈", layout="wide")

# Set current page for Claude context
st.session_state.current_page = "Analytics Dashboard"

# Render Claude sidebar
if claude_available:
    render_claude_sidebar()
else:
    st.sidebar.error("Claude integration not available")

st.title("📈 Analytics Dashboard")
st.subheader("Power BI for NHS Data")

st.info("🚧 Sample dashboards coming soon!")

st.markdown("""
### Planned Dashboard Types:

1. **Biosimilar Adoption Tracker**
2. **High-Cost Drug Monitor** 
3. **Prescribing Patterns Analysis**
4. **ICB Performance Comparison**
""")