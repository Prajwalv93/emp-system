import os, time
import pymysql
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

def get_conn():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "mysql-db"),
        user=os.environ.get("DB_USER", "empuser"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "empdb"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

def init_db():
    # MySQL takes 20-40 s to boot, so retry instead of crashing
    for _ in range(30):
        try:
            con = get_conn()
            with con.cursor() as cur:
                cur.execute("""CREATE TABLE IF NOT EXISTS employees(
                    emp_id VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    department VARCHAR(50),
                    join_date DATE)""")
            con.close()
            return
        except pymysql.err.OperationalError:
            time.sleep(2)
    raise RuntimeError("Database not reachable")

def get_columns(cur):
    cur.execute("SHOW COLUMNS FROM employees")
    return [c["Field"] for c in cur.fetchall()]

def ids(cols):
    return ",".join("`" + c + "`" for c in cols)

PAGE = """
<h2>Employee Management System</h2>
<form method="post" action="/add">
{% for c in cols %}<input name="{{c}}" placeholder="{{c}}" {{ 'required' if loop.first }}> {% endfor %}
<button>Add / Update</button>
</form><br>
<form method="get"><input name="q" placeholder="Search anything" value="{{q}}"><button>Search</button></form>
<p>{{ rows|length }} record(s)</p>
<table border=1 cellpadding=5>
<tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>
{% for r in rows %}<tr>{% for c in cols %}<td>{{ r[c] if r[c] is not none else '' }}</td>{% endfor %}</tr>{% endfor %}
</table>"""

@app.route("/")
def index():
    q = request.args.get("q", "")
    con = get_conn()
    with con.cursor() as cur:
        cols = get_columns(cur)
        if q:
            cur.execute(f"SELECT * FROM employees WHERE CONCAT_WS(' ',{ids(cols)}) LIKE %s", (f"%{q}%",))
        else:
            cur.execute("SELECT * FROM employees")
        rows = cur.fetchall()
    con.close()
    return render_template_string(PAGE, cols=cols, rows=rows, q=q)

@app.route("/add", methods=["POST"])
def add():
    con = get_conn()
    with con.cursor() as cur:
        cols = [c for c in get_columns(cur) if c in request.form]
        vals = [request.form[c] or None for c in cols]
        cur.execute(f"REPLACE INTO employees ({ids(cols)}) VALUES ({','.join(['%s'] * len(cols))})", vals)
    con.close()
    return redirect("/")

@app.route("/health")
def health():
    con = get_conn()
    with con.cursor() as cur:
        cur.execute("SELECT 1")
    con.close()
    return "ok"

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
