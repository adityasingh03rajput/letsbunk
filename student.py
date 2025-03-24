import tkinter as tk
from tkinter import messagebox
import json
import os
import socket
import threading

# File to store user data
USER_FILE = "users.json"

# Server configuration
HOST = "192.168.189.185"  # Replace with the server's IP address (Pranav's computer)
PORT = 65432

# Connect to the server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Load existing users from the file
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as file:
            return json.load(file)
    return {}

# Save users to the file
def save_users(users):
    with open(USER_FILE, "w") as file:
        json.dump(users, file, indent=4)

# Login function
def login():
    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        messagebox.showwarning("Input Error", "Please fill in all fields.")
        return

    users = load_users()
    if username in users and users[username] == password:
        messagebox.showinfo("Login Success", "Login successful!")
        clear_entries()
        root.destroy()  # Close the login window
        start_attendance_timer(username)  # Launch the attendance timer
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")
        clear_entries()

# Clear input fields
def clear_entries():
    entry_username.delete(0, tk.END)
    entry_password.delete(0, tk.END)

# Function to send data to the server
def send_data(action, username=None):
    data = {"action": action, "username": username, "role": "student"}
    client_socket.send(json.dumps(data).encode("utf-8"))

# Function to update the timer
def update_timer(username):
    global timer, timer_started
    if timer_started:
        if timer > 0:
            timer_label.config(text=f"Time remaining: {timer} seconds")
            timer -= 1
            root_attend.after(1000, update_timer, username)  # Schedule the next update
        else:
            timer_label.config(text="Time's up! Attendance Marked.", fg="green")
            messagebox.showinfo("Attendance", "You are now marked as present.")
            timer_started = False
            start_button.config(state=tk.NORMAL)
            send_data("stop_timer", username)  # Notify server that the timer has stopped

# Function to start the timer
def start_timer(username):
    global timer, timer_started
    timer = 10  # Reset the timer
    timer_started = True
    start_button.config(state=tk.DISABLED)
    send_data("start_timer", username)  # Notify server that the timer has started
    update_timer(username)

# Function to start the attendance timer system
def start_attendance_timer(username):
    global root_attend, timer_label, start_button, timer, timer_started

    # Create the attendance timer window
    root_attend = tk.Tk()
    root_attend.title("Attendance Timer")
    root_attend.geometry("400x250")
    root_attend.resizable(False, False)  # Disable resizing

    # Create and place widgets
    title_label = tk.Label(root_attend, text="Attendance Timer 🕒", font=("Arial", 18, "bold"))
    title_label.pack(pady=10)

    instructions_label = tk.Label(
        root_attend,
        text="Click 'Start Timer' to begin. The timer will mark you as present.",
        wraplength=350,
        font=("Arial", 10)
    )
    instructions_label.pack(pady=10)

    timer_label = tk.Label(root_attend, text="", font=("Arial", 14))
    timer_label.pack(pady=20)

    start_button = tk.Button(
        root_attend,
        text="Start Timer",
        command=lambda: start_timer(username),
        font=("Arial", 12),
        bg="#4CAF50",  # Green background
        fg="white",    # White text
        padx=20,
        pady=10
    )
    start_button.pack(pady=10)

    # Initialize global variables
    timer = 10
    timer_started = False

    # Start the Tkinter event loop for the attendance timer
    root_attend.mainloop()

# Create the main login window
root = tk.Tk()
root.title("Signup and Login System")
root.geometry("300x200")

# Username Label and Entry
label_username = tk.Label(root, text="Username:")
label_username.pack(pady=5)
entry_username = tk.Entry(root)
entry_username.pack(pady=5)

# Password Label and Entry
label_password = tk.Label(root, text="Password:")
label_password.pack(pady=5)
entry_password = tk.Entry(root, show="*")
entry_password.pack(pady=5)

# Login Button
button_login = tk.Button(root, text="Login", command=login)
button_login.pack(pady=10)

# Run the login application
root.mainloop()
