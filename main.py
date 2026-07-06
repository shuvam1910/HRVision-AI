import streamlit as st

# MUST be the first Streamlit command
st.set_page_config(
    page_title="HRVision AI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

from streamlit_option_menu import option_menu
from app.utils import inject_custom_css
from app.auth import check_login, logout
from app.views.dashboard import render_dashboard_page
from app.views.employees import render_employees_page
from app.views.prediction import render_prediction_page
from app.views.explainability import render_explainability_page
from app.views.chatbot_view import render_chatbot_page
from app.views.reports_view import render_reports_page

def main():
    # Inject Custom CSS styles
    inject_custom_css()
    
    # Check authentication status
    if not check_login():
        return
        
    # Sidebar Shell Design
    # Sidebar Shell Design
    st.sidebar.markdown(f"""
    <div style="border:1px solid rgba(128,128,128,0.25); padding:16px; border-radius:12px; margin-bottom:15px; text-align:center;">
        <span style="font-size:2.0rem;">🔮</span>
        <h4 style="margin:8px 0 2px 0; font-weight: 800; color: var(--text-color);">HR Analytics</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Active User details
    role_color = "#ef4444" if st.session_state.user_role == "Admin" else "#3b82f6"
    st.sidebar.markdown(f"""
    <div style="border: 1px solid rgba(128, 128, 128, 0.25); padding: 14px; border-radius: 10px; margin-bottom: 20px; font-size: 1.0rem; color: var(--text-color);">
        <span style="font-weight: 700; color: var(--text-color); opacity: 0.9;">User:</span> <strong style="font-weight: 800; color: var(--text-color);">{st.session_state.user_name}</strong><br/>
        <span style="font-weight: 700; color: var(--text-color); opacity: 0.9;">Role:</span> <span style="color:{role_color}; font-weight: 800;">{st.session_state.user_role}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Platform Header
    st.markdown('<div class="gradient-header" style="font-size: 2.2rem; margin-top: 10px; margin-bottom: 0px;">Enterprise HR Analytics & Employee Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 1.05rem; font-weight: 700; color: var(--text-color); opacity: 0.7; margin-bottom: 20px; letter-spacing: 0.08em; text-transform: uppercase;">Predict &bull; Analyze &bull; Retain</div>', unsafe_allow_html=True)
    
    # Build Menu Navigation
    menu_options = ["Overview", "Employee Directory", "Predictive Portal", "SHAP Explainability", "AI Copilot Chat", "Executive Reports"]
    menu_icons = ["bar-chart-fill", "people-fill", "cpu-fill", "eye-fill", "chat-square-dots-fill", "download"]
        
    selected_page = option_menu(
        menu_title="Navigation",
        options=menu_options,
        icons=menu_icons,
        menu_icon="compass",
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding": "5px", "background-color": "rgba(0,0,0,0)"},
            "icon": {"color": "#6366f1", "font-size": "1.1rem"},
            "nav-link": {"font-size": "0.95rem", "text-align": "left", "margin": "0px", "--hover-color": "rgba(255, 255, 255, 0.05)"},
            "nav-link-selected": {"background-color": "#4f46e5", "font-weight": "600"},
        }
    )
    
    # Logout action
    st.sidebar.write("")
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        logout()

    # Page Router
    if selected_page == "Overview":
        render_dashboard_page()
    elif selected_page == "Employee Directory":
        render_employees_page()
    elif selected_page == "Predictive Portal":
        render_prediction_page()
    elif selected_page == "SHAP Explainability":
        render_explainability_page()
    elif selected_page == "AI Copilot Chat":
        render_chatbot_page()
    elif selected_page == "Executive Reports":
        render_reports_page()

if __name__ == "__main__":
    main()
