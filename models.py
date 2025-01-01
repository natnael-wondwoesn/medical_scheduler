from sqlalchemy import Column,Integer,String,DateTime,Boolean,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base =declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String,nullable=False)
    role = Column(String,nullable= False)
    email = Column(String,unique=True,nullable=False)

    appointments = relationship("Appointment",back_populates="user")

class Patient(Base):
    __tablename__ = 'patients'

    id = Column(Integer , primary_key=True,index=True)
    name= Column(String,nullable=False)
    email = Column(String,nullable=False)
    phone_number = Column(String,nullable=True)
    email_verified = Column(Boolean,default=False,nullable=False)

    appointments = relationship("Appointment",back_populates="patient")

    
class Appointment(Base):
    __tablename__= 'appointments'

    id = Column(Integer,primary_key=True,index=True)
    patient_id = Column(Integer,ForeignKey('patients.id'),nullable=False)
    user_id = Column(Integer,ForeignKey('users.id'),nullable=False)
    appointment_datetime = Column(DateTime, nullable=False)
    status = Column(String,default="Scheduled")

    patient = relationship("Patient",back_populates="appointments")
    user = relationship("User",back_populates="appointments")
    reminders = relationship("Reminder",back_populates="appointments")





class Reminder(Base):
    __tablename__ = 'reminders'

    id = Column(Integer,primary_key=True,index=True)
    appointment_id = Column(Integer,ForeignKey('appointments.id'),nullable=False)
    sent = Column(DateTime,nullable=False)

    appointments = relationship("Appointment",back_populates="reminders")



class Waitlist(Base):
    __tablename__ = 'waitlist'
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    requested_datetime = Column(DateTime, nullable=False)
    added_at = Column(DateTime, nullable=False)
    priority = Column(Integer, default=1)  # Lower number = higher priority
    
    patient = relationship("Patient")


class FollowUp(Base):
    __tablename__ = 'followups'
    
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=False)
    followup_type = Column(String, nullable=False)  
    due_date = Column(DateTime, nullable=False)
    status = Column(String, default='Pending')  
    
    appointment = relationship("Appointment")
    
    adherence = relationship("FollowUpAdherence", back_populates="followup", uselist=False)

class FollowUpAdherence(Base):
    __tablename__ = 'followup_adherence'
    
    id = Column(Integer, primary_key=True, index=True)
    followup_id = Column(Integer, ForeignKey('followups.id'), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    followup = relationship("FollowUp", back_populates="adherence")