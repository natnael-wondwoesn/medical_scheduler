# add_user.py
from database import session
from models import User

def add_user(name, role, email):
    """
    Adds a new user to the database.
    
    Parameters:
        name (str): Name of the user.
        role (str): Role of the user ('Front Desk Medical Assistant' or 'General Practitioner').
        email (str): Email address of the user.
    """
    # Check if user already exists
    existing_user = session.query(User).filter_by(email=email).first()
    if existing_user:
        print(f"User with email {email} already exists.")
        return
    
    # Create a new User instance
    new_user = User(
        name=name,
        role=role,
        email=email
    )
    # Add and commit to the database
    session.add(new_user)
    session.commit()
    print(f"User {name} added successfully.")

if __name__ == "__main__":
    # Example: Adding a Front Desk Medical Assistant
    add_user("Sarah Jones", "Front Desk Medical Assistant", "sarah.jones@example.com")
    
    # Example: Adding a General Practitioner
    add_user("Dr. Emily Carter", "General Practitioner", "emily.carter@example.com")
