import logging
import os
from database import session
from models import Waitlist
from datetime import datetime

def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        filename='logs/app.log',
        level=logging.INFO,
        format='%(asctime)s:%(levelname)s:%(message)s'
    )

def prioritize_waitlist(requested_datetime):
    """
    Prioritizes the waitlist and returns the next patient to assign the open slot.
    
    Parameters:
        requested_datetime (datetime): The datetime of the open appointment slot.
        
    Returns:
        Waitlist: The selected waitlist entry or None if waitlist is empty.
    """
    # Fetch waitlist entries matching the requested_datetime, ordered by priority and added_at
    waitlist_entry = session.query(Waitlist).filter_by(
        requested_datetime=requested_datetime
    ).order_by(
        Waitlist.priority.asc(),
        Waitlist.added_at.asc()
    ).first()
    
    return waitlist_entry
