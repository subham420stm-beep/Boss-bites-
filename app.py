from flask import Flask, request, session, redirect, jsonify
import sqlite3
import random
import time
import json

app = Flask(__name__)
app.secret_key = "subodh_secret_key_v8_4"

conn = sqlite3.connect('orders.db', check_same_thread=False)
c = conn.cursor()

# Tables
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS menu (id INTEGER PRIMARY KEY, item TEXT, price INTEGER, desc TEXT, img TEXT, stock INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS customers (phone TEXT PRIMARY KEY, name TEXT, points INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, phone TEXT, name TEXT, address TEXT, cust_lat REAL, cust_lng REAL, items TEXT, total INTEGER, discount INTEGER, points_used INTEGER, coupon_code TEXT, payment TEXT, status TEXT, time TEXT, boy_lat REAL, boy_lng REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS delivery_boys (id INTEGER PRIMARY KEY, name TEXT, phone TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS coupons (code TEXT PRIMARY KEY, discount INTEGER, min_order INTEGER)''')
conn.commit()

# Default Data
c.execute("INSERT OR IGNORE INTO settings VALUES ('points_earn_rate', '10')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('points_redeem_value', '50')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('shop_name', 'Subodh Fast Food Corner')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('shop_status', 'Open')")
c.execute("INSERT OR IGNORE INTO menu VALUES (1, 'Subodh Special Burger', 99, 'Extra Cheese Patty with Fries', 'https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=500', 1)")
c.execute("INSERT OR IGNORE INTO menu VALUES (2, 'Cheese Pizza', 199, 'Mozzarella Cheese 8 inch', 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500', 1)")
c.execute("INSERT OR IGNORE INTO coupons VALUES ('SUBODH50', 50, 199)")
conn.commit()

def get_setting(key):
    c.execute("SELECT value FROM settings WHERE key=?", (key,)); res = c.fetchone()
    return res[0] if res else ""

SHOP_NAME = get_setting('shop_name')

def check_shop():
    if get_setting('shop_status') == 'Closed' and not session.get("admin"):
        return f'''<!DOCTYPE html><html><head><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:Poppins;text-align:center;padding-top:150px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white}}</style></head><body><h1>😔 {SHOP_NAME} Abhi Band Hai</h1><h3>Jaldi Hi Wapas Khulenge</h3></body></html>'''
    return None

# 1. LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    closed = check_shop(); if closed: return closed
    if request.method == "POST":
        phone = request.form["phone"]; name = request.form["name"]
        session["phone"] = phone; session["name"] = name
        c.execute("INSERT OR IGNORE INTO customers VALUES (?,?, 0)", (phone, name)); conn.commit()
        return redirect("/")
    return f'''<!DOCTYPE html><html><head><title>{SHOP_NAME}</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body{{font-family:Poppins;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);margin:0}}
   .box{{background:white;padding:40px;border-radius:20px;width:90%;max-width:400px;margin:80px auto;box-shadow:0 10px 40px rgba(0,0,0,0.2)}}
    input{{width:90%;padding:14px;margin:10px 0;border:1px solid #ddd;border-radius:10px}}
    button{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:14px;border:none;border-radius:10px;width:95%;font-weight:600;font-size:16px;cursor:pointer}}
   .badge{{background:#22c55e;color:white;padding:5px 12px;border-radius:20px;font-size:12px}}</style></head><body>
    <div class="box"><h1 style="text-align:center">🔥 {SHOP_NAME}</h1>
    <p style="text-align:center">Shop Status: <span class="badge">{get_setting('shop_status')}</span></p>
    <form method=POST><input name=name placeholder="Apna Naam" required><input name=phone placeholder="10 digit Mobile No" required maxlength="10"><button>Continue</button></form></div></body></html>'''

# 2. HOME
@app.route("/")
def home():
    closed = check_shop(); if closed: return closed
    if not session.get("phone"): return redirect("/login")
    phone = session["phone"]; name = session.get("name","Customer")
    c.execute("SELECT points FROM customers WHERE phone=?", (phone,)); points = c.fetchone()[0]
    c.execute("SELECT * FROM menu"); menu = c.fetchall()
    earn_rate = int(get_setting('points_earn_rate')); redeem_value = int(get_setting('points_redeem_value')); rupee_per_point = redeem_value / earn_rate

    html = f'''<!DOCTYPE html><html><head><title>{SHOP_NAME}</title><meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
    *{{box-sizing:border-box}} body{{font-family:Poppins;background:#f8f9fa;margin:0}} 
    header{{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center;background:white;padding:15px 20px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}}
   .card{{background:white;padding:15px;border-radius:16px;box-shadow:0 4px 15px rgba(0,0,0,0.08);transition:0.3s}}
   .card:hover{{transform:translateY(-5px)}}
    img{{width:100%;height:180px;object-fit:cover;border-radius:12px}}
   .add-btn{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;padding:12px;border-radius:10px;width:100%;font-weight:600;cursor:pointer}}
   .out-btn{{background:#ccc;cursor:not-allowed}}
    #cartBox{{position:fixed;right:20px;top:90px;background:white;padding:20px;border-radius:16px;width:320px;box-shadow:0 10px 40px rgba(0,0,0,0.15)}}
    @media(max-width:768px){{#cartBox{{position:static;width:95%;margin:20px auto}}}}
   .price{{color:#e23744;font-size:20px;font-weight:700}}
    </style></head><body>
    <header><h2>🔥 {SHOP_NAME}</h2><div style="font-weight:600">Hi {name} | ⭐ {points} Points | 🛒 <span id="cartCount">0</span></div></header>
    <div style="padding:20px"><div id="menu" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px">'''

    for m in menu:
        if m[5] == 0: stock_btn = '<button class="add-btn out-btn" disabled>OUT OF STOCK</button>'
        else: stock_btn = f'<button class="add-btn" onclick="addToCart({m[0]},\'{m[1]}\',{m[2]})">ADD TO CART</button>'
        html += f'''<div class="card"><img src="{m[4]}"><h3>{m[1]}</h3><p style="color:#666">{m[3]}</p><p class="price">₹{m[2]}</p>{stock_btn}</div>'''

    html += f'''</div></div>
    <div id="cartBox"><h3>🛒 Your Cart</h3><div id="cartItems" style="min-height:50px"></div><hr>
    <input id="coupon" placeholder="Coupon Code" style="padding:10px;width:65%;border:1px solid #ddd;border-radius:8px">
    <button onclick="applyCoupon()" style="padding:10px;border:none;background:#667eea;color:white;border-radius:8px">Apply</button>
    <p>Coupon Discount: -₹<span id="couponDiscount">0</span></p><hr>
    <p>Your Points: {points}</p><button onclick="usePoints()" style="padding:8px;border:none;background:#22c55e;color:white;border-radius:8px">Use Points</button>
    <p>Points Discount: -₹<span id="pointsDiscount">0</span></p><hr>
    <h3>Total: ₹<span id="finalTotal">0</span></h3>
    <form method=POST action="/order">
    <input name=name placeholder="Full Name" value="{name}" required style="width:100%;padding:10px;margin:5px 0;border:1px solid #ddd;border-radius:8px">
    <input name=address placeholder="Full Address" required style="width:100%;padding:10px;margin:5px 0;border:1px solid #ddd;border-radius:8px">
    <input type=hidden name=cust_lat id="cust_lat"><input type=hidden name=cust_lng id="cust_lng">
    <select name=payment style="width:100%;padding:10px;margin:5px 0;border:1px solid #ddd;border-radius:8px"><option>COD</option><option>UPI</option></select>
    <input type=hidden name=items id="itemsInput"><input type=hidden name=total id="totalInput">
    <input type=hidden name=discount id="discountInput"><input type=hidden name=points_used id="pointsUsedInput"><input type=hidden name=coupon_code id="couponCodeInput">
    <button style="background:linear-gradient(135deg,#22c55e 0%,#16a34a 100%);color:white;padding:14px;width:100%;border:none;border-radius:10px;font-weight:600;margin-top:10px">PLACE ORDER</button></form></div>
    <script>let cart=[]; let pointsDiscount=0; let couponDiscount=0; let pointsUsed=0; let couponCode="";
    let customerPoints={points}; let rupeePerPoint={rupee_per_point};
    navigator.geolocation.getCurrentPosition(pos=>{{document.getElementById('cust_lat').value=pos.coords.latitude; document.getElementById('cust_lng').value=pos.coords.longitude;}});
    function addToCart(id,name,price){{let item=cart.find(x=>x.id==id); if(item)item.qty++; else cart.push({{id,name,price,qty:1}}); updateCart();}}
    function updateCart(){{document.getElementById('cartCount').innerText=cart.reduce((a,b)=>a+b.qty,0);
    let subtotal=cart.reduce((a,b)=>a+b.price*b.qty,0); let final = subtotal - pointsDiscount - couponDiscount;
    document.getElementById('finalTotal').innerText=final; document.getElementById('totalInput').value=final; document.getElementById('itemsInput').value=JSON.stringify(cart);
    document.getElementById('cartItems').innerHTML=cart.map(i=>`<div style="display:flex;justify-content:space-between;margin:8px 0">${{i.name}} x ${{i.qty}}<b>₹${{i.price*i.qty}}</b></div>`).join('');}}
    function usePoints(){{let subtotal=cart.reduce((a,b)=>a+b.price*b.qty,0); let maxDiscount = customerPoints * rupeePerPoint;
    pointsDiscount = Math.min(maxDiscount, subtotal-couponDiscount); pointsUsed = Math.floor(pointsDiscount / rupeePerPoint);
    document.getElementById('pointsDiscount').innerText=pointsDiscount; document.getElementById('discountInput').value=pointsDiscount; document.getElementById('pointsUsedInput').value=pointsUsed; updateCart();}}
    function applyCoupon(){{let code=document.getElementById('coupon').value; fetch('/apply_coupon?code='+code+'&total='+cart.reduce((a,b)=>a+b.price*b.qty,0)).then(res=>res.json()).then(data=>{{if(data.valid){{couponDiscount=data.discount; couponCode=code; document.getElementById('couponDiscount').innerText=couponDiscount; document.getElementById('couponCodeInput').value=couponCode;}}else{{alert(data.msg)}} updateCart();}});}}
    </script></body></html>'''
    return html

@app.route("/apply_coupon")
def apply_coupon():
    code = request.args.get('code'); total = int(request.args.get('total',0))
    c.execute("SELECT * FROM coupons WHERE code=?", (code,)); coupon = c.fetchone()
    if coupon and total >= coupon[2]: return jsonify({"valid":True, "discount":coupon[1]})
    return jsonify({"valid":False, "msg":"Invalid Coupon"})

# ORDER + TRACK + BOY same as before
@app.route("/order", methods=["POST"])
def order():
    closed = check_shop(); if closed: return closed
    if not session.get("phone"): return "Login karo"
    phone = session["phone"]; order_id = random.randint(1000,9999); time_now = time.strftime("%d-%m %H:%M")
    name = request.form["name"]; address = request.form["address"]; cust_lat = request.form.get("cust_lat"); cust_lng = request.form.get("cust_lng")
    items = request.form["items"]; total = int(request.form["total"]); discount = int(request.form.get("discount",0)); points_used = int(request.form.get("points_used",0)); coupon_code = request.form.get("coupon_code",""); payment = request.form["payment"]
    earn_rate = int(get_setting('points_earn_rate')); earned_points = int(total/100 * earn_rate)
    c.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(order_id,phone,name,address,cust_lat,cust_lng,items,total,discount,points_used,coupon_code,payment,"New",time_now,None,None))
    c.execute("UPDATE customers SET points = points +? -? WHERE phone=?",(earned_points, points_used, phone)); conn.commit()
    return f'''<!DOCTYPE html><html><head><link href="https://fonts.googleapis.com/css2?family=Poppins&display=swap" rel="stylesheet"><style>body{{font-family:Poppins;text-align:center;padding-top:100px;background:#f0fdf4}}</style></head><body><h1>Order Placed! ✅</h1><h2>Order ID: #{order_id}</h2><a href="/track?id={order_id}" style="background:#2563eb;color:white;padding:15px 25px;border-radius:10px;text-decoration:none">📍 Track Your Order</a></body></html>'''

@app.route("/track")
def track():
    oid = request.args.get('id'); c.execute("SELECT * FROM orders WHERE id=?", (oid,)); o = c.fetchone()
    if not o: return "Order not found"
    status = o[13]; boy_lat = o[15]; boy_lng = o[16]; cust_lat = o[4]; cust_lng = o[5]
    status_steps = ['New','Preparing','Out for Delivery','Delivered']; progress = int((status_steps.index(status) / 3) * 100) if status in status_steps else 0
    map_html = f'''<iframe src="https://www.openstreetmap.org/export/embed.html?bbox={min(boy_lng,cust_lng)-0.01}%2C{min(boy_lat,cust_lat)-0.01}%2C{max(boy_lng,cust_lng)+0.01}%2C{max(boy_lat,cust_lat)+0.01}&layer=mapnik&marker={boy_lat}%2C{boy_lng}" style="width:100%;height:400px;border-radius:12px;border:0"></iframe>''' if boy_lat else ""
    return f'''<!DOCTYPE html><html><head><link href="https://fonts.googleapis.com/css2?family=Poppins&display=swap" rel="stylesheet"><style>body{{font-family:Poppins;padding:20px;text-align:center}}</style></head><body><h1>{SHOP_NAME}</h1><h2>Track Order #{oid}</h2><h3>Status: {status}</h3><div style="background:#ddd;height:20px;border-radius:10px"><div style="background:linear-gradient(90deg,#22c55e,#16a34a);width:{progress}%;height:20px;border-radius:10px"></div></div>{map_html}<script>setTimeout(()=>{{location.reload()}}, 5000);</script></body></html>'''

@app.route("/boy", methods=["GET","POST"])
def boy_login():
    if request.method == "POST":
        phone = request.form["phone"]; c.execute("SELECT * FROM delivery_boys WHERE phone=?", (phone,)); boy = c.fetchone()
        if boy: session["boy_id"] = boy[0]; session["boy_name"] = boy[1]; return redirect("/boy_panel")
        else: return "Ye number registered nahi hai"
    return f'''<!DOCTYPE html><html><head><link href="https://fonts.googleapis.com/css2?family=Poppins&display=swap" rel="stylesheet"><style>body{{font-family:Poppins;text-align:center;padding-top:100px}}</style></head><body><h2>👨‍🍳 {SHOP_NAME} - Delivery Boy</h2><form method=POST><input name=phone placeholder="Registered Mobile No" required style="padding:12px"><button style="padding:12px">Login</button></form></body></html>'''

@app.route("/boy_panel")
def boy_panel():
    if not session.get("boy_id"): return redirect("/boy")
    c.execute("SELECT * FROM orders WHERE status='Out for Delivery' OR status='New' ORDER BY id DESC"); orders = c.fetchall()
    html = f"<div style='padding:20px;font-family:Poppins'><h1>🚚 Hello {session['boy_name']}</h1>"
    for o in orders:
        cust_lat = o[4]; cust_lng = o[5]; map_link = f"https://www.openstreetmap.org/?mlat={cust_lat}&mlon={cust_lng}#map=16/{cust_lat}/{cust_lng}" if cust_lat else "#"
        html += f'''<div style='background:white;padding:15px;margin:10px;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.1)'><b>Order #{o[0]}</b><br>Customer: {o[2]}<br>Address: {o[3]}<br><a href="{map_link}" target="_blank" style="background:#f97316;color:white;padding:8px 12px;border-radius:8px;text-decoration:none">📍 Location</a>
        <button onclick="startTracking({o[0]})" style="background:#22c55e;color:white;padding:10px;border:none;border-radius:8px;margin-left:10px">📍 Live ON</button></div>'''
    html += '''<script>function startTracking(orderId){setInterval(()=>{navigator.geolocation.getCurrentPosition(pos=>{fetch('/update_boy_location', {method: 'POST', headers: {'Content-Type': 'application/json'},body: JSON.stringify({order_id: orderId, lat: pos.coords.latitude, lng: pos.coords.longitude})});});}, 5000);}</script></div>'''
    return html

@app.route("/update_boy_location", methods=["POST"])
def update_boy_location():
    data = request.json; c.execute("UPDATE orders SET boy_lat=?, boy_lng=? WHERE id=?", (data['lat'], data['lng'], data['order_id'])); conn.commit(); return jsonify({"status":"ok"})

# 6. ADMIN - PROFESSIONAL
ADMIN_USER = "boss"; ADMIN_PASS = "1234"
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST" and "user" in request.form:
        if request.form["user"]==ADMIN_USER and request.form["pass"]==ADMIN_PASS: session["admin"] = True
        else: return "Wrong Password"
    if not session.get("admin"): return f'<!DOCTYPE html><html><head><link href="https://fonts.googleapis.com/css2?family=Poppins&display=swap" rel="stylesheet"><style>body{{font-family:Poppins;text-align:center;padding-top:100px}}</style></head><body><form method=POST><h2>{SHOP_NAME} - Admin</h2><input name=user placeholder="User" style="padding:12px"><input name=pass type=password placeholder="Pass" style="padding:12px"><button>Login</button></form></body></html>'

    if request.method == "POST":
        if "toggle_shop" in request.form:
            new_status = "Closed" if get_setting('shop_status') == "Open" else "Open"; c.execute("UPDATE settings SET value=? WHERE key='shop_status'", (new_status,)); conn.commit()
        if "toggle_stock" in request.form:
            item_id = request.form["item_id"]; c.execute("SELECT stock FROM menu WHERE id=?", (item_id,)); current = c.fetchone()[0]
            new_stock = 0 if current == 1 else 1; c.execute("UPDATE menu SET stock=? WHERE id=?", (new_stock, item_id)); conn.commit()
        if "add_item" in request.form:
            c.execute("INSERT INTO menu (item,price,desc,img,stock) VALUES (?,?,?,?,1)",(request.form["item"],request.form["price"],request.form["desc"],request.form["img"])); conn.commit()
        if "del_item" in request.form:
            c.execute("DELETE FROM menu WHERE id=?",(request.form["del_item"],)); conn.commit()
        if "new_boy" in request.form:
            c.execute("INSERT INTO delivery_boys (name,phone) VALUES (?,?)",(request.form["new_boy"],request.form["boy_phone"])); conn.commit()
        if "update_status" in request.form:
            c.execute("UPDATE orders SET status=? WHERE id=?",(request.form["status"],request.form["order_id"])); conn.commit()
        if "update_shop" in request.form:
            c.execute("UPDATE settings SET value=? WHERE key='shop_name'", (request.form["shop_name"],)); conn.commit()
        if "update_points" in request.form:
            c.execute("UPDATE settings SET value=? WHERE key='points_earn_rate'", (request.form["earn_rate"],));
            c.execute("UPDATE settings SET value=? WHERE key='points_redeem_value'", (request.form["redeem_value"],)); conn.commit()
        if "add_coupon" in request.form:
            c.execute("INSERT OR REPLACE INTO coupons VALUES (?,?,?)",(request.form["code"],request.form["discount"],request.form["min_order"])); conn.commit()
        if "del_coupon" in request.form:
            c.execute("DELETE FROM coupons WHERE code=?",(request.form["del_coupon"],)); conn.commit()

    c.execute("SELECT * FROM orders ORDER BY id DESC"); orders = c.fetchall()
    c.execute("SELECT * FROM menu"); menu = c.fetchall()
    c.execute("SELECT * FROM delivery_boys"); boys = c.fetchall()
    c.execute("SELECT * FROM coupons"); coupons = c.fetchall()
    current_status = get_setting('shop_status')
    new_orders = len([o for o in orders if o[13] == 'New'])

        html = f"<!DOCTYPE html><html><head><link href='https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap' rel='stylesheet'><style>body{{font-family:Poppins;background:#f8f9fa;padding:20px}}.box{{background:white;padding:20px;margin-bottom:20px;border-radius:16px;box-shadow:0 4px 15px rgba(0,0,0,0.08)}}</style></head><body><h1>⚙️ {SHOP_NAME} - Admin Panel</h1>"

    if new_orders > 0:
        html += f'''<div class="box" style='background:#fee2e2;border:2px solid #ef4444;text-align:center'><h2>🔔 {new_orders} Naye Order Aaye Hain!</h2><audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-09.mp3" type="audio/mpeg"></audio></div>'''

    html += f'''<div class="box"><h2>🏪 Shop Settings</h2>
    <form method=POST><input type=hidden name=update_shop value=1><input name=shop_name value="{get_setting('shop_name')}" style="padding:10px"><button>Update Name</button></form>
    <h4>Shop Status: <span style="color:{'green' if current_status=='Open' else 'red'}">{current_status}</span></h4>
    <form method=POST><input type=hidden name=toggle_shop value=1><button style="background:{'red' if current_status=='Open' else 'green'};color:white;padding:12px;border:none;border-radius:8px">{"Shop Band Karo" if current_status=="Open" else "Shop Chalu Karo"}</button></form></div>'''

    html += f'''<div class="box"><h2>🎁 Loyalty Points Setting</h2>
    <form method=POST><input type=hidden name=update_points value=1>
    ₹100 pe kitne points: <input name=earn_rate type=number value="{get_setting('points_earn_rate')}" style="padding:8px"><br><br>
    {get_setting('points_earn_rate')} points = ₹ <input name=redeem_value type=number value="{get_setting('points_redeem_value')}" style="padding:8px"><button>Update</button></form></div>'''

    html += '''<div class="box"><h2>🏷️ Coupon Management</h2>
    <form method=POST><input type=hidden name=add_coupon value=1>
    <input name=code placeholder="Coupon Code" required style="padding:8px"><input name=discount placeholder="Discount ₹" type=number required style="padding:8px">
    <input name=min_order placeholder="Min Order ₹" type=number required style="padding:8px"><button>Add</button></form><hr>'''
    for cp in coupons: html += f"<p><b>{cp[0]}</b> - ₹{cp[1]} off on ₹{cp[2]}+ <form method=POST style='display:inline'><input type=hidden name=del_coupon value={cp[0]}><button style='background:red;color:white;border:none;padding:5px 10px'>Delete</button></form></p>"
    html += "</div>"

    html += '''<div class="box"><h2>🍔 Menu Management</h2>
    <form method=POST><input type=hidden name=add_item value=1>
    <input name=item placeholder="Item Name" required style="padding:8px"><input name=price placeholder="Price" type=number required style="padding:8px">
    <input name=desc placeholder="Description" style="padding:8px"><input name=img placeholder="Image URL" style="padding:8px"><button>Add</button></form><hr>'''
    for m in menu:
        stock_status = "IN STOCK" if m[5]==1 else "OUT OF STOCK"
        color = "green" if m[5]==1 else "red"
        html += f"<p><img src='{m[4]}' width=50 style='border-radius:8px'> {m[1]} - ₹{m[2]} - <b style='color:{color}'>{stock_status}</b> <form method=POST style='display:inline'><input type=hidden name=toggle_stock value=1><input name=item_id value={m[0]}><button>Toggle</button></form> <form method=POST style='display:inline'><input type=hidden name=del_item value={m[0]}><button style='background:red;color:white;border:none;padding:5px 10px'>Delete</button></form></p>"
    html += "</div>"

    html += '''<div class="box"><h2>👨‍🍳 Delivery Boys</h2>
    <form method=POST><input name=new_boy placeholder="Name" style="padding:8px"><input name=boy_phone placeholder="Phone" style="padding:8px"><button>Add</button></form>'''
    for b in boys: html += f"<p>{b[1]} - {b[2]}</p>"
    html += "</div>"

    html += "<div class='box'><h2>📦 Orders</h2>"
    for o in orders:
        border = "border:3px solid #ef4444;" if o[13] == 'New' else ""
        html += f"<div style='border:1px solid #ddd;padding:15px;margin:10px 0;border-radius:12px;{border}'><b>Order #{o[0]}</b> | {o[2]} | ₹{o[7]} | Status: {o[13]} <a href='/track?id={o[0]}' target='_blank'>Track</a><form method=POST style='display:inline;margin-left:10px'><input type=hidden name=update_status value=1><input type=hidden name=order_id value={o[0]}><select name=status style='padding:5px'><option>New</option><option>Preparing</option><option>Out for Delivery</option><option>Delivered</option></select><button>Update</button></form></div>"
    html += "</div></body></html>"
    return html

if __name__ == '__main__': app.run()
