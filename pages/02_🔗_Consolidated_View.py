import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Import Claude integration
try:
    from utils.claude_integration import render_claude_sidebar
    claude_available = True
except ImportError:
    claude_available = False

st.set_page_config(page_title="Consolidated View", page_icon="🔗", layout="wide")

# Set current page for Claude context
st.session_state.current_page = "Consolidated View - NHS Drug Data Explorer"

# Render Claude sidebar
if claude_available:
    render_claude_sidebar()
else:
    st.sidebar.error("Claude integration not available")

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
def get_bnf_lookup():
    """Comprehensive BNF code lookup"""
    return {
        # Cardiovascular System (02)
        'ramipril': ('0205051R0', 'ACE Inhibitor'),
        'amlodipine': ('0206020A0', 'Calcium Channel Blocker'),
        'atorvastatin': ('0212000Y0', 'Statin'),
        'simvastatin': ('0212000X0', 'Statin'),
        'warfarin': ('0208020W0', 'Anticoagulant'),
        'clopidogrel': ('0209000C0', 'Antiplatelet'),
        
        # Central Nervous System (04)
        'paracetamol': ('0407010Q0', 'Analgesic'),
        'morphine': ('0407020Q0', 'Opioid Analgesic'),
        'tramadol': ('0407020T0', 'Opioid Analgesic'),
        'sertraline': ('0403030S0', 'SSRI Antidepressant'),
        'fluoxetine': ('0403030F0', 'SSRI Antidepressant'),
        'lorazepam': ('0401020L0', 'Benzodiazepine'),
        
        # Infections (05)
        'amoxicillin': ('0501013B0', 'Penicillin Antibiotic'),
        'flucloxacillin': ('0501011F0', 'Penicillin Antibiotic'),
        'ciprofloxacin': ('0501040C0', 'Quinolone Antibiotic'),
        'metronidazole': ('0501040M0', 'Antibiotic'),
        
        # Endocrine System (06)
        'metformin': ('0601022B0', 'Diabetes - Biguanide'),
        'insulin': ('0601010H0', 'Diabetes - Insulin'),
        'gliclazide': ('0601021G0', 'Diabetes - Sulfonylurea'),
        'levothyroxine': ('0602010L0', 'Thyroid Hormone'),
        'prednisolone': ('0603020P0', 'Corticosteroid'),
        
        # Gastro-Intestinal System (01)
        'omeprazole': ('0103050P0', 'Proton Pump Inhibitor'),
        'lansoprazole': ('0103050L0', 'Proton Pump Inhibitor'),
        'ranitidine': ('0103020R0', 'H2 Receptor Antagonist'),
        'loperamide': ('0104020L0', 'Anti-diarrhoeal'),
        
        # Respiratory System (03)
        'salbutamol': ('0301011R0', 'Beta2 Agonist'),
        'beclometasone': ('0302000N0', 'Corticosteroid'),
        'prednisolone': ('0302020P0', 'Oral Corticosteroid'),
        
        # Immunological Products (08) - High-cost biologics
        'adalimumab': ('0212000AA', 'TNF Alpha Inhibitor'),
        'infliximab': ('0212000AC', 'TNF Alpha Inhibitor'),
        'etanercept': ('0212000AB', 'TNF Alpha Inhibitor'),
        'rituximab': ('0801020T0', 'Monoclonal Antibody'),
        'trastuzumab': ('0801020Q0', 'Monoclonal Antibody'),
        'bevacizumab': ('0801020B0', 'Monoclonal Antibody'),
        
        # Nutrition and Blood (09)
        'folic acid': ('0906011F0', 'Vitamin B9'),
        'iron sulfate': ('0901011I0', 'Iron Supplement'),
        'vitamin d': ('0906060V0', 'Vitamin D'),
        
        # Musculoskeletal (10)
        'ibuprofen': ('1001010I0', 'NSAID'),
        'diclofenac': ('1001010D0', 'NSAID'),
        'naproxen': ('1001010N0', 'NSAID'),
        'allopurinol': ('1003020A0', 'Uric Acid Reducer'),
        
        # Eye (11)
        'chloramphenicol': ('1103010C0', 'Antibiotic Eye Drops'),
        'timolol': ('1106020T0', 'Glaucoma Treatment'),
        
        # ENT (12)
        'sodium chloride': ('1201010S0', 'Nasal Decongestant'),
        
        # Skin (13)
        'hydrocortisone': ('1303020H0', 'Topical Corticosteroid'),
        'emollient': ('1301020E0', 'Skin Moisturizer')
    }

@st.cache_data(ttl=3600)
def search_drugs(query):
    """Search for drugs using BNF lookup or direct BNF code"""
    bnf_lookup = get_bnf_lookup()
    
    # Check if query is a BNF code (10 characters, alphanumeric)
    if len(query) == 10 and query.replace('A', '').replace('B', '').replace('C', '').replace('D', '').replace('E', '').replace('F', '').replace('G', '').replace('H', '').replace('I', '').replace('J', '').replace('K', '').replace('L', '').replace('M', '').replace('N', '').replace('O', '').replace('P', '').replace('Q', '').replace('R', '').replace('S', '').replace('T', '').replace('U', '').replace('V', '').replace('W', '').replace('X', '').replace('Y', '').replace('Z', '').isdigit():
        # Find drug name by BNF code
        for name, (code, category) in bnf_lookup.items():
            if code.upper() == query.upper():
                return [(name, code, category)]
        return [("Unknown Drug", query.upper(), "Direct BNF Code")]
    
    # Search by drug name
    query_lower = query.lower()
    matches = []
    for name, (code, category) in bnf_lookup.items():
        if query_lower in name.lower():
            matches.append((name, code, category))
    
    return matches

@st.cache_data(ttl=3600)  
def get_enhanced_drug_analysis(bnf_code, drug_name, months=36):
    """Get comprehensive drug analysis data for Claude"""
    
    analysis = {
        "drug_name": drug_name,
        "bnf_code": bnf_code,
        "analysis_date": datetime.now().isoformat(),
        "data_sources": []
    }
    
    # 1. Extended trend data (3 years)
    trend_df = get_total_spending_trend(bnf_code, months=months)
    if not trend_df.empty:
        analysis["trend_data"] = {
            "months_of_data": len(trend_df),
            "date_range": f"{trend_df['date'].min().strftime('%Y-%m')} to {trend_df['date'].max().strftime('%Y-%m')}",
            "latest_cost": float(trend_df['actual_cost'].iloc[-1]) if 'actual_cost' in trend_df.columns else 0,
            "latest_items": float(trend_df['items'].iloc[-1]) if 'items' in trend_df.columns else 0
        }
        
        # Calculate trend metrics
        if len(trend_df) >= 2 and 'actual_cost' in trend_df.columns:
            recent_cost = trend_df['actual_cost'].iloc[-1]
            previous_cost = trend_df['actual_cost'].iloc[-2]
            analysis["trend_data"]["mom_change_pct"] = ((recent_cost - previous_cost) / previous_cost) * 100
            
            # Year-over-year if available
            if len(trend_df) >= 12:
                yoy_cost = trend_df['actual_cost'].iloc[-13]
                analysis["trend_data"]["yoy_change_pct"] = ((recent_cost - yoy_cost) / yoy_cost) * 100
            
            # Overall trend direction
            if len(trend_df) >= 6:
                recent_avg = trend_df['actual_cost'].tail(6).mean()
                older_avg = trend_df['actual_cost'].head(6).mean()
                trend_direction = "increasing" if recent_avg > older_avg * 1.1 else "decreasing" if recent_avg < older_avg * 0.9 else "stable"
                analysis["trend_data"]["overall_trend"] = trend_direction
        
        analysis["data_sources"].append("OpenPrescribing trend data (36 months)")
    
    # 2. ICB regional analysis
    icb_df = get_drug_spending_by_icb(bnf_code, months=12)
    if not icb_df.empty and 'name' in icb_df.columns:
        # Group by ICB and calculate totals
        icb_summary = icb_df.groupby('name').agg({
            'actual_cost': 'sum',
            'items': 'sum'
        }).reset_index()
        
        if not icb_summary.empty:
            analysis["regional_data"] = {
                "total_icbs": len(icb_summary),
                "highest_spending_icb": icb_summary.loc[icb_summary['actual_cost'].idxmax(), 'name'],
                "highest_spending_amount": float(icb_summary['actual_cost'].max()),
                "lowest_spending_icb": icb_summary.loc[icb_summary['actual_cost'].idxmin(), 'name'],
                "lowest_spending_amount": float(icb_summary['actual_cost'].min()),
                "national_total_cost": float(icb_summary['actual_cost'].sum()),
                "national_total_items": float(icb_summary['items'].sum()),
                "average_icb_cost": float(icb_summary['actual_cost'].mean()),
                "median_icb_cost": float(icb_summary['actual_cost'].median())
            }
            
            # Find Derby ICB specifically if it exists
            derby_icbs = icb_summary[icb_summary['name'].str.contains('Derby', case=False, na=False)]
            if not derby_icbs.empty:
                derby_cost = float(derby_icbs['actual_cost'].iloc[0])
                national_avg = analysis["regional_data"]["average_icb_cost"]
                analysis["regional_data"]["derby_vs_national"] = {
                    "derby_cost": derby_cost,
                    "vs_average_pct": ((derby_cost - national_avg) / national_avg) * 100,
                    "percentile_rank": float((icb_summary['actual_cost'] <= derby_cost).mean() * 100)
                }
        
        analysis["data_sources"].append("OpenPrescribing ICB data (12 months)")
    
    # 3. Seasonal analysis if we have enough data
    if not trend_df.empty and len(trend_df) >= 12 and 'date' in trend_df.columns:
        trend_df_copy = trend_df.copy()
        trend_df_copy['month'] = trend_df_copy['date'].dt.month
        trend_df_copy['quarter'] = trend_df_copy['date'].dt.quarter
        
        if 'actual_cost' in trend_df_copy.columns:
            monthly_avg = trend_df_copy.groupby('month')['actual_cost'].mean()
            quarterly_avg = trend_df_copy.groupby('quarter')['actual_cost'].mean()
            
            analysis["seasonal_patterns"] = {
                "highest_spending_month": int(monthly_avg.idxmax()),
                "lowest_spending_month": int(monthly_avg.idxmin()),
                "highest_spending_quarter": int(quarterly_avg.idxmax()),
                "seasonal_variation_pct": float(((monthly_avg.max() - monthly_avg.min()) / monthly_avg.mean()) * 100)
            }
    
    return analysis

@st.cache_data(ttl=3600)
def get_bnf_categories():
    """Get BNF chapter information"""
    return {
        '01': 'Gastro-Intestinal System',
        '02': 'Cardiovascular System', 
        '03': 'Respiratory System',
        '04': 'Central Nervous System',
        '05': 'Infections',
        '06': 'Endocrine System',
        '07': 'Obstetrics, Gynaecology, and Urinary-Tract Disorders',
        '08': 'Malignant Disease and Immunosuppression',
        '09': 'Nutrition and Blood',
        '10': 'Musculoskeletal and Joint Diseases',
        '11': 'Eye',
        '12': 'Ear, Nose, and Oropharynx',
        '13': 'Skin',
        '14': 'Immunological Products and Vaccines',
        '15': 'Anaesthesia'
    }

@st.cache_data(ttl=3600)
def get_related_drugs_context(bnf_code):
    """Get context about related drugs in the same BNF chapter"""
    chapter = bnf_code[:2]
    bnf_lookup = get_bnf_lookup()
    
    related_drugs = []
    for name, (code, category) in bnf_lookup.items():
        if code.startswith(chapter) and code != bnf_code:
            related_drugs.append({"name": name, "bnf_code": code, "category": category})
    
    return {
        "bnf_chapter": chapter,
        "related_drugs": related_drugs[:5],  # Top 5 related
        "bnf_categories": get_bnf_categories()
    }

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

# Cache management
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("---")
    st.header("🔍 NHS Drug Data Explorer")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Add space
    if st.button("🔄 Clear Cache", help="Refresh all cached data"):
        st.cache_data.clear()
        st.success("Cache cleared! Data will be refreshed on next search.")

# Drug search interface
col1, col2 = st.columns([2, 1])

with col1:
    drug_query = st.text_input(
        "🔍 Search for a drug or BNF code:", 
        placeholder="e.g., adalimumab, metformin, 0601022B0",
        help="Search by drug name or enter a 10-character BNF code directly"
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
            drug_name, bnf_code, category = matches[0]  # Take first match
            
            # Get enhanced analysis for Claude
            with st.spinner("🔍 Gathering comprehensive data..."):
                enhanced_analysis = get_enhanced_drug_analysis(bnf_code, drug_name)
                related_context = get_related_drugs_context(bnf_code)
                
                # Store for Claude
                st.session_state.current_drug_analysis = enhanced_analysis
                st.session_state.related_drugs_context = related_context
                st.session_state.comprehensive_context = f"""
                
Comprehensive Analysis for {drug_name.title()}:

DRUG INFORMATION:
- BNF Code: {bnf_code}
- Category: {category}
- BNF Chapter: {related_context['bnf_chapter']} - {related_context['bnf_categories'].get(related_context['bnf_chapter'], 'Unknown')}

SPENDING TRENDS:
{f"- Data Period: {enhanced_analysis['trend_data']['date_range']}" if 'trend_data' in enhanced_analysis else "- No trend data available"}
{f"- Latest Monthly Cost: £{enhanced_analysis['trend_data']['latest_cost']:,.0f}" if 'trend_data' in enhanced_analysis else ""}
{f"- Latest Monthly Items: {enhanced_analysis['trend_data']['latest_items']:,.0f}" if 'trend_data' in enhanced_analysis else ""}
{f"- Month-on-Month Change: {enhanced_analysis['trend_data']['mom_change_pct']:+.1f}%" if 'trend_data' in enhanced_analysis and 'mom_change_pct' in enhanced_analysis['trend_data'] else ""}
{f"- Year-on-Year Change: {enhanced_analysis['trend_data']['yoy_change_pct']:+.1f}%" if 'trend_data' in enhanced_analysis and 'yoy_change_pct' in enhanced_analysis['trend_data'] else ""}
{f"- Overall Trend: {enhanced_analysis['trend_data']['overall_trend'].title()}" if 'trend_data' in enhanced_analysis and 'overall_trend' in enhanced_analysis['trend_data'] else ""}

REGIONAL ANALYSIS:
{f"- Total ICBs: {enhanced_analysis['regional_data']['total_icbs']}" if 'regional_data' in enhanced_analysis else "- No regional data available"}
{f"- Highest Spending ICB: {enhanced_analysis['regional_data']['highest_spending_icb']} (£{enhanced_analysis['regional_data']['highest_spending_amount']:,.0f})" if 'regional_data' in enhanced_analysis else ""}
{f"- Lowest Spending ICB: {enhanced_analysis['regional_data']['lowest_spending_icb']} (£{enhanced_analysis['regional_data']['lowest_spending_amount']:,.0f})" if 'regional_data' in enhanced_analysis else ""}
{f"- National Average ICB Cost: £{enhanced_analysis['regional_data']['average_icb_cost']:,.0f}" if 'regional_data' in enhanced_analysis else ""}
{f"- Derby vs National Average: {enhanced_analysis['regional_data']['derby_vs_national']['vs_average_pct']:+.1f}% (£{enhanced_analysis['regional_data']['derby_vs_national']['derby_cost']:,.0f})" if 'regional_data' in enhanced_analysis and 'derby_vs_national' in enhanced_analysis['regional_data'] else ""}

SEASONAL PATTERNS:
{f"- Highest Spending Month: {enhanced_analysis['seasonal_patterns']['highest_spending_month']}" if 'seasonal_patterns' in enhanced_analysis else "- Insufficient data for seasonal analysis"}
{f"- Seasonal Variation: {enhanced_analysis['seasonal_patterns']['seasonal_variation_pct']:.1f}%" if 'seasonal_patterns' in enhanced_analysis else ""}

RELATED DRUGS IN SAME CATEGORY:
{', '.join([drug['name'].title() for drug in related_context['related_drugs'][:3]])}

DATA SOURCES:
{', '.join(enhanced_analysis['data_sources'])}
"""
                # Force Claude to refresh its context
                st.session_state.claude_context_refresh = datetime.now().isoformat()
                st.write("🔍 DEBUG: Stored comprehensive_context, length:", len(st.session_state.comprehensive_context))
                
            # Display drug information
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.success(f"✅ **{drug_name.title()}**")
            with col2:
                st.info(f"**BNF:** {bnf_code}")
            with col3:
                st.info(f"**Category:** {category}")
            
            # BNF Chapter information
            chapter = bnf_code[:2]
            bnf_categories = get_bnf_categories()
            if chapter in bnf_categories:
                st.markdown(f"📖 **BNF Chapter {chapter}:** {bnf_categories[chapter]}")
            
            # Create tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Spending Overview", "🗺️ Regional Analysis", "📈 Trends", "📋 BNF Info"])
            
            with tab1:
                st.subheader(f"💰 {drug_name.title()} Spending Overview")
                
                # Get recent spending data
                spending_df = get_total_spending_trend(bnf_code, months=12)
                
                # Store data for Claude context
                if not spending_df.empty:
                    st.session_state.current_spending_data = spending_df
                    
                    # Give Claude detailed analysis data
                    if 'actual_cost' in spending_df.columns and len(spending_df) >= 2:
                        latest_cost = spending_df['actual_cost'].iloc[-1]
                        previous_cost = spending_df['actual_cost'].iloc[-2]
                        mom_change = ((latest_cost - previous_cost) / previous_cost) * 100
                        
                        # Get min/max for context
                        min_cost = spending_df['actual_cost'].min()
                        max_cost = spending_df['actual_cost'].max()
                        avg_cost = spending_df['actual_cost'].mean()
                        
                        analysis_summary = f"""
{drug_name.title()} Spending Analysis:
- Latest Month: £{latest_cost:,.0f}
- Previous Month: £{previous_cost:,.0f} 
- Month-on-Month Change: {mom_change:+.1f}%
- 12-Month Range: £{min_cost:,.0f} to £{max_cost:,.0f}
- Average Monthly Spend: £{avg_cost:,.0f}
- Total Months of Data: {len(spending_df)}
- Trend Direction: {'Increasing' if mom_change > 5 else 'Decreasing' if mom_change < -5 else 'Stable'}
"""
                        
                        st.session_state.current_analysis = analysis_summary
                    else:
                        st.session_state.current_analysis = f"{drug_name.title()} data loaded but insufficient for trend analysis"
                
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
                
                # Store ICB data for Claude context
                if not icb_df.empty and 'name' in icb_df.columns:
                    st.session_state.current_icb_data = icb_df
                    top_icb = icb_df.groupby('name')['actual_cost'].sum().idxmax() if 'actual_cost' in icb_df.columns else "Unknown"
                    st.session_state.current_icb_summary = f"{drug_name.title()} ICB data: {len(icb_df['name'].unique())} ICBs, top spender: {top_icb}"
                
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
            
            with tab4:
                st.subheader(f"📋 BNF Information - {drug_name.title()}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🔢 BNF Code Breakdown")
                    st.code(f"""
BNF Code: {bnf_code}

Chapter:     {bnf_code[:2]} - {bnf_categories.get(bnf_code[:2], 'Unknown')}
Section:     {bnf_code[:4]}
Subsection:  {bnf_code[:6]}  
Paragraph:   {bnf_code[:7]}
Chemical:    {bnf_code[:9]}
Product:     {bnf_code}
                    """)
                
                with col2:
                    st.markdown("### 📖 Drug Classification")
                    st.write(f"**Primary Category:** {category}")
                    st.write(f"**Generic Name:** {drug_name.title()}")
                    
                    # Additional info based on category
                    if "TNF Alpha Inhibitor" in category:
                        st.info("🔬 **High-cost biologic** used for autoimmune conditions like rheumatoid arthritis, inflammatory bowel disease")
                    elif "Statin" in category:
                        st.info("💊 **Cholesterol-lowering medication** for cardiovascular disease prevention")
                    elif "Diabetes" in category:
                        st.info("🩺 **Diabetes medication** for blood glucose control")
                    elif "Antibiotic" in category:
                        st.info("🦠 **Antimicrobial medication** for treating bacterial infections")
                
                # BNF Chapter overview
                st.markdown("### 📚 BNF Chapter Overview")
                chapter_info = {
                    '01': 'Includes antacids, antiemetics, laxatives, antidiarrhoeals',
                    '02': 'Includes ACE inhibitors, beta blockers, diuretics, statins',
                    '03': 'Includes bronchodilators, corticosteroids, antihistamines',
                    '04': 'Includes analgesics, antidepressants, antiepileptics',
                    '05': 'Includes antibiotics, antifungals, antivirals',
                    '06': 'Includes diabetes medications, thyroid hormones, corticosteroids',
                    '08': 'Includes cytotoxic drugs, immunosuppressants, biologics',
                    '09': 'Includes vitamins, minerals, blood products',
                    '10': 'Includes NSAIDs, disease-modifying drugs, muscle relaxants'
                }
                
                if chapter in chapter_info:
                    st.write(chapter_info[chapter])
                
                # Quick BNF search
                st.markdown("### 🔍 Quick BNF Search")
                other_drugs_in_chapter = [(name, code, cat) for name, (code, cat) in get_bnf_lookup().items() if code.startswith(chapter) and name != drug_name]
                
                if other_drugs_in_chapter:
                    st.write(f"**Other drugs in Chapter {chapter}:**")
                    for name, code, cat in other_drugs_in_chapter[:5]:  # Show first 5
                        if st.button(f"🔍 {name.title()}", key=f"related_{name}"):
                            st.session_state.current_drug = name
                            st.rerun()
                    
                    if len(other_drugs_in_chapter) > 5:
                        st.write(f"...and {len(other_drugs_in_chapter) - 5} more")
                    
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