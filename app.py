from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-later"

@app.route("/")
def home():
    return "TaskQuest is running!"

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

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT task_id, title, due_date, is_completed, created_at FROM tasks WHERE user_id = %s ORDER BY created_at DESC",
        (session["user_id"],)
    )
    tasks = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("dashboard.html", tasks=tasks)



@app.route("/tasks/add", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form["title"]
    due_date = request.form["due_date"] or None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO tasks (user_id, title, due_date) VALUES (%s, %s, %s)",
            (session["user_id"], title, due_date)
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



if __name__ == "__main__":
    app.run(debug=True)