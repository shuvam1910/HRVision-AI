import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from app.utils import load_data, load_models, inject_custom_css, get_risk_driver_analysis, generate_recommendations
from app.reports import generate_single_employee_report

def render_employees_page():
    st.markdown('<div class="gradient-header">Employee Directory & Profiles</div>', unsafe_allow_html=True)
    st.caption("Inspect individual records, run ML risk predictions, and review retention recommendations")
    
    # Load data & models
    df = load_data()
    model, preprocessor = load_models()
    
    # Sidebar search filters
    st.sidebar.markdown("### 🔍 Directory Filters")
    search_query = st.sidebar.text_input("Search Employee Name/ID", placeholder="e.g. Employee ID or search query")
    dept = st.sidebar.selectbox("Department", ["All"] + list(df["Department"].unique()))
    role = st.sidebar.selectbox("Job Role", ["All"] + list(df["JobRole"].unique()))
    
    # Let's mock a column 'EmployeeName' since IBM dataset doesn't have names
    # Seed names using a deterministic mapping from index
    np.random.seed(42)
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    
    # Create employee names and unique IDs
    # In IBM dataset, we have EmployeeNumber. Let's make sure to use it.
    df["Employee ID"] = df.index + 1001  # Sequential ID starting from 1001
    
    # Deterministic generation of names based on index
    names = []
    for idx in range(len(df)):
        fn = first_names[idx % len(first_names)]
        ln = last_names[(idx * 3) % len(last_names)]
        names.append(f"{fn} {ln}")
    df["Full Name"] = names
    
    # Filter dataset
    filtered_df = df.copy()
    if dept != "All":
        filtered_df = filtered_df[filtered_df["Department"] == dept]
    if role != "All":
        filtered_df = filtered_df[filtered_df["JobRole"] == role]
        
    if search_query:
        # Search by ID or Name
        search_query_lower = search_query.lower()
        filtered_df = filtered_df[
            filtered_df["Full Name"].str.lower().str.contains(search_query_lower) |
            filtered_df["Employee ID"].astype(str).str.contains(search_query_lower)
        ]
        
    # Main grid list
    st.write(f"Showing **{len(filtered_df)}** Employees")
    
    # Select employee to view detail
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📋 Select Employee Profile")
    
    employee_options = {f"{row['Employee ID']} - {row['Full Name']} ({row['JobRole']})": row["Employee ID"] for _, row in filtered_df.iterrows()}
    
    if not employee_options:
        st.warning("No employees found matching the filters.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
        
    selected_label = st.selectbox("Choose employee to inspect:", options=list(employee_options.keys()))
    selected_id = employee_options[selected_label]
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get details for selected employee
    employee_row = df[df["Employee ID"] == selected_id].iloc[0]
    
    # Show profile layout
    st.write("")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # Personal & Professional Details Card
        st.markdown(f"""
        <div class="glass-card animate-fade-in" style="height:100%">
            <h3>👤 Employee Details</h3>
            <hr style="border:0.5px solid rgba(255,255,255,0.08); margin-bottom:15px;"/>
            <table style="width:100%; border-collapse:collapse; font-size:0.95rem; margin-top:10px;">
                <tr style="border-bottom:1px solid rgba(128, 128, 128, 0.25);"><td style="padding:12px; text-align:center; font-weight:700; color:var(--text-color); vertical-align:middle;">Full Name</td><td style="padding:12px; text-align:center; font-weight:600; color:var(--text-color); vertical-align:middle;">{employee_row['Full Name']}</td></tr>
                <tr style="border-bottom:1px solid rgba(128, 128, 128, 0.25);"><td style="padding:12px; text-align:center; font-weight:700; color:var(--text-color); vertical-align:middle;">Employee ID</td><td style="padding:12px; text-align:center; color:var(--text-color); vertical-align:middle;">{employee_row['Employee ID']}</td></tr>
                <tr style="border-bottom:1px solid rgba(128, 128, 128, 0.25);"><td style="padding:12px; text-align:center; font-weight:700; color:var(--text-color); vertical-align:middle;">Age / Gender</td><td style="padding:12px; text-align:center; color:var(--text-color); vertical-align:middle;">{employee_row['Age']} / {employee_row['Gender']}</td></tr>
                <tr style="border-bottom:1px solid rgba(128, 128, 128, 0.25);"><td style="padding:12px; text-align:center; font-weight:700; color:var(--text-color); vertical-align:middle;">Department</td><td style="padding:12px; text-align:center; color:var(--text-color); vertical-align:middle;">{employee_row['Department']}</td></tr>
                <tr style="border-bottom:1px solid rgba(128, 128, 128, 0.25);"><td style="padding:12px; text-align:center; font-weight:700; color:var(--text-color); vertical-align:middle;">Job Role</td><td style="padding:12px; text-align:center; color:var(--text-color); vertical-align:middle;">{employee_row['JobRole']}</td></tr>
                <tr style="border-bottom:1px solid rgba(128, 128, 128, 0.25);"><td style="padding:12px; text-align:center; font-weight:700; color:var(--text-color); vertical-align:middle;">Monthly Salary</td><td style="padding:12px; text-align:center; font-weight:700; color:#10b981; vertical-align:middle;">${employee_row['MonthlyIncome']:,}</td></tr>
                <tr style="border-bottom:1px solid rgba(128, 128, 128, 0.25);"><td style="padding:12px; text-align:center; font-weight:700; color:var(--text-color); vertical-align:middle;">Overtime Required</td><td style="padding:12px; text-align:center; color:{'#ef4444' if employee_row['OverTime'] == 'Yes' else '#10b981'}; font-weight:700; vertical-align:middle;">{employee_row['OverTime']}</td></tr>
                <tr style="border-bottom:1px solid rgba(128, 128, 128, 0.25);"><td style="padding:12px; text-align:center; font-weight:700; color:var(--text-color); vertical-align:middle;">Total Work Experience</td><td style="padding:12px; text-align:center; color:var(--text-color); vertical-align:middle;">{employee_row['TotalWorkingYears']} Years</td></tr>
                <tr style="border-bottom:1px solid rgba(128, 128, 128, 0.25);"><td style="padding:12px; text-align:center; font-weight:700; color:var(--text-color); vertical-align:middle;">Tenure at Company</td><td style="padding:12px; text-align:center; color:var(--text-color); vertical-align:middle;">{employee_row['YearsAtCompany']} Years</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    with col_right:
        # Attrition Prediction Gauges
        if model is not None and preprocessor is not None:
            # Reconstruct the feature set of 20 elements
            features_needed = preprocessor.feature_names_in_
            employee_features = pd.DataFrame([employee_row[features_needed]])
            
            # Predict
            transformed_features = preprocessor.transform(employee_features)
            prob = model.predict_proba(transformed_features)[0][1] # Probability of Attrition (class 1)
            
            st.markdown('<div class="glass-card animate-fade-in" style="height:100%">', unsafe_allow_html=True)
            st.markdown("### 🔮 ML Attrition Risk Predictor")
            
            # Create gauge chart
            risk_color = "#10b981" if prob < 0.3 else ("#f59e0b" if prob < 0.7 else "#ef4444")
            risk_label = "LOW RISK" if prob < 0.3 else ("MEDIUM RISK" if prob < 0.7 else "HIGH RISK")
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = prob * 100,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': f"Risk Status: {risk_label}", 'font': {'size': 16, 'color': risk_color}},
                number = {'suffix': "%", 'font': {'color': risk_color}},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': risk_color},
                    'bgcolor': "rgba(255,255,255,0.05)",
                    'borderwidth': 1,
                    'bordercolor': "rgba(255,255,255,0.1)",
                    'steps': [
                        {'range': [0, 30], 'color': 'rgba(16, 185, 129, 0.15)'},
                        {'range': [30, 70], 'color': 'rgba(245, 158, 11, 0.15)'},
                        {'range': [70, 100], 'color': 'rgba(239, 68, 68, 0.15)'}
                    ]
                }
            ))
            
            fig.update_layout(
                height=230,
                margin=dict(l=15, r=15, t=40, b=15),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#ffffff" if st.get_option("theme.base") == "dark" else "#1f2937")
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Risk details summary
            st.markdown(f"Actual Database Attrition Status: **{'Left Company' if employee_row['Attrition'] == 'Yes' else 'Active Employee'}**")
            
            # Compile single employee PDF report
            pdf_report_bytes = generate_single_employee_report(
                employee_data=employee_row,
                prob=prob,
                drivers=get_risk_driver_analysis(employee_row),
                generated_by=st.session_state.user_name
            )
            
            st.download_button(
                label="📥 Download Diagnostic PDF Report",
                data=pdf_report_bytes,
                file_name=f"Attrition_Diagnosis_{employee_row['Employee ID']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("Model unavailable. Prediction skipped.")
            
    # Drivers and action items
    st.write("")
    col_driver, col_action = st.columns(2)
    
    # Calculate custom feature drivers
    drivers = get_risk_driver_analysis(employee_row)
    
    with col_driver:
        st.markdown('<div class="glass-card animate-fade-in" style="height:100%">', unsafe_allow_html=True)
        st.markdown("### 📊 Predictive Drivers (SHAP Analogue)")
        st.caption("Key parameters driving risk probability up (+) or down (-)")
        
        # Display drivers as small styled lists
        for impact, title, desc in drivers:
            icon = "🔺" if "+" in impact else "🔹"
            color = "#f87171" if "+" in impact else "#34d399"
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); padding:10px 14px; border-radius:10px; margin-bottom:10px;">
                <span style="font-weight:600; color:{color}; float:right;">{impact}</span>
                <strong>{icon} {title}</strong>
                <p style="margin:4px 0 0 0; font-size:0.8rem; color:rgba(255,255,255,0.5);">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_action:
        st.markdown('<div class="glass-card animate-fade-in" style="height:100%">', unsafe_allow_html=True)
        st.markdown("### 💡 Retention Action Items")
        st.caption("Actionable steps compiled by HR AI Copilot engine")
        
        recommendations = generate_recommendations(drivers)
        
        for rec in recommendations:
            st.markdown(f"- {rec}")
            
        # Satisfaction Gauges list
        st.markdown("---")
        st.markdown("#### 🎯 Satisfaction and Balance Scorecard")
        
        # Create a small table of satisfaction scores
        sat_cols = st.columns(3)
        with sat_cols[0]:
            st.metric("Job Satisfaction", f"{employee_row['JobSatisfaction']}/4")
        with sat_cols[1]:
            st.metric("Work Life Balance", f"{employee_row['WorkLifeBalance']}/4")
        with sat_cols[2]:
            st.metric("Env Satisfaction", f"{employee_row['EnvironmentSatisfaction']}/4")
            
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Table list below for reference
    st.write("")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📂 Filtered Employee Dataset Reference")
    st.dataframe(
        filtered_df[["Employee ID", "Full Name", "Age", "Gender", "Department", "JobRole", "MonthlyIncome", "Attrition"]],
        use_container_width=True,
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
