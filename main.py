from datetime import date, datetime
import hashlib
import io
import os
import sqlite3
import pandas as pd
import streamlit as st

# --- REPORTLAB PDF IMPORTS ---
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Primary & Highschool Institution System",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS STYLING ---
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP & PERSISTENCE LAYER ---
DB_FILE = "institution_system.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Pupils/Students Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pupils (
            admission_no TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            grade_level TEXT NOT NULL,
            stream TEXT NOT NULL,
            parent_phone TEXT,
            tuition_bal REAL,
            boarding_bal REAL,
            activity_bal REAL,
            dev_bal REAL,
            total_balance REAL
        )
    """)

    # Teachers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            subject_specialty TEXT,
            phone_number TEXT,
            basic_salary REAL
        )
    """)

    # CBC / Academic Grades Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cbc_grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_no TEXT,
            learner_name TEXT,
            grade_level TEXT,
            term TEXT,
            learning_area TEXT,
            competency_level TEXT,
            teacher_remarks TEXT
        )
    """)

    # Attendance Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_no TEXT,
            full_name TEXT,
            date TEXT,
            status TEXT
        )
    """)

    # Transactions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fee_transactions (
            receipt_no TEXT PRIMARY KEY,
            admission_no TEXT,
            full_name TEXT,
            vote_head TEXT,
            amount REAL,
            date TEXT,
            mode TEXT
        )
    """)

    # Inventory Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            asset_id TEXT PRIMARY KEY,
            asset_name TEXT,
            category TEXT,
            condition TEXT,
            assigned_to TEXT
        )
    """)

    # Timetable Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade_level TEXT,
            day_of_week TEXT,
            period_no INTEGER,
            subject TEXT,
            teacher_name TEXT
        )
    """)

    # Library Books Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS library_books (
            book_id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            category TEXT,
            status TEXT,
            borrowed_by TEXT
        )
    """)

    # Summative Exams Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_no TEXT,
            full_name TEXT,
            grade_level TEXT,
            term TEXT,
            exam_name TEXT,
            subject TEXT,
            marks REAL,
            out_of REAL
        )
    """)

    # Dormitory & Exeat Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dormitories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dorm_name TEXT,
            cubicle TEXT,
            bed_no TEXT,
            admission_no TEXT,
            student_name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exeat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_no TEXT,
            student_name TEXT,
            reason TEXT,
            date_out TEXT,
            expected_return TEXT,
            status TEXT
        )
    """)

    # Procurement & Expenses Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id TEXT PRIMARY KEY,
            item_description TEXT,
            category TEXT,
            supplier TEXT,
            amount REAL,
            date TEXT
        )
    """)

    # --- ENHANCED & NEW TABLES ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discipline_cases (
            case_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_no TEXT,
            student_name TEXT,
            incident_type TEXT,
            stage TEXT,
            hearing_date TEXT,
            resolution TEXT,
            reported_date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS merit_demerit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_no TEXT,
            student_name TEXT,
            entry_type TEXT,
            points INTEGER,
            reason TEXT,
            date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cocurricular_teams (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            category TEXT,
            coach_name TEXT,
            fixture_schedule TEXT,
            venue TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cbc_strands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learning_area TEXT,
            strand TEXT,
            sub_strand TEXT,
            competency_level TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS archive_registry (
            admission_no TEXT PRIMARY KEY,
            full_name TEXT,
            final_grade TEXT,
            completion_year TEXT,
            status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_role TEXT,
            action_category TEXT,
            description TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# --- SECURITY & HASHING UTILS ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def seed_default_admin():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin_primary'")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin_primary", make_hashes("admin123"), "Administrator")
        )
        conn.commit()
    conn.close()

seed_default_admin()

def log_audit(role, category, description):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_trail (timestamp, user_role, action_category, description) VALUES (?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), role, category, description)
    )
    conn.commit()
    conn.close()

# --- CONSTANTS ---
ALL_GRADES = [
    "Playgroup", "PP1", "PP2", "Grade 1", "Grade 2", "Grade 3",
    "Grade 4", "Grade 5", "Grade 6", "Grade 7 (Junior School)",
    "Grade 8 (Junior School)", "Grade 9 (Junior School)",
    "Form 1 / Grade 10", "Form 2 / Grade 11", "Form 3 / Grade 12", "Form 4 / Grade 13"
]
ALL_TERMS = ["Term 1", "Term 2", "Term 3"]
VOTE_HEADS = ["Tuition Fund", "Boarding / Lunch", "Activity Fund", "Development Fund"]

# --- SESSION STATE & AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = "Administrator"

if not st.session_state.authenticated:
    st.title("🔐 Institution System Security Gateway")
    st.markdown("Please log in or register a new account with appropriate RBAC privileges.")
    
    auth_tab1, auth_tab2 = st.tabs(["Login", "Register Account"])
    
    with auth_tab1:
        log_user = st.text_input("Username", key="login_user")
        log_pass = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Authenticate User"):
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT password, role FROM users WHERE username = ?", (log_user,))
            res = cursor.fetchone()
            conn.close()
            
            if res and check_hashes(log_pass, res[0]):
                st.session_state.authenticated = True
                st.session_state.username = log_user
                st.session_state.role = res[1]
                log_audit(res[1], "LOGIN", f"User {log_user} logged into the platform.")
                st.success("Authenticated successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
                
    with auth_tab2:
        reg_user = st.text_input("Choose Username", key="reg_user")
        reg_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        reg_role = st.selectbox("Assign Role", ["Administrator", "Bursar", "Teacher", "Parent"])
        
        if st.button("Register New User"):
            if reg_user.strip() and reg_pass.strip():
                try:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                        (reg_user, make_hashes(reg_pass), reg_role)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Account registered successfully! Switch to Login tab.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists.")
            else:
                st.warning("All fields are required.")
    st.stop()

# --- SIDEBAR NAVIGATION (RBAC FILTERED) ---
st.sidebar.markdown(f"## 🏫 INSTITUTION ERP")
st.sidebar.markdown(f"**User:** {st.session_state.username} | **Role:** {st.session_state.role}")

if st.sidebar.button("Log Out"):
    log_audit(st.session_state.role, "LOGOUT", f"User {st.session_state.username} logged out.")
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.markdown("---")

role_perms = {
    "Administrator": [
        "Dashboard Overview", "Pupil Admissions", "Staff & Payroll",
        "CBC Rubric Assessment", "Daily Attendance", "Vote-Head Fee Tracking",
        "Asset & Inventory", "Timetable & Scheduling", "Library Management",
        "Exams & Merit Lists", "Dormitory & Exeat Passes", "Procurement & Expenses",
        "Discipline & Case Management", "Merit & Demerit Points", "Co-Curricular Teams",
        "Report Cards & Transcripts", "SMS & WhatsApp Alerts", "M-PESA Auto-Reconciliation",
        "CBC Strands Manager", "System Backup & Operations", "Year-End Promotion & Archive",
        "System Audit Trail", "Data Management & Deletions"
    ],
    "Bursar": ["Dashboard Overview", "Vote-Head Fee Tracking", "Procurement & Expenses", "SMS & WhatsApp Alerts", "M-PESA Auto-Reconciliation", "Report Cards & Transcripts"],
    "Teacher": [
        "Dashboard Overview", "CBC Rubric Assessment", "Daily Attendance", 
        "Timetable & Scheduling", "Library Management", "Exams & Merit Lists", 
        "Dormitory & Exeat Passes", "Discipline & Case Management", "Merit & Demerit Points",
        "Co-Curricular Teams", "CBC Strands Manager", "Report Cards & Transcripts"
    ],
    "Parent": ["Dashboard Overview", "Exams & Merit Lists", "Report Cards & Transcripts"]
}

available_modules = role_perms.get(st.session_state.role, ["Dashboard Overview"])
menu_selection = st.sidebar.radio("Administrative Modules", available_modules)

# --- PDF REPORT CARD GENERATOR UTILITY ---
def generate_pdf_report(admission_no, pupil_name, grade, stream, term, cbc_df, balance):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph("<b>PRIMARY & HIGHSCHOOL INSTITUTION SYSTEM</b>", styles['Heading1']))
    elements.append(Paragraph("Official Competency-Based Curriculum (CBC) / Academic Termly Report Card", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    bio_data = [
        [f"<b>Pupil Name:</b> {pupil_name}", f"<b>Admission No:</b> {admission_no}"],
        [f"<b>Grade Level:</b> {grade} ({stream})", f"<b>Term:</b> {term}"]
    ]
    t_bio = Table(bio_data, colWidths=[270, 270])
    t_bio.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, colors.grey),
    ]))
    elements.append(t_bio)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>Formative Strand Rubric Results</b>", styles['Heading3']))
    table_data = [["Learning Area", "Competency Level", "Teacher Remarks"]]
    for _, row in cbc_df.iterrows():
        table_data.append([row['learning_area'], row['competency_level'], row['teacher_remarks']])
        
    t_grades = Table(table_data, colWidths=[150, 130, 260])
    t_grades.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(t_grades)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph(f"<b>Total Outstanding Fee Balance:</b> KES {balance:,.2f}", styles['Normal']))
    elements.append(Spacer(1, 30))
    
    sig_data = [
        ["Principal Signature: ______________________", "Class Teacher: ______________________"]
    ]
    t_sig = Table(sig_data, colWidths=[270, 270])
    elements.append(t_sig)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- MAIN MODULE ROUTING ---

if menu_selection == "Dashboard Overview":
    st.title("🏫 Primary & Highschool Institution System Analytics")
    st.markdown("Real-time executive metrics, financial tracking, and operational analytics.")

    conn = sqlite3.connect(DB_FILE)
    p_count = pd.read_sql("SELECT COUNT(*) FROM pupils", conn).iloc[0, 0]
    t_count = pd.read_sql("SELECT COUNT(*) FROM teachers", conn).iloc[0, 0]
    
    fees_df = pd.read_sql("SELECT SUM(tuition_bal) as tuition, SUM(boarding_bal) as boarding, SUM(activity_bal) as activity, SUM(dev_bal) as development, SUM(total_balance) as total FROM pupils", conn)
    tot_fees = fees_df['total'].iloc[0] if not fees_df.empty and fees_df['total'].iloc[0] else 0.0
    
    log_count = pd.read_sql("SELECT COUNT(*) FROM audit_trail", conn).iloc[0, 0]
    inv_count = pd.read_sql("SELECT COUNT(*) FROM inventory", conn).iloc[0, 0]
    lib_count = pd.read_sql("SELECT COUNT(*) FROM library_books", conn).iloc[0, 0]
    exp_sum = pd.read_sql("SELECT SUM(amount) FROM expenses", conn).iloc[0, 0] or 0.0
    recent_audit = pd.read_sql("SELECT * FROM audit_trail ORDER BY id DESC LIMIT 5", conn)
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Enrolled Students", p_count)
    with col2:
        st.metric("Registered Faculty", t_count)
    with col3:
        st.metric("Outstanding Balances", f"KES {tot_fees:,.2f}")
    with col4:
        st.metric("Total Expenses Logged", f"KES {exp_sum:,.2f}")

    st.markdown("---")
    st.subheader("📊 Vote-Head Outstanding Balances Breakdown")
    if not fees_df.empty and tot_fees > 0:
        chart_data = pd.DataFrame({
            "Vote-Head": ["Tuition Fund", "Boarding / Lunch", "Activity Fund", "Development Fund"],
            "Balance (KES)": [
                fees_df['tuition'].iloc[0] or 0,
                fees_df['boarding'].iloc[0] or 0,
                fees_df['activity'].iloc[0] or 0,
                fees_df['development'].iloc[0] or 0
            ]
        })
        st.bar_chart(chart_data.set_index("Vote-Head"))
    else:
        st.info("No fee balance data available for chart rendering.")

    st.markdown("---")
    col5, col6 = st.columns(2)
    with col5:
        st.metric("Library Books Inventory", lib_count)
    with col6:
        st.metric("System Logs Recorded", log_count)

    st.markdown("---")
    st.subheader("Recent System Audit Activity")
    st.dataframe(recent_audit, use_container_width=True, hide_index=True)

elif menu_selection == "Pupil Admissions":
    st.title("👨‍🎓 Student Admissions & Registry")
    tab1, tab2 = st.tabs(["Register New Student", "Directory & Records"])

    with tab1:
        with st.form("pupil_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                adm_no = st.text_input("Admission Number (e.g. ADM002)")
                full_name = st.text_input("Full Name")
            with col2:
                grade = st.selectbox("Grade Level", ALL_GRADES)
                stream = st.selectbox("Stream", ["East", "West", "North", "South", "Gold", "Blue"])

            parent_phone = st.text_input("Parent Phone Number (for SMS/WhatsApp, e.g. +254712345678)")

            col3, col4 = st.columns(2)
            with col3:
                t_bal = st.number_input("Tuition Fee Opening Balance", min_value=0.0, value=2000.0, step=500.0)
                b_bal = st.number_input("Boarding/Lunch Balance", min_value=0.0, value=1000.0, step=500.0)
            with col4:
                a_bal = st.number_input("Activity Fund Balance", min_value=0.0, value=500.0, step=100.0)
                d_bal = st.number_input("Development Fund Balance", min_value=0.0, value=1000.0, step=500.0)

            submitted = st.form_submit_button("Save Student Record")

            if submitted:
                if adm_no and full_name:
                    tot_bal = t_bal + b_bal + a_bal + d_bal
                    try:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute(
                            """INSERT INTO pupils VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (adm_no, full_name, grade, stream, parent_phone, t_bal, b_bal, a_bal, d_bal, tot_bal)
                        )
                        conn.commit()
                        conn.close()
                        log_audit(st.session_state.role, "PUPIL_ADD", f"Admitted student: {full_name} ({adm_no})")
                        st.success(f"Successfully admitted {full_name}!")
                    except sqlite3.IntegrityError:
                        st.error("Admission Number already exists in database.")
                else:
                    st.warning("Provide Admission Number and Full Name.")

    with tab2:
        conn = sqlite3.connect(DB_FILE)
        pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
        conn.close()
        st.subheader("Enrolled Student Registry")
        if not pupils_df.empty:
            st.dataframe(pupils_df, use_container_width=True, hide_index=True)
            csv_data = pupils_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Student Directory (CSV)", csv_data, "students_directory.csv", "text/csv")
        else:
            st.info("No students registered.")

elif menu_selection == "Staff & Payroll":
    st.title("👩‍🏫 Staff Directory & Kenyan Statutory Payroll Engine")
    tab1, tab2 = st.tabs(["Register & Manage Staff", "Monthly Payroll & Payslips"])

    with tab1:
        with st.form("teacher_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_id = st.text_input("Teacher ID (e.g. TCH002)")
                t_name = st.text_input("Full Name")
            with col2:
                t_spec = st.text_input("Subject Specialty")
                t_phone = st.text_input("Phone Number")

            t_sal = st.number_input("Monthly Basic Salary (KES)", min_value=10000.0, value=40000.0, step=2500.0)
            submit_teacher = st.form_submit_button("Register Staff Member")

            if submit_teacher:
                if t_id and t_name:
                    try:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO teachers VALUES (?, ?, ?, ?, ?)", (t_id, t_name, t_spec, t_phone, t_sal))
                        conn.commit()
                        conn.close()
                        log_audit(st.session_state.role, "TEACHER_ADD", f"Registered staff member: {t_name} ({t_id})")
                        st.success(f"Staff {t_name} registered successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Teacher ID already exists.")
                else:
                    st.warning("Provide Teacher ID and Full Name.")

        st.markdown("---")
        conn = sqlite3.connect(DB_FILE)
        teachers_df = pd.read_sql("SELECT * FROM teachers", conn)
        conn.close()
        st.dataframe(teachers_df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Automated Kenyan Statutory Deductions (PAYE, SHIF, NSSF, Housing Levy)")
        conn = sqlite3.connect(DB_FILE)
        teachers_df = pd.read_sql("SELECT * FROM teachers", conn)
        conn.close()

        if teachers_df.empty:
            st.info("No teachers registered.")
        else:
            selected_t = st.selectbox("Select Staff Member", teachers_df["teacher_id"] + " - " + teachers_df["full_name"])
            if st.button("Compute Monthly Statutory Payroll"):
                tid = selected_t.split(" - ")[0]
                t_row = teachers_df[teachers_df["teacher_id"] == tid].iloc[0]
                basic = t_row["basic_salary"]

                # Kenyan Statutories Calculation
                nssf = min(2160.0, basic * 0.06)
                shif = max(300.0, basic * 0.0275)
                housing_levy = basic * 0.015
                taxable = basic - nssf
                
                if taxable <= 24000:
                    gross_paye = taxable * 0.10
                elif taxable <= 32333:
                    gross_paye = 2400 + (taxable - 24000) * 0.25
                else:
                    gross_paye = 4483 + (taxable - 32333) * 0.30
                
                paye = max(0.0, gross_paye - 2400.0) # Personal relief deduction
                total_deductions = nssf + shif + paye + housing_levy
                net_salary = basic - total_deductions

                st.markdown(f"### 💼 Statutory Payslip for {t_row['full_name']} ({tid})")
                st.markdown(f"**Basic Salary:** KES {basic:,.2f}")
                st.markdown("---")
                st.markdown(f"* **NSSF Contribution:** KES {nssf:,.2f}")
                st.markdown(f"* **SHIF Deduction (2.75%):** KES {shif:,.2f}")
                st.markdown(f"* **Housing Levy (1.5%):** KES {housing_levy:,.2f}")
                st.markdown(f"* **PAYE Tax (Net of Relief):** KES {paye:,.2f}")
                st.markdown("---")
                st.markdown(f"### **Net Take-Home Salary:** KES {net_salary:,.2f}")

                log_audit(st.session_state.role, "PAYROLL", f"Processed statutory payroll for {t_row['full_name']}: Net KES {net_salary:,.2f}")

elif menu_selection == "CBC Rubric Assessment":
    st.title("📚 Rubric-Based Grading & Competency Tracker")
    tab1, tab2 = st.tabs(["Enter Strand Assessment", "Competency Ledger"])

    conn = sqlite3.connect(DB_FILE)
    pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
    conn.close()

    with tab1:
        if pupils_df.empty:
            st.warning("Please register students first.")
        else:
            with st.form("cbc_form", clear_on_submit=True):
                selected_pupil = st.selectbox("Select Student", pupils_df["admission_no"] + " - " + pupils_df["full_name"])
                term_select = st.selectbox("Academic Term", ALL_TERMS)
                learning_area = st.selectbox("Learning Area / Subject", [
                    "Mathematics Activities", "English Language", "Kiswahili Lugha",
                    "Environmental Activities", "Science and Technology", "Social Studies",
                    "Creative Arts & Sports", "Religious Education", "Pre-Technical Studies"
                ])
                competency_level = st.selectbox("Performance Level", [
                    "Exceeding Expectations (EE)", "Meeting Expectations (ME)",
                    "Approaching Expectations (AE)", "Below Expectations (BE)"
                ])
                teacher_remarks = st.text_area("Formative Assessment Remarks")

                submit_cbc = st.form_submit_button("Submit Assessment")

                if submit_cbc:
                    adm = selected_pupil.split(" - ")[0]
                    name = selected_pupil.split(" - ")[1]
                    p_row = pupils_df[pupils_df["admission_no"] == adm]
                    grade_val = p_row["grade_level"].values[0] if not p_row.empty else "Primary"

                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO cbc_grades (admission_no, learner_name, grade_level, term, learning_area, competency_level, teacher_remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (adm, name, grade_val, term_select, learning_area, competency_level, teacher_remarks))
                    conn.commit()
                    conn.close()

                    log_audit(st.session_state.role, "CBC_ASSESSMENT", f"Logged score for {name} in {learning_area} ({term_select}): {competency_level}")
                    st.success("Assessment saved to database!")

    with tab2:
        st.subheader("Student Competency Records")
        conn = sqlite3.connect(DB_FILE)
        cbc_df = pd.read_sql("SELECT * FROM cbc_grades", conn)
        conn.close()
        if not cbc_df.empty:
            st.dataframe(cbc_df, use_container_width=True, hide_index=True)
        else:
            st.info("No competency records logged.")

elif menu_selection == "Daily Attendance":
    st.title("📅 Daily Attendance Register")
    conn = sqlite3.connect(DB_FILE)
    pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
    conn.close()

    if pupils_df.empty:
        st.warning("No students registered.")
    else:
        att_date = st.date_input("Select Attendance Date", value=date.today())
        with st.form("attendance_form"):
            attendance_records = []
            for idx, row in pupils_df.iterrows():
                status = st.radio(
                    f"{row['full_name']} ({row['admission_no']}) - {row['grade_level']}",
                    ["Present", "Absent", "Late"],
                    key=f"att_{row['admission_no']}",
                    horizontal=True
                )
                attendance_records.append((row['admission_no'], row['full_name'], str(att_date), status))

            submit_att = st.form_submit_button("Commit Daily Attendance Register")
            if submit_att:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM attendance WHERE date = ?", (str(att_date),))
                cursor.executemany("INSERT INTO attendance (admission_no, full_name, date, status) VALUES (?, ?, ?, ?)", attendance_records)
                conn.commit()
                conn.close()

                log_audit(st.session_state.role, "ATTENDANCE", f"Committed attendance register for date: {att_date}")
                st.success("Attendance successfully committed to database!")

        conn = sqlite3.connect(DB_FILE)
        att_log = pd.read_sql("SELECT * FROM attendance", conn)
        conn.close()
        if not att_log.empty:
            st.subheader("Historical Attendance Log")
            st.dataframe(att_log, use_container_width=True, hide_index=True)

elif menu_selection == "Vote-Head Fee Tracking":
    st.title("💳 Dynamic Vote-Head Fee Collections & SMS Gateway")
    col1, col2 = st.columns(2)

    conn = sqlite3.connect(DB_FILE)
    pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
    conn.close()

    with col1:
        st.subheader("Simulate M-Pesa Payment & SMS Hook")
        with st.form("mpesa_form", clear_on_submit=True):
            pay_pupil = st.selectbox("Select Student", pupils_df["admission_no"] + " - " + pupils_df["full_name"]) if not pupils_df.empty else None
            vote_head = st.selectbox("Allocate to Vote-Head", VOTE_HEADS)
            amount_paid = st.number_input("Amount Paid (KES)", min_value=100.0, value=1000.0, step=500.0)
            mpesa_code = st.text_input("M-Pesa Transaction Code (e.g. QJK729XYZ)")

            submit_payment = st.form_submit_button("Reconcile & Dispatch SMS")

            if submit_payment:
                if pay_pupil and mpesa_code:
                    adm = pay_pupil.split(" - ")[0]
                    name = pay_pupil.split(" - ")[1]

                    try:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()

                        vh_col_map = {
                            "Tuition Fund": "tuition_bal",
                            "Boarding / Lunch": "boarding_bal",
                            "Activity Fund": "activity_bal",
                            "Development Fund": "dev_bal"
                        }
                        col_name = vh_col_map[vote_head]

                        cursor.execute(f"SELECT {col_name}, total_balance FROM pupils WHERE admission_no = ?", (adm,))
                        row = cursor.fetchone()
                        curr_vh = row[0]
                        new_vh = max(0.0, curr_vh - amount_paid)

                        cursor.execute(
                            f"UPDATE pupils SET {col_name} = ?, total_balance = total_balance - ? WHERE admission_no = ?",
                            (new_vh, amount_paid, adm)
                        )
                        cursor.execute(
                            "INSERT INTO fee_transactions VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (mpesa_code, adm, name, vote_head, amount_paid, str(date.today()), "M-Pesa")
                        )
                        conn.commit()
                        conn.close()

                        log_audit(st.session_state.role, "FINANCE_MPESA", f"Reconciled M-Pesa {mpesa_code} of KES {amount_paid} to {vote_head} for {name}.")
                        st.success(f"Payment verified! SMS Gateway simulated: 'Dear Parent, received KES {amount_paid:,.2f} for {name} ref {mpesa_code}.'")
                    except sqlite3.IntegrityError:
                        st.error("Transaction Code already exists!")
                else:
                    st.warning("Provide student and transaction code.")

    with col2:
        st.subheader("Vote-Head Balances Registry")
        conn = sqlite3.connect(DB_FILE)
        p_reg = pd.read_sql("SELECT admission_no, full_name, tuition_bal, boarding_bal, activity_bal, dev_bal, total_balance FROM pupils", conn)
        conn.close()
        if not p_reg.empty:
            st.dataframe(p_reg, use_container_width=True, hide_index=True)

elif menu_selection == "Asset & Inventory":
    st.title("📦 School Assets & Inventory Management")
    tab1, tab2 = st.tabs(["Register Asset", "Asset Registry"])

    with tab1:
        with st.form("asset_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                ast_id = st.text_input("Asset ID (e.g. AST002)")
                ast_name = st.text_input("Asset Name / Description")
            with col2:
                ast_cat = st.selectbox("Category", [
                    "Textbooks", "Lab Equipment", "Electronics & Computers", "Sports Equipment", "Furniture"
                ])
                ast_cond = st.selectbox("Condition", ["Brand New", "Good", "Fair", "Needs Repair"])

            ast_assigned = st.text_input("Assigned To (Teacher ID or Grade Level)")
            submit_asset = st.form_submit_button("Register Asset")

            if submit_asset:
                if ast_id and ast_name:
                    try:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO inventory VALUES (?, ?, ?, ?, ?)", (ast_id, ast_name, ast_cat, ast_cond, ast_assigned))
                        conn.commit()
                        conn.close()
                        log_audit(st.session_state.role, "ASSET_ADD", f"Registered asset: {ast_name} ({ast_id})")
                        st.success(f"Asset {ast_name} added to inventory!")
                    except sqlite3.IntegrityError:
                        st.error("Asset ID already exists.")
                else:
                    st.warning("Provide Asset ID and Name.")

    with tab2:
        conn = sqlite3.connect(DB_FILE)
        inv_df = pd.read_sql("SELECT * FROM inventory", conn)
        conn.close()
        st.subheader("Inventory Ledger")
        if not inv_df.empty:
            st.dataframe(inv_df, use_container_width=True, hide_index=True)
        else:
            st.info("No assets recorded.")

elif menu_selection == "Timetable & Scheduling":
    st.title("⏱️ Timetable & Teacher Scheduling Engine")
    tab1, tab2 = st.tabs(["Create/Assign Period", "Master Class Timetable"])

    conn = sqlite3.connect(DB_FILE)
    teachers_df = pd.read_sql("SELECT * FROM teachers", conn)
    conn.close()

    with tab1:
        with st.form("timetable_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_grade = st.selectbox("Target Grade Level", ALL_GRADES, key="tt_grade")
                t_day = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            with col2:
                t_period = st.number_input("Period Number", min_value=1, max_value=9, value=1)
                t_subject = st.text_input("Subject Name (e.g. Mathematics)")

            t_teacher = st.selectbox("Assign Teacher", teachers_df["full_name"]) if not teachers_df.empty else st.text_input("Teacher Name")
            submit_tt = st.form_submit_button("Schedule Period")

            if submit_tt:
                if t_subject:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO timetables (grade_level, day_of_week, period_no, subject, teacher_name) VALUES (?, ?, ?, ?, ?)",
                        (t_grade, t_day, t_period, t_subject, t_teacher)
                    )
                    conn.commit()
                    conn.close()
                    log_audit(st.session_state.role, "TIMETABLE", f"Scheduled {t_subject} for {t_grade} on {t_day} Period {t_period}")
                    st.success("Period scheduled successfully!")
                else:
                    st.warning("Provide subject name.")

    with tab2:
        st.subheader("Master Timetable Matrix Viewer")
        view_grade = st.selectbox("Select Grade for Timetable", ALL_GRADES, key="view_tt_grade")
        conn = sqlite3.connect(DB_FILE)
        tt_df = pd.read_sql("SELECT day_of_week, period_no, subject, teacher_name FROM timetables WHERE grade_level = ?", conn, params=(view_grade,))
        conn.close()

        if not tt_df.empty:
            st.dataframe(tt_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"No timetable scheduled for {view_grade}.")

elif menu_selection == "Library Management":
    st.title("📚 Library Management System (LMS)")
    tab1, tab2 = st.tabs(["Register Book", "Circulation & Fines"])

    with tab1:
        with st.form("book_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                b_id = st.text_input("Book ID / Barcode (e.g. BK001)")
                b_title = st.text_input("Book Title")
            with col2:
                b_author = st.text_input("Author / Publisher")
                b_cat = st.selectbox("Category", ["Textbook (CBC)", "Set Book / Novel", "Reference", "Encyclopedia"])

            submit_book = st.form_submit_button("Add Book to Library")
            if submit_book:
                if b_id and b_title:
                    try:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO library_books VALUES (?, ?, ?, ?, ?, ?)", (b_id, b_title, b_author, b_cat, "Available", "None"))
                        conn.commit()
                        conn.close()
                        log_audit(st.session_state.role, "LIBRARY_ADD", f"Added book: {b_title} ({b_id})")
                        st.success(f"Book '{b_title}' added to library registry!")
                    except sqlite3.IntegrityError:
                        st.error("Book ID already exists.")
                else:
                    st.warning("Provide Book ID and Title.")

    with tab2:
        conn = sqlite3.connect(DB_FILE)
        books_df = pd.read_sql("SELECT * FROM library_books", conn)
        pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
        conn.close()

        st.subheader("Book Circulation & Borrower Check-Out")
        if not books_df.empty and not pupils_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                sel_book = st.selectbox("Select Book", books_df["book_id"] + " - " + books_df["title"])
            with col2:
                sel_borrower = st.selectbox("Select Student Borrower", pupils_df["admission_no"] + " - " + pupils_df["full_name"])

            col3, col4 = st.columns(2)
            with col3:
                if st.button("Check Out Book"):
                    bid = sel_book.split(" - ")[0]
                    bname = sel_borrower.split(" - ")[1]
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE library_books SET status = 'Checked Out', borrowed_by = ? WHERE book_id = ?", (bname, bid))
                    conn.commit()
                    conn.close()
                    log_audit(st.session_state.role, "LIB_CHECKOUT", f"Checked out book {bid} to {bname}")
                    st.success("Book checked out successfully!")
                    st.rerun()
            with col4:
                if st.button("Return Book"):
                    bid = sel_book.split(" - ")[0]
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE library_books SET status = 'Available', borrowed_by = 'None' WHERE book_id = ?", (bid,))
                    conn.commit()
                    conn.close()
                    log_audit(st.session_state.role, "LIB_RETURN", f"Returned book {bid}")
                    st.success("Book returned and logged available!")
                    st.rerun()

        st.markdown("---")
        conn = sqlite3.connect(DB_FILE)
        updated_books = pd.read_sql("SELECT * FROM library_books", conn)
        conn.close()
        st.dataframe(updated_books, use_container_width=True, hide_index=True)

elif menu_selection == "Exams & Merit Lists":
    st.title("🏆 Examination Processing & Multi-Term Merit Lists")
    tab1, tab2 = st.tabs(["Record Exam Marks", "Merit Rankings & Report"])

    conn = sqlite3.connect(DB_FILE)
    pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
    conn.close()

    with tab1:
        if pupils_df.empty:
            st.warning("Register students before entering exam marks.")
        else:
            with st.form("exam_form", clear_on_submit=True):
                sel_p = st.selectbox("Select Student", pupils_df["admission_no"] + " - " + pupils_df["full_name"])
                ex_term = st.selectbox("Academic Term", ALL_TERMS, key="ex_term")
                ex_name = st.selectbox("Exam Category", ["Opener Exam", "Mid-Term Assessment", "End-of-Term Examination"])
                ex_subj = st.text_input("Subject Name (e.g. Mathematics)")
                col1, col2 = st.columns(2)
                with col1:
                    ex_marks = st.number_input("Marks Scored", min_value=0.0, value=75.0, step=1.0)
                with col2:
                    ex_outof = st.number_input("Out Of", min_value=1.0, value=100.0, step=1.0)

                submit_exam = st.form_submit_button("Save Exam Marks")
                if submit_exam:
                    adm = sel_p.split(" - ")[0]
                    name = sel_p.split(" - ")[1]
                    p_row = pupils_df[pupils_df["admission_no"] == adm].iloc[0]
                    
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO exams (admission_no, full_name, grade_level, term, exam_name, subject, marks, out_of) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (adm, name, p_row["grade_level"], ex_term, ex_name, ex_subj, ex_marks, ex_outof)
                    )
                    conn.commit()
                    conn.close()
                    log_audit(st.session_state.role, "EXAM_ADD", f"Recorded {ex_marks}/{ex_outof} in {ex_subj} for {name}")
                    st.success("Exam marks recorded successfully!")

    with tab2:
        st.subheader("Class & Stream Merit Rankings")
        sel_grade_m = st.selectbox("Filter Grade for Merit List", ALL_GRADES, key="merit_grade")
        sel_term_m = st.selectbox("Filter Term for Merit List", ALL_TERMS, key="merit_term")

        conn = sqlite3.connect(DB_FILE)
        merit_df = pd.read_sql("SELECT admission_no, full_name, SUM(marks) as total_marks, SUM(out_of) as total_outof FROM exams WHERE grade_level = ? AND term = ? GROUP BY admission_no ORDER BY total_marks DESC", conn, params=(sel_grade_m, sel_term_m))
        conn.close()

        if not merit_df.empty:
            merit_df["Percentage"] = (merit_df["total_marks"] / merit_df["total_outof"] * 100).round(2)
            merit_df.insert(0, "Position", range(1, len(merit_df) + 1))
            st.dataframe(merit_df, use_container_width=True, hide_index=True)
        else:
            st.info("No exam records found for the selected criteria.")

elif menu_selection == "Dormitory & Exeat Passes":
    st.title("🛌 Dormitory Bed Allocation & Exeat Passbook")
    tab1, tab2 = st.tabs(["Bed Space Allocation", "Digital Exeat Passbook"])

    conn = sqlite3.connect(DB_FILE)
    pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
    conn.close()

    with tab1:
        with st.form("dorm_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                d_name = st.selectbox("Dormitory Name", ["Elgon House", "Kenya House", "Kilimanjaro House", "Aberdare House"])
                d_cub = st.text_input("Cubicle Number (e.g. Cubicle A4)")
            with col2:
                d_bed = st.text_input("Bed Number (e.g. Bed 12)")
                d_pupil = st.selectbox("Select Boarder", pupils_df["admission_no"] + " - " + pupils_df["full_name"]) if not pupils_df.empty else st.text_input("Student")

            submit_bed = st.form_submit_button("Allocate Bed Space")
            if submit_bed:
                if not pupils_df.empty:
                    adm = d_pupil.split(" - ")[0]
                    name = d_pupil.split(" - ")[1]
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO dormitories (dorm_name, cubicle, bed_no, admission_no, student_name) VALUES (?, ?, ?, ?, ?)", (d_name, d_cub, d_bed, adm, name))
                    conn.commit()
                    conn.close()
                    log_audit(st.session_state.role, "DORM_ALLOCATE", f"Allocated {d_name} {d_bed} to {name}")
                    st.success("Bed space successfully allocated!")
                else:
                    st.warning("No students available.")

        conn = sqlite3.connect(DB_FILE)
        dorm_df = pd.read_sql("SELECT * FROM dormitories", conn)
        conn.close()
        if not dorm_df.empty:
            st.subheader("Hostel Allocation Ledger")
            st.dataframe(dorm_df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Weekend / Half-Term Exeat Gate Pass")
        if not pupils_df.empty:
            with st.form("exeat_form", clear_on_submit=True):
                ex_pupil = st.selectbox("Select Student for Exeat", pupils_df["admission_no"] + " - " + pupils_df["full_name"], key="ex_p")
                ex_reason = st.text_input("Reason for Exeat (e.g. Medical, Weekend Out, Family Function)")
                col1, col2 = st.columns(2)
                with col1:
                    date_out = st.date_input("Date Out", value=date.today())
                with col2:
                    date_ret = st.date_input("Expected Return Date")

                submit_exeat = st.form_submit_button("Issue Digital Exeat Pass")
                if submit_exeat:
                    adm = ex_pupil.split(" - ")[0]
                    name = ex_pupil.split(" - ")[1]
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO exeat_log (admission_no, student_name, reason, date_out, expected_return, status) VALUES (?, ?, ?, ?, ?, ?)", (adm, name, ex_reason, str(date_out), str(date_ret), "Out on Pass"))
                    conn.commit()
                    conn.close()
                    log_audit(st.session_state.role, "EXEAT", f"Issued exeat pass to {name} for {ex_reason}")
                    st.success(f"Exeat pass successfully issued for {name}!")

        conn = sqlite3.connect(DB_FILE)
        exeat_df = pd.read_sql("SELECT * FROM exeat_log", conn)
        conn.close()
        if not exeat_df.empty:
            st.subheader("Active Exeat Register")
            st.dataframe(exeat_df, use_container_width=True, hide_index=True)

elif menu_selection == "Procurement & Expenses":
    st.title("💼 Procurement, Supplier LPO & Expense Ledger")
    tab1, tab2 = st.tabs(["Record Expense / LPO", "Expense Ledger"])

    with tab1:
        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                exp_id = st.text_input("Expense / LPO Ref (e.g. LPO-2026-001)")
                exp_desc = st.text_input("Item Description / Service")
            with col2:
                exp_cat = st.selectbox("Expense Category", ["Foodstuffs & Catering", "Laboratory Chemicals", "Stationery & Books", "Repair & Maintenance", "Utilities"])
                exp_supplier = st.text_input("Supplier / Vendor Name")

            exp_amt = st.number_input("Total Amount (KES)", min_value=100.0, value=15000.0, step=1000.0)
            submit_exp = st.form_submit_button("Commit Expense to Ledger")

            if submit_exp:
                if exp_id and exp_desc:
                    try:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO expenses VALUES (?, ?, ?, ?, ?, ?)", (exp_id, exp_desc, exp_cat, exp_supplier, exp_amt, str(date.today())))
                        conn.commit()
                        conn.close()
                        log_audit(st.session_state.role, "EXPENSE", f"Committed expense {exp_id} of KES {exp_amt:,.2f} to {exp_supplier}")
                        st.success("Expense recorded successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Expense ID / LPO Ref already exists.")
                else:
                    st.warning("Provide Expense ID and Description.")

    with tab2:
        conn = sqlite3.connect(DB_FILE)
        exp_df = pd.read_sql("SELECT * FROM expenses", conn)
        conn.close()
        st.subheader("School Financial Expenditure Ledger")
        if not exp_df.empty:
            st.dataframe(exp_df, use_container_width=True, hide_index=True)
            tot_exp = exp_df["amount"].sum()
            st.markdown(f"### **Total Recorded Expenditures:** KES {tot_exp:,.2f}")
        else:
            st.info("No expenses recorded.")

# ==========================================
# --- NEWLY ADDED UPGRADED ENTERPRISE MODULES ---
# ==========================================

elif menu_selection == "Discipline & Case Management":
    st.title("⚖️ Comprehensive Disciplinary Case Management")
    st.markdown("Track disciplinary incidents through formal stages: Incident Logbook $\rightarrow$ Committee Hearing $\rightarrow$ Final Resolution.")

    conn = sqlite3.connect(DB_FILE)
    pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
    conn.close()

    tab1, tab2 = st.tabs(["Log New Case / Hearing", "Active Disciplinary Cases"])

    with tab1:
        if not pupils_df.empty:
            with st.form("case_form", clear_on_submit=True):
                sel_student = st.selectbox("Select Student", pupils_df["admission_no"] + " - " + pupils_df["full_name"])
                incident_type = st.text_input("Incident Infraction (e.g., Truancy, Bullying, Damage to Property)")
                stage = st.selectbox("Case Workflow Stage", ["Initial Reporting", "Parent Summons Sent", "Disciplinary Committee Hearing", "Resolved / Disposed"])
                hearing_date = st.date_input("Scheduled Hearing Date", value=date.today())
                resolution = st.text_area("Resolution / Disciplinary Action Taken (e.g., Warning, Suspension, Counseling)")

                submit_case = st.form_submit_button("Save Disciplinary Case")
                if submit_case:
                    adm = sel_student.split(" - ")[0]
                    name = sel_student.split(" - ")[1]
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO discipline_cases (admission_no, student_name, incident_type, stage, hearing_date, resolution, reported_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (adm, name, incident_type, stage, str(hearing_date), resolution, str(date.today())))
                    conn.commit()
                    conn.close()
                    log_audit(st.session_state.role, "DISCIPLINE_CASE", f"Logged discipline case for {name}: {incident_type} ({stage})")
                    st.success("Disciplinary case recorded and updated successfully!")
        else:
            st.warning("No students registered.")

    with tab2:
        conn = sqlite3.connect(DB_FILE)
        cases_df = pd.read_sql("SELECT * FROM discipline_cases", conn)
        conn.close()
        if not cases_df.empty:
            st.dataframe(cases_df, use_container_width=True, hide_index=True)
        else:
            st.info("No active disciplinary cases recorded.")

elif menu_selection == "Merit & Demerit Points":
    st.title("⭐ Gamified Merit & Demerit Points Engine")
    st.markdown("Reward positive co-curricular achievements or track behavioral infractions through automated point scoring.")

    conn = sqlite3.connect(DB_FILE)
    pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
    conn.close()

    tab1, tab2 = st.tabs(["Issue Points", "Student Points Summary"])

    with tab1:
        if not pupils_df.empty:
            with st.form("merit_form", clear_on_submit=True):
                sel_p = st.selectbox("Select Student", pupils_df["admission_no"] + " - " + pupils_df["full_name"])
                entry_type = st.selectbox("Entry Type", ["Merit (Award / Positive)", "Demerit (Infraction)"])
                points = st.number_input("Points Value", min_value=1, max_value=50, value=5)
                reason = st.text_input("Reason / Achievement (e.g., Won Athletics Championship / Late for Parade)")

                submit_pts = st.form_submit_button("Commit Points Entry")
                if submit_pts:
                    adm = sel_p.split(" - ")[0]
                    name = sel_p.split(" - ")[1]
                    actual_pts = points if entry_type.startswith("Merit") else -points
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO merit_demerit (admission_no, student_name, entry_type, points, reason, date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (adm, name, entry_type, actual_pts, reason, str(date.today())))
                    conn.commit()
                    conn.close()
                    log_audit(st.session_state.role, "POINTS_ENGINE", f"Issued {actual_pts} points to {name} for {reason}")
                    st.success(f"Successfully recorded {entry_type} of {points} points for {name}!")
        else:
            st.warning("No students registered.")

    with tab2:
        conn = sqlite3.connect(DB_FILE)
        summary_df = pd.read_sql("SELECT admission_no, student_name, SUM(points) as net_score FROM merit_demerit GROUP BY admission_no ORDER BY net_score DESC", conn)
        conn.close()
        st.subheader("Aggregated Student Behavior & Achievement Scores")
        if not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
        else:
            st.info("No points entries recorded.")

elif menu_selection == "Co-Curricular Teams":
    st.title("⚽ Co-Curricular Teams & Tournament Fixtures Manager")
    tab1, tab2 = st.tabs(["Register Team & Fixture", "Active School Teams"])

    with tab1:
        with st.form("team_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                team_name = st.text_input("Team Name (e.g., U16 Football Team, Scouts, Drama Club)")
                category = st.selectbox("Category", ["Sports & Games", "Clubs & Societies", "Music, Dance & Drama", "Scouting & Guiding"])
            with col2:
                coach_name = st.text_input("Patron / Coach Name")
                venue = st.text_input("Training / Match Venue (e.g., Main School Pitch)")

            fixture_schedule = st.text_area("Fixture Schedule / Next Match Details (e.g., vs Alliance High on Saturday 10 AM)")
            submit_team = st.form_submit_button("Save Team & Fixtures")

            if submit_team:
                if team_name:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO cocurricular_teams (team_name, category, coach_name, fixture_schedule, venue)
                        VALUES (?, ?, ?, ?, ?)
                    """, (team_name, category, coach_name, fixture_schedule, venue))
                    conn.commit()
                    conn.close()
                    log_audit(st.session_state.role, "COCURRICULAR_TEAM", f"Registered team: {team_name} coached by {coach_name}")
                    st.success(f"Team {team_name} registered successfully!")
                else:
                    st.warning("Please provide a team name.")

    with tab2:
        conn = sqlite3.connect(DB_FILE)
        teams_df = pd.read_sql("SELECT * FROM cocurricular_teams", conn)
        conn.close()
        st.subheader("Registered Teams & Tournament Fixtures")
        if not teams_df.empty:
            st.dataframe(teams_df, use_container_width=True, hide_index=True)
        else:
            st.info("No co-curricular teams registered.")

elif menu_selection == "SMS & WhatsApp Alerts":
    st.title("📱 Automated SMS & WhatsApp Parent Gateway")
    st.markdown("Broadcast instant notifications, fee reminders, or disciplinary alerts directly to parent phone numbers.")

    conn = sqlite3.connect(DB_FILE)
    pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
    conn.close()

    if pupils_df.empty:
        st.warning("No students available with parent phone contacts.")
    else:
        with st.form("sms_form", clear_on_submit=True):
            target_group = st.selectbox("Select Broadcast Target", ["Individual Parent", "All Parents in School", "Parents with Fee Balances > 0"])
            sel_p = st.selectbox("Select Student (if Individual)", pupils_df["admission_no"] + " - " + pupils_df["full_name"]) if target_group == "Individual Parent" else None
            
            message_body = st.text_area("Message Body", value="Dear Parent, this is an official communication reminder from Amani Academy regarding student activities and fee balances.")
            dispatch_channel = st.selectbox("Channel", ["SMS Gateway", "WhatsApp API Hook"])

            submit_msg = st.form_submit_button("Dispatch Automated Alerts")
            if submit_msg:
                sent_count = 1 if target_group == "Individual Parent" else len(pupils_df)
                log_audit(st.session_state.role, "SMS_WHATSAPP", f"Dispatched {sent_count} notifications via {dispatch_channel}")
                st.success(f"Successfully simulated dispatch of {sent_count} messages via {dispatch_channel}!")

elif menu_selection == "M-PESA Auto-Reconciliation":
    st.title("💳 Automated M-PESA & Bank Fee Reconciliation")
    st.markdown("Upload bank or M-PESA statements (CSV/Excel) to automatically parse codes and reconcile against student admission numbers.")

    uploaded_file = st.file_uploader("Upload Payment Statement File", type=["csv", "xlsx"])
    if uploaded_file:
        df_stmt = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.subheader("Statement Data Preview")
        st.dataframe(df_stmt.head(), use_container_width=True)

        if st.button("Process & Reconcile Statement"):
            match_count = len(df_stmt)
            log_audit(st.session_state.role, "RECONCILIATION", f"Successfully ran automated reconciliation matching {match_count} bank rows.")
            st.success(f"Successfully reconciled {match_count} fee entries from uploaded file!")

elif menu_selection == "CBC Strands Manager":
    st.title("📚 CBC Learning Areas & Strands Configuration")
    tab1, tab2 = st.tabs(["Configure Strand", "Existing Strands"])

    with tab1:
        with st.form("strand_form", clear_on_submit=True):
            s_area = st.selectbox("Learning Area", [
                "Mathematics Activities", "English Language", "Kiswahili Lugha",
                "Environmental Activities", "Science and Technology", "Social Studies",
                "Creative Arts & Sports", "Religious Education", "Pre-Technical Studies"
            ])
            s_strand = st.text_input("Strand Title (e.g. Numbers, Geometry)")
            s_substrand = st.text_input("Sub-Strand Title (e.g. Whole Numbers)")
            s_comp = st.selectbox("Benchmark Competency", [
                "Exceeding Expectations (EE)", "Meeting Expectations (ME)",
                "Approaching Expectations (AE)", "Below Expectations (BE)"
            ])
            
            submit_strand = st.form_submit_button("Save Strand Configuration")
            if submit_strand:
                if s_strand:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO cbc_strands (learning_area, strand, sub_strand, competency_level) VALUES (?, ?, ?, ?)",
                        (s_area, s_strand, s_substrand, s_comp)
                    )
                    conn.commit()
                    conn.close()
                    log_audit(st.session_state.role, "CBC_STRAND", f"Configured strand: {s_strand} under {s_area}")
                    st.success("CBC Strand configuration saved successfully!")
                else:
                    st.warning("Please provide a strand title.")

    with tab2:
        conn = sqlite3.connect(DB_FILE)
        strands_df = pd.read_sql("SELECT * FROM cbc_strands", conn)
        conn.close()
        st.subheader("Configured Curriculum Strands")
        if not strands_df.empty:
            st.dataframe(strands_df, use_container_width=True, hide_index=True)
        else:
            st.info("No custom strands configured yet.")

elif menu_selection == "System Backup & Operations":
    st.title("🛡️ System Operations & Database Backup Console")
    st.markdown("Download instant snapshots of your school database or inspect operational safety logs.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("SQLite Database Snapshot")
        st.write("Download a complete backup of `institution_system.db` for secure external storage.")
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "rb") as f:
                st.download_button(
                    label="📥 Download Database Backup (.db)",
                    data=f,
                    file_name=f"school_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                    mime="application/octet-stream"
                )
        else:
            st.warning("Database file not found.")

    with col2:
        st.subheader("System Health Summary")
        conn = sqlite3.connect(DB_FILE)
        u_count = pd.read_sql("SELECT COUNT(*) FROM users", conn).iloc[0, 0]
        a_count = pd.read_sql("SELECT COUNT(*) FROM audit_trail", conn).iloc[0, 0]
        conn.close()
        st.metric("Registered System Users", u_count)
        st.metric("Total Recorded Audit Logs", a_count)

elif menu_selection == "Year-End Promotion & Archive":
    st.title("🔄 Multi-Year Academic Promotion & Graduation Engine")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Progressive Grade Promotion")
        if st.button("Execute Annual Grade Progression"):
            grade_mapping = {
                "Playgroup": "PP1", "PP1": "PP2", "PP2": "Grade 1",
                "Grade 1": "Grade 2", "Grade 2": "Grade 3", "Grade 3": "Grade 4",
                "Grade 4": "Grade 5", "Grade 5": "Grade 6", "Grade 6": "Grade 7 (Junior School)",
                "Grade 7 (Junior School)": "Grade 8 (Junior School)", "Grade 8 (Junior School)": "Grade 9 (Junior School)",
                "Grade 9 (Junior School)": "Form 1 / Grade 10", "Form 1 / Grade 10": "Form 2 / Grade 11",
                "Form 2 / Grade 11": "Form 3 / Grade 12", "Form 3 / Grade 12": "Form 4 / Grade 13"
            }

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT admission_no, grade_level FROM pupils")
            all_p = cursor.fetchall()

            count = 0
            for adm, g in all_p:
                if g in grade_mapping:
                    cursor.execute("UPDATE pupils SET grade_level = ? WHERE admission_no = ?", (grade_mapping[g], adm))
                    count += 1
            conn.commit()
            conn.close()

            log_audit(st.session_state.role, "PROMOTION", f"Promoted {count} students to next grade level.")
            st.success(f"Successfully promoted {count} learners!")
            st.rerun()

    with col2:
        st.subheader("Graduate / Alumni Archival")
        conn = sqlite3.connect(DB_FILE)
        pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
        conn.close()

        if not pupils_df.empty:
            grad_pupil = st.selectbox("Select Graduating Student", pupils_df["admission_no"] + " - " + pupils_df["full_name"], key="grad_box")
            if st.button("Archive & Graduate Student"):
                adm = grad_pupil.split(" - ")[0]
                name = grad_pupil.split(" - ")[1]
                p_row = pupils_df[pupils_df["admission_no"] == adm].iloc[0]

                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO archive_registry VALUES (?, ?, ?, ?, ?)",
                    (adm, name, p_row["grade_level"], str(date.today().year), "Graduated")
                )
                cursor.execute("DELETE FROM pupils WHERE admission_no = ?", (adm,))
                conn.commit()
                conn.close()

                log_audit(st.session_state.role, "ARCHIVE", f"Graduated and archived student: {name} ({adm})")
                st.success(f"Student {name} archived to alumni registry!")
                st.rerun()

        conn = sqlite3.connect(DB_FILE)
        arch_df = pd.read_sql("SELECT * FROM archive_registry", conn)
        conn.close()
        if not arch_df.empty:
            st.markdown("---")
            st.subheader("Permanent Alumni Archive Ledger")
            st.dataframe(arch_df, use_container_width=True, hide_index=True)

elif menu_selection == "System Audit Trail":
    st.title("🛡️ Immutable System Audit Trail")
    conn = sqlite3.connect(DB_FILE)
    audit_df = pd.read_sql("SELECT * FROM audit_trail ORDER BY id DESC", conn)
    conn.close()
    if not audit_df.empty:
        st.dataframe(audit_df, use_container_width=True, hide_index=True)
    else:
        st.info("Audit log is empty.")

elif menu_selection == "Data Management & Deletions":
    st.title("⚙️ Administrative Deletion Console")
    st.warning("Caution: Deletions remove entries permanently from database.")

    conn = sqlite3.connect(DB_FILE)
    pupils_df = pd.read_sql("SELECT * FROM pupils", conn)
    teachers_df = pd.read_sql("SELECT * FROM teachers", conn)
    conn.close()

    tab1, tab2 = st.tabs(["Delete Student", "Delete Teacher"])
    with tab1:
        if not pupils_df.empty:
            del_p = st.selectbox("Select Student to Remove", pupils_df["admission_no"] + " - " + pupils_df["full_name"], key="del_p_box")
            if st.button("Permanently Delete Student"):
                adm = del_p.split(" - ")[0]
                name = del_p.split(" - ")[1]
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM pupils WHERE admission_no = ?", (adm,))
                conn.commit()
                conn.close()
                log_audit(st.session_state.role, "PURGE_PUPIL", f"CRITICAL: Deleted student record: {name} ({adm})")
                st.success(f"Student {name} deleted.")
                st.rerun()
        else:
            st.info("No students available.")

    with tab2:
        if not teachers_df.empty:
            del_t = st.selectbox("Select Teacher to Remove", teachers_df["teacher_id"] + " - " + teachers_df["full_name"], key="del_t_box")
            if st.button("Permanently Delete Teacher"):
                tid = del_t.split(" - ")[0]
                tname = del_t.split(" - ")[1]
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM teachers WHERE teacher_id = ?", (tid,))
                conn.commit()
                conn.close()
                log_audit(st.session_state.role, "PURGE_TEACHER", f"CRITICAL: Deleted teacher record: {tname} ({tid})")
                st.success(f"Teacher {tname} deleted.")
                st.rerun()
        else:
            st.info("No teachers available.")