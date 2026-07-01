from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection
import os
from dotenv import load_dotenv

load_dotenv()
print("SECRET KEY:", os.getenv("SECRET_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

#--------------------- REWARDS CHECKING ---------------

def check_and_award_rewards(user_id):
    conn = get_connection()
    cur = conn.cursor()

    # Count completed tasks
    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s AND is_completed = TRUE", (user_id,))
    completed_tasks = cur.fetchone()[0]

    # Count completed goals
    cur.execute("SELECT COUNT(*) FROM goals WHERE user_id = %s AND is_completed = TRUE", (user_id,))
    completed_goals = cur.fetchone()[0]

    # Fetch already earned reward titles
    cur.execute("SELECT title FROM rewards WHERE user_id = %s", (user_id,))
    earned = [row[0] for row in cur.fetchall()]

    new_rewards = []

    if completed_tasks >= 1 and "First Step" not in earned:
        new_rewards.append(("First Step", "Completed your first task!", "🌱"))

    if completed_tasks >= 5 and "On a Roll" not in earned:
        new_rewards.append(("On a Roll", "Completed 5 tasks!", "🔥"))

    if completed_tasks >= 10 and "Task Master" not in earned:
        new_rewards.append(("Task Master", "Completed 10 tasks!", "💪"))

    if completed_goals >= 1 and "Goal Getter" not in earned:
        new_rewards.append(("Goal Getter", "Completed your first goal!", "🎯"))

    if completed_goals >= 3 and "Overachiever" not in earned:
        new_rewards.append(("Overachiever", "Completed 3 goals!", "⭐"))

    for title, description, icon in new_rewards:
        cur.execute(
            "INSERT INTO rewards (user_id, title, description, icon) VALUES (%s, %s, %s, %s)",
            (user_id, title, description, icon)
        )

    conn.commit()
    cur.close()
    conn.close()

    return new_rewards

# -------------------- REWARDS CHECKING ENDS HERE -----------------------


# --------------------- STERAK UPDATE FUNCTION ---------------------------

def update_streak(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT streak, last_activity_date FROM users WHERE user_id = %s",
        (user_id,)
    )
    result = cur.fetchone()
    current_streak = result[0] or 0
    last_date = result[1]

    from datetime import date
    today = date.today()

    if last_date is None:
        new_streak = 1
    elif last_date == today:
        new_streak = current_streak  # already updated today
    elif (today - last_date).days == 1:
        new_streak = current_streak + 1  # consecutive day
    else:
        new_streak = 1  # streak broken, reset

    cur.execute(
        "UPDATE users SET streak = %s, last_activity_date = %s WHERE user_id = %s",
        (new_streak, today, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return new_streak



@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )
            conn.commit()
            flash("Account created! Please log in.")
            return redirect(url_for("login"))
        except Exception as e:
            conn.rollback()
            flash(f"Error: {e}")
        finally:
            cur.close()
            conn.close()

    return render_template("signup.html")

# ************* login **************


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, password_hash FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash(f"Welcome back, {user[1]}!")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.")

    return render_template("login.html")

# ***************** log out *********************

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


# ********************************************************************

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    page = request.args.get("page", 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_connection()
    cur = conn.cursor()

    # Paginated tasks
    cur.execute(
        """SELECT task_id, title, due_date, is_completed, created_at
           FROM tasks WHERE user_id = %s
           ORDER BY created_at DESC
           LIMIT %s OFFSET %s""",
        (session["user_id"], per_page, offset)
    )
    tasks = cur.fetchall()

    # Total task count for pagination
    cur.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id = %s",
        (session["user_id"],)
    )
    total_tasks = cur.fetchone()[0]
    total_pages = (total_tasks + per_page - 1) // per_page

    # Goals for dropdown
    cur.execute(
        "SELECT goal_id, title FROM goals WHERE user_id = %s AND is_completed = FALSE ORDER BY created_at DESC",
        (session["user_id"],)
    )
    goals = cur.fetchall()

    # Stats
    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s AND is_completed = TRUE", (session["user_id"],))
    completed_tasks = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM goals WHERE user_id = %s AND is_completed = TRUE", (session["user_id"],))
    completed_goals = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM rewards WHERE user_id = %s", (session["user_id"],))
    total_rewards = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s AND is_completed = FALSE", (session["user_id"],))
    pending_tasks = cur.fetchone()[0]

    cur.execute("SELECT streak FROM users WHERE user_id = %s", (session["user_id"],))
    streak = cur.fetchone()[0] or 0

    cur.close()
    conn.close()

    return render_template("dashboard.html",
        tasks=tasks,
        goals=goals,
        completed_tasks=completed_tasks,
        completed_goals=completed_goals,
        total_rewards=total_rewards,
        pending_tasks=pending_tasks,
        streak=streak,
        page=page,
        total_pages=total_pages
    )


@app.route("/tasks/add", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form["title"]
    due_date = request.form["due_date"] or None
    goal_id = request.form.get("goal_id") or None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO tasks (user_id, title, due_date, goal_id) VALUES (%s, %s, %s, %s)",
            (session["user_id"], title, due_date, goal_id)
        )
        conn.commit()
        flash("Task added!")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("dashboard"))


@app.route("/tasks/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE tasks SET is_completed = TRUE, completed_at = CURRENT_TIMESTAMP WHERE task_id = %s AND user_id = %s",
            (task_id, session["user_id"])
        )
        conn.commit()
        flash("Task completed! 🎉")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

        update_streak(session["user_id"])

        new_rewards = check_and_award_rewards(session["user_id"])
    for reward in new_rewards:
        flash(f"🏆 New Trophy Unlocked: {reward[2]} {reward[0]}!")

    return redirect(url_for("dashboard"))


@app.route("/tasks/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM tasks WHERE task_id = %s AND user_id = %s",
            (task_id, session["user_id"])
        )
        conn.commit()
        flash("Task deleted.")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/goals")
def goals():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # Fetch goals with task progress
    cur.execute("""
        SELECT g.goal_id, g.title, g.description, g.target_date, g.is_completed,
               COUNT(t.task_id) AS total_tasks,
               SUM(CASE WHEN t.is_completed THEN 1 ELSE 0 END) AS completed_tasks
        FROM goals g
        LEFT JOIN tasks t ON t.goal_id = g.goal_id
        WHERE g.user_id = %s
        GROUP BY g.goal_id
        ORDER BY g.created_at DESC
    """, (session["user_id"],))
    goals = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("goals.html", goals=goals)


@app.route("/goals/add", methods=["POST"])
def add_goal():
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form["title"]
    description = request.form["description"] or None
    target_date = request.form["target_date"] or None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO goals (user_id, title, description, target_date) VALUES (%s, %s, %s, %s)",
            (session["user_id"], title, description, target_date)
        )
        conn.commit()
        flash("Goal created!")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("goals"))


@app.route("/goals/complete/<int:goal_id>", methods=["POST"])
def complete_goal(goal_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE goals SET is_completed = TRUE WHERE goal_id = %s AND user_id = %s",
            (goal_id, session["user_id"])
        )
        conn.commit()
        flash("Goal completed! 🏆")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}")
    finally:
        cur.close()
        conn.close()
        new_rewards = check_and_award_rewards(session["user_id"])
    for reward in new_rewards:
        flash(f"🏆 New Trophy Unlocked: {reward[2]} {reward[0]}!")

    return redirect(url_for("goals"))


@app.route("/goals/delete/<int:goal_id>", methods=["POST"])
def delete_goal(goal_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM goals WHERE goal_id = %s AND user_id = %s",
            (goal_id, session["user_id"])
        )
        conn.commit()
        flash("Goal deleted.")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("goals"))

# ------------------------------- REWARDS ROUTE -----------------------------

@app.route("/rewards")
def rewards():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT title, description, icon, earned_at FROM rewards WHERE user_id = %s ORDER BY earned_at DESC",
        (session["user_id"],)
    )
    rewards = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("rewards.html", rewards=rewards)

# ----------------------------- REWARDS ROUTE ENDS -----------------------------

# ----------------------------- EDIT TASK ROUTE --------------------------

@app.route("/tasks/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        due_date = request.form["due_date"] or None
        try:
            cur.execute(
                "UPDATE tasks SET title = %s, due_date = %s WHERE task_id = %s AND user_id = %s",
                (title, due_date, task_id, session["user_id"])
            )
            conn.commit()
            flash("Task updated!")
            return redirect(url_for("dashboard"))
        except Exception as e:
            conn.rollback()
            flash(f"Error: {e}")
        finally:
            cur.close()
            conn.close()

    cur.execute(
        "SELECT task_id, title, due_date FROM tasks WHERE task_id = %s AND user_id = %s",
        (task_id, session["user_id"])
    )
    task = cur.fetchone()
    cur.close()
    conn.close()

    if not task:
        flash("Task not found.")
        return redirect(url_for("dashboard"))

    return render_template("edit_task.html", task=task)


@app.route("/goals/edit/<int:goal_id>", methods=["GET", "POST"])
def edit_goal(goal_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"] or None
        target_date = request.form["target_date"] or None
        try:
            cur.execute(
                "UPDATE goals SET title = %s, description = %s, target_date = %s WHERE goal_id = %s AND user_id = %s",
                (title, description, target_date, goal_id, session["user_id"])
            )
            conn.commit()
            flash("Goal updated!")
            return redirect(url_for("goals"))
        except Exception as e:
            conn.rollback()
            flash(f"Error: {e}")
        finally:
            cur.close()
            conn.close()

    cur.execute(
        "SELECT goal_id, title, description, target_date FROM goals WHERE goal_id = %s AND user_id = %s",
        (goal_id, session["user_id"])
    )
    goal = cur.fetchone()
    cur.close()
    conn.close()

    if not goal:
        flash("Goal not found.")
        return redirect(url_for("goals"))

    return render_template("edit_goal.html", goal=goal)



if __name__ == "__main__":
    app.run(debug=True)