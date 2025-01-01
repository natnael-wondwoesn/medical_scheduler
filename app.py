import streamlit as st
import pandas as pd
from datetime import datetime
from database import session
from models import User, Patient, Appointment, FollowUp, FollowUpAdherence
from follow_up import *
from waitlist import *
from hunterIo import verify
from gcalender import add_app_to_cal
from notif import send_remainder
from follow_up import generate_adherence_report
from scheduler import start_scheduler
from dotenv import load_dotenv
import os


# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
# load_dotenv()



st.set_page_config(page_title="Medical Scheduler", layout="wide")

st.title("Medical Scheduler: Comprehensive Management Dashboard")

st.sidebar.title("Navigation")
tabs = st.sidebar.radio("Go to", ["Dashboard", "Manage Patients", "Manage Appointments", "Waitlist Management", "Cancellations", "Follow-Up Management", "Reports"])

if tabs == "Dashboard":
    st.header("Dashboard Overview")
    total_patients = session.query(Patient).count()
    total_appointments = session.query(Appointment).count()
    pending_cancellations = session.query(Appointment).filter_by(status="Cancelled").count()
    waitlist_count = session.query(Waitlist).count()
    followups_pending = session.query(FollowUp).filter_by(status="Pending").count()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Patients", total_patients)
    col2.metric("Total Appointments", total_appointments)
    col3.metric("Pending Cancellations", pending_cancellations)
    col4.metric("Waitlist Count", waitlist_count)
    col5.metric("Pending Follow-Ups", followups_pending)
    
    st.markdown("---")
    
    st.subheader("Recent Activities")
    recent_appointments = session.query(Appointment).order_by(Appointment.appointment_datetime.desc()).limit(5).all()
    if recent_appointments:
        for appt in recent_appointments:
            st.write(f"**Appointment ID:** {appt.id} | **Patient:** {appt.patient.name} | **Time:** {appt.appointment_datetime.strftime('%Y-%m-%d %H:%M')} | **Status:** {appt.status}")
    else:
        st.info("No recent appointments found.")

elif tabs == "Manage Patients":
    st.header("Manage Patients")
    
    st.subheader("Add New Patient")
    with st.form("add_patient_form"):
        patient_name = st.text_input("Patient Name", placeholder="Enter patient name")
        patient_email = st.text_input("Patient Email", placeholder="Enter patient email")
        submitted = st.form_submit_button("Add Patient")
        
        if submitted:
            if patient_name and patient_email:
                new_patient = Patient(name=patient_name, email=patient_email)
                session.add(new_patient)
                session.commit()
                st.success(f"Patient '{patient_name}' added successfully with ID {new_patient.id}.")
            else:
                st.error("Please fill in all the fields.")
    
    st.markdown("---")
    
    st.subheader("Existing Patients")
    patients = session.query(Patient).all()
    if patients:
        for patient in patients:
            st.write(f"**ID:** {patient.id} | **Name:** {patient.name} | **Email:** {patient.email}")
    else:
        st.info("No patients found.")

elif tabs == "Manage Appointments":
    st.header("Manage Appointments")
    
    st.subheader("Schedule New Appointment")
    with st.form("schedule_appointment_form"):
        patient_id = st.number_input("Patient ID", min_value=1, step=1, placeholder="Enter Patient ID")
        practitioner = st.text_input("Practitioner Name", placeholder="Enter practitioner name")
         # Input for date
        appointment_date = st.date_input("Appointment Date")

#         # Input for time
        appointment_time = st.time_input("Appointment Time")

#         # Combine date and time into a datetime object
        appointment_datetime = datetime.combine(appointment_date, appointment_time)
        submitted = st.form_submit_button("Schedule Appointment")
        
        if submitted:
            patient = session.query(Patient).filter_by(id=patient_id).first()
            if patient:
                new_appointment = Appointment(
                    patient_id=patient_id,
                    practitioner=practitioner,
                    appointment_datetime=appointment_datetime,
                    status="Scheduled"
                )
                session.add(new_appointment)
                session.commit()
                st.success(f"Appointment scheduled successfully with ID {new_appointment.id}.")
            else:
                st.error("Patient not found. Please enter a valid Patient ID.")
    
    st.markdown("---")
    
    st.subheader("Scheduled Appointments")
    appointments = session.query(Appointment).filter_by(status="Scheduled").order_by(Appointment.appointment_datetime).all()
    if appointments:
        for appt in appointments:
            st.write(f"**ID:** {appt.id} | **Patient:** {appt.patient.name} | **Time:** {appt.appointment_datetime.strftime('%Y-%m-%d %H:%M')} | **Status:** {appt.status}")
    else:
        st.info("No scheduled appointments found.")

elif tabs == "Waitlist Management":
    st.header("Waitlist Management")
    
    st.subheader("Add Patient to Waitlist")
    with st.form("add_waitlist_form"):
        patient_id = st.number_input("Patient ID", min_value=1, step=1, placeholder="Enter Patient ID")
        priority = st.slider("Priority Score", min_value=1, max_value=100, value=50)
        requested_time = st.date_input("Preferred Date")
        submitted = st.form_submit_button("Add to Waitlist")
        
        if submitted:
            patient = session.query(Patient).filter_by(id=patient_id).first()
            if patient:
                if add_to_waitlist(patient_id=patient_id, urgency=priority,requested_datetime=requested_time):
                    st.success(f"Patient ID {patient_id} added to the waitlist with priority {priority}.")
                else:
                    st.error("Failed to add patient to the waitlist. They might already be on the waitlist.")
            else:
                st.error("Patient not found. Please enter a valid Patient ID.")
    
    st.markdown("---")
    
    st.subheader("Current Waitlist")
    waitlisted_patients = session.query(Waitlist).order_by(Waitlist.priority.desc(), Waitlist.added_at).all()
    if waitlisted_patients:
        for waitlist in waitlisted_patients:
            st.write(f"**Patient ID:** {waitlist.patient_id} | **Priority Score:** {waitlist.priority} | **Added At:** {waitlist.added_at.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("No patients on the waitlist.")
    
    st.markdown("---")
    
    st.subheader("Prioritize Waitlist")
    if st.button("Show Next Patient"):
        next_patient = prioritize_waitlist()
        if next_patient:
            st.success(f"Next patient to assign: Patient ID {next_patient.patient_id} with Priority Score {next_patient.priority}.")
        else:
            st.info("No patients available in the waitlist.")

elif tabs == "Cancellations":
    st.header("Cancellations Management")
    
    st.subheader("Manage Cancellations")
    
    canceled_appointments = session.query(Appointment).filter_by(status="Cancelled").all()
    if canceled_appointments:
        st.write("### Canceled Appointments")
        for appt in canceled_appointments:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**ID:** {appt.id} | **Patient:** {appt.patient.name} | **Time:** {appt.appointment_datetime.strftime('%Y-%m-%d %H:%M')}")
            with col2:
                if st.button(f"Process Cancellation (ID {appt.id})", key=f"cancel-{appt.id}"):
                    if process_cancellation(appt.id):
                        st.success(f"Successfully processed cancellation for Appointment ID {appt.id}.")
                        appt.status = "Processed"
                        session.commit()
                    else:
                        st.error(f"Failed to process cancellation for Appointment ID {appt.id}.")
    else:
        st.info("No canceled appointments to process.")
    
    st.markdown("---")
    
    st.subheader("Cancel an Appointment")
    with st.form("manual_cancel_form"):
        appointment_id = st.number_input("Appointment ID", min_value=1, step=1, placeholder="Enter Appointment ID to Cancel")
        submitted = st.form_submit_button("Cancel Appointment")
        
        if submitted:
            appt = session.query(Appointment).filter_by(id=int(appointment_id)).first()
            if appt and appt.status == "Scheduled":
                appt.status = "Cancelled"
                session.commit()
                st.success(f"Appointment ID {appointment_id} has been cancelled.")
            else:
                st.error("Invalid Appointment ID or Appointment is not in a cancellable state.")

elif tabs == "Follow-Up Management":
    st.header("Follow-Up Management")
    
    st.subheader("Schedule Follow-Up")
    with st.form("schedule_followup_form"):
        appointment_id = st.number_input("Appointment ID", min_value=1, step=1, placeholder="Enter Appointment ID")
        followup_type = st.selectbox("Follow-Up Type", ["Prescription Refill", "Lab Results", "Satisfaction Survey"])
        days_after = st.number_input("Days After Appointment", min_value=1, max_value=30, value=1)
        submitted = st.form_submit_button("Schedule Follow-Up")
        
        if submitted:
            appt = session.query(Appointment).filter_by(id=int(appointment_id)).first()
            if appt and appt.status == "Completed":
                if schedule_followup(appointment_id=int(appointment_id), followup_type=followup_type, days_after=int(days_after)):
                    st.success(f"Follow-up '{followup_type}' scheduled for Appointment ID {appointment_id} in {days_after} day(s).")
                else:
                    st.error("Failed to schedule follow-up. It might already be scheduled.")
            else:
                st.error("Invalid Appointment ID or Appointment is not completed.")
    
    st.markdown("---")
    
    st.subheader("Scheduled Follow-Ups")
    scheduled_followups = session.query(FollowUp).filter_by(status="Pending").all()
    if scheduled_followups:
        for followup in scheduled_followups:
            st.write(f"**Follow-Up ID:** {followup.id} | **Appointment ID:** {followup.appointment_id} | **Type:** {followup.followup_type} | **Due Date:** {followup.due_date.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("No scheduled follow-ups.")
    
    st.markdown("---")
    
    st.subheader("Mark Follow-Up as Completed")
    with st.form("complete_followup_form"):
        followup_id = st.number_input("Follow-Up ID", min_value=1, step=1, placeholder="Enter Follow-Up ID to Complete")
        submitted = st.form_submit_button("Mark as Completed")
        
        if submitted:
            followup = session.query(FollowUp).filter_by(id=int(followup_id)).first()
            if followup and followup.status == "Pending":
                followup.status = "Completed"
                adherence = session.query(FollowUpAdherence).filter_by(followup_id=followup.id).first()
                if adherence:
                    adherence.completed = True
                    adherence.completed_at = datetime.now()
                session.commit()
                st.success(f"Follow-Up ID {followup_id} marked as completed.")
            else:
                st.error("Invalid Follow-Up ID or Follow-Up is already completed.")
    
    st.markdown("---")
    
    st.subheader("Generate Adherence Report")
    if st.button("Generate Adherence Report"):
        try:
            report = generate_adherence_report()
            if report.empty:
                st.info("No adherence data available.")
            else:
                csv = report.to_csv(index=False)
                st.download_button(
                    label="Download Report as CSV",
                    data=csv,
                    file_name=f"adherence_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv',
                )
                st.success("Adherence report generated successfully.")
        except Exception as e:
            st.error(f"Failed to generate adherence report: {e}")
    
    # if st.button("Send Adherence Report via Email"):
    #     try:
    #         send_adherence_report()
    #         st.success("Adherence report sent successfully.")
    #     except Exception as e:
    #         st.error(f"Failed to send adherence report: {e}")

elif tabs == "Reports":
    st.header("Reports")
    
    st.subheader("Download Adherence Report")
    if st.button("Download Adherence Report"):
        try:
            report = generate_adherence_report()
            if report.empty:
                st.info("No adherence data available.")
            else:
                csv = report.to_csv(index=False)
                st.download_button(
                    label="Download Report as CSV",
                    data=csv,
                    file_name=f"adherence_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv',
                )
                st.success("Adherence report downloaded successfully.")
        except Exception as e:
            st.error(f"Failed to generate adherence report: {e}")
    
    st.markdown("---")
    
    # st.subheader("Send Adherence Report via Email")
    # if st.button("Send Adherence Report"):
    #     try:
    #         send_adherence_report()
    #         st.success("Adherence report sent successfully.")
    #     except Exception as e:
    #         st.error(f"Failed to send adherence report: {e}")


# def main():
#     # Initialize session state variables
#     if "logged_in" not in st.session_state:
#         st.session_state.logged_in = False
#         st.session_state.user = None

#     # Title of the app
#     st.title("Medical Scheduler Application")
#     start_scheduler()

#     # Check if the user is logged in
#     if not st.session_state.logged_in:
#         email = st.text_input("Enter your email to login")
#         if st.button("Login"):
#             user = session.query(User).filter_by(email=email).first()
#             if user:
#                 st.session_state.logged_in = True
#                 st.session_state.user = user
#                 st.success(f"Welcome, {user.name} ({user.role})")
#             else:
#                 st.error("User not found")
#     else:
#         user = st.session_state.user
#         st.success(f"Welcome back, {user.name} ({user.role})")

#         # Provide a logout button
#         if st.button("Logout"):
#             st.session_state.logged_in = False
#             st.session_state.user = None
#             st.rerun()  

#         # Handle roles
#         if "Front Desk" in user.role:
#             front_desk_interface(user)
#         elif "General" in user.role:
#             practitioner_interface(user)
#         else:
#             st.error("Unknown role")

# def front_desk_interface(user):
#     st.header("Appointment Scheduling")
    
#     # Add New Patient
#     st.subheader("Add New Patient")
#     patient_name = st.text_input("Patient Name")
#     patient_email = st.text_input("Patient Email")
#     patient_phone = st.text_input("Patient Phone Number (Optional)")

#     if st.button("Add Patient"):
#         if patient_name and patient_email:
#             new_patient = Patient(
#                     name=patient_name,
#                     email=patient_email,
#                     phone_number=patient_phone,
#                     email_verified=True
#                 )
#             session.add(new_patient)
#             session.commit()
#             st.success("Patient added successfully with verified email.")
#             # print(patient_email)
#             # res = verify(str(patient_email))
#             # if res== True:
#             #     new_patient = Patient(
#             #         name=patient_name,
#             #         email=patient_email,
#             #         phone_number=patient_phone,
#             #         email_verified=True
#             #     )
#             #     session.add(new_patient)
#             #     session.commit()
#             #     st.success("Patient added successfully with verified email.")
                
#             # else:
#             #     st.error("Invalid email address. Please provide a valid email.")
#         else:
#             st.error("Please provide both name and email.")
    
#     st.markdown("---")
    
#     # Schedule Appointment
#     st.subheader("Schedule New Appointment")
#     patients = session.query(Patient).all()
#     if patients:
#         patient_options = {f"{p.name} (ID: {p.id})": p.id for p in patients}
#         patient_selection = st.selectbox("Select Patient", options=list(patient_options.keys()))
#         # appointment_datetime = st.time_input("Appointment Date and Time", value=datetime.now())
#         # Input for date
#         appointment_date = st.date_input("Appointment Date")

#         # Input for time
#         appointment_time = st.time_input("Appointment Time")

#         # Combine date and time into a datetime object
#         appointment_datetime = datetime.datetime.combine(appointment_date, appointment_time)
        
#         if st.button("Schedule Appointment"):
#             selected_patient_id = patient_options[patient_selection]
#             overlapping = session.query(Appointment).filter(
#                 Appointment.appointment_datetime == appointment_datetime,
#                 Appointment.status == 'Scheduled'
#             ).first()
#             if overlapping:
#                 st.error("This time slot is already booked.")
#             else:
#                 new_appointment = Appointment(
#                     patient_id=selected_patient_id,
#                     user_id=user.id,
#                     appointment_datetime=appointment_datetime,
#                     status='Scheduled'
#                 )
#                 session.add(new_appointment)
#                 session.commit()
#                 st.success("Appointment scheduled successfully.")
                
#                 # Add to Google Calendar
#                 # if add_app_to_cal(new_appointment):
#                 #     st.success("Appointment added to Google Calendar.")
#                 # else:
#                 #     st.warning("Failed to add appointment to Google Calendar.")
                
#                 # Send Reminder
#                 if send_remainder(new_appointment):
#                     st.success("Reminder sent to patient.")
#                 else:
#                     st.warning("Failed to send reminder.")
#     else:
#         st.info("No patients found. Please add a patient first.")
    
#     st.markdown("---")
    
#     # View Today's Appointments
#     st.subheader("Today's Appointments")
#     today = datetime.datetime.now().date()
#     appointments = session.query(Appointment).join(Patient).filter(
#         Appointment.appointment_datetime >= datetime.datetime.combine(today, datetime.datetime.min.time()),
#         Appointment.appointment_datetime < datetime.datetime.combine(today, datetime.datetime.max.time())
#     ).all()
    
#     if appointments:
#         data = [{
#             "Patient Name": appt.patient.name,
#             "Appointment Time": appt.appointment_datetime.strftime("%Y-%m-%d %H:%M"),
#             "Status": appt.status
#         } for appt in appointments]
#         st.table(data)
#     else:
#         st.info("No appointments scheduled for today.")
    

#         st.markdown("---")
    
#     # Section to view and manage follow-up adherence
#     st.header("Follow-Up Adherence Management")
#     followups = session.query(FollowUp).join(Appointment).join(Patient).filter(
#         Appointment.appointment_datetime >= datetime.datetime.combine(today, datetime.datetime.min.time()),
#         Appointment.appointment_datetime < datetime.datetime.combine(today, datetime.datetime.max.time()),
#         FollowUp.status == 'Pending'
#     ).all()
    
#     if followups:
#         st.subheader("Pending Follow-Ups")
#         for followup in followups:
#             st.write(f"**Patient:** {followup.appointment.patient.name}")
#             st.write(f"**Follow-Up Type:** {followup.followup_type}")
#             st.write(f"**Due Date:** {followup.due_date.strftime('%Y-%m-%d %H:%M')}")
#             if st.button(f"Mark as Completed - FollowUp ID {followup.id}", key=f"complete_followup_{followup.id}"):
#                 # Update adherence
#                 update_adherence(followup.id, completed=True)
#                 # Update follow-up status
#                 followup.status = 'Completed'
#                 session.commit()
#                 st.success(f"Follow-up ID {followup.id} marked as completed.")
#     else:
#         st.info("No pending follow-ups for today.")













# def practitioner_interface(user):
#     st.header("Today's Schedule Summary")
    
#     today = datetime.datetime.now().date()
#     appointments_all = session.query(Appointment).join(Patient).filter(
        
#     ).all()
#     appointments = session.query(Appointment).join(Patient).filter(
#         Appointment.appointment_datetime >= datetime.datetime.combine(today, datetime.datetime.min.time()),
#         Appointment.appointment_datetime < datetime.datetime.combine(today, datetime.datetime.max.time())
#     ).all()

    
    
#     if appointments:
#         data = [{
#             "Patient Name": appt.patient.name,
#             "Appointment Time": appt.appointment_datetime.strftime("%Y-%m-%d %H:%M"),
#             "Status": appt.status
#         } for appt in appointments]
#         st.table(data)
#     else:
#         st.info("No appointments scheduled for today.")
#     st.header("All Active Schedule Summary")

#     data_all = [{
#         "Patient Name": appt.patient.name,
#         "Appointment Time": appt.appointment_datetime.strftime("%Y-%m-%d %H:%M"),
#         "Status": appt.status
#         } for appt in appointments_all]
#     st.table(data_all)



#     st.markdown("---")
    
#     # Adherence Report Section
#     st.header("Follow-Up Adherence Report")
#     if st.button("Generate Adherence Report"):
#         report_df = generate_adherence_report()
#         if report_df.empty:
#             st.info("No adherence data available.")
#         else:
#             st.dataframe(report_df)
#             # Optionally, allow downloading the report
#             csv = report_df.to_csv(index=False)
#             st.download_button(
#                 label="Download Report as CSV",
#                 data=csv,
#                 file_name=f"adherence_report_{today.strftime('%Y%m%d')}.csv",
#                 mime='text/csv',
#             )

# if __name__ == "__main__":
#     main()
