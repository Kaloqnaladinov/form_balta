from datetime import date
import sqlite3, secrets
from functools import wraps
from pathlib import Path
from flask import Flask,render_template,request,redirect,url_for,session,jsonify,flash
from werkzeug.security import generate_password_hash,check_password_hash
from config import DATABASE,SECRET_KEY,ADMIN_EMAIL,DEFAULT_ADMIN_PASSWORD,SITE

app=Flask(__name__); app.secret_key=SECRET_KEY
BASE=Path(__file__).parent

def db():
    c=sqlite3.connect(DATABASE); c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON"); return c

def init_db():
    c=db(); c.executescript((BASE/"schema.sql").read_text()); c.executescript((BASE/"seed.sql").read_text())
    if not c.execute("SELECT id FROM admins WHERE email=?",(ADMIN_EMAIL,)).fetchone():
        c.execute("INSERT INTO admins(name,email,password_hash) VALUES(?,?,?)",
                  ("Forn Baltà Admin",ADMIN_EMAIL,generate_password_hash(DEFAULT_ADMIN_PASSWORD)))
    c.commit(); c.close()

@app.before_request
def boot():
    if not DATABASE.exists(): init_db()

def csrf():
    if "csrf" not in session: session["csrf"]=secrets.token_hex(32)
    return session["csrf"]

@app.context_processor
def globals():
    return {"site":SITE,"csrf":csrf(),"admin_name":session.get("admin_name")}

def admin(view):
    @wraps(view)
    def w(*a,**k):
        if "admin_id" not in session:return redirect(url_for("login"))
        return view(*a,**k)
    return w

def check_csrf():
    return secrets.compare_digest(request.form.get("csrf",""),session.get("csrf",""))

@app.get("/")
def home():
    c=db(); featured=c.execute("""SELECT p.*,c.name category_name FROM products p JOIN categories c ON c.id=p.category_id
      WHERE p.active=1 AND p.featured=1 ORDER BY c.sort_order,p.sort_order LIMIT 6""").fetchall(); c.close()
    return render_template("home.html",featured=featured)

@app.get("/menu")
def menu():
    c=db(); cats=c.execute("SELECT * FROM categories WHERE active=1 ORDER BY sort_order").fetchall()
    products=c.execute("""SELECT p.*,c.name category_name FROM products p JOIN categories c ON c.id=p.category_id
      WHERE p.active=1 AND c.active=1 ORDER BY c.sort_order,p.sort_order,p.id""").fetchall(); c.close()
    return render_template("menu.html",categories=cats,products=products)

@app.get("/order")
def order(): return render_template("order.html")

@app.post("/api/orders")
def create_order():
    x=request.get_json(silent=True) or {}; name=str(x.get("customer_name","")).strip(); phone=str(x.get("customer_phone","")).strip()
    d=str(x.get("pickup_date","")).strip(); t=str(x.get("pickup_time","")).strip(); notes=str(x.get("notes","")).strip(); items=x.get("items",[])
    if not all([name,phone,d,t]) or not isinstance(items,list) or not items:return jsonify(ok=False,message="Complete all required fields."),400
    try: parsed=date.fromisoformat(d)
    except ValueError:return jsonify(ok=False,message="Invalid pickup date."),400
    if parsed<date.today():return jsonify(ok=False,message="Pickup date cannot be in the past."),400
    ids=[]; qty={}
    try:
        for i in items:
            pid=int(i["id"]); q=int(i["qty"]); 
            if q<1 or q>50: raise ValueError
            ids.append(pid); qty[pid]=q
    except (KeyError,TypeError,ValueError):return jsonify(ok=False,message="Invalid cart."),400
    ids=sorted(set(ids)); c=db(); ph=",".join("?"*len(ids))
    rows=c.execute(f"SELECT id,name,price,active FROM products WHERE id IN ({ph})",ids).fetchall(); pm={r["id"]:r for r in rows}
    if len(pm)!=len(ids):c.close(); return jsonify(ok=False,message="A product is unavailable."),400
    total=0; clean=[]
    for pid in ids:
        p=pm[pid]
        if not p["active"]:c.close(); return jsonify(ok=False,message=f'{p["name"]} is unavailable.'),400
        line=round(float(p["price"])*qty[pid],2); total+=line; clean.append((pid,p["name"],qty[pid],p["price"],line))
    cur=c.execute("""INSERT INTO orders(customer_name,customer_phone,pickup_date,pickup_time,notes,total) VALUES(?,?,?,?,?,?)""",(name,phone,d,t,notes,total))
    oid=cur.lastrowid
    c.executemany("""INSERT INTO order_items(order_id,product_id,product_name,quantity,unit_price,line_total) VALUES(?,?,?,?,?,?)""",
                  [(oid,*r) for r in clean]); c.commit(); c.close()
    return jsonify(ok=True,order_id=oid,message=f"Comanda #{oid} rebuda. L'equip confirmarà la disponibilitat.")

@app.route("/admin/login",methods=["GET","POST"])
def login():
    if "admin_id" in session:return redirect(url_for("dashboard"))
    error=None
    if request.method=="POST":
        if not check_csrf():error="Invalid request."
        else:
            c=db(); a=c.execute("SELECT * FROM admins WHERE email=?",(request.form.get("email","").strip().lower(),)).fetchone(); c.close()
            if a and check_password_hash(a["password_hash"],request.form.get("password","")):
                session.clear(); session["admin_id"]=a["id"]; session["admin_name"]=a["name"]; session["csrf"]=secrets.token_hex(32); return redirect(url_for("dashboard"))
            error="Incorrect email or password."
    return render_template("admin_login.html",error=error)

@app.post("/admin/logout")
@admin
def logout(): session.clear(); return redirect(url_for("login"))

@app.get("/admin")
@admin
def dashboard():
    c=db(); stats={"new":c.execute("SELECT COUNT(*) FROM orders WHERE status='new'").fetchone()[0],
      "today":c.execute("SELECT COUNT(*) FROM orders WHERE pickup_date=?",(date.today().isoformat(),)).fetchone()[0],
      "products":c.execute("SELECT COUNT(*) FROM products WHERE active=1").fetchone()[0]}
    recent=c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 10").fetchall(); c.close()
    return render_template("admin_dashboard.html",stats=stats,recent=recent)

@app.route("/admin/menu",methods=["GET","POST"])
@admin
def admin_menu():
    c=db()
    if request.method=="POST":
        if not check_csrf():c.close(); flash("Invalid request."); return redirect(url_for("admin_menu"))
        action=request.form.get("action"); pid=int(request.form.get("id",0))
        if action=="toggle":c.execute("UPDATE products SET active=1-active WHERE id=?",(pid,))
        if action=="save":
            vals=(int(request.form["category_id"]),request.form["name"].strip(),request.form.get("description","").strip(),float(request.form["price"]),int(request.form.get("featured",0)))
            if pid:c.execute("UPDATE products SET category_id=?,name=?,description=?,price=?,featured=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(*vals,pid))
            else:c.execute("INSERT INTO products(category_id,name,description,price,featured) VALUES(?,?,?,?,?)",vals)
        c.commit(); c.close(); return redirect(url_for("admin_menu"))
    cats=c.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
    products=c.execute("""SELECT p.*,c.name category_name FROM products p JOIN categories c ON c.id=p.category_id
      ORDER BY c.sort_order,p.sort_order,p.id""").fetchall(); c.close()
    return render_template("admin_menu.html",categories=cats,products=products)

@app.route("/admin/orders",methods=["GET","POST"])
@admin
def admin_orders():
    c=db()
    if request.method=="POST":
        if not check_csrf():c.close(); return redirect(url_for("admin_orders"))
        status=request.form.get("status","new")
        if status in {"new","confirmed","ready","completed","cancelled"}:
            c.execute("UPDATE orders SET status=? WHERE id=?",(status,int(request.form["id"]))); c.commit()
    orders=c.execute("SELECT * FROM orders ORDER BY pickup_date DESC,created_at DESC LIMIT 100").fetchall()
    items={o["id"]:c.execute("SELECT * FROM order_items WHERE order_id=?",(o["id"],)).fetchall() for o in orders}; c.close()
    return render_template("admin_orders.html",orders=orders,items=items)

@app.cli.command("init-db")
def init_command():init_db();print("Database initialized.")

if __name__=="__main__":
    init_db(); app.run(host="127.0.0.1",port=5000,debug=True)
