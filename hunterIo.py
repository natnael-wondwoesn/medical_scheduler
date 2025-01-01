import os
from pyhunter import PyHunter
from dotenv import load_dotenv

load_dotenv()

HUNT_IO_KEY = os.getenv('HUNTERIO_API_KEY')
hunter = PyHunter(HUNT_IO_KEY)

def verify(email):
    # Just to Check If the email is valid  Returns A TRue or False Boolean Value

    res = hunter.email_verifier(email)

    if res and res.get('result') == 'deliverable':
        return True
    return False
