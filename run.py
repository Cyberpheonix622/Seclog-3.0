import customtkinter as ctk
from main_app import SecurityLogApp

if __name__ == "__main__":
    
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("dark-blue")

    app = SecurityLogApp()
    app.mainloop()