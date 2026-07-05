import streamlit as st
import pandas as pd
from app.utils import load_data, load_models, restrict_view_access
from app.reports import generate_pdf_report, generate_docx_report

def render_reports_page():
    # Restricted to Admin and User
    if not restrict_view_access(["Admin", "User"]):
        return
        
    st.markdown('<div class="gradient-header">Executive Reports Portal</div>', unsafe_allow_html=True)
    st.caption("Generate publication-ready PDF / Word summaries and export full predictive data structures")
    
    st.markdown('<div class="glass-card animate-fade-in">', unsafe_allow_html=True)
    st.markdown("### Export Managerial Analytics")
    st.write("Generate and download reports detailing critical KPIs and employees at high risk of attrition.")
    
    # Load data and models
    df = load_data()
    model, preprocessor = load_models()
    
    if model is None or preprocessor is None:
        st.error("ML Model files are offline. PDF reports cannot compile predicted values.")
        return
        
    with st.spinner("Processing roster attrition predictions for PDF compiling..."):
        # Select expected 20 columns
        features_needed = preprocessor.feature_names_in_
        df_features = df[features_needed]
        
        # Predict all rows
        transformed = preprocessor.transform(df_features)
        probs = model.predict_proba(transformed)[:, 1]
        
        # Reconstruct names for PDF report
        df["Employee ID"] = df.index + 1001
        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
        df["Full Name"] = [f"{first_names[i % len(first_names)]} Smith" for i in range(len(df))]
        
        # Append predicted columns
        df_predicted = df.copy()
        df_predicted["Attrition Risk (%)"] = (probs * 100).round(1)
        df_predicted["Risk Level"] = pd.cut(
            probs * 100,
            bins=[0, 30, 70, 101],
            labels=["Low", "Medium", "High"]
        )
        
        # Filter high risk employees (Risk > 70%)
        high_risk_df = df_predicted[df_predicted["Risk Level"] == "High"].sort_values(by="Attrition Risk (%)", ascending=False)
        
    col_pdf, col_docx, col_csv = st.columns(3)
    
    with col_pdf:
        st.markdown("#### 📄 Executive PDF Report")
        st.write("Generates a print-ready document containing KPI scorecards, high-risk rosters, and guidelines.")
        
        pdf_bytes = generate_pdf_report(
            df=df_predicted,
            high_risk_df=high_risk_df,
            generated_by=st.session_state.user_name
        )
        
        st.download_button(
            label="📥 Download Executive PDF",
            data=pdf_bytes,
            file_name="HR_Analytics_Executive_Report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        
    with col_docx:
        st.markdown("#### 📝 Microsoft Word Report")
        st.write("Generates an editable Word document containing KPIs, tables, and AI guidelines.")
        
        docx_bytes = generate_docx_report(
            df=df_predicted,
            high_risk_df=high_risk_df,
            generated_by=st.session_state.user_name
        )
        
        st.download_button(
            label="📥 Download Word DOCX",
            data=docx_bytes,
            file_name="HR_Analytics_Executive_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
        
    with col_csv:
        st.markdown("#### 📊 Raw Predictive CSV")
        st.write("Exports the complete roster of employees with age, salary, and calculated attrition risk.")
        
        csv_buffer = df_predicted.to_csv(index=False)
        
        st.download_button(
            label="📥 Export Full Roster CSV",
            data=csv_buffer,
            file_name="HR_Analytics_Roster_Predictions.csv",
            mime="text/csv",
            type="secondary",
            use_container_width=True
        )
        
    st.markdown("---")
    st.markdown("#### 📈 Summary Statistics of calculated risk roster")
    sum_cols = st.columns(3)
    with sum_cols[0]:
        st.metric("Total Roster Count", len(df_predicted))
    with sum_cols[1]:
        st.metric("High-Risk Employees Count", len(high_risk_df))
    with sum_cols[2]:
        st.metric("Average Attrition Probability", f"{probs.mean()*100:.1f}%")
        
    st.markdown('</div>', unsafe_allow_html=True)
