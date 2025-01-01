# scheduler.py

import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

from database import session
from models import Appointment, User, Waitlist, FollowUp, FollowUpAdherence,Patient
from notif import send_remainder, send_mail, send_email_with_attachment
# from gcalender import add_event_to_calendar
from waitlist import process_cancellation, add_to_waitlist
from follow_up import *
from utils import prioritize_waitlist

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='logs/scheduler.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)


def start_scheduler():
    """
    Starts the background scheduler and adds scheduled jobs.
    """
    # Initialize the BackgroundScheduler
    scheduler = BackgroundScheduler()
    
    # Schedule send_reminders to run every hour
    scheduler.add_job(send_reminders, 'interval', hours=1)
    
    # Schedule generate_daily_summary to run daily at 6 PM
    scheduler.add_job(generate_daily_summary, 'cron', hour=18, minute=0)
    
    # Schedule monitor_cancellations to run every 10 minutes
    scheduler.add_job(monitor_cancellations, 'interval', minutes=10)
    
    # Schedule follow-up reminders to run daily at 9 AM
    scheduler.add_job(send_followup_reminders, 'cron', hour=9, minute=0)
    
    # Schedule adherence report to run daily at 7 PM
    scheduler.add_job(send_adherence_report, 'cron', hour=19, minute=0)
    
    # Start the scheduler
    scheduler.start()
    print("Scheduler started.")


def send_adherence_report():
    # Generate the report
    report_df = generate_adherence_report()
    
    if report_df.empty:
        print("No adherence data to report.")
        return
    
    # Convert DataFrame to CSV
    report_csv = report_df.to_csv(index=False)
    
    # Define email parameters
    subject = f"Daily Follow-Up Adherence Report - {datetime.now().strftime('%Y-%m-%d')}"
    body = "Please find attached the daily follow-up adherence report."
    
    # Save CSV to a temporary file
    report_filename = f"adherence_report_{datetime.now().strftime('%Y%m%d')}.csv"
    report_df.to_csv(report_filename, index=False)
    
    recipients = session.query(User).filter_by(role='Front Desk Medical Assistant').all()
    
    for user in recipients:
        # Send the report as an email attachment
        send_email_with_attachment(user.email, subject, body, report_filename)
        print(f"Adherence report sent to {user.email}")
    

    os.remove(report_filename)



def send_reminders():
    logging.info("Starting send_reminders job.")
    now = datetime.now()
    reminder_time = now + timedelta(hours=24)
    
    # Fetch appointments scheduled for the next 24 hours with status 'Scheduled'
    appointments = session.query(Appointment).join(User).join(Patient).filter(
        Appointment.appointment_datetime >= reminder_time,
        Appointment.appointment_datetime < reminder_time + timedelta(minutes=30),
        Appointment.status == 'Scheduled'
    ).all()
    
    logging.info(f"Found {len(appointments)} appointments to send reminders for.")
    
    for appt in appointments:
        patient = appt.patient
        subject = "Appointment Reminder"
        body = f"Dear {patient.name},\n\nThis is a reminder for your appointment on {appt.appointment_datetime.strftime('%Y-%m-%d %H:%M')}.\n\nThank you."
        
        if send_remainder(patient.email, subject, body):
            logging.info(f"Reminder sent to {patient.email} for appointment ID {appt.id}.")
        else:
            logging.error(f"Failed to send reminder to {patient.email} for appointment ID {appt.id}.")

def generate_daily_summary():
    """
    Generates and sends a daily summary of scheduled appointments to General Practitioners.
    """
    logging.info("Starting generate_daily_summary job.")
    today = datetime.now().date()
    
    # Fetch appointments for today with status 'Scheduled'
    appointments = session.query(Appointment).join(User).join(Patient).filter(
        Appointment.appointment_datetime >= datetime.combine(today, datetime.min.time()),
        Appointment.appointment_datetime < datetime.combine(today, datetime.max.time()),
        Appointment.status == 'Scheduled'
    ).all()
    
    if not appointments:
        logging.info("No appointments scheduled for today.")
        return
    
    summary = "Daily Appointment Summary:\n\n"
    for appt in appointments:
        summary += f"Time: {appt.appointment_datetime.strftime('%H:%M')}, Patient: {appt.patient.name}, Practitioner: {appt.user.name}\n"
    
    # Fetch all General Practitioners
    practitioners = session.query(User).filter_by(role='General Practitioner').all()
    
    logging.info(f"Sending daily summary to {len(practitioners)} practitioners.")
    
    for practitioner in practitioners:
        subject = f"Daily Appointment Summary for {today.strftime('%Y-%m-%d')}"
        body = summary
        
        if send_mail(practitioner.email, subject, body):
            logging.info(f"Daily summary sent to {practitioner.email}.")
        else:
            logging.error(f"Failed to send daily summary to {practitioner.email}.")

def monitor_cancellations():
    """
    Monitors canceled appointments and backfills them using the waitlist.
    """
    logging.info("Starting monitor_cancellations job.")
    
    # Fetch appointments with status 'Cancelled'
    canceled_appointments = session.query(Appointment).filter_by(status='Cancelled').all()
    logging.info(f"Found {len(canceled_appointments)} canceled appointments to process.")
    
    for appt in canceled_appointments:
        try:
            process_cancellation(appt.id)
            # Update appointment status to 'Processed' to avoid re-processing
            appt.status = 'Processed'
            session.commit()
            logging.info(f"Processed cancellation for appointment ID {appt.id}.")
        except Exception as e:
            logging.error(f"Error processing cancellation for appointment ID {appt.id}: {e}")

def send_followup_reminders():
    """
    Sends follow-up reminders to patients based on their scheduled follow-up tasks.
    """
    logging.info("Starting send_followup_reminders job.")
    send_followup_reminders()

def send_adherence_report_job():
    """
    Generates and sends adherence reports on patient follow-ups.
    """
    logging.info("Starting send_adherence_report_job.")
    send_adherence_report()

def schedule_jobs():
    """
    Initializes the scheduler and schedules all the necessary jobs.
    """
    scheduler = BackgroundScheduler(timezone=os.getenv('TIMEZONE'))
    
    # Schedule send_reminders to run every hour
    scheduler.add_job(
        send_reminders,
        trigger=IntervalTrigger(hours=1),
        id='send_reminders',
        name='Send appointment reminders every hour',
        replace_existing=True
    )
    
    # Schedule generate_daily_summary to run daily at 6 PM
    scheduler.add_job(
        generate_daily_summary,
        trigger=CronTrigger(hour=18, minute=0),
        id='generate_daily_summary',
        name='Generate daily appointment summary at 6 PM',
        replace_existing=True
    )
    
    # Schedule monitor_cancellations to run every 10 minutes
    scheduler.add_job(
        monitor_cancellations,
        trigger=IntervalTrigger(minutes=10),
        id='monitor_cancellations',
        name='Monitor and process appointment cancellations every 10 minutes',
        replace_existing=True
    )
    
    # Schedule send_followup_reminders to run daily at 9 AM
    scheduler.add_job(
        send_followup_reminders,
        trigger=CronTrigger(hour=9, minute=0),
        id='send_followup_reminders',
        name='Send follow-up reminders at 9 AM daily',
        replace_existing=True
    )
    
    # Schedule send_adherence_report to run daily at 7 PM
    scheduler.add_job(
        send_adherence_report_job,
        trigger=CronTrigger(hour=19, minute=0),
        id='send_adherence_report',
        name='Generate and send adherence reports at 7 PM daily',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    logging.info("Scheduler started and all jobs have been scheduled.")

def main():
    """
    Main function to start the scheduler.
    """
    logging.info("Initializing scheduler.")
    schedule_jobs()

if __name__ == "__main__":
    main()
