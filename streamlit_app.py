import streamlit as st

st.set_page_config(
    page_title="NHS Data Hub",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 NHS Data Hub")
st.subheader("Stop wrestling with NHS data in Excel. Get AI-powered insights in minutes.")

st.markdown("""
**Transform your ePACT2 exports, OpenPrescribing data, and NHSBSA datasets into actionable insights.**

👈 **Use the sidebar to navigate** through different features.
""")

# Simple demo for now
if st.button("🚀 Quick Demo"):
    st.success("Welcome to your NHS Data Hub! Navigate using the sidebar.")