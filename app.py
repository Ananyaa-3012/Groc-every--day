import os
from flask import Flask, render_template, url_for, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import random

current_dir=os.path.abspath(os.path.dirname(__file__))
app=Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"+os.path.join(current_dir,"mad1db.sqlite3")
db = SQLAlchemy()
db.init_app(app)
app.secret_key="secretkey"
app.app_context().push()

#--------------------MODELS-----------------
class User(db.Model):
    __tablename__='user'
    id=db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    name=db.Column(db.String, unique=True, nullable=False)
    username=db.Column(db.String, unique=True, nullable=False)
    email=db.Column(db.String, unique=True, nullable=False)
    password=db.Column(db.String, unique=True, nullable=False)
    order=db.relationship('Order', cascade='delete')

class Admin(db.Model):
    __tablename__='admin'
    id=db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    name=db.Column(db.String, unique=True, nullable=False)
    username=db.Column(db.String, unique=True, nullable=False)
    email=db.Column(db.String, unique=True, nullable=False)
    password=db.Column(db.String, unique=True, nullable=False)

class Category(db.Model):
    __tablename__='category'
    id=db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    name=db.Column(db.String, unique=True, nullable=False)
    desc=db.Column(db.String, nullable=False)
    pdt = db.relationship('Product', cascade='delete')   
    
class Product(db.Model):
    __tablename__='product'
    id=db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    name=db.Column(db.String, nullable=False)
    category = db.Column(db.Integer, db.ForeignKey('category.id'))
    stock=db.Column(db.Integer, nullable=False)
    unit=db.Column(db.Integer, nullable=False)
    expiry=db.Column(db.String)
    price=db.Column(db.Integer, nullable=False)
    order = db.relationship('Order', cascade='delete')   

class Cart(db.Model):
    __tablename__='cart'
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id=db.Column(db.Integer)
    product=db.Column(db.String)
    price=db.Column(db.Integer)
    qty=db.Column(db.Integer, nullable=False)
    
class Order(db.Model):
    __tablename__='order'
    id=db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'))
    pdt=db.Column(db.String, db.ForeignKey('product.name'))
    qty=db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime(timezone=True), server_default=func.now())

db.create_all()

#-------------------------USER ROUTES---------------------------
@app.route("/user/signup", methods=["GET","POST"])
def signup():
    if request.method=="POST": 
        name=request.form["name"]
        usrnm=request.form["username"]
        eml=request.form["email"]
        pwd=request.form["password"]
        print(name)
        usr=User(name=name,username=usrnm,email=eml,password=pwd)
        db.session.add(usr)
        db.session.commit()
        return redirect(url_for("login", message=0))
    return render_template('signup.html', title="Sign Up",message=0)
    
@app.route("/", methods=["GET", "POST"])
@app.route("/user/login/<message>", methods=["GET", "POST"])
def login(message=0):
        if request.method=="POST": 
            usrnm=request.form["username"]
            pwd=request.form["password"]
            user=User.query.filter_by(username=usrnm).first()
            if user and usrnm==user.username and pwd==user.password:
                session['current_user']={'id':user.id,'name':user.username,'is_admin':0}
                return(redirect(url_for("dashboard",message=0)))
            else:
                return render_template("login.html", title="Login", message="Invalid Credentials. Log in Again")        

        return render_template("login.html", title="Login",message=message)


@app.route("/user/dashboard/<message>", methods=["GET", "POST"])
def dashboard(message=False):
    tot_price=0
    if session['current_user']:
        cat=Category.query.all()
        if cat:
            return render_template('dashboard.html', title="Dashboard", category=cat, message=message, total=tot_price)
        else:
            return render_template('dashboard.html', title="Dashboard", message="No categories exist", total=tot_price)
        
    else:
        return redirect(url_for("login", message=0))

@app.route("/user/category/<int:cid>/products",methods=["GET","POST"])
def products(cid):
    tot_price=0
    if session['current_user']:
        cat=Category.query.filter_by(id=cid).one()
        pdt=Product.query.filter_by(category=cid).all()
        if pdt:
            return render_template("products.html", title="Products", pdt=pdt, cat=cat, total=tot_price, message=False)
        else:
            return render_template("products.html", title="Products", pdt=0, cat=cat, total=tot_price, message=False)
    else:
        return redirect(url_for("login", message=0))

#-------------------------CART ROUTES---------------------------

def total_price():
    total=0
    id=session['current_user']['id']
    cart=Cart.query.filter_by(user_id=id).all()
    for i in cart:
        total+=(i.price*i.qty)
    return total

@app.route("/user/category/<int:cid>/product/<int:pid>/add",methods=["GET","POST"])
def add_to_cart(cid,pid):
    if session['current_user']:
        cat=Category.query.filter_by(id=cid).one()
        pdt=Product.query.filter_by(id=pid).one()
        tot_price=0
        if request.method=="POST":
            id=session['current_user']['id']
            qty=int(request.form['units'])
            cart=Cart(user_id=id,product=pdt.name,price=pdt.price,qty=qty)
            db.session.add(cart)
            db.session.commit()
            total=total_price()
            return redirect(url_for("cart", tot_price=total))

        return render_template("add_cart.html", title="Add To Cart", pdt=pdt, cat=cat, total=tot_price, message=False)
    else:
        return redirect(url_for("login", message=0))

@app.route("/user/cart/<int:tot_price>", methods=["GET","POST"])
def cart(tot_price):
    tot_price=total_price()
    if request.method=="GET":
        id=session['current_user']['id']
        cart=Cart.query.filter_by(user_id=id).all()
        pdt=Product.query.all()
        return render_template("cart.html", title="Cart",cart=cart, pdt=pdt, total=tot_price, message=False)

@app.route("/user/clr_cart",methods=["GET"])
def clr_cart():
    id=session['current_user']['id']
    cart=Cart.query.filter_by(user_id=id).all()
    for i in cart:
        db.session.delete(i)
        db.session.commit()
    return(redirect(url_for("dashboard", message="Cart cleared successfully")))

@app.route("/user/checkout", methods=["GET","POST"])
def checkout():
        if request.method=="GET":
            id=session['current_user']['id']
            cart=Cart.query.filter_by(user_id=id).all()
            
            for item in cart:
                db.session.add(Order(user_id=id, pdt=item.product, qty=item.qty))
                pdt=Product.query.filter_by(name=item.product).one()
                pdt.stock-=item.qty
                db.session.delete(item)
            db.session.commit()
            pdt=Order.query.filter_by(user_id=id).all()
            return render_template('order.html',title="Orders",pdt=pdt, message=False)

@app.route("/user/search", methods=["POST"])
def search():
    query=request.form['catname']
    cat=Category.query.filter(Category.name.like(f'%{query}%')).all()
    return render_template("search.html", cat=cat,message=0)
#-------------------------ADMIN ROUTES---------------------------
@app.route("/admin/login/<message>", methods=["GET", "POST"])
def admin_login(message):
        if request.method=="POST": 
            usrnm=request.form["username"]
            pwd=request.form["password"]
            admin=Admin.query.filter_by(username=usrnm).first()
            if admin:
                if usrnm==admin.username and pwd==admin.password:
                    session["current_user"]={"name":admin.username,'is_admin':1}
                    return(redirect(url_for("admin_dashboard")))
                return render_template("admin_login.html", title="Admin Login",message="Wrong Credentials")        
            return render_template("admin_login.html", title="Admin Login",message="Wrong Credentials")        
        return render_template("admin_login.html", title="Admin Login",message=0)

@app.route("/admin/dashboard")
def admin_dashboard():
    if session['current_user']:
        cat=Category.query.all()
        if cat:
            return render_template("admin_dashboard.html", title="Admin Dashboard", category=cat)
        else:
            return render_template("admin_dashboard.html", title="Admin Dashboard", category=0)
    else:
        return redirect(url_for("admin_login"))

#-------------------------CATEGORY CRUD---------------------------
@app.route("/admin/category/create", methods=["GET","POST"])
def create_category():
    if session['current_user']:
        if request.method=="POST":
            name=request.form["name"]
            desc=request.form["desc"]
            cat=Category(name=name, desc=desc)
            db.session.add(cat)
            db.session.commit()
            return redirect(url_for("admin_dashboard"))

        return render_template("new_cat.html", title="Add Category")
    else:
        return redirect(url_for("admin_login"))

@app.route("/admin/category/edit/<int:id>/", methods=["GET","POST"])
def edit_category(id):
    if session['current_user']:
        if request.method=="POST":
            cat=Category.query.filter_by(id=id).one()    
            name=request.form["name"]
            desc=request.form["desc"]    
            cat.name=name
            cat.desc=desc
            db.session.commit()
            return redirect(url_for("admin_dashboard"))
        cat=Category.query.filter_by(id=id).one()
        return render_template("edit_cat.html", title="Edit Category",cat=cat)
    else:
        return redirect(url_for("admin_login"))

@app.route("/admin/category/del/<int:id>/", methods=["GET"])
def del_category(id):
    if session['current_user']:
        if request.method=="GET":
            cat=Category.query.filter_by(id=id).one()    
            db.session.delete(cat)
            db.session.commit()
            return redirect(url_for("admin_dashboard"))
    else:
        return redirect(url_for("admin_login"))

#-------------------------PRODUCT CRUD---------------------------
@app.route("/admin/category/<int:id>/products")
def view_products(id):
    if session['current_user']:
        cat=Category.query.filter_by(id=id).one()
        pdt=Product.query.filter_by(category=id).all()
        if pdt:
            return render_template("view_products.html", title="Products", pdt=pdt, cat=cat)
        else:
            return render_template("view_products.html", title="Products", pdt=0,cat=cat)
    else:
        return redirect(url_for("admin_login"))

@app.route("/admin/category/<int:id>/products/add", methods=["GET","POST"])
def add_products(id):
    if session['current_user']:
        cat=Category.query.filter_by(id=id).one()
        if request.method=="POST":
            name=request.form["name"]
            stock=request.form["stock"]
            unit=request.form["unit"]
            exp=request.form["expiry"]
            price=request.form["price"]
            pdt=Product(name=name, category=id, stock=stock, unit=unit, expiry=exp, price=price)
            db.session.add(pdt)
            db.session.commit()
            return redirect(url_for("view_products",id=id))

        return render_template("new_pdt.html", title="Add Product", cat=cat)
    else:
        return redirect(url_for("admin_login"))

@app.route("/admin/category/<int:cid>/product/<int:pid>/edit", methods=["GET","POST"])
def edit_products(cid,pid):
    if session['current_user']:
        cat=Category.query.filter_by(id=cid).one()
        pdt=Product.query.filter_by(id=pid).one()        
        if request.method=="POST":
            name=request.form["name"]
            stock=request.form["stock"]
            unit=request.form["unit"]
            exp=request.form["expiry"]
            price=request.form["price"]
            pdt.name=name
            pdt.category=cid
            pdt.stock=stock
            pdt.unit=unit
            pdt.expiry=exp
            pdt.price=price
            db.session.commit()
            return redirect(url_for("view_products",id=cid))

        return render_template("edit_pdt.html", title="Add Product", cat=cat, pdt=pdt)
    else:
        return redirect(url_for("admin_login"))
    
@app.route("/admin/category/<int:cid>/product/<int:pid>/del", methods=["GET","POST"])
def del_pdts(cid,pid):
    if session['current_user']:
        if request.method=="GET":
            pdt=Product.query.filter_by(id=pid).one()        
            db.session.delete(pdt)
            db.session.commit()
            return redirect(url_for("view_products",id=cid))
    else:
        return redirect(url_for("admin_login"))

#-------------------------LOG OUT---------------------------
@app.route("/logout", methods=["GET"])
def logout():
    if session['current_user']['is_admin']:
        session.clear()
        return redirect(url_for("admin_login", message="Logged Out Successfully"))
    else:
        session.clear()
        return redirect(url_for("login", message="Logged Out Successfully"))

if __name__=='__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)