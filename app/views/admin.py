import streamlit as st
import pandas as pd
from app.utils import restrict_view_access
from app.database import DatabaseManager

db_mgr = DatabaseManager()

def render_admin_page():
    # Enforce Admin-only access
    if not restrict_view_access(["Admin"]):
        return
        
    st.markdown('<div class="gradient-header">Admin Control Center</div>', unsafe_allow_html=True)
    st.caption("Manage user access approvals, audit activity logs, and configure system connections")
    
    # Grid summary cards
    users = db_mgr.get_all_users()
    logs = db_mgr.get_logs(limit=100)
    db_status = db_mgr.get_status()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Database Backend", db_status)
    with col2:
        st.metric("Total Registered Users", len(users))
    with col3:
        st.metric("Audited Logs Captured", len(logs))
        
    st.write("")
    
    tab_users, tab_logs = st.tabs(["👥 User Approvals & Roles", "📋 System Activity Logs"])
    
    with tab_users:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### User Roster and Approvals")
        st.caption("Grant application access and assign execution privileges to employees.")
        
        # Format into a clean table
        users_data = []
        for u in users:
            users_data.append({
                "Username": u["username"],
                "Full Name": u["name"],
                "Assigned Role": u["role"],
                "Access Status": "Approved" if u.get("approved", False) else "Pending Approval",
                "Created At": u.get("created_at", "N/A")[:16].replace("T", " ")
            })
        
        df_users = pd.DataFrame(users_data)
        st.dataframe(df_users, use_container_width=True, hide_index=True)
        
        # User Action Form
        st.markdown("---")
        st.markdown("#### Modify User Status")
        
        # Selector for target user
        user_list = [u["username"] for u in users]
        target_user = st.selectbox("Select User to Edit:", options=user_list)
        
        user_doc = next((u for u in users if u["username"] == target_user), None)
        
        if user_doc:
            col_act1, col_act2, col_act3 = st.columns(3)
            
            with col_act1:
                # Approval Toggle
                current_approval = user_doc.get("approved", False)
                new_approval = st.checkbox("Grant Platform Access (Approve)", value=current_approval)
                if current_approval != new_approval:
                    db_mgr.update_user_approval(target_user, new_approval)
                    db_mgr.log_activity(st.session_state.username, "Update Approval", f"Set approval of {target_user} to {new_approval}")
                    st.success(f"Access status updated for {target_user}!")
                    st.rerun()
                    
            with col_act2:
                # Role Selection
                role_opts = ["User", "Admin"]
                current_role = user_doc["role"]
                role_index = role_opts.index(current_role) if current_role in role_opts else 0
                new_role = st.selectbox("Update User Role:", options=role_opts, index=role_index)
                if current_role != new_role:
                    db_mgr.update_user_role(target_user, new_role)
                    db_mgr.log_activity(st.session_state.username, "Update Role", f"Changed role of {target_user} from {current_role} to {new_role}")
                    st.success(f"Role updated for {target_user} to {new_role}!")
                    st.rerun()
                    
            with col_act3:
                # Delete User Button
                st.write("") # Spacer
                # Prevent deleting yourself
                if target_user == st.session_state.username:
                    st.warning("You cannot delete your own account.")
                else:
                    if st.button("❌ Permanently Delete Account", type="primary", use_container_width=True):
                        db_mgr.delete_user(target_user)
                        db_mgr.log_activity(st.session_state.username, "Delete User", f"Removed user {target_user}")
                        st.error(f"User {target_user} has been deleted.")
                        st.rerun()
                        
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab_logs:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Operational Activity Logs")
        st.caption("Live audit trail of user logins, predictions, exports, and chat requests.")
        
        # Convert logs to DataFrame for easy visualization
        log_list = []
        for l in logs:
            log_list.append({
                "Timestamp": l.get("timestamp", "")[:19].replace("T", " "),
                "User": l.get("username", "System"),
                "Action performed": l.get("action", ""),
                "Log details": l.get("details", "")
            })
            
        df_logs = pd.DataFrame(log_list)
        
        # Filters in logs tab
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            log_user_filter = st.selectbox("Filter by User:", ["All"] + list(df_logs["User"].unique()))
        with col_f2:
            log_action_filter = st.selectbox("Filter by Action:", ["All"] + list(df_logs["Action performed"].unique()))
            
        filtered_logs = df_logs.copy()
        if log_user_filter != "All":
            filtered_logs = filtered_logs[filtered_logs["User"] == log_user_filter]
        if log_action_filter != "All":
            filtered_logs = filtered_logs[filtered_logs["Action performed"] == log_action_filter]
            
        st.dataframe(filtered_logs, use_container_width=True, hide_index=True)
        
        # Clear Logs Button
        if st.button("🧹 Clear Logs Display"):
            st.info("System logs are held securely in database. Refreshed view.")
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)
