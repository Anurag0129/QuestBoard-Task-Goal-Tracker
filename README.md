# 🏆 QuestBoard – Task & Goal Tracker

A gamified task and goal tracker built with Flask, PostgreSQL, and HTML/CSS.
Track your tasks, set goals, earn trophies, and build daily streaks.

## Features
- User signup, login, logout with secure password hashing
- Task management — add, complete, edit, delete tasks
- Goal tracking with progress bars
- Link tasks to goals
- Trophy/reward system for hitting milestones
- Streak counter for consecutive days of activity
- Stats dashboard — completed tasks, goals, trophies, pending tasks

## Tech Stack
- **Backend:** Python, Flask
- **Database:** PostgreSQL, psycopg2
- **Frontend:** HTML, CSS, Jinja2
- **Auth:** werkzeug.security (password hashing), Flask sessions

## Setup Instructions

1. Clone the repo
2. Create a virtual environment and install dependencies:
        
        python -m venv venv
        
        venv\Scripts\activate
        
        pip install -r requirements.txt

3. Create a PostgreSQL database called `taskquest`
4. Copy `.env.example` to `.env` and fill in your credentials
5. Run the SQL schema to create tables (see `schema.sql`)
6. Run the app:

        python app.py

7. Visit `http://127.0.0.1:5000`

## Project Structure

        
        taskquest/
        
        ├── app.py          # Flask routes and app logic
        ├── db.py           # PostgreSQL connection
        ├── templates/      # Jinja2 HTML templates
        ├── static/         # CSS and images
        ├── .env.example    # Environment variable template
        └── requirements.txt

