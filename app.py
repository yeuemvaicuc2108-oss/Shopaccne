from flask import Flask, render_template, request, redirect, session
import sqlite3, hashlib, time

app = Flask(__name__)
app.secret_key = "secret123"

def db():
    return sqlite3.connect("database.db")

# INIT DATABASE
with db() as con:
    con.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS accounts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game TEXT,
        rank TEXT,
        price INTEGER,
        user TEXT,
        pass TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        acc_id INTEGER,
        code TEXT,
        status TEXT
    )""")

    # tạo admin mặc định
    cur = con.execute("SELECT * FROM users")
    if not cur.fetchone():
        pwd = hashlib.sha256("admin123".encode()).hexdigest()
        con.execute("INSERT INTO users VALUES (1,'admin',?)", (pwd,))

# SHOP
@app.route("/")
def home():
    accs = db().execute("SELECT * FROM accounts").fetchall()
    return render_template("index.html", accs=accs)

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["user"]
        p = hashlib.sha256(request.form["pass"].encode()).hexdigest()
        cur = db().execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (u,p)
        )
        if cur.fetchone():
            session["admin"] = True
            return redirect("/admin")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ADMIN
@app.route("/admin", methods=["GET","POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    con = db()
    if request.method == "POST":
        con.execute(
            "INSERT INTO accounts(game,rank,price,user,pass) VALUES(?,?,?,?,?)",
            (
                request.form["game"],
                request.form["rank"],
                request.form["price"],
                request.form["user"],
                request.form["pass"]
            )
        )
        con.commit()
        return redirect("/admin")

    accs = con.execute("SELECT * FROM accounts").fetchall()
    orders = con.execute("SELECT * FROM orders").fetchall()
    return render_template("admin.html", accs=accs, orders=orders)

@app.route("/delete/<int:id>")
def delete(id):
    if session.get("admin"):
        con = db()
        con.execute("DELETE FROM accounts WHERE id=?", (id,))
        con.commit()
    return redirect("/admin")

# MUA
@app.route("/buy/<int:id>")
def buy(id):
    code = f"ACC{int(time.time())}"
    con = db()
    con.execute(
        "INSERT INTO orders(acc_id,code,status) VALUES(?,?,?)",
        (id, code, "PENDING")
    )
    con.commit()
    return redirect(f"/checkout/{code}")

# THANH TOÁN
@app.route("/checkout/<code>")
def checkout(code):
    con = db()
    order = con.execute("SELECT * FROM orders WHERE code=?", (code,)).fetchone()
    acc = con.execute("SELECT * FROM accounts WHERE id=?", (order[1],)).fetchone()
    return render_template("checkout.html", acc=acc, code=code)

# ADMIN XÁC NHẬN
@app.route("/confirm/<int:id>")
def confirm(id):
    if session.get("admin"):
        con = db()
        con.execute("UPDATE orders SET status='PAID' WHERE id=?", (id,))
        con.commit()
    return redirect("/admin")

# GIAO ACC 1 LẦN
@app.route("/view/<code>")
def view(code):
    con = db()
    order = con.execute(
        "SELECT * FROM orders WHERE code=? AND status='PAID'",
        (code,)
    ).fetchone()
    if not order:
        return "Chưa xác nhận"

    acc = con.execute(
        "SELECT * FROM accounts WHERE id=?",
        (order[1],)
    ).fetchone()

    con.execute("DELETE FROM accounts WHERE id=?", (acc[0],))
    con.execute("DELETE FROM orders WHERE id=?", (order[0],))
    con.commit()

    return render_template("view_acc.html", acc=acc)

if __name__ == "__main__":
    app.run()