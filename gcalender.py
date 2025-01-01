import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import datetime
from models import User
from database import session

# Define the scope for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service():
    creds = None

    # Check if token.pickle file exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no valid credentials, initiate the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials to token.pickle
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            print("token.pickle created successfully!")

    service_new = build('calendar', 'v3', credentials=creds)

    return service_new

# Test the function



#######################################

def add_app_to_cal(appointment):
    service = get_calendar_service()
    
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
        


