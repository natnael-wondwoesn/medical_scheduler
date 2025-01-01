import logging
import os

def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        filename='logs/app.log',
        level=logging.INFO,
        format='%(asctime)s:%(levelname)s:%(message)s'
    )
