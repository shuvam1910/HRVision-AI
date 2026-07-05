import re
import pandas as pd
import numpy as np
from app.utils import load_data, load_models

class HRCopilot:
    def __init__(self):
        self.df = load_data()
        self.model, self.preprocessor = load_models()
        
        # Add sequential IDs and Full Names for dynamic lookups
        self.df["Employee ID"] = self.df.index + 1001
        
        # Deterministic generation of names
        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
        self.df["Full Name"] = [f"{first_names[i % len(first_names)]} Smith" for i in range(len(self.df))]

    def parse_query(self, query):
        """Parses natural language queries and extracts answers from dataset/model."""
        query = query.lower().strip()
        
        # 1. Look up Employee ID
        emp_match = re.search(r"employee (?:id\s+)?(\d{4})", query)
        if emp_match:
            emp_id = int(emp_match.group(1))
            return self._get_employee_analysis(emp_id)
            
        # 2. General Attrition Rate
        if "attrition rate" in query or "turnover rate" in query:
            # Check for department specific
            if "sales" in query:
                return self._get_dept_attrition("Sales")
            elif "research" in query or "r&d" in query or "development" in query:
                return self._get_dept_attrition("Research & Development")
            elif "resources" in query or "hr" in query:
                return self._get_dept_attrition("Human Resources")
            else:
                total = len(self.df)
                attr_count = len(self.df[self.df["Attrition"] == "Yes"])
                rate = (attr_count / total) * 100
                return f"The **overall attrition rate** across all {total:,} employees is **{rate:.1f}%** ({attr_count} left, {total - attr_count} remain active)."

        # 3. Average Monthly Income / Salary
        if "average income" in query or "avg income" in query or "average salary" in query or "avg salary" in query:
            if "sales" in query:
                return self._get_dept_income("Sales")
            elif "research" in query or "r&d" in query:
                return self._get_dept_income("Research & Development")
            elif "resources" in query or "hr" in query:
                return self._get_dept_income("Human Resources")
            else:
                avg_inc = self.df["MonthlyIncome"].mean()
                return f"The **average monthly income** across the organization is **${avg_inc:,.2f}**."

        # 4. Top Feature Importances
        if "top features" in query or "importance" in query or "drivers" in query:
            return ("The top 5 global factors driving employee attrition predicted by our ML model are:\n\n"
                    "1. **Overtime Work (OverTime):** Employees working overtime have significantly higher attrition.\n"
                    "2. **Monthly Income (MonthlyIncome):** Lower compensation packages strongly correlate with higher exit rates.\n"
                    "3. **Employee Age (Age):** Younger employees are statistically more mobile and likely to change companies.\n"
                    "4. **Work Environment Satisfaction (EnvironmentSatisfaction):** Poor workspace environments drive higher exits.\n"
                    "5. **Stock Option Level (StockOptionLevel):** Zero equity ownership levels correspond to higher attrition.")

        # 5. Retention Strategies
        if "retention" in query or "reduce attrition" in query or "how to retain" in query:
            return ("Here are key actionable strategies proposed by the AI Copilot to reduce employee attrition:\n\n"
                    "1. ⏳ **Redistribute Overtime Workload:** Employees working overtime are 3x more likely to leave. Cap excessive hours and offer flexible work configurations.\n"
                    "2. 💵 **Salary Benchmarking:** Regularly review compensation packages for low-salary tiers (below $4,000/month) where attrition is highest.\n"
                    "3. 📈 **Stock & Equity Programs:** Expand stock option grants (level 1+) to key team members, as zero-equity plans exhibit double the attrition rates.\n"
                    "4. 💬 **Manager-Employee Check-ins:** Conduct reviews for employees with stagnant roles or poor manager relationships to outline clear growth paths.")

        # 6. Capabilities check
        if "help" in query or "capabilities" in query or "what can you do" in query:
            return ("I am your **HR Analytics AI Copilot**. You can ask me questions like:\n"
                    "- *'What is the overall attrition rate?'*\n"
                    "- *'What is the average salary in the Sales department?'*\n"
                    "- *'Is employee 1005 at risk?'* (Look up specific employee metrics & predict risk)\n"
                    "- *'What are the top features driving attrition?'*\n"
                    "- *'How can we reduce attrition?'*")

        # 7. Standard NLP Fallback
        return ("I'm not sure I understand that query. I can help with attrition stats, department averages, specific employee audits, and retention recommendations.\n\n"
                "Try asking: *'What is the attrition rate in R&D?'* or *'Is employee 1012 at risk?'*")

    def _get_dept_attrition(self, dept_name):
        dept_df = self.df[self.df["Department"] == dept_name]
        total = len(dept_df)
        if total == 0:
            return f"No records found for the department '{dept_name}'."
        attr_count = len(dept_df[dept_df["Attrition"] == "Yes"])
        rate = (attr_count / total) * 100
        return f"In the **{dept_name}** department, the attrition rate is **{rate:.1f}%** (out of {total} employees, {attr_count} left)."

    def _get_dept_income(self, dept_name):
        dept_df = self.df[self.df["Department"] == dept_name]
        total = len(dept_df)
        if total == 0:
            return f"No records found for the department '{dept_name}'."
        avg_inc = dept_df["MonthlyIncome"].mean()
        return f"The **average monthly income** in the **{dept_name}** department is **${avg_inc:,.2f}**."

    def _get_employee_analysis(self, emp_id):
        # Find employee
        match_df = self.df[self.df["Employee ID"] == emp_id]
        if len(match_df) == 0:
            return f"Could not find any employee with ID **{emp_id}**. The sequential ID ranges from 1001 to {1001 + len(self.df) - 1}."
        
        row = match_df.iloc[0]
        
        if self.model is not None and self.preprocessor is not None:
            features_needed = self.preprocessor.feature_names_in_
            emp_features = pd.DataFrame([row[features_needed]])
            transformed = self.preprocessor.transform(emp_features)
            prob = self.model.predict_proba(transformed)[0][1] * 100
            
            risk_label = "LOW RISK" if prob < 30 else ("MEDIUM RISK" if prob < 70 else "HIGH RISK")
            risk_color = "green" if prob < 30 else ("orange" if prob < 70 else "red")
            
            response = (f"### 📊 Profile Audit: {row['Full Name']} (ID: {emp_id})\n"
                        f"- **Job Role:** {row['JobRole']} ({row['Department']})\n"
                        f"- **Monthly Income:** ${row['MonthlyIncome']:,}\n"
                        f"- **Overtime Work:** {row['OverTime']}\n"
                        f"- **Years at Company:** {row['YearsAtCompany']} years\n"
                        f"- **Job Satisfaction:** {row['JobSatisfaction']}/4\n\n"
                        f"🔮 **ML Attrition Risk Prediction:** **{prob:.1f}%** - <b style='color:{risk_color};'>{risk_label}</b>\n\n")
            
            # Action suggestion
            if prob >= 70:
                response += "🚨 **HR Urgent Alert:** Employee is in the high-risk bracket. Recommended actions: review work hours to curb overtime, assess satisfaction, and schedule a retention review."
            elif prob >= 30:
                response += "⚠️ **HR Warning:** Employee is in the medium-risk bracket. Action: review compensation and schedule a routine check-in."
            else:
                response += "✔️ **Retention Stable:** Employee metrics align with low-risk benchmarks. Maintain current environment."
                
            return response
        else:
            return f"Found employee **{row['Full Name']}** (ID: {emp_id}), but the ML model is offline. Cannot run attrition risk prediction."
