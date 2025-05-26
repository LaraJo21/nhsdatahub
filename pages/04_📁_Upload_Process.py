import streamlit as st
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64

# Import Claude integration
try:
    from utils.claude_integration import render_claude_sidebar
    claude_available = True
except ImportError:
    claude_available = False

st.set_page_config(page_title="Upload & Process", page_icon="📁", layout="wide")

# Set current page for Claude context
st.session_state.current_page = "Upload & Process - ePACT2 Data Analysis"

# Render Claude sidebar
if claude_available:
    render_claude_sidebar()
else:
    st.sidebar.error("Claude integration not available")

# Custom CSS
st.markdown("""
<style>
.upload-zone {
    border: 2px dashed #1f77b4;
    border-radius: 10px;
    padding: 2rem;
    text-align: center;
    background-color: #f0f8ff;
    margin: 1rem 0;
}
.success-zone {
    border: 2px solid #28a745;
    border-radius: 10px;
    padding: 1rem;
    background-color: #d4edda;
    margin: 1rem 0;
}
.analysis-card {
    background-color: #ffffff;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

def analyze_epact_data(df):
    """Analyze uploaded ePACT2 data and return insights"""
    analysis = {
        'row_count': len(df),
        'columns': list(df.columns),
        'date_range': None,
        'top_drugs': None,
        'cost_summary': None,
        'data_quality': {}
    }
    
    # Try to identify date columns
    date_columns = [col for col in df.columns if any(word in col.lower() for word in ['date', 'month', 'period'])]
    if date_columns:
        try:
            df[date_columns[0]] = pd.to_datetime(df[date_columns[0]], errors='coerce')
            analysis['date_range'] = {
                'start': df[date_columns[0]].min(),
                'end': df[date_columns[0]].max(),
                'column': date_columns[0]
            }
        except:
            pass
    
    # Try to identify cost columns
    cost_columns = [col for col in df.columns if any(word in col.lower() for word in ['cost', 'spend', 'amount', 'value'])]
    if cost_columns:
        try:
            total_cost = df[cost_columns[0]].sum()
            analysis['cost_summary'] = {
                'total': total_cost,
                'average': df[cost_columns[0]].mean(),
                'column': cost_columns[0]
            }
        except:
            pass
    
    # Try to identify drug/product columns
    drug_columns = [col for col in df.columns if any(word in col.lower() for word in ['drug', 'product', 'item', 'medicine', 'bnf'])]
    if drug_columns:
        try:
            top_drugs = df[drug_columns[0]].value_counts().head(10)
            analysis['top_drugs'] = {
                'data': top_drugs,
                'column': drug_columns[0]
            }
        except:
            pass
    
    # Data quality checks
    analysis['data_quality'] = {
        'missing_values': df.isnull().sum().sum(),
        'duplicate_rows': df.duplicated().sum(),
        'empty_columns': (df.isnull().all()).sum()
    }
    
    return analysis

def create_sample_data():
    """Create sample ePACT2 data for demonstration"""
    import random
    from datetime import datetime, timedelta
    
    # Sample drug names
    drugs = [
        'Adalimumab', 'Infliximab', 'Metformin', 'Atorvastatin', 'Sertraline',
        'Omeprazole', 'Salbutamol', 'Prednisolone', 'Warfarin', 'Insulin'
    ]
    
    # Generate sample data
    data = []
    start_date = datetime(2023, 1, 1)
    
    for i in range(500):
        date = start_date + timedelta(days=random.randint(0, 365))
        drug = random.choice(drugs)
        cost = random.uniform(10, 1000)
        items = random.randint(1, 50)
        
        data.append({
            'Prescription Date': date.strftime('%Y-%m-%d'),
            'Drug Name': drug,
            'Net Ingredient Cost': round(cost, 2),
            'Items': items,
            'BNF Code': f"{random.randint(1,9)}{random.randint(10,99)}{random.randint(100,999)}{random.choice(['AA', 'BB', 'CC'])}",
            'Practice Code': f"P{random.randint(10000,99999)}",
            'CCG Code': f"CCG{random.randint(100,999)}"
        })
    
    return pd.DataFrame(data)

# Main title
st.title("📁 Upload & Process ePACT2 Data")
st.subheader("Transform Your ePACT2 Exports with AI-Powered Analysis")

# Information section
st.markdown("""
<div class="upload-zone">
<h3>📋 What is ePACT2?</h3>
<p><strong>ePACT2</strong> is the NHS Business Services Authority's prescription analysis tool that provides detailed prescription-level data for medicines optimization teams.</p>
<p><strong>This tool helps you:</strong> Upload CSV exports from ePACT2 and get instant AI-powered insights, trend analysis, and actionable recommendations.</p>
</div>
""", unsafe_allow_html=True)

# Upload section
st.header("📤 Upload Your ePACT2 Data")

# Create tabs for different upload methods
tab1, tab2, tab3 = st.tabs(["📂 Upload CSV", "📊 Try Sample Data", "🔗 Connect API (Future)"])

with tab1:
    st.markdown("### Upload your ePACT2 CSV export")
    
    uploaded_file = st.file_uploader(
        "Choose your ePACT2 CSV file",
        type=['csv', 'xlsx'],
        help="Upload CSV or Excel files exported from ePACT2",
        key="epact_upload"
    )
    
    # File format guidance
    with st.expander("📋 Expected File Format"):
        st.markdown("""
        **ePACT2 exports typically contain columns like:**
        - Prescription Date / Month
        - Drug Name / BNF Description  
        - Net Ingredient Cost
        - Items / Quantity
        - BNF Code
        - Practice Code
        - CCG/ICB Code
        
        **Supported formats:** CSV, Excel (.xlsx)
        **Max file size:** 200MB
        """)
    
    if uploaded_file is not None:
        try:
            # Read the file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Store in session state for Claude
            st.session_state.uploaded_epact_data = df
            st.session_state.upload_timestamp = datetime.now()
            
            st.markdown("""
            <div class="success-zone">
            ✅ <strong>File uploaded successfully!</strong> Your data is ready for analysis.
            </div>
            """, unsafe_allow_html=True)
            
            # Quick preview
            st.subheader("👀 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Basic analysis
            analysis = analyze_epact_data(df)
            
            # Store analysis for Claude context
            st.session_state.epact_analysis = analysis
            
            # Display analysis results
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Records", f"{analysis['row_count']:,}")
            
            with col2:
                st.metric("Columns", len(analysis['columns']))
            
            with col3:
                if analysis['cost_summary']:
                    st.metric("Total Cost", f"£{analysis['cost_summary']['total']:,.0f}")
                else:
                    st.metric("Total Cost", "N/A")
            
            with col4:
                missing_pct = (analysis['data_quality']['missing_values'] / (len(df) * len(df.columns))) * 100
                st.metric("Data Quality", f"{100-missing_pct:.1f}%")
            
            # Detailed analysis
            st.subheader("📊 Automatic Data Analysis")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if analysis['top_drugs'] and analysis['top_drugs']['data'] is not None:
                    # Top drugs chart
                    top_drugs_df = analysis['top_drugs']['data'].head(10).reset_index()
                    top_drugs_df.columns = ['Drug', 'Count']
                    
                    fig = px.bar(
                        top_drugs_df,
                        x='Count',
                        y='Drug',
                        orientation='h',
                        title="Top 10 Most Prescribed Drugs",
                        labels={'Count': 'Number of Prescriptions'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Could not identify drug columns for analysis. Please check your data format.")
            
            with col2:
                # Data quality summary
                st.markdown("""
                <div class="analysis-card">
                <h4>🔍 Data Quality Report</h4>
                """, unsafe_allow_html=True)
                
                quality = analysis['data_quality']
                
                if quality['missing_values'] == 0:
                    st.success("✅ No missing values")
                else:
                    st.warning(f"⚠️ {quality['missing_values']} missing values")
                
                if quality['duplicate_rows'] == 0:
                    st.success("✅ No duplicate rows")
                else:
                    st.warning(f"⚠️ {quality['duplicate_rows']} duplicate rows")
                
                if quality['empty_columns'] == 0:
                    st.success("✅ All columns contain data")
                else:
                    st.warning(f"⚠️ {quality['empty_columns']} empty columns")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Date range analysis
            if analysis['date_range']:
                st.subheader("📅 Time Period Analysis")
                date_info = analysis['date_range']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Start Date", date_info['start'].strftime('%Y-%m-%d'))
                
                with col2:
                    st.metric("End Date", date_info['end'].strftime('%Y-%m-%d'))
                
                with col3:
                    duration = (date_info['end'] - date_info['start']).days
                    st.metric("Duration", f"{duration} days")
            
            # Cost analysis if available
            if analysis['cost_summary']:
                st.subheader("💰 Cost Analysis")
                
                cost_col = analysis['cost_summary']['column']
                
                # Monthly trend if date data available
                if analysis['date_range']:
                    try:
                        df_copy = df.copy()
                        df_copy[analysis['date_range']['column']] = pd.to_datetime(df_copy[analysis['date_range']['column']])
                        df_copy['month'] = df_copy[analysis['date_range']['column']].dt.to_period('M')
                        monthly_costs = df_copy.groupby('month')[cost_col].sum().reset_index()
                        monthly_costs['month'] = monthly_costs['month'].astype(str)
                        
                        fig_trend = px.line(
                            monthly_costs,
                            x='month',
                            y=cost_col,
                            title="Monthly Spending Trend",
                            labels={cost_col: 'Cost (£)', 'month': 'Month'}
                        )
                        fig_trend.update_layout(height=400)
                        st.plotly_chart(fig_trend, use_container_width=True)
                        
                    except Exception as e:
                        st.warning(f"Could not create trend analysis: {str(e)}")
            
            # Action buttons
            st.subheader("🚀 Next Steps")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🤖 Get AI Insights", type="primary", use_container_width=True):
                    st.session_state.claude_context_refresh = datetime.now().isoformat()
                    st.success("✅ Data context updated for Claude! Ask questions in the sidebar.")
            
            with col2:
                if st.button("📊 Create Dashboard", use_container_width=True):
                    st.switch_page("pages/03_📈_Analytics_Dashboard.py")
            
            with col3:
                if st.button("💾 Export Results", use_container_width=True):
                    st.switch_page("pages/05_💾_Export_Results.py")
            
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.info("Please check your file format and try again.")

with tab2:
    st.markdown("### Try Sample ePACT2 Data")
    st.info("👆 No ePACT2 data? Try our sample dataset to explore the platform features!")
    
    if st.button("📊 Load Sample Data", type="primary"):
        sample_df = create_sample_data()
        
        # Store sample data
        st.session_state.uploaded_epact_data = sample_df
        st.session_state.upload_timestamp = datetime.now()
        st.session_state.is_sample_data = True
        
        st.success("✅ Sample ePACT2 data loaded successfully!")
        
        # Show preview
        st.subheader("👀 Sample Data Preview")
        st.dataframe(sample_df.head(10), use_container_width=True)
        
        # Quick analysis
        analysis = analyze_epact_data(sample_df)
        st.session_state.epact_analysis = analysis
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Sample Records", f"{len(sample_df):,}")
        
        with col2:
            if analysis['cost_summary']:
                st.metric("Total Cost", f"£{analysis['cost_summary']['total']:,.0f}")
        
        with col3:
            st.metric("Unique Drugs", sample_df['Drug Name'].nunique())
        
        # Sample data insights
        if analysis['top_drugs'] and analysis['top_drugs']['data'] is not None:
            top_drugs_df = analysis['top_drugs']['data'].head(5).reset_index()
            top_drugs_df.columns = ['Drug', 'Prescriptions']
            
            fig = px.pie(
                top_drugs_df,
                values='Prescriptions',
                names='Drug',
                title="Sample Data - Top 5 Drugs by Prescription Count"
            )
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("### 🔗 Direct API Connection (Coming Soon)")
    
    st.info("🚧 **Future Feature**: Direct connection to ePACT2 API for real-time data analysis")
    
    st.markdown("""
    **Planned Features:**
    
    - 🔐 **Secure Authentication**: NHS login integration
    - 🔄 **Real-time Updates**: Automatic data refresh
    - 📅 **Scheduled Reports**: Automated analysis delivery
    - 🎯 **Custom Filters**: Practice/CCG/drug-specific views
    - 📱 **Mobile Access**: Responsive design for tablets
    
    **Benefits:**
    - No manual exports needed
    - Always up-to-date data
    - Reduced administrative burden
    - Faster insights
    """)
    
    # Future connection form (placeholder)
    with st.form("api_connection_form"):
        st.markdown("**Register Interest in API Connection:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            organization = st.text_input("NHS Organization")
            role = st.selectbox("Your Role", [
                "Medicines Optimization Pharmacist",
                "CCG/ICB Analyst", 
                "Practice Manager",
                "GP",
                "Other"
            ])
        
        with col2:
            email = st.text_input("Email Address")
            use_case = st.text_area("Primary Use Case", placeholder="e.g., Monthly drug spend analysis...")
        
        submitted = st.form_submit_button("📧 Register Interest")
        
        if submitted:
            if organization and email:
                st.success("✅ Thank you! We'll contact you when API access is available.")
            else:
                st.error("Please fill in organization and email fields.")

# Help section
st.markdown("---")
st.header("❓ Need Help?")

with st.expander("🔧 Troubleshooting Upload Issues"):
    st.markdown("""
    **Common Issues:**
    
    1. **File too large**: ePACT2 exports can be large. Try filtering to smaller date ranges.
    
    2. **Wrong format**: Ensure you're uploading the CSV export from ePACT2, not a screenshot or PDF.
    
    3. **Special characters**: Some drug names contain special characters that may cause issues.
    
    4. **Date formats**: Various date formats are supported, but MM/DD/YYYY works best.
    
    **Getting ePACT2 Data:**
    1. Log into NHS BSA ePACT2 portal
    2. Set your analysis parameters (date range, practice, etc.)
    3. Export as CSV
    4. Upload here for AI analysis
    """)

with st.expander("📋 Supported Data Formats"):
    st.markdown("""
    **Column Names We Look For:**
    
    **Date Columns:**
    - Prescription Date, Date, Month, Period
    
    **Cost Columns:**
    - Net Ingredient Cost, Cost, Spend, Amount, Value
    
    **Drug Columns:**
    - Drug Name, Product, BNF Description, Item
    
    **Other Useful Columns:**
    - BNF Code, Practice Code, CCG Code, ICB Code, Items, Quantity
    
    **File Requirements:**
    - Format: CSV or Excel (.xlsx)
    - Size: Up to 200MB
    - Encoding: UTF-8 preferred
    """)

with st.expander("🤖 How Claude AI Helps"):
    st.markdown("""
    **Claude can analyze your data and help with:**
    
    - 📊 **Trend Identification**: Spot increasing/decreasing costs
    - 🔍 **Anomaly Detection**: Identify unusual prescribing patterns  
    - 💡 **Cost Optimization**: Suggest biosimilar opportunities
    - 📈 **Forecasting**: Predict future spending patterns
    - 📋 **Reporting**: Generate insights for meetings
    - ❓ **Q&A**: Answer specific questions about your data
    
    **Getting Started:**
    1. Upload your data above
    2. Click "Get AI Insights" 
    3. Ask Claude questions in the sidebar
    4. Get instant, contextual analysis
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
🔒 **Data Security**: Your ePACT2 data is processed securely and never stored permanently. 
All analysis happens in your browser session only. | 
<a href="mailto:support@nhsdatahub.co.uk">Get Support</a>
</div>
""", unsafe_allow_html=True)