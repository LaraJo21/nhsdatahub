import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="NHS Data Hub",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 1rem;
}
.subtitle {
    font-size: 1.3rem;
    color: #666;
    text-align: center;
    margin-bottom: 2rem;
}
.value-prop {
    background-color: #f0f8ff;
    padding: 2rem;
    border-radius: 10px;
    border-left: 5px solid #1f77b4;
    margin: 2rem 0;
}
.stats-container {
    display: flex;
    justify-content: space-around;
    margin: 2rem 0;
}
.stat-box {
    text-align: center;
    padding: 1rem;
    background-color: #f9f9f9;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🏥 NHS Data Hub</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Stop wrestling with NHS data in Excel. Get AI-powered insights in minutes.</p>', unsafe_allow_html=True)

# Value Proposition
st.markdown("""
<div class="value-prop">
<h3>📊 Transform Your NHS Data Analysis</h3>
<p><strong>Consolidate ePACT2, OpenPrescribing, and NHSBSA data with intelligent AI analysis.</strong></p>
<p>Built by NHS analysts, for NHS analysts. Turn hours of manual data processing into minutes of actionable insights.</p>
</div>
""", unsafe_allow_html=True)

# Quick Stats (placeholder for now)
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("NHS Analysts Using Platform", "500+", "+50 this month")

with col2:
    st.metric("Cost Savings Identified", "£2.3M", "+£400K this quarter")

with col3:
    st.metric("Data Sources Integrated", "5", "+2 planned")

# Problem Statement
st.markdown("---")
st.header("📋 The Problem We Solve")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
    **Current NHS Data Reality:**
    
    - 🔒 **ePACT2**: Manual exports, no automation
    - 🧩 **OpenPrescribing**: Complex API for non-technical users  
    - 📁 **NHSBSA**: Multiple portals, inconsistent formats
    - 📄 **NICE Guidelines**: PDF documents, not machine-readable
    - 🏢 **Local ICB Data**: Siloed in different systems
    
    **Result**: Analysts spend 60% of their time finding and cleaning data instead of generating insights.
    """)

with col2:
    # Create a simple visual showing data fragmentation
    data_sources = ['ePACT2', 'OpenPrescribing', 'NHSBSA Open Data', 'NICE', 'Local ICB']
    complexity_score = [8, 6, 7, 9, 8]
    
    fig = px.bar(
        x=data_sources, 
        y=complexity_score,
        title="Current Data Access Complexity",
        labels={'x': 'Data Source', 'y': 'Complexity Score (1-10)'},
        color=complexity_score,
        color_continuous_scale='Reds'
    )
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

# Solution Preview
st.markdown("---")
st.header("💡 Our Solution")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    **📥 Upload**
    
    Drag & drop your ePACT2 exports or connect to live APIs
    """)

with col2:
    st.markdown("""
    **🤖 AI Analysis**
    
    Claude AI processes and combines your data intelligently
    """)

with col3:
    st.markdown("""
    **📊 Insights**
    
    Interactive dashboards with actionable findings
    """)

with col4:
    st.markdown("""
    **💾 Export**
    
    Power BI, Excel, PDF - whatever format you need
    """)

# Quick Demo
st.markdown("---")
st.header("🚀 Quick Start")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("🔍 Explore Live Data", type="primary", use_container_width=True):
        st.switch_page("pages/02_🔗_Consolidated_View.py")
    
    if st.button("📁 Upload ePACT2 Data", use_container_width=True):
        st.switch_page("pages/04_📁_Upload_Process.py")

with col2:
    if st.button("📊 View Sample Dashboard", use_container_width=True):
        st.switch_page("pages/03_📈_Analytics_Dashboard.py")
    
    if st.button("📋 See All Data Sources", use_container_width=True):
        st.switch_page("pages/01_📊_Data_Sources.py")

# Navigation hint
st.markdown("---")
st.info("👈 **Use the sidebar to navigate** through all features, or click the buttons above for quick access!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
Built with ❤️ by NHS analysts, for NHS analysts | 
<a href="mailto:support@nhsdatahub.co.uk">Contact Support</a> | 
<a href="https://github.com/yourusername/nhs-data-hub">GitHub</a>
</div>
""", unsafe_allow_html=True)