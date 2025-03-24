import socket
import threading
import json
import os
from datetime import datetime

# Server configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 65432

# File to store data
DATA_FILE = "data.json"
ATTENDANCE_LOG_FILE = "attendance_log.json"

# Load data from file
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as file:
                data = json.load(file)
                # Ensure all required keys are present
                if "attendance" not in data:
                    data["attendance"] = {}
                if "students_online" not in data:
                    data["students_online"] = {}
                if "teachers_online" not in data:
                    data["teachers_online"] = {}
                if "active_timers" not in data:
                    data["active_timers"] = {}
                return data
        except json.JSONDecodeError:
            # If the file is empty or invalid, return default data
            return {"attendance": {}, "students_online": {}, "teachers_online": {}, "active_timers": {}}
    return {"attendance": {}, "students_online": {}, "teachers_online": {}, "active_timers": {}}

# Save data to file
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Log attendance to a separate file
def log_attendance(username):
    log_entry = {username: datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    if os.path.exists(ATTENDANCE_LOG_FILE):
        with open(ATTENDANCE_LOG_FILE, "r") as file:
            try:
                log_data = json.load(file)
            except json.JSONDecodeError:
                log_data = {}
    else:
        log_data = {}
    log_data.update(log_entry)
    with open(ATTENDANCE_LOG_FILE, "w") as file:
        json.dump(log_data, file, indent=4)

# Handle client connections
def handle_client(conn, addr):
    print(f"Connected by {addr}")
    data = load_data()
    while True:
        try:
            message = conn.recv(1024).decode("utf-8")
            if not message:
                break

            message = json.loads(message)
            action = message.get("action")

            if action == "login":
                username = message.get("username")
                role = message.get("role")
                if role == "student":
                    data["students_online"][username] = conn
                elif role == "teacher":
                    data["teachers_online"][username] = conn
                save_data(data)
                broadcast_attendance()

            elif action == "start_timer":
                username = message.get("username")
                data["active_timers"][username] = True
                save_data(data)
                broadcast_attendance()

            elif action == "stop_timer":
                username = message.get("username")
                if username in data["active_timers"]:
                    del data["active_timers"][username]
                save_data(data)
                broadcast_attendance()
                log_attendance(username)  # Log attendance when timer stops

        except Exception as e:
            print(f"Error: {e}")
            break

    # Remove the user from the online list when they disconnect
    for username, client_conn in data["students_online"].items():
        if client_conn == conn:
            del data["students_online"][username]
            save_data(data)
            broadcast_attendance()
            break
    for username, client_conn in data["teachers_online"].items():
        if client_conn == conn:
            del data["teachers_online"][username]
            save_data(data)
            broadcast_attendance()
            break

    conn.close()

# Broadcast attendance data to all clients
def broadcast_attendance():
    data = load_data()
    active_students = list(data["active_timers"].keys())
    attendance_data = json.dumps({"action": "update_attendance", "data": active_students}).encode("utf-8")
    for conn in data["students_online"].values():
        conn.send(attendance_data)
    for conn in data["teachers_online"].values():
        conn.send(attendance_data)

# Start the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server started on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
