from flask import Flask, request, redirect, session, jsonify
import sqlite3
import datetime
import random
import json

app = Flask(__name__)
app.secret_key = "bossfullfinal_deliveryprice_otp_v5_6_7"

conn = sqlite3.connect('orders.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS menu (id INTEGER PRIMARY KEY, category TEXT, item TEXT, price INTEGER, desc TEXT, img TEXT, stock INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, phone TEXT, name TEXT, address TEXT, items TEXT, total INTEGER, discount INTEGER, points_used INTEGER, coupon_code TEXT, coupon_discount INTEGER, delivery_charge INTEGER, payment TEXT, time TEXT, scheduled_time TEXT, status TEXT, boy_name TEXT, boy_phone TEXT, boy_lat REAL, boy_lng REAL, cust_lat REAL, cust_lng REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS customers (phone TEXT PRIMARY KEY, name TEXT, address TEXT, points INTEGER, favourites TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS delivery_boys (id INTEGER PRIMARY KEY, name TEXT, phone TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS coupons (id INTEGER PRIMARY KEY, code TEXT UNIQUE, discount INTEGER, min_order INTEGER)''')

c.execute("INSERT OR IGNORE INTO settings VALUES ('min_order', '149')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('delivery_charge', '20')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('admin_whatsapp', '917320905255')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('points_earn_rate', '10')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('points_redeem_value', '50')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('shop_name', 'BOSS STREET BITES SITAMARHI')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('delivery_time', '30 mins')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('upi_id', 'boss@upi')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('shop_phone', '+91 73209 05255')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('shop_status', 'OPEN')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('shop_open_time', '10:00')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('shop_close_time', '22:00')")
c.execute("INSERT OR IGNORE INTO menu VALUES (1, 'Burgers', 'Cheese Burger', 99, 'Extra Cheese, Crispy Patty', 'https://via.placeholder.com/600x400/FF0000/FFFFFF?text=Cheese+Burger', 50)")
conn.commit()

ADMIN_USER = "boss"
ADMIN_PASS = "1234"

def get_setting(key):
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = c.fetchone()
    return res[0] if res else ""

def is_shop_open():
    status = get_setting('shop_status')
    if status == 'CLOSED':
        return False
    open_time = get_setting('shop_open_time')
    close_time = get_setting('shop_close_time')
    now = datetime.datetime.now().strftime("%H:%M")
    return open_time <= now <= close_time

@app.route("/login", methods=["GET", "POST"])
def customer_login():
    if request.method == "POST":
        phone = request.form["phone"]
        if len(phone)!= 10:
            return "10 digit number dalo"
        session["customer_phone"] = phone
        c.execute("INSERT OR IGNORE INTO customers (phone, points) VALUES (?,0)", (phone,))
        conn.commit()
        return redirect("/")
    return f'''<div style="text-align:center; margin-top:100px; font-family:Poppins"><h1>🔥 {get_setting('shop_name')}</h1><h2>Customer Login</h2><form method=POST><input name=phone placeholder="10 Digit Mobile No" required maxlength="10" style="padding:12px; width:250px"><button style="background:#e63946; color:white; padding:12px 20px; border:none; border-radius:8px">Login</button></form></div>'''

@app.route("/logout")
def logout():
    session.pop("customer_phone", None)
    return redirect("/login")

@app.route("/")
def home():
    if not session.get("customer_phone"):
        return redirect("/login")
    if not is_shop_open():
        return f"<div style='text-align:center; margin-top:100px; font-family:Poppins'><h1>🔒 {get_setting('shop_name')} is Closed Now</h1></div>"
    customer_phone = session["customer_phone"]
    c.execute("SELECT points FROM customers WHERE phone=?", (customer_phone,))
    cust = c.fetchone()
    customer_points = cust[0] if cust else 0
    c.execute("SELECT * FROM menu")
    menu = c.fetchall()
    categories = list(set([m[1] for m in menu]))
    earn_rate = int(get_setting('points_earn_rate'))
    redeem_value = int(get_setting('points_redeem_value'))
    rupee_per_point = redeem_value / earn_rate if earn_rate > 0 else 0

    html = f'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet"><style>*{{font-family:'Poppins'}}.phone-banner{{background:#FF5722;color:white;text-align:center;padding:10px}}header{{background:#e63946;color:white;padding:18px 20px;display:flex;justify-content:space-between}}.add-btn{{background:#e63946;color:white;width:100%;padding:14px;border:none;border-radius:10px}}.points-box{{background:#fff3cd;padding:15px;border-radius:10px;margin:15px 0;border:1px solid #ffeeba}}.coupon-box{{background:#d4edda;padding:15px;border-radius:10px;margin:15px 0;border:1px solid #c3e6cb}}</style></head><body><div class="phone-banner">📍 Sitamarhi | Logged in: {customer_phone} | <a href="/logout" style="color:white">Logout</a></div><header><div class="logo">🔥 {get_setting('shop_name')}</div><button onclick="showCart()">🛒 <span id="cartCount">0</span></button></header>'''
    html += f'<div style="background:#f77f00;color:white;text-align:center;padding:25px"><h2>Delivery in {get_setting("delivery_time")}</h2><p>Earn {earn_rate} Points per ₹100</p></div><div style="padding:20px">'
    for cat in categories:
        html += f'<h2>{cat}</h2><div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:20px">'
        for m in menu:
            if m[1] == cat:
                img = m[5] if m[5] else 'https://via.placeholder.com/600x400'
                btn = '<button class="add-btn" disabled>SOLD OUT</button>' if m[6] == 0 else f'<button class="add-btn" onclick="addToCart({m[0]},\'{m[2]}\',{m[3]})">ADD TO CART</button>'
                html += f'<div style="background:white; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1)"><img src="{img}" style="width:100%; height:180px; object-fit:cover"><div style="padding:15px"><h3>{m[2]}</h3><p>{m[4]}</p><h3 style="color:#e63946">₹{m[3]}</h3>{btn}</div></div>'
        html += '</div>'
    html += f'''</div><div id="cartModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7)"><div style="background:white; width:90%; max-width:500px; margin:40px auto; padding:20px; border-radius:12px"><h2>🛒 Cart</h2><div id="cartItems"></div><div class="coupon-box"><h3>🎟️ Coupon Code</h3><input id="couponInput" placeholder="FESTIVE50"><button type="button" onclick="applyCoupon()" style="background:blue; color:white; padding:8px; border:none; border-radius:5px">Apply</button><p>Discount: -₹<span id="couponDiscount">0</span></p></div><div class="points-box"><h3>🎁 Your Points: <span id="availablePoints">{customer_points}</span></h3><p>1 Point = ₹{rupee_per_point}</p><button type="button" onclick="usePoints()" style="background:green; color:white; padding:10px; border:none; border-radius:8px">Use Points</button><p>Discount: -₹<span id="discountAmount">0</span></p></div><h3>Subtotal: ₹<span id="subTotal">0</span></h3><h3>Final Total: ₹<span id="finalTotal">0</span></h3><form method=POST action='/order'><input name=name placeholder="Full Name" required><br><br><input name=address placeholder="Delivery Address" required><br><br><select name=payment><option value="COD">COD</option><option value="UPI">UPI</option></select><br><br><input type=hidden name=items id="itemsInput"><input type=hidden name=total id="totalInput"><input type=hidden name=discount id="discountInput" value="0"><input type=hidden name=points_used id="pointsUsedInput" value="0"><input type=hidden name=coupon_code id="couponCodeInput" value=""><input type=hidden name=coupon_discount id="couponDiscountInput" value="0"><button class="add-btn">PLACE ORDER</button></form></div></div><script>let cart=[];let customerPoints={customer_points};let rupeePerPoint={rupee_per_point};let discount=0;let pointsUsed=0;let couponDiscount=0;let couponCode="";function addToCart(id,name,price){{let item=cart.find(x=>x.id==id);if(item)item.qty++;else cart.push({{id,name,price,qty:1}});updateCart();}}function updateCart(){{document.getElementById('cartCount').innerText=cart.reduce((a,b)=>a+b.qty,0);let subtotal=cart.reduce((a,b)=>a+b.price*b.qty,0);let final=subtotal-discount-couponDiscount;document.getElementById('subTotal').innerText=subtotal;document.getElementById('finalTotal').innerText=final;document.getElementById('totalInput').value=final;document.getElementById('itemsInput').value=JSON.stringify(cart);document.getElementById('cartItems').innerHTML=cart.map(i=>`<p>${{i.name}} x ${{i.qty}} = ₹${{i.price*i.qty}}</p>`).join('');}}function usePoints(){{let subtotal=cart.reduce((a,b)=>a+b.price*b.qty,0);let maxDiscount=customerPoints*rupeePerPoint;discount=Math.min(maxDiscount,subtotal-couponDiscount);pointsUsed=Math.floor(discount/rupeePerPoint);document.getElementById('discountAmount').innerText=discount;document.getElementById('discountInput').value=discount;document.getElementById('pointsUsedInput').value=pointsUsed;updateCart();}}function applyCoupon(){{let code=document.getElementById('couponInput').value;fetch('/apply_coupon?code='+code+'&total='+cart.reduce((a,b)=>a+b.price*b.qty,0)).then(res=>res.json()).then(data=>{{if(data.valid){{couponDiscount=data.discount;couponCode=code;document.getElementById('couponDiscount').innerText=couponDiscount;document.getElementById('couponDiscountInput').value=couponDiscount;document.getElementById('couponCodeInput').value=couponCode;}}else{{alert(data.msg)}}updateCart();}});}}function showCart(){{document.getElementById('cartModal').style.display='block'}}</script></body></html>'''
    return html

@app.route("/apply_coupon")
def apply_coupon():
    code = request.args.get('code')
    total = int(request.args.get('total', 0))
    c.execute("SELECT * FROM coupons WHERE code=?", (code,))
    coupon = c.fetchone()
    if coupon and total >= coupon[3]:
        return jsonify({"valid": True, "discount": coupon[2]})
    return jsonify({"valid": False, "msg": "Invalid Coupon or Min Order not met"})

@app.route("/order", methods=["POST"])
def order():
    if not session.get("customer_phone"):
        return "Pehle Login karo"
    phone = session["customer_phone"]
    order_id = random.randint(1000, 9999)
    time_now = datetime.datetime.now().strftime("%d-%m %H:%M")
    name = request.form["name"]
    address = request.form["address"]
    items = request.form["items"]
    total = int(request.form["total"])
    discount = int(request.form.get("discount", 0))
    points_used = int(request.form.get("points_used", 0))
    coupon_code = request.form.get("coupon_code", "")
    coupon_discount = int(request.form.get("coupon_discount", 0))
    payment = request.form["payment"]
    earn_rate = int(get_setting('points_earn_rate'))
    earned_points = int(total / 100 * earn_rate)
    admin_whatsapp = get_setting('admin_whatsapp')

    c.execute("INSERT INTO orders (id,phone,name,address,items,total,discount,points_used,coupon_code,coupon_discount,payment,time,status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (order_id, phone, name, address, items, total, discount, points_used, coupon_code, coupon_discount, payment, time_now, "New"))
    c.execute("UPDATE customers SET points = COALESCE(points,0) +? -? WHERE phone=?", (earned_points, points_used, phone))
    conn.commit()

    admin_msg = f"🔥 *Naya Order - {get_setting('shop_name')}* 🔥%0A%0A*Order ID:* #{order_id}%0A*Customer:* {name}%0A*Phone:* {phone}%0A*Total:* ₹{total} %0A*Discount:* ₹{discount}%0A*Coupon:* {coupon_code} -₹{coupon_discount}%0A*Payment:* {payment}%0A*Address:* {address}%0A%0AAdmin Panel: {request.host_url}admin"
    wa_admin_link = f"https://wa.me/{admin_whatsapp}?text={admin_msg}"
    return f'''<div style='text-align:center; margin-top:80px; font-family:Poppins'><h1>Order Placed! ✅</h1><h2>Order ID: #{order_id}</h2><p>🎉 Earned {earned_points} Points | Used {points_used} Points</p><a href="{wa_admin_link}" target="_blank" style="background:green;color:white;padding:15px 25px;border-radius:10px;text-decoration:none">📢 Admin ko WhatsApp Notification Bhejo</a><p style="margin-top:20px"><a href='/track?id={order_id}'>Track Live</a></p></div><script>window.open("{wa_admin_link}", "_blank");</script>'''

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST" and "user" in request.form:
        if request.form["user"] == ADMIN_USER and request.form["pass"] == ADMIN_PASS:
            session["login"] = True
        else:
            return "Wrong Password"
    if not session.get("login"):
        return '<div style="text-align:center; margin-top:100px; font-family:Poppins"><form method=POST><h2>Admin Login</h2><input name=user placeholder="User"><input name=pass type=password placeholder="Pass"><button>Login</button></form></div>'
    
    if request.method == "POST" and "save_all_settings" in request.form:
        for key in ['shop_name', 'admin_whatsapp', 'upi_id', 'shop_phone', 'min_order', 'delivery_charge', 'points_earn_rate', 'points_redeem_value', 'shop_status', 'shop_open_time', 'shop_close_time']:
            c.execute("UPDATE settings SET value=? WHERE key=?", (request.form[key], key))
        conn.commit()
        return redirect("/admin")
    if request.method == "POST" and "new_boy" in request.form:
        c.execute("INSERT INTO delivery_boys (name,phone) VALUES (?,?)", (request.form["new_boy"], request.form["boy_phone"]))
        conn.commit()
    if request.method == "POST" and "add_item" in request.form:
        c.execute("INSERT INTO menu (category,item,price,desc,img,stock) VALUES (?,?,?,?,?,?)", (request.form["category"], request.form["item"], request.form["price"], request.form["desc"], request.form["img"], request.form["stock"]))
        conn.commit()
    if request.method == "POST" and "del_item" in request.form:
        c.execute("DELETE FROM menu WHERE id=?", (request.form["del_item"],))
        conn.commit()
    if request.method == "POST" and "add_coupon" in request.form:
        c.execute("INSERT OR REPLACE INTO coupons (code,discount,min_order) VALUES (?,?,?)", (request.form["coupon_code"], request.form["coupon_discount"], request.form["coupon_min"]))
        conn.commit()
    if request.method == "POST" and "update_status" in request.form:
        c.execute("UPDATE orders SET status=? WHERE id=?", (request.form["status"], request.form["order_id"]))
        conn.commit()

    c.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = c.fetchall()
    c.execute("SELECT * FROM delivery_boys")
    boys = c.fetchall()
    c.execute("SELECT * FROM customers ORDER BY points DESC")
    customers = c.fetchall()
    c.execute("SELECT * FROM menu")
    menu = c.fetchall()
    c.execute("SELECT * FROM coupons")
    coupons = c.fetchall()
    earn_rate = get_setting('points_earn_rate')
    redeem_value = get_setting('points_redeem_value')

    html = f"<div style='padding:20px; font-family:Poppins; background:#f5f5f5'><h1>⚙️ Admin - {get_setting('shop_name')}</h1><a href='/logout_admin' style='float:right'>Logout</a>"
    html += f'''<form method=POST style='background:white; padding:20px; border-radius:12px; margin-bottom:20px'><h2>⚙️ Shop + Loyalty Settings</h2><input type=hidden name=save_all_settings value=1><b>Shop Name:</b> <input name=shop_name value="{get_setting('shop_name')}"><br><br><b>Admin WhatsApp:</b> <input name=admin_whatsapp value="{get_setting('admin_whatsapp')}"><br><br><b>Earn Points:</b> <input name=points_earn_rate value="{earn_rate}" type=number><br><br><b>Redeem Value:</b> <input name=points_redeem_value value="{redeem_value}" type=number><br><br><button style='background:green;color:white;padding:10px 20px;border:none;border-radius:8px'>Save</button></form>'''
    html += f'''<div style='background:white; padding:20px; border-radius:12px; margin-bottom:20px'><h2>🍔 Menu Management</h2><form method=POST><input type=hidden name=add_item value=1><input name=category placeholder="Category"><input name=item placeholder="Item Name"><input name=price placeholder="Price" type=number><input name=stock placeholder="Stock" type=number><br><br><input name=desc placeholder="Description" style="width:300px"><br><br><input name=img placeholder="Image URL" style="width:400px"><br><br><button>Add Item</button></form><hr>'''
    for m in menu:
        html += f"<p><img src='{m[5]}' width=50> {m[2]} - ₹{m[3]} <form method=POST style='display:inline'><input type=hidden name=del_item value={m[0]}><button style='background:red;color:white'>Delete</button></form></p>"
    html += "</div>"
    html += f'''<div style='background:#d4edda; padding:20px; border-radius:12px; margin-bottom:20px'><h2>🎟️ Coupon Management</h2><form method=POST><input type=hidden name=add_coupon value=1><input name=coupon_code placeholder="CODE"><input name=coupon_discount placeholder="Discount ₹" type=number><input name=coupon_min placeholder="Min Order ₹" type=number><button>Add Coupon</button></form>'''
    for cp in coupons:
        html += f"<p>{cp[1]} - ₹{cp[2]} off on ₹{cp[3]}+</p>"
    html += "</div>"
    html += f'''<div style='background:white; padding:20px; border-radius:12px; margin-bottom:20px'><h2>👥 Customers</h2><table border=1 width=100%><tr style='background:#e63946;color:white'><th>Phone</th><th>Name</th><th>Points</th></tr>'''
    for cust in customers:
        html += f"<tr><td>{cust[0]}</td><td>{cust[1]}</td><td><b>{cust[3]}</b></td></tr>"
    html += "</table></div>"
    html += f'''<div style='background:#cce5ff; padding:20px; border-radius:12px; margin-bottom:20px'><h2>👨‍🍳 Delivery Boys</h2><form method=POST><input name=new_boy placeholder="Name"><input name=boy_phone placeholder="Phone"><button>Add Boy</button></form>'''
    for b in boys:
        html += f"<p>{b[1]} - {b[2]}</p>"
    html += "</div>"
    html += "<div style='background:white; padding:20px; border-radius:12px'><h2>📦 Orders</h2>"
    for o in orders:
        html += f"<div style='border:1px solid #ccc; padding:10px; margin:10px 0'><b>Order #{o[0]}</b> | {o[2]} | ₹{o[5]} | Status: {o[14]}<form method=POST style='display:inline; margin-left:10px'><input type=hidden name=update_status value=1><input type=hidden name=order_id value={o[0]}><select name=status><option>New</option><option>Preparing</option><option>Out for Delivery</option><option>Delivered</option></select><button>Update</button></form></div>"
    html += "</div></div>"
    return html

@app.route("/logout_admin")
def logout_admin():
    session.pop("login", None)
    return redirect("/admin")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
