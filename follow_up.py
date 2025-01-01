import os
import datetime
from database import session
from models import *
import pandas as pd



def schedule_followup(appointment_id, followup_type, days_after=1):
    """
    Schedules a follow-up task based on the appointment.
    
    Parameters:

        appointment_id (int): ID of the completed appointment.
        followup_type (str): Type of follow-up (e.g., 'Prescription Refill').
        days_after (int): Number of days after the appointment to schedule the follow-up.
    """
    # Fetch the appointment from the database
    appointment = session.query(Appointment).filter_by(id=appointment_id).first()
    if not appointment:
        print("Appointment not found.")
        return
    
    # Calculate the due date for the follow-up
    due_date = appointment.appointment_datetime + datetime.timedelta(days=days_after)
    
    # Create a new FollowUp entry
    followup = FollowUp(
        appointment_id=appointment.id,
        followup_type=followup_type,
        due_date=due_date,
        status='Pending'
    )
    # Create a corresponding FollowUpAdherence entry
    adherence = FollowUpAdherence(
        followup_id=followup.id,
        completed=False,
        completed_at=None
    )
    # Establish relationship
    followup.adherence = adherence
    
    # Add to session and commit to save in the database
    session.add(followup)
    session.commit()
    print(f"Follow-up '{followup_type}' scheduled for Appointment ID {appointment_id} on {due_date}")



def generate_adherence_report():
    # Join FollowUp, FollowUpAdherence, Appointment, and Patient tables

    report_data = session.query(

        Patient.name.label('Patient Name'),

        FollowUp.followup_type.label('Follow-Up Type'),

        FollowUp.due_date.label('Due Date'),

        FollowUpAdherence.completed.label('Completed'),

        FollowUpAdherence.completed_at.label('Completed At')

    ).join(FollowUp, FollowUp.appointment_id == Appointment.id) \
     .join(FollowUpAdherence, FollowUpAdherence.followup_id == FollowUp.id) \
     .join(Patient, Patient.id == FollowUp.appointment.patient_id) \
     .all()
    
    # Convert to DataFrame
    df = pd.DataFrame(report_data, columns=['Patient Name', 'Follow-Up Type', 'Due Date', 'Completed', 'Completed At'])
    
    return df


    
def update_adherence(followup_id, completed=True):
    """
    Updates the adherence status of a follow-up task.
    
    Parameters:
        followup_id (int): ID of the follow-up task.
        completed (bool): Whether the follow-up was completed.
    """
    followup_adherence = session.query(FollowUpAdherence).filter_by(followup_id=followup_id).first()
    if not followup_adherence:
        print("Follow-up adherence record not found.")

        return
    
    followup_adherence.completed = completed
    if completed:
        followup_adherence.completed_at = datetime.now()
    session.commit()
    print(f"Follow-up adherence updated for FollowUp ID {followup_id}")