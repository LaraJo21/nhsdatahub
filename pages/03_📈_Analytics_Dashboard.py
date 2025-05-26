import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import numpy as np

# Import Claude integration
try:
    from utils.claude_integration import render_claude_sidebar
    claude_available = True
except ImportError:
    claude_available = False

st.set_page_config(page_title="Analytics Dashboard", page_icon="📈", layout="wide")

# Set current page for Claude context
st.session_state.current_page = "Analytics Dashboard - NHS Prescribing Analytics"

# Render Claude sidebar
if claude_available:
    render_claude_sidebar()
else:
    st.sidebar.error("Claude integration not available")

# Custom CSS for better dashboard styling
st.markdown("""
<style>
.metric-card {
    background-color: #f0f8ff;
    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #1f77b4;
    margin: 0.5rem 0;
}
.kpi-container {
    background-color: #ffffff;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 1rem 0;
}
.dashboard-header {
    background: linear-gradient(90deg, #1f77b4, #17becf);
    color: white;
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
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
def get_high_cost_drugs_data():
    """Get data for high-cost biologics"""
    high_cost_drugs = ['adalimumab', 'infliximab', 'rituximab', 'trastuzumab', 'omalizumab']
    all_data = []
    
    for drug in high_cost_drugs:
        params = {'q': drug, 'format': 'json'}
        data = get_openprescribing_data('spending', params)
        if data:
            df = pd.DataFrame(data)
            if not df.empty:
                df['drug_name'] = drug.title()
                df['date'] = pd.to_datetime(df['date'])
                # Get last 12 months
                cutoff_date = datetime.now() - timedelta(days=365)
                df = df[df['date'] >= cutoff_date]
                all_data.append(df)
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_biosimilar_analysis():
    """Analyze biosimilar adoption for key drugs"""
    # Focus on adalimumab as an example
    params = {'q': 'adalimumab', 'format': 'json'}
    data = get_openprescribing_data('spending', params)
    
    if data:
        df = pd.DataFrame(data)
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            # Get last 24 months for trend analysis
            cutoff_date = datetime.now() - timedelta(days=730)
            df = df[df['date'] >= cutoff_date]
            return df
    
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_icb_performance_data():
    """Get ICB performance comparison"""
    params = {
        'org_type': 'sicbl',
        'q': 'adalimumab',  # Using adalimumab as example
        'format': 'json'
    }
    
    data = get_openprescribing_data('spending_by_org', params)
    if data:
        df = pd.DataFrame(data)
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            # Get last 6 months
            cutoff_date = datetime.now() - timedelta(days=180)
            df = df[df['date'] >= cutoff_date]
            return df
    
    return pd.DataFrame()

# Dashboard Header
st.markdown("""
<div class="dashboard-header">
<h1>📈 NHS Prescribing Analytics Dashboard</h1>
<p>Real-time insights from NHS prescribing data with AI-powered analysis</p>
</div>
""", unsafe_allow_html=True)

# Dashboard selection
dashboard_type = st.selectbox(
    "📊 Select Dashboard Type:",
    ["High-Cost Drug Monitor", "Biosimilar Adoption Tracker", "ICB Performance Comparison", "Prescribing Patterns Analysis"]
)

if dashboard_type == "High-Cost Drug Monitor":
    st.header("💰 High-Cost Drug Monitor")
    
    with st.spinner("Loading high-cost drug data..."):
        high_cost_df = get_high_cost_drugs_data()
    
    if not high_cost_df.empty:
        # Store data for Claude context
        st.session_state.dashboard_data = high_cost_df
        st.session_state.dashboard_type = "High-Cost Drug Monitor"
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_cost = high_cost_df['actual_cost'].sum()
            st.metric("Total Annual Cost", f"£{total_cost:,.0f}")
        
        with col2:
            total_items = high_cost_df['items'].sum()
            st.metric("Total Items", f"{total_items:,.0f}")
        
        with col3:
            avg_cost_per_item = total_cost / total_items if total_items > 0 else 0
            st.metric("Avg Cost per Item", f"£{avg_cost_per_item:.0f}")
        
        with col4:
            unique_drugs = high_cost_df['drug_name'].nunique()
            st.metric("Drugs Monitored", unique_drugs)
        
        # Monthly spending trend by drug
        col1, col2 = st.columns([2, 1])
        
        with col1:
            monthly_spending = high_cost_df.groupby(['date', 'drug_name'])['actual_cost'].sum().reset_index()
            
            fig = px.line(
                monthly_spending,
                x='date',
                y='actual_cost',
                color='drug_name',
                title="Monthly Spending Trends - High-Cost Biologics",
                labels={'actual_cost': 'Cost (£)', 'date': 'Date', 'drug_name': 'Drug'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Drug spending breakdown
            drug_totals = high_cost_df.groupby('drug_name')['actual_cost'].sum().reset_index()
            
            fig_pie = px.pie(
                drug_totals,
                values='actual_cost',
                names='drug_name',
                title="Spending Distribution"
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Alert system
        st.subheader("🚨 Cost Alerts")
        
        # Calculate month-over-month changes
        latest_month = high_cost_df['date'].max()
        previous_month = latest_month - timedelta(days=30)
        
        alerts = []
        for drug in high_cost_df['drug_name'].unique():
            drug_data = high_cost_df[high_cost_df['drug_name'] == drug]
            
            latest_cost = drug_data[drug_data['date'] == latest_month]['actual_cost'].sum()
            previous_cost = drug_data[drug_data['date'] >= previous_month]['actual_cost'].sum()
            
            if previous_cost > 0:
                change_pct = ((latest_cost - previous_cost) / previous_cost) * 100
                if abs(change_pct) > 10:  # Alert if >10% change
                    alerts.append({
                        'drug': drug,
                        'change': change_pct,
                        'latest_cost': latest_cost
                    })
        
        if alerts:
            for alert in alerts:
                if alert['change'] > 0:
                    st.warning(f"📈 **{alert['drug']}**: {alert['change']:+.1f}% increase (£{alert['latest_cost']:,.0f})")
                else:
                    st.success(f"📉 **{alert['drug']}**: {alert['change']:+.1f}% decrease (£{alert['latest_cost']:,.0f})")
        else:
            st.info("✅ No significant cost changes detected this month")
    
    else:
        st.warning("Unable to load high-cost drug data. Please try again later.")

elif dashboard_type == "Biosimilar Adoption Tracker":
    st.header("🧬 Biosimilar Adoption Tracker")
    
    with st.spinner("Analyzing biosimilar adoption..."):
        biosimilar_df = get_biosimilar_analysis()
    
    if not biosimilar_df.empty:
        # Store for Claude context
        st.session_state.dashboard_data = biosimilar_df
        st.session_state.dashboard_type = "Biosimilar Adoption Tracker"
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Adoption trend over time
            fig = px.line(
                biosimilar_df,
                x='date',
                y='actual_cost',
                title="Adalimumab Spending Trend (Originator + Biosimilars)",
                labels={'actual_cost': 'Monthly Cost (£)', 'date': 'Date'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Calculate potential savings
            if len(biosimilar_df) >= 12:
                recent_avg = biosimilar_df.tail(6)['actual_cost'].mean()
                baseline_avg = biosimilar_df.head(6)['actual_cost'].mean()
                
                st.markdown("""
                <div class="kpi-container">
                <h4>💰 Potential Savings Analysis</h4>
                """, unsafe_allow_html=True)
                
                if recent_avg < baseline_avg:
                    savings = baseline_avg - recent_avg
                    savings_pct = (savings / baseline_avg) * 100
                    annual_savings = savings * 12
                    
                    st.metric("Monthly Savings", f"£{savings:,.0f}", f"{savings_pct:.1f}%")
                    st.metric("Projected Annual Savings", f"£{annual_savings:,.0f}")
                else:
                    st.info("No significant cost reduction detected yet")
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Biosimilar insights
        st.subheader("📊 Key Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            latest_cost = biosimilar_df['actual_cost'].iloc[-1]
            st.metric("Latest Monthly Cost", f"£{latest_cost:,.0f}")
        
        with col2:
            latest_items = biosimilar_df['items'].iloc[-1]
            st.metric("Latest Monthly Items", f"{latest_items:,.0f}")
        
        with col3:
            cost_per_item = latest_cost / latest_items if latest_items > 0 else 0
            st.metric("Cost per Item", f"£{cost_per_item:.0f}")
    
    else:
        st.warning("Unable to load biosimilar data. Please try again later.")

elif dashboard_type == "ICB Performance Comparison":
    st.header("🗺️ ICB Performance Comparison")
    
    with st.spinner("Loading ICB performance data..."):
        icb_df = get_icb_performance_data()
    
    if not icb_df.empty and 'row_name' in icb_df.columns:
        # Store for Claude context
        st.session_state.dashboard_data = icb_df
        st.session_state.dashboard_type = "ICB Performance Comparison"
        
        # Group by ICB
        icb_summary = icb_df.groupby('row_name').agg({
            'actual_cost': 'sum',
            'items': 'sum'
        }).reset_index()
        
        icb_summary['cost_per_item'] = icb_summary['actual_cost'] / icb_summary['items']
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Top spending ICBs
            top_icbs = icb_summary.nlargest(15, 'actual_cost')
            
            fig = px.bar(
                top_icbs,
                x='actual_cost',
                y='row_name',
                orientation='h',
                title="ICB Spending Comparison - Adalimumab (Last 6 months)",
                labels={'actual_cost': 'Total Cost (£)', 'row_name': 'ICB'},
                color='actual_cost',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Performance Metrics")
            
            # Calculate benchmarks
            avg_cost = icb_summary['actual_cost'].mean()
            median_cost = icb_summary['actual_cost'].median()
            
            st.metric("Average ICB Cost", f"£{avg_cost:,.0f}")
            st.metric("Median ICB Cost", f"£{median_cost:,.0f}")
            
            # Efficiency analysis
            st.subheader("⚡ Efficiency Analysis")
            
            # Cost per item analysis
            avg_cost_per_item = icb_summary['cost_per_item'].mean()
            efficient_icbs = icb_summary[icb_summary['cost_per_item'] < avg_cost_per_item * 0.9]
            
            st.metric("Efficient ICBs", f"{len(efficient_icbs)}")
            st.metric("Avg Cost per Item", f"£{avg_cost_per_item:.0f}")
            
            if not efficient_icbs.empty:
                st.success(f"🌟 Most efficient: {efficient_icbs.nsmallest(1, 'cost_per_item')['row_name'].iloc[0]}")
        
        # Performance quartiles
        st.subheader("📈 Performance Quartiles")
        
        icb_summary['quartile'] = pd.qcut(icb_summary['actual_cost'], 4, labels=['Q1 (Lowest)', 'Q2', 'Q3', 'Q4 (Highest)'])
        quartile_counts = icb_summary['quartile'].value_counts()
        
        fig_quartiles = px.bar(
            x=quartile_counts.index,
            y=quartile_counts.values,
            title="ICB Distribution by Spending Quartile",
            labels={'x': 'Quartile', 'y': 'Number of ICBs'}
        )
        st.plotly_chart(fig_quartiles, use_container_width=True)
    
    else:
        st.warning("Unable to load ICB performance data. Please try again later.")

elif dashboard_type == "Prescribing Patterns Analysis":
    st.header("📋 Prescribing Patterns Analysis")
    
    st.info("🚧 Advanced prescribing pattern analysis coming soon!")
    
    # Placeholder for future development
    st.markdown("""
    ### Planned Features:
    
    1. **Seasonal Prescribing Patterns**
       - Identify drugs with seasonal variations
       - Holiday period impacts
       - Weather-related prescribing
    
    2. **Anomaly Detection**
       - Unusual prescribing spikes
       - Regional outliers
       - Cost per item variations
    
    3. **Therapeutic Area Analysis**
       - Compare similar drugs
       - Market share analysis
       - New drug adoption rates
    
    4. **Predictive Analytics**
       - Forecast future spending
       - Budget planning support
       - Trend extrapolation
    """)

# Data export section
st.markdown("---")
st.header("💾 Export Dashboard Data")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Export to Excel", type="primary"):
        st.info("Excel export functionality coming soon!")

with col2:
    if st.button("📈 Export to Power BI"):
        st.info("Power BI integration coming soon!")

with col3:
    if st.button("📄 Generate PDF Report"):
        st.info("PDF report generation coming soon!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
💡 **Pro Tip**: Use the Claude assistant in the sidebar to ask questions about any data displayed on this dashboard!
</div>
""", unsafe_allow_html=True)