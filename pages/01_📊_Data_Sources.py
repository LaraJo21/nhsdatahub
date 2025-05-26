import streamlit as st
import pandas as pd
import plotly.express as px

# Import Claude integration
try:
    from utils.claude_integration import render_claude_sidebar
    claude_available = True
except ImportError:
    claude_available = False

st.set_page_config(
    page_title="NHS Data Sources",
    page_icon="📊",
    layout="wide"
)

# Set current page for Claude context
st.session_state.current_page = "Data Sources - NHS Data Landscape"

# Render Claude sidebar
if claude_available:
    render_claude_sidebar()
else:
    st.sidebar.error("Claude integration not available")

st.title("📊 NHS Data Sources")
st.subheader("Understanding the Current NHS Data Landscape")

# Problem statement
st.markdown("""
NHS analysts currently juggle multiple disconnected data sources, each with different access methods, 
formats, and limitations. This fragmentation leads to inefficient workflows and missed insights.
""")

# Data sources overview
st.header("🔍 Current Data Sources")

# Create tabs for each data source
tab1, tab2, tab3, tab4, tab5 = st.tabs(["ePACT2", "OpenPrescribing", "NHSBSA Open Data", "NICE", "Local ICB Data"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### ePACT2 - Prescription Analytics
        
        **What it is:**
        - NHS Business Services Authority's prescription analysis tool
        - Contains detailed prescription-level data
        - Used by pharmacy teams and medicines optimisation specialists
        
        **Current Limitations:**
        - ❌ Manual login required
        - ❌ No API access
        - ❌ Data exports only in CSV/Excel
        - ❌ No automated reporting
        - ❌ Limited to authorized NHS users only
        
        **Data Available:**
        - Individual prescription details
        - Cost and volume analysis
        - Prescriber-level breakdowns
        - Patient demographic data (anonymized)
        """)
    
    with col2:
        st.markdown("""
        **Access Method:**
        ```
        1. Manual login to NHSBSA portal
        2. Navigate to ePACT2 dashboard
        3. Configure analysis parameters
        4. Export data manually
        5. Process in Excel/local tools
        ```
        
        **Update Frequency:**
        Monthly (6 weeks lag)
        
        **Data Volume:**
        🔴 **High** - Prescription level detail
        """)

with tab2:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### OpenPrescribing - Public API
        
        **What it is:**
        - University of Oxford's open platform
        - Makes NHS prescribing data accessible
        - Web interface + REST API available
        
        **Current Advantages:**
        - ✅ Public API with no authentication required
        - ✅ JSON and CSV export options
        - ✅ Updated monthly
        - ✅ Practice and ICB level analysis
        - ✅ Historical trend data
        
        **Limitations:**
        - ⚠️ Complex API for non-technical users
        - ⚠️ Limited to primary care prescribing
        - ⚠️ No patient-level detail
        """)
    
    with col2:
        st.markdown("""
        **API Example:**
        ```python
        # Get adalimumab spending by ICB
        url = "https://openprescribing.net/api/1.0/spending_by_org/"
        params = {
            "org_type": "sicbl",
            "code": "0212000AA",
            "format": "json"
        }
        ```
        
        **Update Frequency:**
        Monthly
        
        **Data Volume:**
        🟡 **Medium** - Practice level aggregation
        """)

with tab3:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### NHSBSA Open Data Portal
        
        **What it is:**
        - Official NHS Business Services Authority data releases
        - Various healthcare datasets
        - FOI responses and statistical releases
        
        **Current Advantages:**
        - ✅ Official NHS data
        - ✅ No authentication required
        - ✅ Various formats (CSV, Excel, JSON)
        - ✅ Covers multiple healthcare areas
        
        **Limitations:**
        - ⚠️ Multiple separate portals
        - ⚠️ Inconsistent data formats
        - ⚠️ Manual download required
        - ⚠️ Limited API functionality
        """)
    
    with col2:
        st.markdown("""
        **Access Method:**
        ```
        1. Navigate to opendata.nhsbsa.net
        2. Browse available datasets
        3. Download individual files
        4. Process locally
        ```
        
        **Update Frequency:**
        Varies by dataset
        
        **Data Volume:**
        🟡 **Medium** - Statistical aggregations
        """)

with tab4:
    st.markdown("""
    ### NICE Guidelines & Data
    
    **Current State:** Mostly PDF documents and web pages, not machine-readable
    
    **Future Integration:** We plan to add NICE guideline integration for context-aware analysis
    """)

with tab5:
    st.markdown("""
    ### Local ICB Data
    
    **Current State:** Siloed in various local systems, often Excel-based
    
    **Future Integration:** Custom upload functionality for local datasets
    """)

# Integration matrix
st.header("🔗 Our Integration Approach")

# Create comparison table
integration_data = {
    'Data Source': ['ePACT2', 'OpenPrescribing', 'NHSBSA Open Data', 'NICE Guidelines', 'Local ICB Data'],
    'Current Access': ['Manual Export', 'Complex API', 'Manual Download', 'PDF Documents', 'Excel Files'],
    'Our Solution': ['Upload & AI Analysis', 'Natural Language Queries', 'Unified Interface', 'Context Integration (Planned)', 'Custom Upload'],
    'Status': ['✅ Available', '✅ Available', '✅ Available', '🔄 Planned', '🔄 Planned']
}

df = pd.DataFrame(integration_data)
st.dataframe(df, use_container_width=True)

# Benefits section
st.header("💡 Benefits of Integration")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **⏱️ Time Savings**
    - Reduce data collection from hours to minutes
    - Eliminate manual format conversions
    - Automated data validation and cleaning
    """)

with col2:
    st.markdown("""
    **🎯 Better Insights**
    - Cross-source data correlation
    - AI-powered trend identification
    - Context-aware recommendations
    """)

with col3:
    st.markdown("""
    **🔄 Standardization**
    - Consistent data formats
    - Unified terminology
    - Repeatable analysis workflows
    """)

# Call to action
st.markdown("---")
st.header("🚀 Ready to Get Started?")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Explore Live API Data", type="primary", use_container_width=True):
        st.switch_page("pages/02_🔗_Consolidated_View.py")

with col2:
    if st.button("📁 Upload Your ePACT2 Data", use_container_width=True):
        st.switch_page("pages/04_📁_Upload_Process.py")