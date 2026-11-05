import csv, sys
from app import get_conn, init_db

def main(path):
    init_db()
    con = get_conn()
    with con.cursor() as cur, open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        raw = reader.fieldnames
        cols = [h.strip() for h in raw]
        cur.execute("SHOW COLUMNS FROM employees")
        existing = {c["Field"].lower() for c in cur.fetchall()}
        for h in cols:
            if h.lower() not in existing:
                cur.execute(f"ALTER TABLE employees ADD COLUMN `{h}` VARCHAR(255)")
        sql = ("REPLACE INTO employees (" + ",".join(f"`{h}`" for h in cols) +
               ") VALUES (" + ",".join(["%s"] * len(cols)) + ")")
        n = 0
        for row in reader:
            cur.execute(sql, [row[r] or None for r in raw]); n += 1
    print(n, "rows loaded")

main(sys.argv[1])
