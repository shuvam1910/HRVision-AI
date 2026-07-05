import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.utils import load_data, render_kpi

def render_dashboard_page():
    st.markdown('<div class="gradient-header">HRVision AI Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 1.05rem; font-weight: 600; color: var(--text-color); opacity: 0.75; margin-bottom: 20px;">Enterprise Workforce Intelligence at a Glance</div>', unsafe_allow_html=True)
    
    # Load dataset
    df = load_data()
    
    # Filters - Let's use containers inside the sidebar or a collapsable expander for a clean UI
    st.sidebar.markdown("### 🔍 Dashboard Filters")
    departments = st.sidebar.multiselect("Department", options=sorted(df["Department"].unique()), default=[])
    job_roles = st.sidebar.multiselect("Job Role", options=sorted(df["JobRole"].unique()), default=[])
    genders = st.sidebar.multiselect("Gender", options=sorted(df["Gender"].unique()), default=[])
    overtime_filter = st.sidebar.multiselect("Overtime Status", options=sorted(df["OverTime"].unique()), default=[])
    
    # Filter operations
    filtered_df = df.copy()
    if departments:
        filtered_df = filtered_df[filtered_df["Department"].isin(departments)]
    if job_roles:
        filtered_df = filtered_df[filtered_df["JobRole"].isin(job_roles)]
    if genders:
        filtered_df = filtered_df[filtered_df["Gender"].isin(genders)]
    if overtime_filter:
        filtered_df = filtered_df[filtered_df["OverTime"].isin(overtime_filter)]
        
    # Attrition rate and KPI logic
    total_emp = len(filtered_df)
    
    if total_emp > 0:
        attrition_count = len(filtered_df[filtered_df["Attrition"] == "Yes"])
        attrition_rate = (attrition_count / total_emp) * 100
        avg_income = filtered_df["MonthlyIncome"].mean()
        avg_tenure = filtered_df["YearsAtCompany"].mean()
    else:
        attrition_rate = 0
        avg_income = 0
        avg_tenure = 0
        
    # Render KPI Cards in a modern grid
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown(render_kpi("Total Employees", f"{total_emp:,}", card_class="success"), unsafe_allow_html=True)
    with kpi_cols[1]:
        attr_class = "danger" if attrition_rate > 15 else ("warning" if attrition_rate > 10 else "")
        st.markdown(render_kpi("Attrition Rate", f"{attrition_rate:.1f}%", f"{len(filtered_df[filtered_df['Attrition']=='Yes'])} Employees", "negative" if attrition_rate > 15 else "positive", attr_class), unsafe_allow_html=True)
    with kpi_cols[2]:
        st.markdown(render_kpi("Avg Monthly Income", f"${avg_income:,.0f}", "+1.2% vs last Q", "positive"), unsafe_allow_html=True)
    with kpi_cols[3]:
        st.markdown(render_kpi("Avg Work Tenure", f"{avg_tenure:.1f} Yrs", "-0.4 Yrs turnover", "negative"), unsafe_allow_html=True)
        
    if total_emp == 0:
        st.warning("⚠️ No records match the current filters. Please broaden your selection.")
        return
        
    st.write("")
    
    # Grid Layout for Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Attrition by Department
        dept_attr = filtered_df.groupby(["Department", "Attrition"]).size().unstack(fill_value=0).reset_index()
        dept_attr["Total"] = dept_attr["Yes"] + dept_attr["No"]
        dept_attr["Attrition Rate (%)"] = (dept_attr["Yes"] / dept_attr["Total"]) * 100
        
        fig_dept = px.bar(
            dept_attr,
            x="Department",
            y="Attrition Rate (%)",
            title="Attrition Rate by Department",
            color="Department",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            text=dept_attr["Attrition Rate (%)"].apply(lambda x: f"{x:.1f}%")
        )
        fig_dept.update_traces(textposition='outside')
        fig_dept.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#ffffff" if st.get_option("theme.base") == "dark" else "#1f2937"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)" if st.get_option("theme.base") == "dark" else "rgba(0,0,0,0.05)")
        )
        st.plotly_chart(fig_dept, use_container_width=True)
        
    with col2:
        # Attrition vs Overtime
        ot_attr = filtered_df.groupby(["OverTime", "Attrition"]).size().unstack(fill_value=0).reset_index()
        ot_attr["Total"] = ot_attr["Yes"] + ot_attr["No"]
        ot_attr["Attrition Rate (%)"] = (ot_attr["Yes"] / ot_attr["Total"]) * 100
        
        fig_ot = px.bar(
            ot_attr,
            x="OverTime",
            y="Attrition Rate (%)",
            title="Overtime Impact on Attrition Rate",
            color="OverTime",
            color_discrete_map={"Yes": "#ef4444", "No": "#10b981"},
            text=ot_attr["Attrition Rate (%)"].apply(lambda x: f"{x:.1f}%")
        )
        fig_ot.update_traces(textposition='outside')
        fig_ot.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#ffffff" if st.get_option("theme.base") == "dark" else "#1f2937"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)" if st.get_option("theme.base") == "dark" else "rgba(0,0,0,0.05)")
        )
        st.plotly_chart(fig_ot, use_container_width=True)
        
    # Second Row of Charts
    col3, col4 = st.columns(2)
    
    with col3:
        # Monthly Income Distribution vs Attrition
        fig_income = px.box(
            filtered_df,
            x="Attrition",
            y="MonthlyIncome",
            color="Attrition",
            title="Monthly Income vs Attrition",
            color_discrete_map={"Yes": "#f43f5e", "No": "#10b981"},
            points="outliers"
        )
        fig_income.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#ffffff" if st.get_option("theme.base") == "dark" else "#1f2937"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)" if st.get_option("theme.base") == "dark" else "rgba(0,0,0,0.05)")
        )
        st.plotly_chart(fig_income, use_container_width=True)
        
    with col4:
        # Job Satisfaction & Environment Satisfaction impact on Attrition
        # Group by JobSatisfaction & EnvironmentSatisfaction and calculate Attrition Rate
        sat_df = filtered_df.groupby(["JobSatisfaction", "Attrition"]).size().unstack(fill_value=0).reset_index()
        sat_df["Total"] = sat_df["Yes"] + sat_df["No"]
        sat_df["Attrition Rate (%)"] = (sat_df["Yes"] / sat_df["Total"]) * 100
        
        # Replace numbers with labels for better visual representation
        sat_df["Job Satisfaction Label"] = sat_df["JobSatisfaction"].map({
            1: "1-Low", 2: "2-Medium", 3: "3-High", 4: "4-Very High"
        })
        
        fig_sat = px.line(
            sat_df,
            x="Job Satisfaction Label",
            y="Attrition Rate (%)",
            title="Attrition Rate by Job Satisfaction Level",
            markers=True,
            line_shape="spline",
            color_discrete_sequence=["#a855f7"]
        )
        fig_sat.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#ffffff" if st.get_option("theme.base") == "dark" else "#1f2937"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)" if st.get_option("theme.base") == "dark" else "rgba(0,0,0,0.05)")
        )
        st.plotly_chart(fig_sat, use_container_width=True)
        
    # Third Row of Charts: Job Role Details
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Attrition Risk by Job Role")
    
    role_attr = filtered_df.groupby(["JobRole", "Attrition"]).size().unstack(fill_value=0).reset_index()
    role_attr["Total"] = role_attr["Yes"] + role_attr["No"]
    role_attr["Attrition Rate (%)"] = (role_attr["Yes"] / role_attr["Total"]) * 100
    role_attr = role_attr.sort_values(by="Attrition Rate (%)", ascending=True)
    
    fig_role = px.bar(
        role_attr,
        y="JobRole",
        x="Attrition Rate (%)",
        orientation="h",
        color="Attrition Rate (%)",
        color_continuous_scale=px.colors.sequential.Sunsetdark,
        title="Job Role Attrition Rate (%)"
    )
    fig_role.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#ffffff" if st.get_option("theme.base") == "dark" else "#1f2937"),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)" if st.get_option("theme.base") == "dark" else "rgba(0,0,0,0.05)"),
        yaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig_role, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
