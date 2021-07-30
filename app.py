from operator import le
import re
from flask import Flask, render_template, url_for, request, redirect, session, jsonify
from flask.helpers import flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, not_, or_, delete,select,update,values
from flask_migrate import Migrate
import sys
import json
import bcrypt

# PARA USAR EL HASH VE: https://github.com/Vuka951/tutorial-code/blob/master/flask-bcrypt/main.py

app = Flask(__name__)
app.secret_key = 'supersecretkey'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/smartstockers'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db) 

class Productos(db.Model):
    __tablename__ = 'productos'
    # Se hizo el cambio de db.Integer a db.BigInteger probar!
    # id_productos = db.Column(db.BigInteger, primary_key=True)
    id_productos = db.Column(db.BigInteger, primary_key=True)
    Codigo = db.Column(db.Integer, nullable=False)
    Producto = db.Column(db.String(50), nullable=False)
    Categoria = db.Column(db.String(30), nullable=False)
    Ubicacion = db.Column(db.String(60), nullable=False)
    Precio = db.Column(db.Float, nullable=False)
    Vencimiento = db.Column(db.Date, nullable=False)

    # FOREIGN KEY, 'user' ES POR EL BACKREF DE LINEA 41
    #user (ES COMO SU HUBIERA UNA COLUMAN EXTRA LLAMADA user)
    id_usuario = db.Column(db.Integer, db.ForeignKey('cuentas.id_cuentas'), nullable=False)

class Cuentas(db.Model):
    __tablename__ = 'cuentas'
    id_cuentas = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(40), nullable=False, unique=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False, unique=True)

    #DB.RELATIONSHIP
    productos = db.relationship("Productos", backref="user")

db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signin', methods=['POST'])
def signin():
    _mail = request.form.get('mail')
    _password = request.form.get('password').encode('utf-8')
    results = Cuentas.query.filter_by(email=_mail)
    if(results.count() == 0):
        flash("Alguno(s) de los campos es vacio(s) o es erroneo(s)!","info")
        return redirect(url_for('index'))
    else:
        if bcrypt.checkpw(_password, results.first().password.encode('utf-8')):
            session['loggedin'] = True
            session['id'] = results.first().id_cuentas
            session['username'] = results.first().username
            return redirect(url_for('home'))
        else:
            flash("Uno de los campos es vacio o es erroneo!","info")
            return redirect(url_for('index'))
        
    
@app.route('/signup', methods=['POST'])
def signup():
    _username = request.form.get('username')
    _password = request.form.get('password').encode('utf-8')
    _password = bcrypt.hashpw(_password,bcrypt.gensalt()).decode('utf-8')
    _mail = request.form.get('mail')
    prueba1=Cuentas.query.filter_by(email=_mail)
    prueba2=Cuentas.query.filter_by(username=_username)
    prueba3=Cuentas.query.filter_by(password=_password)
    if (prueba1.count()==0 and prueba2.count()==0 and prueba3.count()==0):
        if (_username=='' or _password=='' or _mail==''):
            flash("Un campo es vacio! ","info")
            return redirect(url_for('register'))
        else:
            user = Cuentas(email=_mail,password=_password,username=_username)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('index'))
    flash("Uno o mas campos ya estan registrados!","info")
    return redirect(url_for("register"))
            
@app.route('/logout')
def logout():
    if 'loggedin' in session:
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('username', None)
        flash("You've been logged out!","info")
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/registro')
def register():
    return render_template('register.html')

@app.route('/home')
def home():
    if 'loggedin' in session:
        user = session['username']
        flash(f"Bienvenido {user}","info")
        return render_template('home.html')
    
    return redirect(url_for('index'))

@app.route('/agregar')
def agregar():
    if 'loggedin' in session:
        username = session['username']
        flash(f" Has iniciado sesion como: {username}","info")
        return render_template('agregar.html', stock=Productos.query.filter_by(id_usuario=str(session['id'])))
    
    return redirect(url_for('index'))
    
@app.route('/consumir')
def consumir():
    if 'loggedin' in session:
        username = session['username']
        flash(f"Your are logged as: {username}","info")
        return render_template('consumir.html', stock=Productos.query.filter_by(id_usuario=str(session['id'])))
    
    return redirect(url_for('index'))

@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    response = {}
    error = False
    try:
        #ASIGNAMOS UN OBJETO DE TIPO CUENTAS
        id_usuario = session['id']
        usuario = Cuentas.query.filter_by(id_cuentas=id_usuario).first()
        cantidad = request.get_json()['cantidad']
        codigo = request.get_json()['codigo']
        producto = request.get_json()['producto']
        categoria = request.get_json()['categoria']
        ubicacion = request.get_json()['ubicacion']
        precio = request.get_json()['precio']
        vencimiento = request.get_json()['vencimiento']

        for i in range(int(cantidad)):
            #ASIGNAMOS A USER EL OBJETO DE TIPO CUENTAS PARA LA RELACION
            _productos = Productos(Codigo=codigo,Producto=producto,Categoria=categoria,Ubicacion=ubicacion,
                                    Precio=precio,Vencimiento=vencimiento, user=usuario) 
            db.session.add(_productos)
            db.session.commit()
        
        response['cantidad']=int(cantidad)
        response['codigo']=_productos.Codigo
        response['producto']=_productos.Producto
        response['categoria']=_productos.Categoria
        response['ubicacion']=_productos.Ubicacion
        response['precio']=_productos.Precio
        response['vencimiento']=_productos.Vencimiento
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        response['error_message'] = 'Algo salio mal en el servidor!'
    response['error'] = error
    return jsonify(response)

@app.route('/consumir_producto', methods=['POST'])
def consumir_producto():
    _searchProd = request.form.get('producto','')
    _deleteCant = int(request.form.get('cantidad',''))

    usuario = Cuentas.query.filter_by(id_cuentas=session["id"]).first()
    results = Productos.query.filter_by(Producto=_searchProd, user=usuario)


    idlist= []
    if _deleteCant <= results.count() and _deleteCant >= 0:
        for w in range(_deleteCant):
            idlist.append(int(results[w].id_productos))
    else:
        return render_template("Error.html")

    
    sql = delete(Productos).where(Productos.id_productos.in_(idlist))

    db.session.execute(sql)
    db.session.commit()
    

    return redirect(url_for('consumir'))

@app.errorhandler(IndexError)
def _indexError(err):
    return render_template("Error.html",err = err)
@app.errorhandler(ValueError)
def _valueError(err):
    return render_template("Error.html",err = err)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8085 ,debug=True)
