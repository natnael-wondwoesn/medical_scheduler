# app.py
import streamlit as st
from datetime import datetime
from database import session
from models import User, Patient, Appointment
from hunterIo import verify
from gcalender import add_event_to_calendar
from notif import send_reminder
# from scheduler import start_scheduler
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    st.title("Medical Scheduler Application")
    
    # Start the scheduler
    # start_scheduler()
    
    # Simple user login
    email = st.text_input("Enter your email to login")
    if st.button("Login"):
        user = session.query(User).filter_by(email=email).first()
        if user:
            st.success(f"Welcome, {user.name} ({user.role})")
            if user.role == "Front Desk Medical Assistant":
                front_desk_interface(user)
            elif user.role == "General Practitioner":
                practitioner_interface(user)
            else:
                st.error("Unknown role")
        else:
            st.error("User not found")

def front_desk_interface(user):
    st.header("Appointment Scheduling")
    
    # Add New Patient
    st.subheader("Add New Patient")
    patient_name = st.text_input("Patient Name", key="patient_name")
    patient_email = st.text_input("Patient Email", key="patient_email")
    patient_phone = st.text_input("Patient Phone Number (Optional)", key="patient_phone")
    if st.button("Add Patient", key="add_patient"):
        if patient_name and patient_email:
            if verify(patient_email):
                new_patient = Patient(
                    name=patient_name,
                    email=patient_email,
                    phone_number=patient_phone,
                    email_verified=True
                )
                session.add(new_patient)
                session.commit()
                st.success("Patient added successfully with verified email.")
            else:
                st.error("Invalid email address. Please provide a valid email.")
        else:
            st.error("Please provide both name and email.")
    
    st.markdown("---")
    
    # Schedule Appointment
    st.subheader("Schedule New Appointment")
    patients = session.query(Patient).all()
    if patients:
        patient_options = {f"{p.name} (ID: {p.id})": p.id for p in patients}
        patient_selection = st.selectbox("Select Patient", options=list(patient_options.keys()))
        appointment_datetime = st.datetime_input("Appointment Date and Time", value=datetime.now())
        
        if st.button("Schedule Appointment", key="schedule_appointment"):
            selected_patient_id = patient_options[patient_selection]
            # Check for overlapping appointments
            overlapping = session.query(Appointment).filter(
                Appointment.appointment_datetime == appointment_datetime,
                Appointment.status == 'Scheduled'
            ).first()
            if overlapping:
                st.error("This time slot is already booked.")
            else:
                new_appointment = Appointment(
                    patient_id=selected_patient_id,
                    user_id=user.id,
                    appointment_datetime=appointment_datetime,
                    status='Scheduled'
                )
                session.add(new_appointment)
                session.commit()
                st.success("Appointment scheduled successfully.")
                
                # Add to Google Calendar
                if add_event_to_calendar(new_appointment):
                    st.success("Appointment added to Google Calendar.")
                else:
                    st.warning("Failed to add appointment to Google Calendar.")
                
                # Send Reminder
                if send_reminder(new_appointment):
                    st.success("Reminder sent to patient.")
                else:
                    st.warning("Failed to send reminder.")
    else:
        st.info("No patients found. Please add a patient first.")
    
    st.markdown("---")
    
    # View Today's Appointments
    st.subheader("Today's Appointments")
    today = datetime.now().date()
    appointments = session.query(Appointment).join(Patient).filter(
        Appointment.appointment_datetime >= datetime.combine(today, datetime.min.time()),
        Appointment.appointment_datetime < datetime.combine(today, datetime.max.time())
    ).all()
    
    if appointments:
        data = [{
            "Patient Name": appt.patient.name,
            "Appointment Time": appt.appointment_datetime.strftime("%Y-%m-%d %H:%M"),
            "Status": appt.status
        } for appt in appointments]
        st.table(data)
    else:
        st.info("No appointments scheduled for today.")

def practitioner_interface(user):
    st.header("Daily Schedule Summary")
    
    # Display daily summary
    today = datetime.now().date()
    appointments = session.query(Appointment).join(Patient).filter(
        Appointment.appointment_datetime >= datetime.combine(today, datetime.min.time()),
        Appointment.appointment_datetime < datetime.combine(today, datetime.max.time())
    ).all()
    
    if appointments:
        data = [{
            "Patient Name": appt.patient.name,
            "Appointment Time": appt.appointment_datetime.strftime("%Y-%m-%d %H:%M"),
            "Status": appt.status
        } for appt in appointments]
        st.table(data)
    else:
        st.info("No appointments scheduled for today.")

if __name__ == "__main__":
    main()
