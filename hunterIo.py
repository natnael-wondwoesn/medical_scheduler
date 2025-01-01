import os
from pyhunter import PyHunter
from dotenv import load_dotenv
import requests

load_dotenv()

HUNT_IO_KEY = os.getenv('HUNTERIO_API_KEY')

def verify(email):
    # Just to Check If the email is valid  Returns A TRue or False Boolean Value

    try:
        url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNT_IO_KEY}"

        response = requests.get(url)
        
        if response.status_code==200 and response.json()['data']['score'] > 60:
            print("dctfvygbuhinjmk")
            return True
        return False
    except Exception as e:
        print(f"Error verifying email: {e}")
        return False

