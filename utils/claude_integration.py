import streamlit as st
import pandas as pd
from anthropic import Anthropic
import json
from datetime import datetime

def initialize_claude():
    """Initialize Claude client"""
    try:
        # You'll need to add your Anthropic API key to Streamlit secrets
        api_key = st.secrets.get("ANTHROPIC_API_KEY", None)
        if not api_key:
            st.sidebar.error("⚠️ Anthropic API key not found. Add it to Streamlit secrets.")
            return None
        return Anthropic(api_key=api_key)
    except Exception as e:
        st.sidebar.error(f"Error initializing Claude: {str(e)}")
        return None

def get_page_context():
    """Get current page context for Claude"""
    context = {
        "timestamp": datetime.now().isoformat(),
        "page": "Unknown",
        "data_displayed": "None",
        "charts_visible": [],
        "user_selections": {},
        "current_data_summary": "No data visible"
    }
    
    # Get current page from URL or session state
    try:
        # Streamlit doesn't directly expose current page, so we'll use session state
        if hasattr(st.session_state, 'current_page'):
            context["page"] = st.session_state.current_page
        
        # Get any data currently being displayed
        if hasattr(st.session_state, 'current_drug'):
            context["user_selections"]["drug"] = st.session_state.current_drug
            context["current_data_summary"] = f"User is viewing data for {st.session_state.current_drug}"
            
        if hasattr(st.session_state, 'search_performed') and st.session_state.search_performed:
            context["user_selections"]["search_performed"] = True
            context["current_data_summary"] += f" - Search was performed"
            
        # Look for comprehensive analysis data
        if hasattr(st.session_state, 'comprehensive_context'):
            context["comprehensive_analysis"] = st.session_state.comprehensive_context
            context["current_data_summary"] = "Comprehensive drug analysis with 3-year trends, regional benchmarking, and seasonal patterns available"
            
        # Add any dataframes in session state
        data_summary = []
        for key, value in st.session_state.items():
            if isinstance(value, pd.DataFrame) and not value.empty:
                # Get basic stats from dataframe
                summary = {
                    "name": key,
                    "shape": value.shape,
                    "columns": list(value.columns) if len(value.columns) < 10 else list(value.columns[:10]) + ["..."]
                }
                
                # Add sample data for context
                if 'actual_cost' in value.columns:
                    summary["latest_cost"] = f"£{value['actual_cost'].iloc[-1]:,.0f}" if not value.empty else "N/A"
                if 'items' in value.columns:
                    summary["latest_items"] = f"{value['items'].iloc[-1]:,.0f}" if not value.empty else "N/A"
                if 'date' in value.columns:
                    summary["date_range"] = f"{value['date'].min()} to {value['date'].max()}" if not value.empty else "N/A"
                
                data_summary.append(summary)
        
        if data_summary:
            context["data_displayed"] = data_summary
            context["current_data_summary"] = f"Data visible: {len(data_summary)} datasets loaded"
            
    except Exception as e:
        context["error"] = f"Error getting context: {str(e)}"
    
    return context

def create_system_prompt():
    """Create system prompt for NHS data analysis"""
    return """You are Claude, an AI assistant specialized in NHS data analysis and pharmacy insights. You are integrated into the NHS Data Hub application and can see the current page content and data.

Key capabilities:
- Analyze NHS prescribing data from OpenPrescribing API
- Interpret BNF codes and drug classifications  
- Explain spending trends and regional variations
- Provide insights on biosimilar adoption and cost savings
- Help with medicines optimization strategies
- Generate actionable recommendations for NHS pharmacy teams

Context awareness:
- You can see what page the user is currently viewing
- You have access to any data currently displayed on screen
- You remember the conversation history within this session
- You understand NHS terminology, ICB structures, and pharmacy workflows

Communication style:
- Professional but friendly, suitable for NHS healthcare professionals
- Use NHS terminology correctly (ICB, CCG, QIPP, etc.)
- Provide specific, actionable insights rather than generic responses
- Reference the actual data when providing analysis
- Offer practical next steps and recommendations

Always start responses by acknowledging what you can see on the current page, then provide relevant analysis or answers."""

def get_chat_history():
    """Get chat history from session state"""
    if "claude_chat_history" not in st.session_state:
        st.session_state.claude_chat_history = []
    return st.session_state.claude_chat_history

def add_to_chat_history(user_message, claude_response):
    """Add message pair to chat history"""
    if "claude_chat_history" not in st.session_state:
        st.session_state.claude_chat_history = []
    
    st.session_state.claude_chat_history.append({
        "timestamp": datetime.now().isoformat(),
        "user": user_message,
        "claude": claude_response,
        "context": get_page_context()
    })
    
    # Keep only last 10 exchanges to manage memory
    if len(st.session_state.claude_chat_history) > 10:
        st.session_state.claude_chat_history = st.session_state.claude_chat_history[-10:]

def query_claude(client, user_message):
    """Send query to Claude with context"""
    if not client:
        return "⚠️ Claude is not available. Please check your API key configuration."
    
    try:
        # Get current context
        context = get_page_context()
        chat_history = get_chat_history()
        
        # Build context message
        context_str = f"""
Current Page Context:
- Page: {context.get('page', 'Unknown')}
- User Selections: {json.dumps(context.get('user_selections', {}), indent=2)}
- Data Displayed: {json.dumps(context.get('data_displayed', 'None'), indent=2)}

Recent Chat History:
{json.dumps(chat_history[-3:], indent=2) if chat_history else 'No previous conversation'}
"""

        # Create messages for Claude
        messages = [
            {
                "role": "user",
                "content": f"""Page Context: {context_str}

User Question: {user_message}

Please provide a helpful response based on the current page context and any data you can see."""
            }
        ]
        
        # Call Claude
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.3,
            system=create_system_prompt(),
            messages=messages
        )
        
        claude_response = response.content[0].text
        
        # Add to chat history
        add_to_chat_history(user_message, claude_response)
        
        return claude_response
        
    except Exception as e:
        return f"❌ Error querying Claude: {str(e)}"

def render_claude_sidebar():
    """Render the Claude sidebar interface"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🤖 Claude Assistant")
        st.caption("Ask me about any data on screen")
        
        # Initialize Claude if not already done
        if "claude_client" not in st.session_state:
            st.session_state.claude_client = initialize_claude()
        
        # Chat interface
        user_input = st.text_input(
            "Ask Claude...",
            placeholder="e.g., Why is spending increasing?",
            key="claude_input"
        )
        
        # Send button
        if st.button("💬 Send", key="claude_send") and user_input:
            with st.spinner("🤔 Claude is thinking..."):
                response = query_claude(st.session_state.claude_client, user_input)
                st.session_state.claude_latest_response = response
        
        # Display latest response
        if hasattr(st.session_state, 'claude_latest_response'):
            st.markdown("#### 🤖 Claude's Response:")
            st.markdown(st.session_state.claude_latest_response)
        
        # Chat history expander
        chat_history = get_chat_history()
        if chat_history:
            with st.expander(f"💬 Chat History ({len(chat_history)} messages)"):
                for i, exchange in enumerate(reversed(chat_history[-5:])):  # Show last 5
                    st.markdown(f"**You:** {exchange['user']}")
                    st.markdown(f"**Claude:** {exchange['claude'][:200]}...")
                    st.markdown("---")
        
        # Quick context info
        with st.expander("🔍 What Claude Can See"):
            context = get_page_context()
            st.json(context)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", key="clear_claude_chat"):
            st.session_state.claude_chat_history = []
            if hasattr(st.session_state, 'claude_latest_response'):
                del st.session_state.claude_latest_response
            st.rerun()