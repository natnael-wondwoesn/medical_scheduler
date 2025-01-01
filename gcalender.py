import os
import datetime
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from database import session
from models import Appointment,User
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_ser():
    cred = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('calendar', 'v3', credentials=creds)
    return service



#######################################

def add_app_to_cal(appointment):
    service = get_calendar_ser()
    user = session.query(User).filter_by(id=appointment.user_id).first()
    if not user:
        print("Doctor not found for appointment")
        return False
    
    event = {
        'Summary':f"Appointment with {appointment.patient.name}",
        "Description": f"Patient ID: {appointment.patient.id}",
        "start":{
            'dateTime':appointment.appointment_datetime.isoformat(),
            'timeZone': os.getenv('TIMEZONE','UTC')
        },
        'end':{
            'dateTime':(appointment.appointment_datetime + datetime.timedelta(minutes=60)).isoformat(),
            'timeZone': os.getenv('TIMEZONE','UTC')
        },
        'attendess':[
            {'Doctor email':user.email},
            {'Patient Email': appointment.patient.email},
        ],
        'remainders':{
            'useDefault':False,
            'overrides':[
                {'method':'email','minutes':24 * 60},
                {'method':'email','minutes':30},

            ],
        },
    }

    try:
        event = service.events().insert(calendarId='primary',body=event).execute()
        print(f"Event Created:{event.get('htmlLink')}")
        return True
    except Exception as q:
        print(f"Erroor Creating Calendar Event: {q}")
        


