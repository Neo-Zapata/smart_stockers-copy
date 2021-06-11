from operator import le
from flask import Flask, render_template, url_for, request, redirect,session
from flask.helpers import flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, not_, or_



app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/smartstockers'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Productos(db.Model):
    __tablename__ = 'productos'
    id_productos = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer)
    # Codigo es unique LISTO
    Codigo = db.Column(db.Integer, nullable=False, unique=True)
    Producto = db.Column(db.String(50), nullable=False)
    Categoria = db.Column(db.String(30), nullable=False)
    Ubicacion = db.Column(db.String(60), nullable=False)
    Precio = db.Column(db.Float, nullable=False)
    Vencimiento = db.Column(db.Date, nullable=False)
#Como es id es foreign key??
class Cuentas(db.Model):
    __tablename__ = 'cuentas'
    id_cuentas = db.Column(db.Integer, primary_key=True)
       # Los tres deben ser unique
    email = db.Column(db.String(40), nullable=False, unique=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(30), nullable=False, unique=True)


db.create_all()

#1
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    if 'loggedin' in session:
        user = session['username']
        flash(f"welcome {user}","info")
        return render_template('home.html')
    
    return redirect(url_for('index'))
#1.1
@app.route('/registro')
def register():
    return render_template('register.html')

@app.route('/agregar')
def agregar():
    if 'loggedin' in session:
        username = session['username']
        flash(f"Your are logged as: {username}","info")
        return render_template('agregar.html')
    
    return redirect(url_for('index'))
    

@app.route('/consumir')
def consumir():
    if 'loggedin' in session:
        username = session['username']
        flash(f"Your are logged as: {username}","info")
        return render_template('consumir.html')
    
    return redirect(url_for('index'))
    

@app.route('/stock')
def stock():
    if 'loggedin' in session:
        username = session['username']
        flash(f"Your are logged as: {username}","info")
        return render_template('stock.html', stock=Productos.query.filter_by(id_usuario=str(session['id'])))
    
    return redirect(url_for('index'))
    

@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    #El id_usuario podria asignarse como foreign key (y pasar otros parametros al session)
    id_usuario = session['id']
    cantidad = int(request.form.get('cantidad',''))
    codigo = request.form.get('codigo','')
    producto = request.form.get('producto','')
    categoria = request.form.get('categoria','')
    ubicacion = request.form.get('ubicacion','')
    precio = request.form.get('precio','')
    vencimiento = request.form.get('vencimiento','')

    for i in range(cantidad):
        _productos = Productos(id_usuario=id_usuario,Codigo=codigo,Producto=producto,Categoria=categoria,Ubicacion=ubicacion,Precio=precio,Vencimiento=vencimiento)
        db.session.add(_productos)
        db.session.commit()
    # poner mensaje para que el usuario sepa que fue exitoso
    return redirect(url_for('agregar'))
#1.2
@app.route('/signin', methods=['POST'])
def signin():
    _mail = request.form.get('mail')
    _password = request.form.get('password')
    results = Cuentas.query.filter_by(email=_mail,password=_password)
    if(results.count() == 0):
        flash("Uno de los campos es vacio o es erroneo!","info")
        return redirect(url_for('index'))
    else:
        session['loggedin'] = True
        session['id'] = results.first().id_cuentas
        session['username'] = results.first().username
        return redirect(url_for('home'))
    
#1.1.2
@app.route('/signup', methods=['POST'])
def signup():
    _username = request.form.get('username')
    _password = request.form.get('password')
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
            
#1.2.1
@app.route('/logout')
def logout():
    if 'loggedin' in session:
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('username', None)
        flash("You've been logged out!","info")
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/consumir_producto', methods=['POST'])
def consumir_producto():
    _searchProd = request.form.get('producto','')
   # _searchVenc = request.form.get('vencimiento','')
    _deleteCant = int(request.form.get('cantidad',''))

    results = Productos.query.filter_by(Producto=_searchProd )#Vencimiento=_searchVenc
    cant=0
    for x in results:
        cant= cant+1
    if _deleteCant < cant:
        for i in range(_deleteCant):
            db.session.delete(results[i])
            db.session.commit()
    else:
        return render_template("Error.html")

    return redirect(url_for('consumir'))

@app.route('/mostrar_stock', methods=['POST'])
def mostrar_stock():
    _searchCodigo = request.form.get('ver_producto','')
    _searchProduc = request.form.get('ver_vencimiento','')
    _searchCatego = request.form.get('ver_categoria','')
    _searchUbicac = request.form.get('ver_ubicacion','')
    _searchPrecio = request.form.get('ver_precio','')
    _searchVencim = request.form.get('ver_vencimiento','')

    if (_searchCodigo == ""):
        _searchCodigo = '%'
    if (_searchProduc == ""):
        _searchProduc = '%'
    if (_searchCatego == ""):
        _searchCatego = '%'
    if (_searchUbicac == ""):
        _searchUbicac = '%'
    if (_searchPrecio == ""):
        _searchPrecio = '%'
    if (_searchVencim == ""):
        _searchVencim = '%'
#revisar esta parte, falla
    resultados = Productos.query.filter(Productos.Codigo==_searchCodigo, 
                                    Productos.Producto==_searchProduc, 
                                    Productos.Categoria==_searchCatego,
                                    Productos.Ubicacion==_searchUbicac, 
                                    Productos.Precio==_searchPrecio,
                                    Productos.Vencimiento==_searchVencim,
                                    Productos.id_usuario == session['id'])

    return render_template('stock.html', stockFiltered=resultados, stock=Productos.query.filter_by(id_usuario=str(session['id'])))

# hay otras maneras de manejar errores (para que el usuario pueda seguir interactuando
@app.errorhandler(IndexError)
def _indexError(err):
    return render_template("Error.html",err = err)
@app.errorhandler(ValueError)
def _valueError(err):
    return render_template("Error.html",err = err)



if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8085 ,debug=True)