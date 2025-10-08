# create_admin.py

from modules.user_auth import UserAuthenticator
import getpass

def main():
    """A simple script to create the first admin user."""
    auth = UserAuthenticator()
    
    print("--- Create SecLog Admin User ---")
    username = input("Enter username for the new admin: ")
    password = getpass.getpass("Enter password: ")
    
    if not username or not password:
        print("Username and password cannot be empty.")
        return

    auth.create_user(username, password)

if __name__ == "__main__":
    main()