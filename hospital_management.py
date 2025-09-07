"""
This is my Hospital Management System
"""

import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import re
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import random
import time

# Set page configuration
st.set_page_config(
    page_title="Hospital Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'patients' not in st.session_state:
    st.session_state.patients = []
if 'doctors' not in st.session_state:
    st.session_state.doctors = []
if 'appointments' not in st.session_state:
    st.session_state.appointments = []
if 'bills' not in st.session_state:
    st.session_state.bills = []
if 'user' not in st.session_state:
    st.session_state.user = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Initialize database
def init_db():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    # Create patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            blood_group TEXT,
            medical_history TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT,
            phone TEXT,
            email TEXT,
            schedule TEXT,
            fee REAL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create appointments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            date TEXT,
            time TEXT,
            reason TEXT,
            status TEXT DEFAULT 'Scheduled',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    ''')
    
    # Create bills table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_fee REAL,
            medicine_fee REAL,
            room_charge REAL,
            other_charges REAL,
            total_amount REAL,
            date TEXT,
            status TEXT DEFAULT 'Pending',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Create users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default admin user if not exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', hashed_password, 'admin')
        )
    
    conn.commit()
    conn.close()

# Load data from database
def load_data():
    conn = sqlite3.connect('hospital.db')
    
    # Load patients
    st.session_state.patients = pd.read_sql_query("SELECT * FROM patients", conn).to_dict('records')
    
    # Load doctors
    st.session_state.doctors = pd.read_sql_query("SELECT * FROM doctors", conn).to_dict('records')
    
    # Load appointments
    st.session_state.appointments = pd.read_sql_query("SELECT * FROM appointments", conn).to_dict('records')
    
    # Load bills
    st.session_state.bills = pd.read_sql_query("SELECT * FROM bills", conn).to_dict('records')
    
    conn.close()

# Initialize database and load data
init_db()
load_data()

# Authentication functions
def login_user(username, password):
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hashed_password)
    )
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        st.session_state.user = {
            'id': user[0],
            'username': user[1],
            'role': user[3]
        }
        st.session_state.logged_in = True
        return True
    return False

def create_user(username, password, role):
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, role)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# Utility functions
def generate_patient_id():
    return f"P{random.randint(10000, 99999)}"

def generate_doctor_id():
    return f"D{random.randint(10000, 99999)}"

def generate_appointment_id():
    return f"A{random.randint(10000, 99999)}"

def generate_bill_id():
    return f"B{random.randint(10000, 99999)}"

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, phone) is not None

# Login page
def login_page():
    st.title("🏥 Hospital Management System")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if login_user(username, password):
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("---")
        st.subheader("Create New Account")
        with st.form("register_form"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            role = st.selectbox("Role", ["staff", "doctor", "admin"])
            register_button = st.form_submit_button("Register")
            
            if register_button:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long")
                elif create_user(new_username, new_password, role):
                    st.success("Account created successfully! Please login.")
                else:
                    st.error("Username already exists")

# Dashboard page
def dashboard_page():
    st.title("🏥 Hospital Management Dashboard")
    
    # Display KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Patients", len(st.session_state.patients))
    
    with col2:
        st.metric("Total Doctors", len(st.session_state.doctors))
    
    with col3:
        st.metric("Today's Appointments", 
                 len([a for a in st.session_state.appointments if a['date'] == datetime.now().strftime('%Y-%m-%d')]))
    
    with col4:
        total_revenue = sum(b['total_amount'] for b in st.session_state.bills if b['status'] == 'Paid')
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    st.markdown("---")
    
    # Recent appointments
    st.subheader("📅 Recent Appointments")
    recent_appointments = st.session_state.appointments[-10:] if st.session_state.appointments else []
    
    if recent_appointments:
        appt_data = []
        for appt in recent_appointments:
            patient = next((p for p in st.session_state.patients if p['id'] == appt['patient_id']), {})
            doctor = next((d for d in st.session_state.doctors if d['id'] == appt['doctor_id']), {})
            
            appt_data.append({
                'ID': appt['id'],
                'Patient': patient.get('name', 'Unknown'),
                'Doctor': doctor.get('name', 'Unknown'),
                'Date': appt['date'],
                'Time': appt['time'],
                'Reason': appt['reason'],
                'Status': appt['status']
            })
        
        appt_df = pd.DataFrame(appt_data)
        st.dataframe(appt_df, use_container_width=True, hide_index=True)
    else:
        st.info("No appointments scheduled yet.")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Patients by Gender")
        if st.session_state.patients:
            gender_counts = pd.DataFrame(st.session_state.patients)['gender'].value_counts()
            fig = px.pie(values=gender_counts.values, names=gender_counts.index, 
                         title="Patient Gender Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No patient data available for chart.")
    
    with col2:
        st.subheader("📈 Revenue Trend (Last 7 Days)")
        if st.session_state.bills:
            bill_df = pd.DataFrame(st.session_state.bills)
            bill_df['date'] = pd.to_datetime(bill_df['date'])
            last_week = datetime.now() - timedelta(days=7)
            recent_bills = bill_df[bill_df['date'] >= last_week]
            
            if not recent_bills.empty:
                revenue_trend = recent_bills.groupby('date')['total_amount'].sum().reset_index()
                fig = px.line(revenue_trend, x='date', y='total_amount', 
                             title="Daily Revenue Trend", labels={'total_amount': 'Revenue ($)'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No revenue data for the last 7 days.")
        else:
            st.info("No billing data available for chart.")

# Patient management page
def patient_management_page():
    st.title("👥 Patient Management")
    
    tab1, tab2, tab3 = st.tabs(["Add Patient", "View Patients", "Search Patients"])
    
    with tab1:
        st.subheader("Add New Patient")
        
        with st.form("patient_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name*")
                age = st.number_input("Age*", min_value=0, max_value=120, value=0)
                gender = st.selectbox("Gender*", ["", "Male", "Female", "Other"])
                phone = st.text_input("Phone Number*")
            
            with col2:
                email = st.text_input("Email")
                blood_group = st.selectbox("Blood Group", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
                address = st.text_area("Address")
            
            medical_history = st.text_area("Medical History")
            
            submitted = st.form_submit_button("Add Patient")
            
            if submitted:
                if not name or not age or not gender or not phone:
                    st.error("Please fill in all required fields (*)")
                elif email and not validate_email(email):
                    st.error("Please enter a valid email address")
                elif not validate_phone(phone):
                    st.error("Please enter a valid phone number")
                else:
                    conn = sqlite3.connect('hospital.db')
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO patients (name, age, gender, address, phone, email, blood_group, medical_history)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (name, age, gender, address, phone, email, blood_group, medical_history))
                    
                    conn.commit()
                    patient_id = cursor.lastrowid
                    conn.close()
                    
                    # Update session state
                    st.session_state.patients.append({
                        'id': patient_id, 'name': name, 'age': age, 'gender': gender,
                        'address': address, 'phone': phone, 'email': email,
                        'blood_group': blood_group, 'medical_history': medical_history
                    })
                    
                    st.success(f"Patient added successfully with ID: {patient_id}")
    
    with tab2:
        st.subheader("Patient Records")
        
        if st.session_state.patients:
            patient_df = pd.DataFrame(st.session_state.patients)
            st.dataframe(patient_df, use_container_width=True, hide_index=True)
        else:
            st.info("No patient records found.")
    
    with tab3:
        st.subheader("Search Patients")
        
        search_option = st.radio("Search by", ["Name", "Phone", "ID"])
        search_query = st.text_input("Search term")
        
        if search_query:
            if search_option == "Name":
                results = [p for p in st.session_state.patients if search_query.lower() in p['name'].lower()]
            elif search_option == "Phone":
                results = [p for p in st.session_state.patients if search_query in p['phone']]
            else:  # ID
                results = [p for p in st.session_state.patients if search_query == str(p['id'])]
            
            if results:
                st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
            else:
                st.warning("No patients found matching your search criteria.")

# Doctor management page
def doctor_management_page():
    st.title("👨‍⚕️ Doctor Management")
    
    tab1, tab2 = st.tabs(["Add Doctor", "View Doctors"])
    
    with tab1:
        st.subheader("Add New Doctor")
        
        with st.form("doctor_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name*")
                specialization = st.text_input("Specialization*")
                phone = st.text_input("Phone Number*")
            
            with col2:
                email = st.text_input("Email")
                fee = st.number_input("Consultation Fee*", min_value=0.0, value=0.0, step=10.0)
                schedule = st.text_input("Schedule (e.g., Mon-Fri 9AM-5PM)*")
            
            submitted = st.form_submit_button("Add Doctor")
            
            if submitted:
                if not name or not specialization or not phone or not fee or not schedule:
                    st.error("Please fill in all required fields (*)")
                elif email and not validate_email(email):
                    st.error("Please enter a valid email address")
                elif not validate_phone(phone):
                    st.error("Please enter a valid phone number")
                else:
                    conn = sqlite3.connect('hospital.db')
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO doctors (name, specialization, phone, email, fee, schedule)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (name, specialization, phone, email, fee, schedule))
                    
                    conn.commit()
                    doctor_id = cursor.lastrowid
                    conn.close()
                    
                    # Update session state
                    st.session_state.doctors.append({
                        'id': doctor_id, 'name': name, 'specialization': specialization,
                        'phone': phone, 'email': email, 'fee': fee, 'schedule': schedule
                    })
                    
                    st.success(f"Doctor added successfully with ID: {doctor_id}")
    
    with tab2:
        st.subheader("Doctor Records")
        
        if st.session_state.doctors:
            doctor_df = pd.DataFrame(st.session_state.doctors)
            st.dataframe(doctor_df, use_container_width=True, hide_index=True)
        else:
            st.info("No doctor records found.")

# Appointment management page
def appointment_management_page():
    st.title("📅 Appointment Management")
    
    tab1, tab2 = st.tabs(["Schedule Appointment", "View Appointments"])
    
    with tab1:
        st.subheader("Schedule New Appointment")
        
        if not st.session_state.patients or not st.session_state.doctors:
            st.error("Please add patients and doctors first before scheduling appointments.")
        else:
            with st.form("appointment_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    patient_options = {p['id']: f"{p['name']} (ID: {p['id']})" for p in st.session_state.patients}
                    patient_id = st.selectbox("Select Patient*", options=list(patient_options.keys()), 
                                             format_func=lambda x: patient_options[x])
                    
                    doctor_options = {d['id']: f"Dr. {d['name']} ({d['specialization']})" for d in st.session_state.doctors}
                    doctor_id = st.selectbox("Select Doctor*", options=list(doctor_options.keys()), 
                                           format_func=lambda x: doctor_options[x])
                
                with col2:
                    appointment_date = st.date_input("Appointment Date*", min_value=datetime.now().date())
                    appointment_time = st.time_input("Appointment Time*", value=datetime.now().time())
                
                reason = st.text_area("Reason for Appointment*")
                
                submitted = st.form_submit_button("Schedule Appointment")
                
                if submitted:
                    if not reason:
                        st.error("Please provide a reason for the appointment")
                    else:
                        conn = sqlite3.connect('hospital.db')
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            INSERT INTO appointments (patient_id, doctor_id, date, time, reason)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (patient_id, doctor_id, appointment_date.strftime('%Y-%m-%d'), 
                              appointment_time.strftime('%H:%M'), reason))
                        
                        conn.commit()
                        appointment_id = cursor.lastrowid
                        conn.close()
                        
                        # Update session state
                        st.session_state.appointments.append({
                            'id': appointment_id, 'patient_id': patient_id, 'doctor_id': doctor_id,
                            'date': appointment_date.strftime('%Y-%m-%d'), 
                            'time': appointment_time.strftime('%H:%M'),
                            'reason': reason, 'status': 'Scheduled'
                        })
                        
                        st.success(f"Appointment scheduled successfully with ID: {appointment_id}")
    
    with tab2:
        st.subheader("Appointment Records")
        
        if st.session_state.appointments:
            # Create enhanced appointment data with patient and doctor names
            appt_data = []
            for appt in st.session_state.appointments:
                patient = next((p for p in st.session_state.patients if p['id'] == appt['patient_id']), {})
                doctor = next((d for d in st.session_state.doctors if d['id'] == appt['doctor_id']), {})
                
                appt_data.append({
                    'ID': appt['id'],
                    'Patient': patient.get('name', 'Unknown'),
                    'Doctor': doctor.get('name', 'Unknown'),
                    'Date': appt['date'],
                    'Time': appt['time'],
                    'Reason': appt['reason'],
                    'Status': appt['status']
                })
            
            appt_df = pd.DataFrame(appt_data)
            st.dataframe(appt_df, use_container_width=True, hide_index=True)
            
            # Status update options
            st.subheader("Update Appointment Status")
            appt_ids = [appt['id'] for appt in st.session_state.appointments]
            selected_appt = st.selectbox("Select Appointment", options=appt_ids)
            new_status = st.selectbox("New Status", ["Scheduled", "Completed", "Cancelled"])
            
            if st.button("Update Status"):
                conn = sqlite3.connect('hospital.db')
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE appointments SET status = ? WHERE id = ?",
                    (new_status, selected_appt)
                )
                
                conn.commit()
                conn.close()
                
                # Update session state
                for appt in st.session_state.appointments:
                    if appt['id'] == selected_appt:
                        appt['status'] = new_status
                        break
                
                st.success("Appointment status updated successfully!")
                st.rerun()
        else:
            st.info("No appointment records found.")

# Billing management page
def billing_management_page():
    st.title("💰 Billing Management")
    
    tab1, tab2 = st.tabs(["Generate Bill", "View Bills"])
    
    with tab1:
        st.subheader("Generate New Bill")
        
        if not st.session_state.patients:
            st.error("Please add patients first before generating bills.")
        else:
            with st.form("bill_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    patient_options = {p['id']: f"{p['name']} (ID: {p['id']})" for p in st.session_state.patients}
                    patient_id = st.selectbox("Select Patient*", options=list(patient_options.keys()), 
                                             format_func=lambda x: patient_options[x])
                    
                    doctor_fee = st.number_input("Doctor Fee ($)*", min_value=0.0, value=0.0, step=10.0)
                    medicine_fee = st.number_input("Medicine Fee ($)*", min_value=0.0, value=0.0, step=10.0)
                
                with col2:
                    room_charge = st.number_input("Room Charge ($)*", min_value=0.0, value=0.0, step=10.0)
                    other_charges = st.number_input("Other Charges ($)*", min_value=0.0, value=0.0, step=10.0)
                    bill_date = st.date_input("Bill Date*", value=datetime.now().date())
                
                submitted = st.form_submit_button("Generate Bill")
                
                if submitted:
                    total_amount = doctor_fee + medicine_fee + room_charge + other_charges
                    
                    conn = sqlite3.connect('hospital.db')
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO bills (patient_id, doctor_fee, medicine_fee, room_charge, other_charges, total_amount, date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_id, doctor_fee, medicine_fee, room_charge, other_charges, total_amount, 
                          bill_date.strftime('%Y-%m-%d')))
                    
                    conn.commit()
                    bill_id = cursor.lastrowid
                    conn.close()
                    
                    # Update session state
                    st.session_state.bills.append({
                        'id': bill_id, 'patient_id': patient_id, 'doctor_fee': doctor_fee,
                        'medicine_fee': medicine_fee, 'room_charge': room_charge, 
                        'other_charges': other_charges, 'total_amount': total_amount,
                        'date': bill_date.strftime('%Y-%m-%d'), 'status': 'Pending'
                    })
                    
                    st.success(f"Bill generated successfully with ID: {bill_id}")
                    st.info(f"Total Amount: ${total_amount:,.2f}")
    
    with tab2:
        st.subheader("Bill Records")
        
        if st.session_state.bills:
            # Create enhanced bill data with patient names
            bill_data = []
            for bill in st.session_state.bills:
                patient = next((p for p in st.session_state.patients if p['id'] == bill['patient_id']), {})
                
                bill_data.append({
                    'ID': bill['id'],
                    'Patient': patient.get('name', 'Unknown'),
                    'Doctor Fee': f"${bill['doctor_fee']:,.2f}",
                    'Medicine Fee': f"${bill['medicine_fee']:,.2f}",
                    'Room Charge': f"${bill['room_charge']:,.2f}",
                    'Other Charges': f"${bill['other_charges']:,.2f}",
                    'Total Amount': f"${bill['total_amount']:,.2f}",
                    'Date': bill['date'],
                    'Status': bill['status']
                })
            
            bill_df = pd.DataFrame(bill_data)
            st.dataframe(bill_df, use_container_width=True, hide_index=True)
            
            # Payment status update options
            st.subheader("Update Payment Status")
            bill_ids = [bill['id'] for bill in st.session_state.bills]
            selected_bill = st.selectbox("Select Bill", options=bill_ids)
            new_status = st.selectbox("Payment Status", ["Pending", "Paid"])
            
            if st.button("Update Payment Status"):
                conn = sqlite3.connect('hospital.db')
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE bills SET status = ? WHERE id = ?",
                    (new_status, selected_bill)
                )
                
                conn.commit()
                conn.close()
                
                # Update session state
                for bill in st.session_state.bills:
                    if bill['id'] == selected_bill:
                        bill['status'] = new_status
                        break
                
                st.success("Payment status updated successfully!")
                st.rerun()
        else:
            st.info("No bill records found.")

# Reports and analytics page
def reports_page():
    st.title("📊 Reports & Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Patient Analytics", "Financial Reports", "Appointment Reports"])
    
    with tab1:
        st.subheader("Patient Analytics")
        
        if st.session_state.patients:
            # Age distribution chart
            age_data = pd.DataFrame(st.session_state.patients)
            fig = px.histogram(age_data, x='age', nbins=10, title="Patient Age Distribution")
            st.plotly_chart(fig, use_container_width=True)
            
            # Gender distribution
            gender_counts = age_data['gender'].value_counts()
            fig = px.pie(values=gender_counts.values, names=gender_counts.index, 
                         title="Patient Gender Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No patient data available for analytics.")
    
    with tab2:
        st.subheader("Financial Reports")
        
        if st.session_state.bills:
            # Revenue by month
            bill_data = pd.DataFrame(st.session_state.bills)
            bill_data['date'] = pd.to_datetime(bill_data['date'])
            bill_data['month'] = bill_data['date'].dt.to_period('M')
            
            monthly_revenue = bill_data.groupby('month')['total_amount'].sum().reset_index()
            monthly_revenue['month'] = monthly_revenue['month'].astype(str)
            
            fig = px.bar(monthly_revenue, x='month', y='total_amount', 
                         title="Monthly Revenue", labels={'total_amount': 'Revenue ($)'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Payment status
            status_counts = bill_data['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                         title="Payment Status Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No billing data available for financial reports.")
    
    with tab3:
        st.subheader("Appointment Reports")
        
        if st.session_state.appointments:
            # Appointment status
            appt_data = pd.DataFrame(st.session_state.appointments)
            status_counts = appt_data['status'].value_counts()
            
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                         title="Appointment Status Distribution")
            st.plotly_chart(fig, use_container_width=True)
            
            # Appointments by date
            appt_data['date'] = pd.to_datetime(appt_data['date'])
            daily_appointments = appt_data.groupby('date').size().reset_index(name='count')
            
            fig = px.line(daily_appointments, x='date', y='count', 
                         title="Daily Appointments Trend")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No appointment data available for reports.")

# Main application
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        # Sidebar navigation
        with st.sidebar:
            st.title(f"Welcome, {st.session_state.user['username']}!")
            st.write(f"Role: {st.session_state.user['role']}")
            st.markdown("---")
            
            # Navigation menu
            selected = option_menu(
                menu_title="Navigation",
                options=["Dashboard", "Patient Management", "Doctor Management", 
                         "Appointment Management", "Billing Management", "Reports"],
                icons=["house", "people", "person-badge", "calendar", "cash-coin", "bar-chart"],
                default_index=0
            )
            
            st.markdown("---")
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.rerun()
        
        # Display selected page
        if selected == "Dashboard":
            dashboard_page()
        elif selected == "Patient Management":
            patient_management_page()
        elif selected == "Doctor Management":
            doctor_management_page()
        elif selected == "Appointment Management":
            appointment_management_page()
        elif selected == "Billing Management":
            billing_management_page()
        elif selected == "Reports":
            reports_page()

if __name__ == "__main__":
    main()