from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import csv
import os
from passlib.context import CryptContext  # For password hashing

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the path to the CSV files
USERS_FILE = "users.csv"
TASKS_FILE = "tasks.csv"

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    password: str 

class Task(BaseModel):
    task: str
    deadline: str 
    user: str

def initialize_files():
    """
    Ensures that the required CSV files (users.csv and tasks.csv) exist.
    If the files do not exist, they will be created with appropriate headers.
    """
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["username", "password", "tasks"])  # Added "tasks" column

    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["task", "deadline", "user"])

# Ensure CSV files exist when the application starts
initialize_files()

@app.post("/create_user/")
async def create_user(user: User):
    """
    Creates a new user by adding their username, hashed password, and an empty task list to users.csv.
    """
    try:
        # Check if the user already exists
        with open(USERS_FILE, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["username"] == user.username:
                    return {"status": "User already exists"}

        # Hash the password before storing it
        hashed_password = pwd_context.hash(user.password)

        # Add the new user with an empty task field
        with open(USERS_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([user.username, hashed_password, ""])  # Empty tasks initially

        return {"status": "User Created"}
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Users file not found.")

@app.post("/create_task/")
async def create_task(task: Task):
    """
    Creates a new task by adding the task description, deadline, and user to tasks.csv.
    Also updates the user's task list in users.csv.
    """
    try:
        user_found = False
        users_data = []

        # Read and check if the user exists, update their task list
        with open(USERS_FILE, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["username"] == task.user:
                    user_found = True
                    existing_tasks = row["tasks"].split(";") if row["tasks"] else []
                    existing_tasks.append(f"{task.task} (Deadline: {task.deadline})")
                    row["tasks"] = ";".join(existing_tasks)
                users_data.append(row)

        if not user_found:
            return {"status": "User does not exist"}

        # Write the updated user data back to users.csv
        with open(USERS_FILE, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["username", "password", "tasks"])
            writer.writeheader()
            writer.writerows(users_data)

        # Add the new task to tasks.csv
        with open(TASKS_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([task.task, task.deadline, task.user])

        return {"status": "Task Created"}
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Tasks file not found.")

@app.get("/get_tasks/")
async def get_tasks(name: str):
    """
    Retrieves all tasks associated with a specific user from users.csv.
    """
    try:
        with open(USERS_FILE, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["username"] == name:
                    tasks_list = row["tasks"].split(";") if row["tasks"] else []
                    return {"tasks": tasks_list}

        return {"status": "User not found"}
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Users file not found.")
