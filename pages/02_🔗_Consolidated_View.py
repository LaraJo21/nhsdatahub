import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="Consolidated View", page_icon="🔗", layout="wide")

st.title("🔗 Consolidated NHS Data View")
st.subheader("Your Unified Interface to NHS Data")

# Helper functions for API calls
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_openprescribing_data(endpoint, params=None):
    """Fetch data from OpenPrescribing API"""
    base_url = "https://openprescribing.net/api/1.0"
    url = f"{base_url}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def search_drugs(query):
    """Search for drugs in OpenPrescribing"""
    # This is a simplified search - in reality you'd use their BNF codes
    common_drugs = {
        'adalimumab': '0212000AA',
        'infliximab': '0212000AC', 
        'rituximab': '0801020T0',
        'trastuzumab': '0801020Q0',
        'etanercept': '0212000AB',
        'metformin': '0601022B0',
        'atorvastatin': '0212000Y0',
        'ramipril': '0205051R0'
    }
    
    query_lower = query.lower()
    matches = [(name, code) for name, code in common_drugs.items() if query_lower in name]
    return matches

@st.cache_data(ttl=3600)
def get_drug_spending_by_icb(bnf_code, months=12):
    """Get drug spending by ICB"""
    params = {
        'org_type': 'sicbl',
        'code': bnf_code,
        'format': 'json'
    }
    
    data = get_openprescribing_data('spending_by_org', params)
    if data:
        df = pd.DataFrame(data)
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            # Get last N months
            cutoff_date = datetime.now() - timedelta(days=months*30)
            df = df[df['date'] >= cutoff_date]
        return df
    return pd.DataFrame()

@st.cache_data(ttl=3600)  
def get_total_spending_trend(bnf_code, months=24):
    """Get total spending trend for a drug"""
    params = {
        'code': bnf_code,
        'format': 'json'
    }
    
    data = get_openprescribing_data('spending', params)
    if data:
        df = pd.DataFrame(data)
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            # Get last N months
            cutoff_date = datetime.now() - timedelta(days=months*30)
            df = df[df['date'] >= cutoff_date]
        return df
    return pd.DataFrame()

# Main interface
st.markdown("---")
st.header("🔍 NHS Drug Data Explorer")

# Drug search interface
col1, col2 = st.columns([2, 1])

with col1:
    drug_query = st.text_input(
        "🔍 Search for a drug:", 
        placeholder="e.g., adalimumab, metformin, atorvastatin",
        help="Search for any drug to see NHS prescribing data"
    )

with col2:
    if st.button("🔍 Search", type="primary", disabled=not drug_query):
        if drug_query:
            st.session_state.search_performed = True
            st.session_state.current_drug = drug_query

# Sample quick searches
st.markdown("**Quick searches:**")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("💊 Adalimumab", help="High-cost biologic drug"):
        st.session_state.search_performed = True
        st.session_state.current_drug = "adalimumab"

with col2:
    if st.button("💉 Infliximab", help="Another biologic drug"):
        st.session_state.search_performed = True
        st.session_state.current_drug = "infliximab"

with col3:
    if st.button("💊 Metformin", help="Diabetes medication"):
        st.session_state.search_performed = True
        st.session_state.current_drug = "metformin"

with col4:
    if st.button("💊 Atorvastatin", help="Cholesterol medication"):
        st.session_state.search_performed = True
        st.session_state.current_drug = "atorvastatin"

# Process search if performed
if hasattr(st.session_state, 'search_performed') and st.session_state.search_performed:
    query = st.session_state.current_drug
    
    with st.spinner(f"🔍 Searching NHS data for '{query}'..."):
        # Search for the drug
        matches = search_drugs(query)
        
        if matches:
            drug_name, bnf_code = matches[0]  # Take first match
            
            st.success(f"✅ Found: **{drug_name.title()}** (BNF Code: {bnf_code})")
            
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📊 Spending Overview", "🗺️ Regional Analysis", "📈 Trends"])
            
            with tab1:
                st.subheader(f"💰 {drug_name.title()} Spending Overview")
                
                # Get recent spending data
                spending_df = get_total_spending_trend(bnf_code, months=12)
                
                if not spending_df.empty:
                    # Key metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        latest_cost = spending_df['actual_cost'].iloc[-1] if 'actual_cost' in spending_df.columns else 0
                        st.metric("Latest Monthly Cost", f"£{latest_cost:,.0f}")
                    
                    with col2:
                        total_items = spending_df['items'].iloc[-1] if 'items' in spending_df.columns else 0
                        st.metric("Latest Monthly Items", f"{total_items:,.0f}")
                    
                    with col3:
                        if len(spending_df) >= 2 and 'actual_cost' in spending_df.columns:
                            prev_cost = spending_df['actual_cost'].iloc[-2]
                            current_cost = spending_df['actual_cost'].iloc[-1]
                            change = ((current_cost - prev_cost) / prev_cost) * 100
                            st.metric("Month-on-Month Change", f"{change:+.1f}%")
                        else:
                            st.metric("Month-on-Month Change", "N/A")
                    
                    # Spending trend chart
                    if 'date' in spending_df.columns and 'actual_cost' in spending_df.columns:
                        fig = px.line(
                            spending_df, 
                            x='date', 
                            y='actual_cost',
                            title=f"Monthly Spending Trend - {drug_name.title()}",
                            labels={'actual_cost': 'Cost (£)', 'date': 'Date'}
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No recent spending data available for this drug.")
            
            with tab2:
                st.subheader(f"🗺️ {drug_name.title()} by ICB")
                
                # Get ICB spending data
                icb_df = get_drug_spending_by_icb(bnf_code, months=6)
                
                if not icb_df.empty and 'name' in icb_df.columns:
                    # Group by ICB and sum recent spending
                    icb_summary = icb_df.groupby('name').agg({
                        'actual_cost': 'sum',
                        'items': 'sum'
                    }).reset_index()
                    
                    # Top spending ICBs
                    top_icbs = icb_summary.nlargest(10, 'actual_cost')
                    
                    fig = px.bar(
                        top_icbs,
                        x='actual_cost',
                        y='name',
                        orientation='h',
                        title=f"Top 10 ICBs by {drug_name.title()} Spending (Last 6 months)",
                        labels={'actual_cost': 'Total Cost (£)', 'name': 'ICB'}
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show data table
                    st.subheader("📋 ICB Spending Data")
                    display_df = icb_summary.copy()
                    display_df['actual_cost'] = display_df['actual_cost'].apply(lambda x: f"£{x:,.0f}")
                    display_df['items'] = display_df['items'].apply(lambda x: f"{x:,.0f}")
                    display_df.columns = ['ICB Name', 'Total Cost', 'Total Items']
                    st.dataframe(display_df, use_container_width=True)
                    
                else:
                    st.warning("No ICB data available for this drug.")
            
            with tab3:
                st.subheader(f"📈 {drug_name.title()} Trends & Analysis")
                
                # Get longer trend data
                trend_df = get_total_spending_trend(bnf_code, months=24)
                
                if not trend_df.empty and 'date' in trend_df.columns:
                    # Items vs Cost trend
                    fig = go.Figure()
                    
                    if 'actual_cost' in trend_df.columns:
                        fig.add_trace(go.Scatter(
                            x=trend_df['date'],
                            y=trend_df['actual_cost'],
                            mode='lines+markers',
                            name='Cost (£)',
                            yaxis='y'
                        ))
                    
                    if 'items' in trend_df.columns:
                        fig.add_trace(go.Scatter(
                            x=trend_df['date'],
                            y=trend_df['items'],
                            mode='lines+markers',
                            name='Items',
                            yaxis='y2'
                        ))
                    
                    fig.update_layout(
                        title=f"{drug_name.title()} - Cost vs Volume Trend",
                        xaxis_title="Date",
                        yaxis=dict(title="Cost (£)", side="left"),
                        yaxis2=dict(title="Number of Items", side="right", overlaying="y"),
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Basic analysis
                    st.markdown("### 🔍 Quick Analysis")
                    
                    if 'actual_cost' in trend_df.columns and len(trend_df) >= 12:
                        # Calculate some basic trends
                        recent_6m = trend_df.tail(6)['actual_cost'].mean()
                        previous_6m = trend_df.iloc[-12:-6]['actual_cost'].mean()
                        cost_trend = ((recent_6m - previous_6m) / previous_6m) * 100
                        
                        if cost_trend > 5:
                            st.warning(f"📈 **Increasing costs**: Spending has increased by {cost_trend:.1f}% over the last 6 months")
                        elif cost_trend < -5:
                            st.success(f"📉 **Decreasing costs**: Spending has decreased by {abs(cost_trend):.1f}% over the last 6 months")
                        else:
                            st.info(f"📊 **Stable costs**: Spending has remained relatively stable (±{abs(cost_trend):.1f}%)")
                    
                else:
                    st.warning("Insufficient trend data available for analysis.")
                    
        else:
            st.error(f"❌ Drug '{query}' not found in our database. Try: adalimumab, infliximab, metformin, atorvastatin")

# Information section
st.markdown("---")
st.header("ℹ️ About This Data")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Data Source:** OpenPrescribing.net  
    **Covers:** NHS England primary care prescribing  
    **Updated:** Monthly (with ~6 week lag)  
    **Accuracy:** Official NHS BSA data  
    """)

with col2:
    st.markdown("""
    **BNF Codes:** British National Formulary classification  
    **ICB:** Integrated Care Board areas  
    **Cost:** Net Ingredient Cost (reimbursement price)  
    **Items:** Number of prescription items (not quantity)  
    """)

# Next steps
st.markdown("---")
st.info("🚀 **Coming Soon**: Upload your ePACT2 data to combine with this live API data for deeper analysis!")

if st.button("📁 Upload ePACT2 Data", type="primary"):
    st.switch_page("pages/04_📁_Upload_Process.py")