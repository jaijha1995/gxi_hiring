import streamlit as st
from datetime import date
import os

# =========================
# 🌟 PAGE CONFIGURATION
# =========================
st.set_page_config(
    page_title="Dynamic Developer Registration Form",
    page_icon="💻",
    layout="centered",
    initial_sidebar_state="expanded",
)

# =========================
# 🌈 CUSTOM CSS FOR STYLING
# =========================
st.markdown("""
<style>
body {
    background-color: #f5f7fa;
}
.form-container {
    background-color: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
    margin-bottom: 25px;
}
h1 {
    color: #FF6B6B;
}
h2 {
    color: #4B6CB7;
}
h3 {
    color: #FF6B6B;
}
input, select, textarea {
    border-radius: 8px !important;
    padding: 8px !important;
}
.stButton>button {
    background-color: #4B6CB7;
    color: white;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    border: none;
}
.stButton>button:hover {
    background-color: #182848;
}
</style>
""", unsafe_allow_html=True)

# =========================
# COMPANY LOGO + NAME
# =========================
st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
logo_path = "./gxi_logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=120)
else:
    st.warning("Logo file not found! Place 'gxi_logo.png' in the same folder as this script.")

st.markdown('<h1>Developer Registration Form</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#6c757d;">Join us as a developer. Fill your details below!</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown("---", unsafe_allow_html=True)

# =========================
# SELECT ROLE TYPE
# =========================
role_type = st.selectbox(
    "Select Developer Role Type",
    ["Select", "RAVE Developer", "Python Developer", "OR", "R Developer", "Other"]
)

# =========================
# PERSONAL INFORMATION
# =========================
st.markdown('<div class="form-container">', unsafe_allow_html=True)
st.header("👤 Personal Information")

col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Full Name", key="name")
    email = st.text_input("Email ID", key="email")
    phone = st.text_input("Phone Number", key="phone")
with col2:
    location = st.text_input("City / Location", key="location")
    country = st.selectbox(
        "Country",
        ["Select", "India", "United States", "United Kingdom", "Canada", "Australia", "Other"],
        key="country"
    )

states = []
if country == "India":
    states = ["Select", "Delhi", "Maharashtra", "Karnataka", "Tamil Nadu", "Uttar Pradesh"]
elif country == "United States":
    states = ["Select", "California", "Texas", "New York", "Florida", "Washington"]
elif country == "United Kingdom":
    states = ["Select", "England", "Scotland", "Wales", "Northern Ireland"]
elif country == "Canada":
    states = ["Select", "Ontario", "Quebec", "British Columbia", "Alberta"]
elif country == "Australia":
    states = ["Select", "New South Wales", "Victoria", "Queensland", "Western Australia"]

state = st.selectbox("State / Province", states if states else ["Select Country First"], key="state")
st.markdown('</div>', unsafe_allow_html=True)

# =========================
# EDUCATION
# =========================
st.markdown('<div class="form-container">', unsafe_allow_html=True)
st.header("🎓 Education Details")

edu_col1, edu_col2 = st.columns(2)
with edu_col1:
    highest_education = st.selectbox(
        "Highest Education Qualification",
        ["Select", "High School", "Diploma", "Bachelor's Degree", "Master's Degree", "PhD"],
        key="edu"
    )
    specialisation = st.text_input("Specialisation / Field of Study", key="specialisation")
    university = st.text_input("University / College Name", key="university")
with edu_col2:
    cgpa = st.text_input("Percentage / CGPA", key="cgpa")
    years_exp = st.number_input("Years of Experience", min_value=0, max_value=50, step=1, key="years_exp")
st.markdown('</div>', unsafe_allow_html=True)

# =========================
# PROFESSIONAL INFO
# =========================
st.markdown('<div class="form-container">', unsafe_allow_html=True)
st.header("💼 Professional Details")

role_col1, role_col2 = st.columns(2)
with role_col1:
    current_role = st.text_input("Current Role / Designation", key="role")
with role_col2:
    organisation = st.text_input("Current Organisation", key="org")

notice_status = st.radio("Are you serving a notice period?", ["Yes", "No"], key="notice_status")
if notice_status == "Yes":
    last_working_day = st.date_input("Last Working Day", value=date.today(), key="last_day")
else:
    notice_period_days = st.selectbox("Notice Period Duration (Days)", [15, 30, 45, 60, 90], key="notice_days")
st.markdown('</div>', unsafe_allow_html=True)

# =========================
# SKILLS & LANGUAGES
# =========================
st.markdown('<div class="form-container">', unsafe_allow_html=True)
st.header("🧠 Skills & Languages")

skills = st.multiselect(
    "Technical Skills",
    ["Python", "R", "RAVE Language", "SQL/RDBMS", "Machine Learning", "Data Analysis", "Power BI", "Tableau", "Excel", "JavaScript"],
    key="skills"
)

languages = st.multiselect(
    "Languages Proficient (Spoken/Written)",
    ["English", "Hindi", "French", "Spanish", "German", "Other"],
    key="languages"
)
st.markdown('</div>', unsafe_allow_html=True)

# =========================
# ROLE-BASED TECHNOLOGY EXPERIENCE
# =========================
st.markdown('<div class="form-container">', unsafe_allow_html=True)
st.header("💻 Role-Based Technology Experience")

def tech_exp_section(tech_name, key_prefix):
    exp = st.radio(f"Do you have experience with {tech_name}?", ["Yes", "No"], key=f"{key_prefix}_exp")
    if exp == "Yes":
        rating = st.slider(f"Rate yourself in {tech_name}", 1, 10, key=f"{key_prefix}_rate")
    else:
        rating = None
    return {"experience": exp, "rating": rating}

role_tech_experience = {}

if role_type == "RAVE Developer":
    role_tech_experience["RAVE"] = tech_exp_section("RAVE Language", "rave")
elif role_type == "Python Developer":
    role_tech_experience["Python"] = tech_exp_section("Python", "python")
    role_tech_experience["RDBMS"] = tech_exp_section("RDBMS", "rdbms")
elif role_type == "OR":
    role_tech_experience["Machine Learning"] = tech_exp_section("Machine Learning", "ml")
    role_tech_experience["Python"] = tech_exp_section("Python", "python")
    role_tech_experience["RDBMS"] = tech_exp_section("RDBMS", "rdbms")
elif role_type == "R Developer":
    role_tech_experience["R"] = tech_exp_section("R Language", "r")
else:
    role_tech_experience["Python"] = tech_exp_section("Python", "python")
    role_tech_experience["RAVE"] = tech_exp_section("RAVE Language", "rave")
    role_tech_experience["RDBMS"] = tech_exp_section("RDBMS", "rdbms")
    role_tech_experience["Machine Learning"] = tech_exp_section("Machine Learning", "ml")
    role_tech_experience["R"] = tech_exp_section("R Language", "r")

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# SUBMIT BUTTON
# =========================
st.markdown('<div class="form-container">', unsafe_allow_html=True)
st.subheader("✅ Submit Your Form")

if st.button("📨 Submit"):
    form_data = {
        "Role_Type": role_type,
        "Name": name,
        "Email": email,
        "Phone": phone,
        "Location": location,
        "Country": country,
        "State": state,
        "Education": highest_education,
        "Specialisation": specialisation,
        "University": university,
        "CGPA/Percentage": cgpa,
        "Experience (Years)": years_exp,
        "Role": current_role,
        "Organisation": organisation,
        "Serving Notice Period": notice_status,
        "Last Working Day": str(last_working_day) if notice_status == "Yes" else None,
        "Notice Period Days": notice_period_days if notice_status == "No" else None,
        "Skills": skills,
        "Languages Known": languages,
        "Tech_Experience": role_tech_experience
    }

    st.success("🎉 Form submitted successfully!")
    st.json(form_data)

    with open("developer_submission.json", "w") as f:
        import json
        json.dump(form_data, f, indent=4)
    st.info("Your response has been saved locally as `developer_submission.json` ✅")

st.markdown('</div>', unsafe_allow_html=True)
st.caption("© 2025 Developer Portal | Built with ❤️ using Streamlit")
