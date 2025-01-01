import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
from hunterIo import verify
from database import session
from models import Reminder
from datetime import datetime

load_dotenv()

SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587


def send_mail(to_email,subject,body):
    """
    SEnds email using SMTP Protocol IF Success REtutns true else false
    """

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
    except Exception as e:
        print(f"Failed to send test email: {e}")

    
def send_remainder(appointment):
    patient = appointment.patient
    appointment_time = appointment.appointment_datetime.strftime("%Y-%m-%d %H:%M")
    subject= 'Appointment Reminder'
    body = f"Dear {patient.name},\n\nThis is a reminder for your appointment on {appointment_time}.\n\nThank you."

    
    if send_mail(patient.email,subject=subject,body=body):
        reminder = Reminder(
                appointment_id=appointment.id,
                sent=datetime.now(),
                
        )
        session.add(reminder)
        session.commit()
        return True
    
def send_email_with_attachment(to_email, subject, body, attachment_path):
    # Create a multipart message
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    
    # Attach the body text
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach the file
    with open(attachment_path, 'rb') as file:
        part = MIMEApplication(file.read(), Name=os.path.basename(attachment_path))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
    msg.attach(part)
    
    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(SMTP_USER, SMTP_PASSWORD)  # Login to SMTP server
        server.send_message(msg)  # Send the email
        server.quit()  # Disconnect from the server
        print(f"Email with attachment sent to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email with attachment to {to_email}: {e}")
        return False