import streamlit as st
from app.database import DatabaseManager

# Initialize Database Manager
db_mgr = DatabaseManager()

def init_session():
    """Initializes standard session variables if they are not already set."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "db_status" not in st.session_state:
        st.session_state.db_status = db_mgr.get_status()
    if "notifications_count" not in st.session_state:
        st.session_state.notifications_count = len(db_mgr.get_notifications(unread_only=True))

def render_login_form():
    """Renders the login interface with glassmorphism layout."""
    st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
    st.subheader("Welcome Back")
    st.markdown('<div style="font-size: 1.05rem; font-weight: 600; color: var(--text-color); opacity: 0.85; margin-bottom: 20px; line-height: 1.4;">Sign in to access intelligent workforce analytics, employee insights, and predictive HR tools.</div>', unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username (Email)", placeholder="e.g. user@hr.com", key="login_user")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="login_pass")
        submit_clicked = st.form_submit_button("Log In", use_container_width=True, type="primary")
        
    if submit_clicked:
        if not username or not password:
            st.error("Please fill in all fields")
        else:
            user = db_mgr.verify_user(username, password)
            if user:
                if not user.get("approved", False):
                    st.warning("Your account is pending approval. Please contact your administrator.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]
                    st.session_state.user_role = user["role"]
                    st.session_state.user_name = user["name"]
                    db_mgr.log_activity(user["username"], "Login", f"User logged in with role: {user['role']}")
                    st.success(f"Welcome back, {user['name']}!")
                    st.rerun()
            else:
                st.error("Invalid username or password")
                    
    if st.button("Need Account? Register", use_container_width=True):
        st.session_state.auth_mode = "register"
        st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)

def render_registration_form():
    """Renders the sign-up page."""
    st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
    st.subheader("Request Account Access")
    st.caption("Create a new user account to access the platform.")
    
    with st.form("registration_form", clear_on_submit=False):
        fullname = st.text_input("Full Name", placeholder="e.g. Jane Doe", key="reg_name")
        email = st.text_input("Email (will be username)", placeholder="e.g. jane.doe@company.com", key="reg_email")
        password = st.text_input("Password", type="password", placeholder="Minimum 6 characters", key="reg_pass")
        role = st.selectbox(
            "Access Role",
            options=["User", "Admin"],
            help="Select the access level appropriate for your position."
        )
        submit_clicked = st.form_submit_button("Submit Registration", use_container_width=True, type="primary")
        
    if submit_clicked:
        if not fullname or not email or not password:
            st.error("Please fill in all fields")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters")
        elif "@" not in email:
            st.error("Please enter a valid email address")
        elif db_mgr.find_user(email):
            st.error("An account with this email already exists")
        else:
            # Auto-approve set to True
            db_mgr.create_user(
                username=email,
                password=password,
                name=fullname,
                role=role,
                approved=True
            )
            db_mgr.log_activity("System", "Registration Completed", f"New user {email} created with {role} role")
            db_mgr.create_notification(
                title="New Registration",
                message=f"{fullname} ({email}) registered as {role}",
                severity="info"
            )
            st.success("Account created successfully! You can now log in immediately.")
                
    if st.button("Back to Login", use_container_width=True):
        st.session_state.auth_mode = "login"
        st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)

def check_login():
    """Gatekeeper function. If user is not logged in, locks down views and displays auth card."""
    init_session()
    
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
        
    # Auto-login check if cookie is present and logout wasn't triggered in this session
    if not st.session_state.logged_in:
        cookie_username = st.context.cookies.get("hrvision_username")
        if cookie_username and not st.session_state.get("logged_out_this_session", False):
            user = db_mgr.find_user(cookie_username)
            if user and user.get("approved", False):
                st.session_state.logged_in = True
                st.session_state.username = user["username"]
                st.session_state.user_role = user["role"]
                st.session_state.user_name = user["name"]
                db_mgr.log_activity(user["username"], "Auto-Login", "User auto-logged in via persistent cookie")
                st.rerun()
        
    if not st.session_state.logged_in:
        # Clear browser cookie if we logged out this session
        if st.context.cookies.get("hrvision_username"):
            st.components.v1.html(
                """
                <script>
                    parent.document.cookie = "hrvision_username=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; SameSite=Lax";
                </script>
                """,
                height=0,
                width=0
            )

        st.markdown('<div class="gradient-header" style="font-size: 3rem; margin-top: 20px; margin-bottom: 5px;">HRVision AI</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 1.35rem; font-weight: 750; color: var(--text-color); margin-bottom: 5px;">Enterprise HR Analytics & Employee Intelligence Platform</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 1.05rem; font-weight: 800; color: var(--text-color); opacity: 0.7; margin-bottom: 25px; letter-spacing: 0.1em; text-transform: uppercase;">Predict &bull; Analyze &bull; Retain</div>', unsafe_allow_html=True)
        
        # Database Status Diagnostics (Only warn if it is local JSON fallback)
        db_status = st.session_state.get("db_status", "Local JSON Fallback")
        if db_status == "Local JSON Fallback":
            st.warning(
                "⚠️ **Database Warning: Local JSON Fallback Active**\n\n"
                "The application is not connected to MongoDB. Any new accounts registered here are temporary and will be lost when Render restarts the service. "
                "To connect persistently, please:\n"
                "1. Add the `MONGODB_URI` environment variable under **Environment Variables** in your Render dashboard.\n"
                "2. Set MongoDB Atlas Network Access to allow access from **0.0.0.0/0** (anywhere)."
            )

        if st.session_state.auth_mode == "login":
            render_login_form()
        else:
            render_registration_form()
            
        return False
        
    # If logged in and cookie is not set in browser, set it
    if st.session_state.logged_in and not st.context.cookies.get("hrvision_username"):
        st.components.v1.html(
            f"""
            <script>
                parent.document.cookie = "hrvision_username={st.session_state.username}; path=/; max-age=604800; SameSite=Lax";
            </script>
            """,
            height=0,
            width=0
        )
        
    return True

def logout():
    """Logs the user out and clears session states."""
    if st.session_state.username:
        db_mgr.log_activity(st.session_state.username, "Logout", "User logged out")
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.logged_out_this_session = True
    st.rerun()
