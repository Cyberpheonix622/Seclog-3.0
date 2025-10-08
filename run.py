# run.py

import customtkinter as ctk
from main_app import SecurityLogApp
from modules.user_auth import UserAuthenticator
from ui_components import LoginWindow

class AppController:
    """Controls the application flow from login to main app launch."""
    def __init__(self):
        # Set theme first
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")
        
        # Create a hidden root window that the login window can sit on top of
        self.root = ctk.CTk()
        self.root.withdraw()

        self.auth = UserAuthenticator()
        
        # Create and show the login window
        self.login_window = LoginWindow(master=self.root, 
                                        auth_instance=self.auth, 
                                        on_success_callback=self.launch_main_app)
        
    def run(self):
        """Start the main event loop."""
        self.root.mainloop()

    def launch_main_app(self):
        """Destroys the login root and launches the main SecurityLogApp."""
        self.root.destroy() # Close the hidden root window
        
        # Create and run the main application
        main_app = SecurityLogApp()
        main_app.mainloop()

if __name__ == "__main__":
    controller = AppController()
    controller.run()