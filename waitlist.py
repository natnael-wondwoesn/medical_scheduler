# waitlist.py (Modify add_to_waitlist to include urgency)

from database import session
from models import Waitlist, Patient, Appointment
from datetime import datetime
from utils import prioritize_waitlist
from hunterIo import verify
from notif import send_mail

def add_to_waitlist(patient_id, requested_datetime, urgency=1):
    # Create a new Waitlist entry with priority
    waitlist_entry = Waitlist(
        patient_id=patient_id,
        requested_datetime=requested_datetime,
        added_at=datetime.now(),
        priority=urgency
    )
    # Add to session and commit to save in the database
    session.add(waitlist_entry)
    session.commit()
    print(f"Patient ID {patient_id} added to waitlist for {requested_datetime} with priority {urgency}")

def process_cancellation(appointment_id):
    # Fetch the canceled appointment
    appointment = session.query(Appointment).filter_by(id=appointment_id).first()
    if not appointment:
        print("Appointment not found.")
        return
    
    # Update the appointment status to 'Cancelled'
    appointment.status = 'Cancelled'
    session.commit()
    
    # Find the next patient in the waitlist using prioritization
    waitlist_entry = prioritize_waitlist(appointment.appointment_datetime)
    
    if waitlist_entry:
        # Assign the appointment to the waitlisted patient
        appointment.patient_id = waitlist_entry.patient_id
        appointment.status = 'Scheduled'
        session.commit()
        
        # Remove the patient from the waitlist
        session.delete(waitlist_entry)
        session.commit()
        
        # Notify the patient via email
        patient = session.query(Patient).filter_by(id=waitlist_entry.patient_id).first()
        if patient:
            subject = "Your Appointment Slot is Confirmed"
            body = f"Dear {patient.name},\n\nGood news! An open appointment slot has become available and has been scheduled for you on {appointment.appointment_datetime.strftime('%Y-%m-%d %H:%M')}.\n\nThank you."
            send_mail(patient.email, subject, body)
            print(f"Patient {patient.email} notified of their new appointment.")
