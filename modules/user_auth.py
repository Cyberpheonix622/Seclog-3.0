# modules/user_auth.py

import json
import os
import bcrypt

class UserAuthenticator:
    """Handles user creation, authentication, and password management."""
    def __init__(self, user_file="data/users.json"):
        self.user_file = user_file
        self.users = self._load_users()

    def _load_users(self):
        """Loads user data from the JSON file."""
        if os.path.exists(self.user_file):
            with open(self.user_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_users(self):
        """Saves the current user data to the JSON file."""
        os.makedirs(os.path.dirname(self.user_file), exist_ok=True)
        with open(self.user_file, 'w') as f:
            json.dump(self.users, f, indent=4)

    def _hash_password(self, password):
        """Hashes a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def check_password(self, username, password):
        """
        Checks if a provided password matches the stored hash for a user.
        
        Returns:
            bool: True if the password is correct, False otherwise.
        """
        user_data = self.users.get(username.lower())
        if not user_data:
            return False # User does not exist
        
        stored_hash = user_data['password_hash'].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

    def create_user(self, username, password):
        """
        Creates a new user with a hashed password.
        
        Returns:
            bool: True if user was created successfully, False if user already exists.
        """
        if username.lower() in self.users:
            print(f"Error: User '{username}' already exists.")
            return False
        
        hashed_password = self._hash_password(password)
        self.users[username.lower()] = {
            "password_hash": hashed_password
        }
        self._save_users()
        print(f"Successfully created user: {username}")
        return True