import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from hunterIo import verify
from database import session
from models import Reminder
from datetime import datetime

load_dotenv()

SMTP_SERV = 'smtp.gmail.com'
SMTP_PORT = 586
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASSWORD')


def send_mail(to_email,subject,body):
    """
    SEnds email using SMTP Protocol IF Success REtutns true else false
    """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email

    try:
        server = smtplib.SMTP(SMTP_SERV,SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER,SMTP_PASS)
        server.send_message(msg)
        server.quit()

        print(f"Email sent to {to_email}")
        return True
    
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False
    
def send_remainder(appointment):
    patient = appointment.patient
    appointment_time = appointment.appointment_date.strftime("%Y-%m-%d %H:%M")
    subject= 'Appointment Reminder'
    body = f"Dear {patient.name},\n\nThis is a reminder for your appointment on {appointment_time}.\n\nThank you."

    if verify(patient.email):
        if send_mail(patient.email,subject=subject,body=body):
            reminder = Reminder(
                    appointment_id=appointment.id,
                    sent=datetime.now(),
                    
            )
            session.add(reminder)
            session.commit()
            return True
    return False