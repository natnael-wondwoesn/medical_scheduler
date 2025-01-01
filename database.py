from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from dotenv import load_dotenv
load_dotenv

DB_URL = os.getenv('DB_URL','sqlite:///data/medical_scheduler.db')

engine = create_engine(DB_URL,echo=True)

SessLocal = sessionmaker(bind=engine)

session = SessLocal()

