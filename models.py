from sqlalchemy import Column,Integer,String,DateTime,Boolean,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base =declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String,nullable=False)
    role = Column(String,nullable= False)
    email = Column(String,unique=True,nullable=False)

    appointments = relationship("Appointment",back_populates="user")


class Patient(Base)
    __tablename__ = 'patients'

    id = Column(Integer , primary_key=True,index=True)
    name= Column(String,nullable=False)
    email = Column(String,nullable=False)
    phone_number = Column(String,nullable=True)
    email_checked = Column(Boolean,default=False,nullable=False)

    