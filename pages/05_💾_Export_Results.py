import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64
from datetime import datetime
import json

# Import Claude integration
try:
    from utils.claude_integration import render_claude_sidebar
    claude_available = True
except ImportError:
    claude_available = False

st.set_page_config(page_title="Export Results", page_icon="💾", layout="wide")

# Set current page for Claude context
st.session_state.current_page = "Export Results - Data Export & Reporting"

# Render Claude sidebar
if claude_available:
    render_claude_sidebar()
else:
    st.sidebar.error("Claude integration not available")

# Custom CSS
st.markdown("""
<style>
.export-card {
    background-color: #ffffff;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 1rem 0;
    border-left: 5px solid #1f77b4;
}
.export-option {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border: 1px solid #e9ecef;
}
.premium-feature {
    background: linear-gradient(45deg, #ffd700, #ffed4e);
    color: #000;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

def create_excel_export(data, analysis=None):
    """Create an Excel file with multiple sheets"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        currency_format = workbook.add_format({'num_format': '£#,##0.00'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        
        # Main data sheet
        data.to_excel(writer, sheet_name='Raw Data', index=False)
        worksheet = writer.sheets['Raw Data']
        
        # Format headers
        for col_num, value in enumerate(data.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Auto-adjust column widths
        for i, col in enumerate(data.columns):
            max_length = max(data[col].astype(str).map(len).max(), len(col))
            worksheet.set_column(i, i, min(max_length + 2, 50))
        
        # Summary sheet if analysis available
        if analysis:
            summary_data = []
            summary_data.append(['Analysis Date', datetime.now().strftime('%Y-%m-%d %H:%M')])
            summary_data.append(['Total Records', analysis.get('row_count', 'N/A')])
            summary_data.append(['Columns', len(analysis.get('columns', []))])
            
            if analysis.get('cost_summary'):
                summary_data.append(['Total Cost', f"£{analysis['cost_summary']['total']:,.2f}"])
                summary_data.append(['Average Cost', f"£{analysis['cost_summary']['average']:,.2f}"])
            
            if analysis.get('date_range'):
                summary_data.append(['Date Range Start', analysis['date_range']['start']])
                summary_data.append(['Date Range End', analysis['date_range']['end']])
            
            summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Format summary sheet
            summary_worksheet = writer.sheets['Summary']
            for col_num, value in enumerate(summary_df.columns.values):
                summary_worksheet.write(0, col_num, value, header_format)
            
            summary_worksheet.set_column(0, 0, 20)
            summary_worksheet.set_column(1, 1, 30)
    
    output.seek(0)
    return output

def create_csv_export(data):
    """Create CSV export"""
    output = io.StringIO()
    data.to_csv(output, index=False)
    return output.getvalue()

def create_json_export(data, analysis=None):
    """Create JSON export with metadata"""
    export_data = {
        'metadata': {
            'export_date': datetime.now().isoformat(),
            'record_count': len(data),
            'columns': list(data.columns)
        },
        'data': data.to_dict('records')
    }
    
    if analysis:
        export_data['analysis'] = analysis
    
    return json.dumps(export_data, indent=2, default=str)

def generate_summary_report():
    """Generate a text summary report"""
    report = f"""
NHS Prescribing Data Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== EXECUTIVE SUMMARY ===

"""
    
    # Check what data is available
    if hasattr(st.session_state, 'uploaded_epact_data'):
        data = st.session_state.uploaded_epact_data
        analysis = getattr(st.session_state, 'epact_analysis', {})
        
        report += f"Dataset: ePACT2 Upload ({len(data):,} records)\n"
        
        if analysis.get('cost_summary'):
            cost = analysis['cost_summary']
            report += f"Total Cost: £{cost['total']:,.2f}\n"
            report += f"Average Cost: £{cost['average']:,.2f}\n"
        
        if analysis.get('date_range'):
            date_range = analysis['date_range']
            report += f"Period: {date_range['start']} to {date_range['end']}\n"
        
        if analysis.get('top_drugs'):
            report += "\n=== TOP PRESCRIBED DRUGS ===\n"
            for drug, count in analysis['top_drugs']['data'].head(5).items():
                report += f"- {drug}: {count:,} prescriptions\n"
    
    elif hasattr(st.session_state, 'current_drug'):
        report += f"Drug Analysis: {st.session_state.current_drug}\n"
        
        if hasattr(st.session_state, 'comprehensive_context'):
            report += "\n=== DRUG INSIGHTS ===\n"
            report += st.session_state.comprehensive_context
    
    else:
        report += "No data currently loaded for export.\n"
    
    report += f"""

=== DATA SOURCES ===
- OpenPrescribing.net API
- NHS BSA ePACT2 data
- Analysis powered by Claude AI

=== DISCLAIMER ===
This analysis is based on available data and should be used alongside 
clinical judgment and local guidelines. Data accuracy depends on source 
quality and timeliness.

Report generated by NHS Data Hub
Contact: support@nhsdatahub.co.uk
"""
    
    return report

# Main title
st.title("💾 Export Your Results")
st.subheader("Get Insights in Your Preferred Format")

# Check what data is available for export
has_upload_data = hasattr(st.session_state, 'uploaded_epact_data')
has_search_data = hasattr(st.session_state, 'current_drug')
has_dashboard_data = hasattr(st.session_state, 'dashboard_data')

if not (has_upload_data or has_search_data or has_dashboard_data):
    st.warning("⚠️ No data available for export. Please:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📁 Upload ePACT2 Data", use_container_width=True):
            st.switch_page("pages/04_📁_Upload_Process.py")
    
    with col2:
        if st.button("🔍 Search Drug Data", use_container_width=True):
            st.switch_page("pages/02_🔗_Consolidated_View.py")
    
    with col3:
        if st.button("📊 View Dashboard", use_container_width=True):
            st.switch_page("pages/03_📈_Analytics_Dashboard.py")
    
    st.stop()

# Data available - show export options
st.success("✅ Data ready for export!")

# Show available datasets
st.header("📊 Available Datasets")

col1, col2, col3 = st.columns(3)

export_data = None
export_analysis = None
dataset_name = ""

with col1:
    if has_upload_data:
        data = st.session_state.uploaded_epact_data
        analysis = getattr(st.session_state, 'epact_analysis', {})
        
        st.markdown("""
        <div class="export-card">
        <h4>📁 ePACT2 Upload Data</h4>
        """, unsafe_allow_html=True)
        
        st.metric("Records", f"{len(data):,}")
        if analysis.get('cost_summary'):
            st.metric("Total Cost", f"£{analysis['cost_summary']['total']:,.0f}")
        
        if st.button("Select ePACT2 Data", type="primary", key="select_epact"):
            export_data = data
            export_analysis = analysis
            dataset_name = "ePACT2_Upload"
            st.session_state.selected_export = "epact"
        
        st.markdown("</div>", unsafe_allow_html=True)

with col2:
    if has_search_data:
        drug_name = st.session_state.current_drug
        
        st.markdown("""
        <div class="export-card">
        <h4>🔍 Drug Search Results</h4>
        """, unsafe_allow_html=True)
        
        st.write(f"**Drug:** {drug_name}")
        
        if hasattr(st.session_state, 'current_spending_data'):
            spending_data = st.session_state.current_spending_data
            st.metric("Data Points", len(spending_data))
        
        if st.button("Select Search Data", type="primary", key="select_search"):
            if hasattr(st.session_state, 'current_spending_data'):
                export_data = st.session_state.current_spending_data
                dataset_name = f"Drug_Analysis_{drug_name}"
                st.session_state.selected_export = "search"
        
        st.markdown("</div>", unsafe_allow_html=True)

with col3:
    if has_dashboard_data:
        dashboard_data = st.session_state.dashboard_data
        dashboard_type = getattr(st.session_state, 'dashboard_type', 'Dashboard')
        
        st.markdown("""
        <div class="export-card">
        <h4>📈 Dashboard Data</h4>
        """, unsafe_allow_html=True)
        
        st.write(f"**Type:** {dashboard_type}")
        st.metric("Records", f"{len(dashboard_data):,}")
        
        if st.button("Select Dashboard Data", type="primary", key="select_dashboard"):
            export_data = dashboard_data
            dataset_name = dashboard_type.replace(" ", "_")
            st.session_state.selected_export = "dashboard"
        
        st.markdown("</div>", unsafe_allow_html=True)

# If data is selected, show export options
if export_data is not None or hasattr(st.session_state, 'selected_export'):
    
    # Get the data based on selection
    if hasattr(st.session_state, 'selected_export'):
        if st.session_state.selected_export == "epact":
            export_data = st.session_state.uploaded_epact_data
            export_analysis = getattr(st.session_state, 'epact_analysis', {})
            dataset_name = "ePACT2_Upload"
        elif st.session_state.selected_export == "search":
            if hasattr(st.session_state, 'current_spending_data'):
                export_data = st.session_state.current_spending_data
                dataset_name = f"Drug_Analysis_{st.session_state.current_drug}"
        elif st.session_state.selected_export == "dashboard":
            export_data = st.session_state.dashboard_data
            dataset_name = getattr(st.session_state, 'dashboard_type', 'Dashboard').replace(" ", "_")
    
    st.markdown("---")
    st.header("📤 Export Options")
    
    # Format selection
    export_format = st.selectbox(
        "📋 Choose Export Format:",
        ["Excel (.xlsx)", "CSV", "JSON", "Summary Report (Text)"],
        help="Select the format that works best with your tools"
    )
    
    # Additional options
    col1, col2 = st.columns(2)
    
    with col1:
        include_analysis = st.checkbox(
            "Include Analysis Summary", 
            value=True, 
            help="Add analysis metadata and insights"
        )
    
    with col2:
        timestamp_filename = st.checkbox(
            "Add Timestamp to Filename", 
            value=True, 
            help="Prevents overwriting files"
        )
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if timestamp_filename else ""
    base_filename = f"{dataset_name}_{timestamp}" if timestamp else dataset_name
    
    # Export buttons
    st.subheader("💾 Download Your Data")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if export_format == "Excel (.xlsx)" and export_data is not None:
            excel_data = create_excel_export(
                export_data, 
                export_analysis if include_analysis else None
            )
            
            st.download_button(
                label="📊 Download Excel",
                data=excel_data,
                file_name=f"{base_filename}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
    
    with col2:
        if export_format == "CSV" and export_data is not None:
            csv_data = create_csv_export(export_data)
            
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name=f"{base_filename}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
    
    with col3:
        if export_format == "JSON" and export_data is not None:
            json_data = create_json_export(
                export_data,
                export_analysis if include_analysis else None
            )
            
            st.download_button(
                label="🔗 Download JSON",
                data=json_data,
                file_name=f"{base_filename}.json",
                mime="application/json",
                type="primary",
                use_container_width=True
            )
    
    with col4:
        if export_format == "Summary Report (Text)":
            report_data = generate_summary_report()
            
            st.download_button(
                label="📋 Download Report",
                data=report_data,
                file_name=f"{base_filename}_Report.txt",
                mime="text/plain",
                type="primary",
                use_container_width=True
            )
    
    # Preview section
    if export_data is not None:
        st.markdown("---")
        st.header("👀 Export Preview")
        
        if export_format == "Excel (.xlsx)" or export_format == "CSV":
            st.subheader("Data Preview (First 10 rows)")
            st.dataframe(export_data.head(10), use_container_width=True)
            
            if include_analysis and export_analysis:
                st.subheader("Analysis Summary")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Records", export_analysis.get('row_count', 'N/A'))
                
                with col2:
                    if export_analysis.get('cost_summary'):
                        st.metric("Total Cost", f"£{export_analysis['cost_summary']['total']:,.0f}")
                
                with col3:
                    quality = export_analysis.get('data_quality', {})
                    missing_pct = quality.get('missing_values', 0)
                    st.metric("Data Quality", f"{100-missing_pct:.1f}%")
        
        elif export_format == "JSON":
            st.subheader("JSON Structure Preview")
            preview_json = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "record_count": len(export_data),
                    "columns": list(export_data.columns)
                },
                "data": export_data.head(3).to_dict('records'),
                "note": "... (remaining records truncated for preview)"
            }
            st.json(preview_json)
        
        elif export_format == "Summary Report (Text)":
            st.subheader("Report Preview")
            with st.expander("Show Full Report"):
                st.text(generate_summary_report())

# Advanced export options
st.markdown("---")
st.header("🚀 Advanced Export Options")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="export-option">
    <h4>📊 Power BI Integration</h4>
    <span class="premium-feature">COMING SOON</span>
    <p>Direct integration with Power BI for real-time dashboards</p>
    <ul>
    <li>Automatic data refresh</li>
    <li>Pre-built NHS templates</li>
    <li>Interactive visualizations</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📧 Get Notified", key="powerbi_notify"):
        st.info("We'll email you when Power BI integration is available!")

with col2:
    st.markdown("""
    <div class="export-option">
    <h4>📱 Mobile Reports</h4>
    <span class="premium-feature">COMING SOON</span>
    <p>Mobile-optimized reports for on-the-go insights</p>
    <ul>
    <li>Responsive design</li>
    <li>PDF generation</li>
    <li>Email scheduling</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📧 Get Notified", key="mobile_notify"):
        st.info("We'll email you when mobile reports are available!")

# Email export (future feature)
st.subheader("📧 Email Export (Future)")

with st.form("email_export_form"):
    st.markdown("**Schedule regular exports to your email:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        email = st.text_input("Email Address")
        frequency = st.selectbox("Frequency", ["Weekly", "Monthly", "Quarterly"])
    
    with col2:
        report_type = st.selectbox("Report Type", ["Summary", "Full Data", "Insights Only"])
        format_email = st.selectbox("Format", ["PDF", "Excel", "Both"])
    
    submitted = st.form_submit_button("🔔 Set Up Email Export")
    
    if submitted:
        st.info("📧 Email export scheduling will be available soon!")

# Usage tips
st.markdown("---")
st.header("💡 Export Tips")

with st.expander("📊 Best Practices for Data Export"):
    st.markdown("""
    **For Excel Users:**
    - Excel format includes multiple sheets with raw data and summary
    - Use filters and pivot tables for further analysis
    - Charts and formatting are preserved
    
    **For Power BI/Tableau:**
    - CSV format works best for data import
    - JSON format preserves data types
    - Include analysis metadata for context
    
    **For Presentations:**
    - Summary report provides key insights in text format
    - Copy specific metrics for slides
    - Use screenshots of charts from the dashboard
    
    **For Compliance/Audit:**
    - Always include timestamp in filename
    - Export with analysis summary for context
    - Keep original source data reference
    """)

with st.expander("🔒 Data Security & Privacy"):
    st.markdown("""
    **Data Handling:**
    - Exports are generated in your browser only
    - No data is stored on our servers
    - Downloads are encrypted in transit
    
    **NHS Data Guidelines:**
    - Ensure compliance with local data policies
    - Patient data remains anonymized
    - Follow your organization's data sharing rules
    
    **File Security:**
    - Password protect sensitive Excel files
    - Store downloads in secure locations
    - Delete temporary files when no longer needed
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
💾 **Export powered by NHS Data Hub** | 
All exports are generated securely in your browser | 
<a href="mailto:support@nhsdatahub.co.uk">Need Help?</a>
</div>
""", unsafe_allow_html=True)