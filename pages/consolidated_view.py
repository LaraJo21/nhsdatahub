import streamlit as st

st.set_page_config(page_title="Consolidated View", page_icon="🔗", layout="wide")

st.title("🔗 Consolidated NHS Data View")
st.subheader("Your Unified Interface to NHS Data")

st.info("🚧 Coming soon: Live API integration with OpenPrescribing and natural language queries!")

st.markdown("""
### What You'll Be Able to Do:

🔍 **Ask Questions in Plain English:**
- "Show me adalimumab biosimilar uptake in Derby vs national average"
- "What are the top 5 high-cost drugs by spend in Q4 2024?"
- "Compare our ICB's antibiotic prescribing to similar regions"

📊 **Get Instant Visualizations:**
- Interactive charts and maps
- Trend analysis
- Regional comparisons
""")