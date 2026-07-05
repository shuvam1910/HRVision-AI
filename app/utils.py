import os
import joblib
import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    """Loads and caches the HR Attrition Dataset."""
    path = r"c:\Users\SHUVAM NAYAK\Downloads\projecttt\data\HR-Employee-Attrition.csv"
    if not os.path.exists(path):
        # Fail-safe search if the path changes during test run
        path = "data/HR-Employee-Attrition.csv"
    df = pd.read_csv(path)
    return df

@st.cache_resource
def load_models():
    """Loads and caches the ML pipeline (preprocessor and prediction model)."""
    model_path = r"c:\Users\SHUVAM NAYAK\Downloads\projecttt\models\model.pkl"
    prep_path = r"c:\Users\SHUVAM NAYAK\Downloads\projecttt\models\preprocessor.pkl"
    
    if not os.path.exists(model_path):
        model_path = "models/model.pkl"
        prep_path = "models/preprocessor.pkl"
        
    try:
        model = joblib.load(model_path)
        preprocessor = joblib.load(prep_path)
        return model, preprocessor
    except Exception as e:
        st.error(f"Failed to load ML models: {e}")
        return None, None

def inject_custom_css():
    """Injects premium CSS for glassmorphism, responsive metrics, and animations."""
    css_path = r"c:\Users\SHUVAM NAYAK\Downloads\projecttt\assets\custom.css"
    if not os.path.exists(css_path):
        css_path = "assets/custom.css"
        
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

def render_kpi(title, value, delta=None, delta_type="positive", card_class=""):
    """Generates a premium glassmorphic KPI card with responsive flex design."""
    delta_html = ""
    if delta is not None:
        klass = "positive" if delta_type == "positive" else "negative"
        sign = "+" if delta_type == "positive" else ""
        delta_html = f'<div class="kpi-delta {klass}">{sign}{delta}</div>'
        
    html = f"""
    <div class="glass-kpi {card_class}">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """
    return html

def is_authorized(required_roles):
    """Checks if the logged-in user has the authorization to view a page."""
    if "user_role" not in st.session_state or st.session_state.user_role not in required_roles:
        return False
    return True

def restrict_view_access(required_roles):
    """Renders a locked screen if the user role is unauthorized."""
    if not is_authorized(required_roles):
        st.error("⛔ Access Denied")
        st.warning(f"This page requires one of the following roles: {', '.join(required_roles)}. Your current role is: {st.session_state.user_role}")
        st.info("Please request access level modification from an Admin or log in with an authorized account.")
        return False
    return True

def get_risk_driver_analysis(row):
    """Calculates local feature risk drivers based on employee metrics."""
    drivers = []
    
    # Check Overtime
    if row["OverTime"] == "Yes":
        drivers.append(("+22% Risk", "Working Overtime", "Overtime is one of the highest drivers of attrition. Consider redistributing workload."))
    else:
        drivers.append(("-8% Risk", "No Overtime", "Balanced workload without extra hours."))
        
    # Check Monthly Income
    if row["MonthlyIncome"] < 4000:
        drivers.append(("+15% Risk", "Low Monthly Income (<$4k)", "Below average industry rate. Review salary compensation."))
    elif row["MonthlyIncome"] > 10000:
        drivers.append(("-12% Risk", "High Monthly Income (>$10k)", "Highly competitive salary. Retention factor."))
        
    # Check Job Satisfaction
    if row["JobSatisfaction"] <= 2:
        drivers.append(("+12% Risk", f"Low Job Satisfaction ({row['JobSatisfaction']}/4)", "Expressed dissatisfaction in role. Conduct feedback review."))
    else:
        drivers.append(("-5% Risk", f"High Job Satisfaction ({row['JobSatisfaction']}/4)", "Satisfied with their job role."))
        
    # Check Stock Option Level
    if row["StockOptionLevel"] == 0:
        drivers.append(("+10% Risk", "No Stock Options", "No equity incentive. Consider offering standard stock options."))
        
    # Check Years Since Last Promotion
    if row["YearsSinceLastPromotion"] >= 3:
        drivers.append(("+8% Risk", f"No Promotion for {row['YearsSinceLastPromotion']} Years", "Stagnant career growth. Plan next career development step."))
        
    # Check Relationship with Manager
    if row["RelationshipSatisfaction"] <= 2:
        drivers.append(("+6% Risk", "Low Relationship Satisfaction", "Poor dynamic with team or manager. Monitor team health."))
        
    return drivers

def generate_recommendations(drivers):
    """Generates actionable retention plans from risk drivers."""
    recommendations = []
    for risk, title, desc in drivers:
        if "+" in risk:
            recommendations.append(f"**{title}**: {desc}")
            
    if not recommendations:
        return ["No action required. Employee metrics indicate high satisfaction and retention stability."]
    return recommendations
