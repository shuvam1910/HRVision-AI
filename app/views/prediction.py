import streamlit as st
import pandas as pd
import io
import plotly.graph_objects as go
from app.utils import load_models, restrict_view_access, get_risk_driver_analysis
from app.reports import generate_single_employee_report
from app.database import DatabaseManager

db_mgr = DatabaseManager()

def render_prediction_page():
    st.markdown('<div class="gradient-header">Predictive Modeling Portal</div>', unsafe_allow_html=True)
    st.caption("Predict individual attrition probability or run batch employee evaluations")
    
    # Load ML pipeline
    model, preprocessor = load_models()
    
    if model is None or preprocessor is None:
        st.error("ML model files could not be loaded. Please ensure models are trained and saved in 'models/' directory.")
        return
        
    # Set up Tabs for Single and Batch predictions
    tab_single, tab_batch = st.tabs(["👤 Single Employee Predictor", "📂 Batch CSV Predictor"])
    
    with tab_single:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Input Employee Profile Metrics")
        st.caption("Fill in the fields to estimate attrition likelihood in real-time.")
        
        # Grid layout for inputs
        col1, col2, col3 = st.columns(3)
        
        # Category lists mapping IBM data values
        dept_options = ["Sales", "Research & Development", "Human Resources"]
        role_options = ["Sales Executive", "Research Scientist", "Laboratory Technician", "Manufacturing Director", 
                        "Healthcare Representative", "Manager", "Sales Representative", "Research Director", "Human Resources"]
        travel_options = ["Travel_Rarely", "Travel_Frequently", "Non-Travel"]
        education_fields = ["Life Sciences", "Medical", "Marketing", "Technical Degree", "Other", "Human Resources"]
        marital_statuses = ["Single", "Married", "Divorced"]
        
        with col1:
            age = st.slider("Age", 18, 65, 34)
            gender = st.selectbox("Gender", ["Female", "Male"])
            department = st.selectbox("Department", dept_options)
            job_role = st.selectbox("Job Role", role_options)
            monthly_income = st.number_input("Monthly Income ($)", min_value=1000, max_value=30000, value=5800, step=100)
            
        with col2:
            travel = st.selectbox("Business Travel", travel_options)
            distance = st.slider("Distance From Home (Miles)", 1, 30, 8)
            education = st.slider("Education Level", 1, 5, 3, help="1: Below College, 2: College, 3: Bachelor, 4: Master, 5: Doctor")
            education_field = st.selectbox("Education Field", education_fields)
            marital_status = st.selectbox("Marital Status", marital_statuses)
            
        with col3:
            satisfaction = st.slider("Job Satisfaction", 1, 4, 3)
            env_satisfaction = st.slider("Environment Satisfaction", 1, 4, 3)
            work_life = st.slider("Work-Life Balance", 1, 4, 3)
            rel_satisfaction = st.slider("Relationship Satisfaction", 1, 4, 3)
            overtime = st.selectbox("Overtime Required", ["No", "Yes"])
            
        # Expansion of remaining 5 parameters
        with st.expander("⚙️ Advanced Tenure & Rating Settings"):
            col_adv1, col_adv2 = st.columns(2)
            with col_adv1:
                years_at_company = st.slider("Years At Company", 0, 40, 5)
                years_with_mgr = st.slider("Years With Current Manager", 0, 17, 3)
                training_times = st.slider("Training Times Last Year", 0, 6, 2)
            with col_adv2:
                stock_level = st.slider("Stock Option Level", 0, 3, 1)
                perf_rating = st.selectbox("Performance Rating", [3, 4], help="3: Excellent, 4: Outstanding")
                
        # Predict execution
        if st.button("Calculate Attrition Likelihood", type="primary", use_container_width=True):
            # Assemble DataFrame corresponding to model features
            input_data = pd.DataFrame([{
                "Age": age,
                "Gender": gender,
                "Department": department,
                "JobRole": job_role,
                "MonthlyIncome": monthly_income,
                "BusinessTravel": travel,
                "DistanceFromHome": distance,
                "Education": education,
                "EducationField": education_field,
                "MaritalStatus": marital_status,
                "JobSatisfaction": satisfaction,
                "EnvironmentSatisfaction": env_satisfaction,
                "WorkLifeBalance": work_life,
                "RelationshipSatisfaction": rel_satisfaction,
                "YearsAtCompany": years_at_company,
                "YearsWithCurrManager": years_with_mgr,
                "TrainingTimesLastYear": training_times,
                "OverTime": overtime,
                "StockOptionLevel": stock_level,
                "PerformanceRating": perf_rating
            }])
            
            try:
                # Preprocess & Predict
                transformed = preprocessor.transform(input_data)
                prob = model.predict_proba(transformed)[0][1]
                
                # Log activity
                db_mgr.log_activity(st.session_state.username, "Single Prediction", f"Calculated risk: {prob*100:.1f}%")
                
                # Create dictionary of inputs for drivers & reports
                row_dict = {
                    "Age": age, "Gender": gender, "Department": department, "JobRole": job_role, 
                    "MonthlyIncome": monthly_income, "BusinessTravel": travel, "DistanceFromHome": distance, 
                    "Education": education, "EducationField": education_field, "MaritalStatus": marital_status, 
                    "JobSatisfaction": satisfaction, "EnvironmentSatisfaction": env_satisfaction, 
                    "WorkLifeBalance": work_life, "RelationshipSatisfaction": rel_satisfaction, 
                    "YearsAtCompany": years_at_company, "YearsWithCurrManager": years_with_mgr, 
                    "TrainingTimesLastYear": training_times, "OverTime": overtime, 
                    "StockOptionLevel": stock_level, "PerformanceRating": perf_rating,
                    "YearsSinceLastPromotion": 0 # Default placeholder
                }
                
                # Compute risk drivers and compile report
                drivers = get_risk_driver_analysis(row_dict)
                pdf_report_bytes = generate_single_employee_report(
                    employee_data=row_dict,
                    prob=prob,
                    drivers=drivers,
                    generated_by=st.session_state.user_name
                )
                
                st.markdown("---")
                col_res1, col_res2 = st.columns([1.2, 1])
                
                with col_res1:
                    risk_color = "#10b981" if prob < 0.3 else ("#f59e0b" if prob < 0.7 else "#ef4444")
                    risk_label = "LOW ATTRITION RISK" if prob < 0.3 else ("MEDIUM ATTRITION RISK" if prob < 0.7 else "HIGH ATTRITION RISK")
                    
                    st.markdown(f"#### Attrition Prediction Results")
                    st.write(f"The employee has a predicted attrition likelihood of **{prob*100:.1f}%**.")
                    
                    # Recommendation alert box
                    if prob < 0.3:
                        st.success(f"✔️ **{risk_label}**: The employee shows metrics aligned with strong retention. Maintain current engagements.")
                    elif prob < 0.7:
                        st.warning(f"⚠️ **{risk_label}**: Key attrition drivers identified. Consider reviewing workload or career development plans.")
                    else:
                        st.error(f"🚨 **{risk_label}**: Immediate action recommended. Employee exhibits high risk indicators (e.g. overtime work, low satisfaction, stagnant salary).")
                        
                with col_res2:
                    # Risk Gauge Chart
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = prob * 100,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        number = {'suffix': "%", 'font': {'color': risk_color}},
                        gauge = {
                            'axis': {'range': [0, 100]},
                            'bar': {'color': risk_color},
                            'bgcolor': "rgba(255,255,255,0.05)",
                            'steps': [
                                {'range': [0, 30], 'color': 'rgba(16, 185, 129, 0.1)'},
                                {'range': [30, 70], 'color': 'rgba(245, 158, 11, 0.1)'},
                                {'range': [70, 100], 'color': 'rgba(239, 68, 68, 0.1)'}
                            ]
                        }
                    ))
                    fig.update_layout(
                        height=200,
                        margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Single diagnostic PDF download button
                st.download_button(
                    label="📥 Download Single Attrition Diagnostic Report (PDF)",
                    data=pdf_report_bytes,
                    file_name=f"HR_Attrition_Diagnosis_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                    
            except Exception as e:
                st.error(f"Prediction failed: {e}")
                
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab_batch:
        # Check permissions for Batch Predictions (Admins and Users)
        if not restrict_view_access(["Admin", "User"]):
            return
            
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Batch Attrition Risk Analyzer")
        st.caption("Upload a roster of employees to evaluate risk at scale. Download predictions table in CSV format.")
        
        # Template Generator Helper
        template_cols = ['Age', 'Gender', 'Department', 'JobRole', 'MonthlyIncome', 'BusinessTravel', 'DistanceFromHome', 
                         'Education', 'EducationField', 'MaritalStatus', 'JobSatisfaction', 'EnvironmentSatisfaction', 
                         'WorkLifeBalance', 'RelationshipSatisfaction', 'YearsAtCompany', 'YearsWithCurrManager', 
                         'TrainingTimesLastYear', 'OverTime', 'StockOptionLevel', 'PerformanceRating']
        
        # Sample row
        sample_row = {
            'Age': 32, 'Gender': 'Male', 'Department': 'Sales', 'JobRole': 'Sales Executive', 'MonthlyIncome': 6200,
            'BusinessTravel': 'Travel_Rarely', 'DistanceFromHome': 12, 'Education': 3, 'EducationField': 'Life Sciences',
            'MaritalStatus': 'Single', 'JobSatisfaction': 2, 'EnvironmentSatisfaction': 3, 'WorkLifeBalance': 3,
            'RelationshipSatisfaction': 3, 'YearsAtCompany': 4, 'YearsWithCurrManager': 2, 'TrainingTimesLastYear': 2,
            'OverTime': 'Yes', 'StockOptionLevel': 0, 'PerformanceRating': 3
        }
        template_df = pd.DataFrame([sample_row])
        
        # Render Download template
        buffer = io.StringIO()
        template_df.to_csv(buffer, index=False)
        st.download_button(
            label="📥 Download CSV Upload Template",
            data=buffer.getvalue(),
            file_name="hr_batch_prediction_template.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        
        uploaded_file = st.file_uploader("Upload CSV Roster File", type=["csv"])
        
        if uploaded_file is not None:
            try:
                # Load CSV
                df_upload = pd.read_csv(uploaded_file)
                
                # Check for necessary headers
                missing_cols = [col for col in template_cols if col not in df_upload.columns]
                
                if missing_cols:
                    st.error(f"Uploaded CSV is missing the following required columns: {', '.join(missing_cols)}")
                else:
                    # Run predictions
                    with st.spinner("Processing batch predictions..."):
                        # Select necessary features
                        df_features = df_upload[template_cols]
                        
                        # Preprocess
                        transformed_batch = preprocessor.transform(df_features)
                        # Predict probability
                        probs = model.predict_proba(transformed_batch)[:, 1]
                        
                        # Append predictions to the output dataframe
                        df_results = df_upload.copy()
                        df_results["Attrition Risk (%)"] = (probs * 100).round(1)
                        df_results["Risk Level"] = pd.cut(
                            probs * 100,
                            bins=[0, 30, 70, 101],
                            labels=["Low", "Medium", "High"]
                        )
                        
                        # Save log
                        db_mgr.log_activity(st.session_state.username, "Batch Prediction", f"Evaluated roster of {len(df_upload)} employees")
                        
                        # Output summary cards
                        num_high = len(df_results[df_results["Risk Level"] == "High"])
                        num_med = len(df_results[df_results["Risk Level"] == "Medium"])
                        num_low = len(df_results[df_results["Risk Level"] == "Low"])
                        
                        sum_cols = st.columns(3)
                        with sum_cols[0]:
                            st.metric("Total Uploaded Records", len(df_results))
                        with sum_cols[1]:
                            st.metric("High Attrition Risk", num_high, f"{num_high/len(df_results)*100:.1f}% of total")
                        with sum_cols[2]:
                            st.metric("Low Risk Status", num_low, f"{num_low/len(df_results)*100:.1f}% of total")
                            
                        st.write("")
                        
                        # Make sure names and IDs exist for the PDF report compiler
                        df_pdf_data = df_results.copy()
                        if "Employee ID" not in df_pdf_data.columns:
                            df_pdf_data["Employee ID"] = [1001 + i for i in range(len(df_pdf_data))]
                        if "Full Name" not in df_pdf_data.columns:
                            df_pdf_data["Full Name"] = [f"Batch Employee {i+1}" for i in range(len(df_pdf_data))]
                        if "Attrition" not in df_pdf_data.columns:
                            df_pdf_data["Attrition"] = df_pdf_data["Risk Level"].apply(lambda x: "Yes" if x == "High" else "No")
                            
                        high_risk_batch = df_pdf_data[df_pdf_data["Risk Level"] == "High"].sort_values(by="Attrition Risk (%)", ascending=False)
                        
                        from app.reports import generate_pdf_report
                        pdf_batch_bytes = generate_pdf_report(
                            df=df_pdf_data,
                            high_risk_df=high_risk_batch,
                            generated_by=st.session_state.user_name
                        )
                        
                        # Export buttons in two columns
                        col_exp1, col_exp2 = st.columns(2)
                        with col_exp1:
                            out_buffer = io.StringIO()
                            df_results.to_csv(out_buffer, index=False)
                            st.download_button(
                                label="📥 Export Predictions Table (CSV)",
                                data=out_buffer.getvalue(),
                                file_name="hr_batch_predictions_output.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        with col_exp2:
                            st.download_button(
                                label="📥 Download Batch PDF Executive Report",
                                data=pdf_batch_bytes,
                                file_name="hr_batch_predictions_report.pdf",
                                mime="application/pdf",
                                type="primary",
                                use_container_width=True
                            )
                        
                        # Table displaying outcomes
                        st.write("#### Predictions Roster View")
                        st.dataframe(df_results[["Attrition Risk (%)", "Risk Level"] + template_cols], use_container_width=True)
                        
            except Exception as e:
                st.error(f"Error parsing or predicting uploaded data: {e}")
                
        st.markdown('</div>', unsafe_allow_html=True)
