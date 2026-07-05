import streamlit as st
from app.chatbot import HRCopilot
from app.database import DatabaseManager

db_mgr = DatabaseManager()

def render_chatbot_page():
    st.markdown('<div class="gradient-header">AI HR Copilot Assistant</div>', unsafe_allow_html=True)
    st.caption("Ask questions about attrition metrics, department stats, individual employees, or retention plans")
    
    # Initialize chatbot engine
    if "copilot_engine" not in st.session_state:
        st.session_state.copilot_engine = HRCopilot()
        
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! I am your AI HR Analytics Copilot. You can ask me questions about company attrition, average department income, employee risk audits (e.g. 'Is employee 1005 at risk?'), or strategies to improve retention. How can I assist you today?"}
        ]
        
    # Sidebar quick query tips
    st.sidebar.markdown("### 💡 Quick Queries")
    st.sidebar.caption("Click any query below to run it instantly:")
    
    queries = [
        "What is the overall attrition rate?",
        "Show me top features",
        "Is employee 1015 at risk?",
        "What is the average salary in Sales?",
        "How do we reduce attrition?"
    ]
    
    clicked_query = None
    for q in queries:
        if st.sidebar.button(f"💬 {q}", use_container_width=True, key=f"q_{q.replace(' ', '_').replace('?', '')}"):
            clicked_query = q
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)
            
    # User Input
    user_query = st.chat_input("Type your question here...")
    
    query_to_process = None
    if clicked_query:
        query_to_process = clicked_query
    elif user_query:
        query_to_process = user_query
        
    if query_to_process:
        # Display user message
        st.session_state.chat_history.append({"role": "user", "content": query_to_process})
        
        # Log chatbot activity
        db_mgr.log_activity(st.session_state.username, "Chatbot Query", f"Query: {query_to_process}")
        
        # Get response
        with st.spinner("Analyzing HR database..."):
            response = st.session_state.copilot_engine.parse_query(query_to_process)
            
        # Display assistant response
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Rerun to keep scroll in place
        st.rerun()
        
    # Clear chat button
    if len(st.session_state.chat_history) > 1:
        st.write("")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Hello! I am your AI HR Analytics Copilot. You can ask me questions about company attrition, average department income, employee risk audits (e.g. 'Is employee 1005 at risk?'), or strategies to improve retention. How can I assist you today?"}
            ]
            st.rerun()
