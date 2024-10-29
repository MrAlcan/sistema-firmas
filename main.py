from flask import Flask, flash, render_template, request, redirect, session, Response, url_for, send_from_directory, send_from_directory, abort
from flask_mysqldb import MySQL, MySQLdb
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from datetime import datetime
import numpy as np
import cv2
import os
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
import subprocess
import torch
import shutil
import json
import base64
import random
from datetime import datetime, timedelta
""" from pymysql.cursors import DictCursor  # Importación adicional necesaria """


def euclidean_distance(vectors):
    (feat_a, feat_b) = vectors
    sum_square = K.sum(K.square(feat_a - feat_b), axis=1, keepdims=True)
    return K.sqrt(K.maximum(sum_square, K.epsilon()))

# Cargar el modelo
siamese_model = load_model('signature_verification/siamese_model.h5', custom_objects={'euclidean_distance': euclidean_distance})

def load_and_process_image(image_path, size=(224, 224)):
    image = cv2.imread(image_path)
    if image is not None:
        image = cv2.resize(image, size)
        image = image.astype('float32') / 255.0  # Normalizamos
    return image


def generar_codigo():
    return random.randint(100000, 999999)



def serializar_fecha(fecha):
    if isinstance(fecha, datetime):
        return fecha.strftime("%Y-%m-%d %H:%M:%S")

def deserializar_fecha(fecha):
        if isinstance(fecha, str):
            try:
                # Intenta convertir la cadena a datetime
                fecha = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
                return fecha
            except ValueError:
                pass  # No es un datetime, no hacer nada

def encriptar_json(data):
    json_data = json.dumps(data).encode()
    print("json_data:    ", json_data)
    data_encriptada = base64.b64encode(json_data)
    print("json_escriptado:       ", data_encriptada)
    return data_encriptada
    
def desencriptar_json(data_encriptada):
    data_desencriptada = base64.b64decode(data_encriptada)
    print(data_desencriptada)
    print(data_desencriptada.decode())
    return json.loads(data_desencriptada.decode())

app = Flask(__name__, template_folder='templates')

# Construir la ruta dinámica del modelo
model_path = os.path.join(os.getcwd(), 'signature_verification', 'signature_model_4_improved.h5')

# Verificar si el archivo del modelo existe antes de cargarlo
if os.path.exists(model_path):
    model = load_model(model_path)  # Cargar el modelo usando la ruta dinámica
    print("Modelo cargado exitosamente desde:", model_path)
else:
    print(f"El archivo del modelo no se encontró en: {model_path}")






# Asegúrate de configurar la SECRET_KEY para usar sesiones
app.secret_key = 'BFERNANDOHC'
#aara enviar correos_ :c :p

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'jhonsantoslimachi@gmail.com'
app.config['MAIL_PASSWORD'] = 'bwfw vevs lscf ngvt'
app.config['MAIL_USE_TLS'] = True
mail = Mail(app)
def enviar_codigo_por_correo(correo, codigo):
    msg = Message('Tu código de verificación', sender='jhonsantoslimachi@gmail.com', recipients=[correo])
    msg.body = f'Tu código de verificación es {codigo}'
    mail.send(msg)
# Configuración de la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'poldocu'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Configuración para usar DictCursor

mySQL = MySQL(app)



# Define la carpeta de destino para las imágenes de perfil
UPLOAD_FOLDER = 'static/Users_Profile/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define la carpeta de destino para las imágenes de los casos
UPLOAD_FOLDER_CASOS = 'static/uploads/'


app.config['UPLOAD_FOLDER_CASOS'] = UPLOAD_FOLDER_CASOS

# Función para verificar la extensión de los archivos
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    if 'id_usuario' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
   
    casoid = session.get('caso')
    usuario_id = session.get('id_usuario')
    cur = mySQL.connection.cursor()

    if casoid:
        query = """
            SELECT * FROM caso 
            WHERE activo = 1 AND (usuario_id = %s OR id_caso = %s) 
            ORDER BY fecha_modificado DESC 
            LIMIT 10
        """
        cur.execute(query, (usuario_id, casoid))
    else:
        query = "SELECT * FROM caso WHERE activo = 1 ORDER BY fecha_modificado DESC LIMIT 10"
        cur.execute(query)
    
    casos = cur.fetchall()
    cur.close()

    return render_template('dashboard.html', casos=casos)


# INICIO DE SESION (INICIO)

@app.route('/acceso-login', methods=['GET', 'POST'])
def login():
    if 'id_usuario' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        _user = request.form['user']
        _password = request.form['password']
        
        cur = mySQL.connection.cursor()
        cur.execute('SELECT * FROM usuario WHERE usuario = %s AND password = %s', (_user, _password,))
        account = cur.fetchone()

        if account:

            hoy = datetime.now()
            print(hoy)
            fecha_codigo_usuario = account['fecha_codigo'].date()

            if hoy.date() == fecha_codigo_usuario:
                fecha = serializar_fecha(account['fecha'])
                cuerpo = {
                    'id_usuario' : account['id_usuario'],
                    'nombre' : account['nombre'],
                    'apellido' : account['apellido'],
                    'rol' : account['admin'],
                    'fecha' : fecha
                }
                cuerpo_encriptado = str(encriptar_json(cuerpo))
                cuerpo_encriptado = cuerpo_encriptado[2:len(cuerpo_encriptado)-1]
                return redirect(url_for('verificacion', cuerpo=cuerpo_encriptado))
            else:

                codigo_generado = generar_codigo()

                correo_usuario = account['email']

                enviar_codigo_por_correo(correo_usuario, codigo_generado)
                
                cur.execute('UPDATE usuario SET codigo_sesion = %s, fecha_codigo = %s WHERE id_usuario = %s', (codigo_generado, hoy, account['id_usuario']))
                mySQL.connection.commit()
                fecha = serializar_fecha(account['fecha'])
                cuerpo = {
                    'id_usuario' : account['id_usuario'],
                    'nombre' : account['nombre'],
                    'apellido' : account['apellido'],
                    'rol' : account['admin'],
                    'fecha' : fecha
                }
                cuerpo_encriptado = str(encriptar_json(cuerpo))
                cuerpo_encriptado = cuerpo_encriptado[2:len(cuerpo_encriptado)-1]
                return redirect(url_for('verificacion', cuerpo=cuerpo_encriptado))
            # Guardar los detalles del usuario en la sesión
            session['logueado'] = True
            session['id_usuario'] = account['id_usuario']
            session['nombre'] = account['nombre']  # Guarda el nombre del usuario en la sesión
            session['apellido'] = account['apellido']  # Guarda el apellido del usuario en la sesión
            session['admin'] = account['admin']
            session['fecha'] = account['fecha']  # Guarda la fecha de creación en la sesión
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')  # Mensaje de error
            return redirect(url_for('login'))  # Redirige de nuevo al login
    
    # Si el método es GET, simplemente renderiza la página de login
    return render_template('login.html')

@app.route('/verificacion/<cuerpo>', methods=['GET', 'POST'])
def verificacion(cuerpo):
    datos_usuario = desencriptar_json(cuerpo)
    print(datos_usuario['id_usuario'])
    print(str(datos_usuario['id_usuario']))
    id_usuario_ingreso = str(datos_usuario['id_usuario'])
    cur = mySQL.connection.cursor()
    cur.execute('SELECT * FROM usuario WHERE id_usuario = %s', (id_usuario_ingreso,))
    account = cur.fetchone()
    codigo_verificacion = account['codigo_sesion']
    fecha = deserializar_fecha(datos_usuario['fecha'])
    if request.method=='POST':
        codigo_enviado = request.form['codigo_ver']
        print('-'*50)
        print('codigo from', codigo_enviado)
        print(' codigo db', codigo_verificacion)
        if str(codigo_enviado)==str(codigo_verificacion):
            '''
            nombre varchar(500),
            apellido varchar(500),
            ci varchar(500),
            telefono varchar(500),
            edad varchar(500),
            imagen varchar(500),
            sexo varchar(500),
            email varchar(500),
            usuario varchar(500),
            password varchar(500),'''
            print('entra')
            session['logueado'] = True
            session['id_usuario'] = account['id_usuario']
            session['nombre'] = account['nombre']  # Guarda el nombre del usuario en la sesión
            session['apellido'] = account['apellido']  # Guarda el apellido del usuario en la sesión
            session['admin'] = account['admin']
            session['fecha'] = account['fecha']  # Guarda la fecha de creación en la sesión
            session['carnet'] = account['ci']
            session['telefono'] = account['telefono']
            session['edad'] = account['edad']
            session['imagen'] = account['imagen']
            session['sexo'] = account['sexo']
            session['email'] = account['email']
            session['usuario'] = account['usuario']
            session['contrasena'] = account['password']
            session['caso'] = account['caso']
            return redirect(url_for('dashboard'))
        else:
            print('no entra')
            flash('Código incorrecto', 'error')  # Mensaje de error
            return redirect(url_for('verificacion', cuerpo=cuerpo))  # Redirige de nuevo al login
    return render_template('verificacion.html')
    

@app.route('/logout', methods=['POST'])
def logout():
    # Eliminar las variables de sesión al cerrar sesión
    session.pop('logueado', None)
    session.pop('id_usuario', None)
    session.pop('nombre', None)
    session.pop('apellido', None)
    session.pop('admin', None)
    session.pop('fecha', None)
    session.pop('carnet',None)
    session.pop('telefono',None)
    session.pop('edad',None)
    session.pop('imagen',None)
    session.pop('sexo',None)
    session.pop('email',None)
    session.pop('usuario',None)
    session.pop('contrasena',None)
    session.pop('caso',None)
    # Redirigir al login después de cerrar sesión
    return redirect(url_for('login'))  # Esto debe ser el nombre de la función de vista

# INICIO DE SESION (FIN)


# USUARIOS REGISTRO EDITAR ELIMINAR (INICIO)

@app.route('/usuarios')
def usuarios():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    conexion = mySQL.connection
    cur = conexion.cursor()
    
    # Solo obtener los usuarios activos
    cur.execute("SELECT * FROM usuario WHERE activo = 1")
    usuarios = cur.fetchall()
    cur.execute("SELECT * FROM caso")
    casos = cur.fetchall()
    
    cur.close()

    return render_template('usuarios.html', Usuarios=usuarios, casos=casos)        

@app.route('/new_user', methods=['POST'])
def new_user():
    
    if request.method == 'POST':
        # Capturando los datos enviados desde el formulario
        nombre = request.form['Nombre'].lower().strip()
        apellido = request.form['apellido'].lower().strip()
        edad = request.form['edad']
        cedula = request.form['cedula'].strip()
        celular = request.form['celular'].strip()
        email = request.form['email'].strip()
        user = request.form['user'].strip()
        password = request.form['password'].strip()
        sexo = request.form['sexo']
        caso = request.form['caso']

        # Validación de imagen subida
        imagen = request.files['imagen']
        imagen_filename = None
        carpeta_usuario = os.path.join(app.config['UPLOAD_FOLDER'], "perfil_usuarios")
        if not os.path.exists(carpeta_usuario):
            # Si no existe, crear la carpeta
            os.makedirs(carpeta_usuario)
        if imagen and allowed_file(imagen.filename):
            imagen_filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(carpeta_usuario, imagen_filename))

        # Validación: Verificar que los campos no estén vacíos
        if not nombre or not apellido or not cedula or not celular or not email or not user or not password or not edad:
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('usuarios'))

        # Validación: Limitar el número de caracteres
        if len(nombre) > 30 or len(apellido) > 30:
            flash('El nombre o apellido no puede exceder los 30 caracteres', 'error')
            return redirect(url_for('usuarios'))

        if len(cedula) > 10 or not cedula.isdigit():
            flash('El CI debe ser un número y no puede exceder los 10 dígitos', 'error')
            return redirect(url_for('usuarios'))

        if len(celular) > 10 or not celular.isdigit():
            flash('El número de celular debe ser un número y no puede exceder los 10 dígitos', 'error')
            return redirect(url_for('usuarios'))

        # Obtener la fecha actual para la columna 'fecha'
        fecha_actual = datetime.now()

        fecha_codigo_def = '2020-10-22 11:35:00'

        # Insertar los datos en la tabla `usuario`, incluyendo la imagen, sexo, y fecha
        cur = mySQL.connection.cursor()
        cur.execute("""
            INSERT INTO usuario (nombre, apellido, edad, ci, telefono, email, usuario, password, sexo, imagen, fecha, caso)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nombre, apellido, edad, cedula, celular, email, user, password, sexo, imagen_filename, fecha_actual, caso))
        mySQL.connection.commit()
        flash('Usuario creado exitosamente', 'success')

        return redirect(url_for('usuarios'))
  # Redirige a la página 'usuarios.html'

@app.route('/editar_perfil/<id>', methods=['POST'])
def editar_perfil(id):
    celular = request.form['celular']
    email = request.form['email']
    usuario = request.form['user']
    password = request.form['password']
    # Obtener la imagen (si se proporciona una nueva)
    imagen = request.files['imagen']
    imagen_actual = request.form['imagen_actual']  # Imagen actual

    session['telefono'] = celular
    
    session['email'] = email
    session['usuario'] = usuario
    session['contrasena'] = password

    # Comprobar si el usuario ha subido una nueva imagen
    if imagen.filename != '':
        # Guardar la imagen en la carpeta 'Users_Profile'
        imagen.save(os.path.join('static/Users_Profile/perfil_usuarios', imagen.filename))
        imagen_a_guardar = imagen.filename
        session['imagen'] = imagen_a_guardar
    else:
        imagen_a_guardar = imagen_actual  # Si no se carga una nueva imagen, conservar la actual

    # Obtener la fecha y hora actual
    fecha_modeficacion = datetime.now()

    # Actualizar el usuario en la base de datos
    cur = mySQL.connection.cursor()
    cur.execute("""
        UPDATE usuario 
        SET telefono=%s, email=%s, usuario=%s, password=%s, imagen=%s, fecha_modeficacion=%s 
        WHERE id_usuario=%s
    """, (celular, email, usuario, password, imagen_a_guardar, fecha_modeficacion, id))
    
    mySQL.connection.commit()
    cur.close()

    # Redirigir a la lista de usuarios
    return redirect(url_for('usuarios'))



@app.route('/edit_user/<int:id>', methods=['POST'])
def edit_user(id):
    # Obtener los datos del formulario
    nombre = request.form['Nombre']
    apellido = request.form['apellido']
    edad = request.form['edad']
    ci = request.form['cedula']
    celular = request.form['celular']
    email = request.form['email']
    usuario = request.form['user']
    password = request.form['password']
    sexo = request.form['sexo']
    print(request.form)

    # Obtener la imagen (si se proporciona una nueva)
    imagen = request.files['imagen']
    imagen_actual = request.form['imagen_actual']  # Imagen actual

    # Comprobar si el usuario ha subido una nueva imagen
    if imagen.filename != '':
        # Guardar la imagen en la carpeta 'Users_Profile'
        imagen.save(os.path.join('static/Users_Profile/perfil_usuarios', imagen.filename))
        imagen_a_guardar = imagen.filename
    else:
        imagen_a_guardar = imagen_actual  # Si no se carga una nueva imagen, conservar la actual

    # Obtener la fecha y hora actual
    fecha_modeficacion = datetime.now()

    # Actualizar el usuario en la base de datos
    cur = mySQL.connection.cursor()
    cur.execute("""
        UPDATE usuario 
        SET nombre=%s, apellido=%s, edad=%s, ci=%s, telefono=%s, email=%s, usuario=%s, password=%s, sexo=%s, imagen=%s, fecha_modeficacion=%s 
        WHERE id_usuario=%s
    """, (nombre, apellido, edad, ci, celular, email, usuario, password, sexo, imagen_a_guardar, fecha_modeficacion, id))
    
    mySQL.connection.commit()
    cur.close()

    # Redirigir a la lista de usuarios
    return redirect(url_for('usuarios'))
    

@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    conexion = mySQL.connection
    cur = conexion.cursor()
    
    # Actualizar el campo activo a 0 y público a 1 en lugar de eliminar el usuario
    cur.execute("""
        UPDATE usuario
        SET activo = 0, publico = 1
        WHERE id_usuario = %s
    """, (id,))
    
    conexion.commit()
    cur.close()
    
    flash('Usuario desactivado exitosamente.', 'success')
    return redirect('/usuarios')


# USUARIOS REGISTRO EDITAR ELIMINAR (FIN)


# CREACION DE CASOS Y LISTADO DE CASOSO (INICIO)


@app.route('/nuevo_caso', methods=['GET', 'POST'])
def new_case():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    cur = mySQL.connection.cursor()
    cur.execute("SELECT * FROM usuario WHERE admin = 0 AND activo = 1")
    usuarios_peritos = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        # Verifica si el usuario está logueado
        if 'id_usuario' not in session:
            flash('Debes iniciar sesión para agregar un caso.', 'error')
            return redirect(url_for('login'))

        n_du_editado = request.form['n_du_editado']
        n_in_editado = request.form['n_in_editado']
        # Capturando los datos del formulario
        tipo_caso = request.form['tipo_caso']
        nombre_caso = request.form['nombre_caso']
        descripcion = request.form['descripcion']
        departamento = request.form['departamento']
        id_usuario_creado = session['id_usuario']
        usuario_designado = request.form['perito']

        cur = mySQL.connection.cursor()
        cur.execute("""
            SELECT COUNT(*) as cantidad FROM caso 
            WHERE nombre_caso = %s AND departamento = %s
        """, (nombre_caso, departamento))
        resultado = cur.fetchone()['cantidad']
        cur.close()

        if resultado > 0:
            print("existe un caso con el mismo nombre")
            flash('El nombre del caso ya existe en este departamento. Por favor, elige otro nombre.', 'error_nombre_caso')
            return render_template('nuevo_caso.html', peritos=usuarios_peritos)
        else:
        
            # Obtener los archivos de firma
            f_dubitada = request.files['f_dubitada']
            f_indubitada = request.files['f_indubitada']
            
            # Verificar si los archivos son permitidos
            if not (f_dubitada and allowed_file(f_dubitada.filename) and f_indubitada and allowed_file(f_indubitada.filename)):
                flash('Formato de archivo no permitido. Solo se aceptan imágenes PNG, JPG o JPEG.', 'error')
                return redirect(url_for('new_case'))

            # Generar nombres seguros para los archivos de firma
            f_dubitada_filename = secure_filename(f_dubitada.filename)
            f_indubitada_filename = secure_filename(f_indubitada.filename)
            
            # Guardar los archivos en la carpeta 'uploads'
            f_dubitada.save(os.path.join(app.config['UPLOAD_FOLDER_CASOS'], f_dubitada_filename))
            f_indubitada.save(os.path.join(app.config['UPLOAD_FOLDER_CASOS'], f_indubitada_filename))


            # Obtener el ID del usuario desde la sesión
            usuario_id = session.get('id_usuario')

            # Obtener la fecha actual
            fecha_actual = datetime.now()

            f_procesado_def = 'no_procesado'

            # Insertar los datos en la tabla `caso`
            cur = mySQL.connection.cursor()
            cur.execute("""
                INSERT INTO caso (usuario_id, tipo_caso, nombre_caso, descripcion, departamento, fecha, f_dubitada, f_indubitada, f_procesada, id_usuario_creado, id_usuario_modificado, n_dubitada, n_indubitada)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (usuario_designado, tipo_caso, nombre_caso, descripcion, departamento, fecha_actual, f_dubitada_filename, f_indubitada_filename, f_procesado_def, id_usuario_creado, id_usuario_creado,n_du_editado,n_in_editado))
            mySQL.connection.commit()

            flash('Caso agregado exitosamente', 'success')
            return redirect(url_for('listar_casos'))

    # Si es GET, solo renderiza el formulario de nuevo caso
    return render_template('nuevo_caso.html', peritos = usuarios_peritos)

@app.route('/listar_casos')
def listar_casos():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    
    casoid = session.get('caso')
    usuario_id = session.get('id_usuario')
    print("????????????????")
    print(casoid)
    cur = mySQL.connection.cursor()
    if casoid:
        query = "SELECT * FROM caso WHERE activo = 1 AND (usuario_id = %s OR id_caso = %s)"
        cur.execute(query, (usuario_id, casoid))
    else:
        query = "SELECT * FROM caso WHERE activo = 1"
        cur.execute(query)
    casos = cur.fetchall()
    return render_template('list_casos.html', casos=casos)

@app.route('/listar_casos_procesados')
def listar_casos_procesados():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    id_usuario_sesion = session['id_usuario']
    cur = mySQL.connection.cursor()
    cur.execute("""
            SELECT * FROM caso 
            WHERE activo = 1 AND f_procesada = 'procesado' AND usuario_id = %s
        """, (id_usuario_sesion,))
    #cur.execute("SELECT * FROM caso WHERE activo = 1")
    casos = cur.fetchall()
    return render_template('list_casos_procesados.html', casos=casos)



@app.route('/firmas')
def signatures():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    
    casoid2 = session.get('caso')
    usuario_id2 = session.get('id_usuario')

    cur2 = mySQL.connection.cursor()
    if casoid2:
        query2 = "SELECT * FROM caso WHERE activo = 1 AND (usuario_id = %s OR id_caso = %s)"
        cur2.execute(query2, (usuario_id2, casoid2))
    else:
        query2 = "SELECT * FROM caso WHERE activo = 1"
        cur2.execute(query2)
    casos2 = cur2.fetchall()





    casoid = session.get('caso')
    usuario_id = session.get('id_usuario')
    cur = mySQL.connection.cursor()
    if casoid:
        query = "SELECT * FROM caso WHERE activo = 1 AND (usuario_id = %s OR id_caso = %s)"
        cur.execute(query, (usuario_id, casoid))
    else:
        query = "SELECT * FROM caso WHERE activo = 1"
        cur.execute(query)
    casos = cur.fetchall()
    casos = ''
    return render_template('spocometria.html', casos=casos,casos2=casos2)



@app.route('/filtrar', methods=['POST'])
def filtrar_casos():
    departamento = request.form.get('departamento')
    rute = request.form.get('rute')
    fecha_inicio = request.form.get('fecha_inicio')
    fecha_final = request.form.get('fecha_fin')
    casoid = session.get('caso')
    usuario_id = session.get('id_usuario')

    query = "SELECT * FROM caso WHERE activo = 1"
    filtros = []
    params = []

    if fecha_inicio:
        try:
            datetime.strptime(fecha_inicio, '%Y-%m-%d')  
            filtros.append("fecha >= %s")
            params.append(fecha_inicio)
        except ValueError:
            return "Fecha de inicio inválida", 400 

    if fecha_final:
        try:
            datetime.strptime(fecha_final, '%Y-%m-%d')  
            filtros.append("fecha <= %s")
            params.append(fecha_final)
        except ValueError:
            return "Fecha final inválida", 400 


    if fecha_inicio and fecha_final:
        if fecha_inicio > fecha_final:
            return "error fecha", 400

    if departamento:
        filtros.append("departamento = %s")
        params.append(departamento)
    
    if casoid:
        filtros.append("(usuario_id = %s OR id_caso = %s)")
        params.extend([usuario_id, casoid])

    if rute:
        filtros.append("id_caso = %s")
        params.append(rute)

    if filtros:
        query += " AND " + " AND ".join(filtros)

    try:
        cur = mySQL.connection.cursor()
        cur.execute(query, params)
        casos = cur.fetchall()
    except Exception as e:
        print("Error al ejecutar la consulta:", e)
        casos = []
    

    casoid2 = session.get('caso')
    usuario_id2 = session.get('id_usuario')

    cur2 = mySQL.connection.cursor()
    if casoid2:
        query2 = "SELECT * FROM caso WHERE activo = 1 AND (usuario_id = %s OR id_caso = %s)"
        cur2.execute(query2, (usuario_id2, casoid2))
    else:
        query2 = "SELECT * FROM caso WHERE activo = 1"
        cur2.execute(query2)
    casos2 = cur2.fetchall()

    return render_template('spocometria.html', casos=casos,casos2=casos2)




@app.route('/guardar', methods=['POST'])
def guardar_datos():
    detalle = request.form.get('detalles')
    casoid = request.form.get('casoids')
    imagen_ruta = request.form.get('imageResultado').strip()  
    
    ahora = datetime.now()
    fecha_hora = ahora.strftime("%Y%m%d_%H%M%S")  
    carpeta_nombre = f"{casoid}_{fecha_hora}"
    carpeta_path = os.path.join('resultados_firmas', carpeta_nombre)
    
    os.makedirs(carpeta_path, exist_ok=True)
    
 
    imagen_filename = os.path.basename(imagen_ruta)
    ruta_imagen = os.path.join(carpeta_path, imagen_filename)

 
    os.rename(imagen_ruta, ruta_imagen) 

    cur = mySQL.connection.cursor()
    query = "INSERT INTO resultados (ruta_imagen, detalle, caso, activo) VALUES (%s, %s, %s, %s)"
    cur.execute(query, (ruta_imagen, detalle, casoid, 1))  
    mySQL.connection.commit()
    cur.execute("""
        UPDATE caso
        SET f_procesada = 'procesado'
        WHERE id_caso = %s
    """, (casoid,))
    mySQL.connection.commit()
    cur.close()
    
    query = "SELECT * FROM caso WHERE activo = 1"
    cur = mySQL.connection.cursor()
    cur.execute(query)
    casos = cur.fetchall()
    cur.close()

    return render_template('spocometria.html', casos=casos, modal=1)

@app.route('/comparar')
def comparar():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    cur = mySQL.connection.cursor()
    cur.execute("SELECT * FROM caso WHERE activo = 1")
    casos = cur.fetchall()
    return render_template('comparar.html', casos=casos)



@app.route('/predict_comparar', methods=['POST'])
def predict_comparar():
    file_dubitada = request.files.get('imageDoubtful')
    file_indubitable = request.files.get('imageIndubitable')

    if not file_dubitada or not file_indubitable:
        return '<p>No se subieron ambos archivos (dubitada e indubitable).</p>', 400

    try:
        basepath = os.path.dirname(__file__)
        dubitada_path = os.path.join(basepath, 'uploads', secure_filename(file_dubitada.filename))
        indubitable_path = os.path.join(basepath, 'uploads', secure_filename(file_indubitable.filename))
        
        # Guardar las imágenes en el sistema
        file_dubitada.save(dubitada_path)
        file_indubitable.save(indubitable_path)

        # Ejecutar el modelo YOLO
        yolo_weights = 'best.pt'  # Ruta al modelo YOLOv7 entrenado
        process = subprocess.Popen(["python", "yolo/detect.py", '--source', dubitada_path, "--weights", yolo_weights], shell=True)
        process.wait()  # Esperar a que el proceso termine
        
        labels_resultados = []
        with open('labels_resultados.txt', 'r') as f:
            labels_resultados = [line.strip() for line in f.readlines()]

        folder_path = 'runs/detect'
        subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
        
        if not subfolders:
            return "Error: No se encontraron subcarpetas en runs/detect.", 500

        latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
        yolo_image_path = os.path.join(folder_path, latest_subfolder, secure_filename(file_dubitada.filename))
        
        if not os.path.exists(yolo_image_path):
            return f"Error: La imagen procesada por YOLO no se encontró en {yolo_image_path}.", 500

        # Leer y procesar las imágenes
        img_dubitada = cv2.imread(dubitada_path)
        img_dubitada = cv2.resize(img_dubitada, (224, 224))
        img_dubitada = img_dubitada.astype('float32') / 255.0
        #img_dubitada = img_dubitada / 255.0
        #img_dubitada = np.expand_dims(img_dubitada, axis=0)

        img_indubitable = cv2.imread(indubitable_path)
        img_indubitable = cv2.resize(img_indubitable, (224, 224))
        img_indubitable = img_indubitable.astype('float32') / 255.0
        #img_indubitable = img_indubitable / 255.0
        #img_indubitable = np.expand_dims(img_indubitable, axis=0)

        prediction = siamese_model.predict([np.expand_dims(img_dubitada, axis=0), np.expand_dims(img_indubitable, axis=0)])
        similarity_score = prediction[0][0] * 10  # Multiplicar por 100 para obtener el porcentaje

        # Predecir similitud
        #prediction_dubitada = model.predict(img_dubitada)
        #prediction_indubitable = model.predict(img_indubitable)
        #similarity_score = 1 - np.abs(prediction_dubitada - prediction_indubitable)
        #similarity_score_value = similarity_score[0][0]

        similarity_score_value = similarity_score

        # Determinar el resultado
        threshold = 50.0  
        if similarity_score_value >= threshold:
            result = 'LA FIRMA ES GENUINA'
        else:
            result = 'LA FIRMA ES FALSA'

        #percentage = similarity_score_value * 100
        yolo_image_path = yolo_image_path.replace('\\', '/')  # Normalizar la ruta

        # Usar url_for para las imágenes
        url_dubitada = url_for('static', filename='uploads/' + secure_filename(file_dubitada.filename))
        url_indubitable = url_for('static', filename='uploads/' + secure_filename(file_indubitable.filename))

        return render_template('comparar.html', result=result, percentage=similarity_score_value, 
                               yolo_image=yolo_image_path, labels_resultados=labels_resultados, 
                               imagen1=url_dubitada, imagen2=url_indubitable)

    except Exception as e:
        return f'<p>Error al procesar las imágenes: {str(e)}</p>', 500

# CREACION DE CASOS Y LISTADO DE CASOSO (FIN)

# Rutas para la aplicación
""" @app.route('/firmas')
def signature_verification():
    return render_template('/firmas.html') """





""" @app.route('/listar_casos_c')
def listar_casos_c():
    cur = mySQL.connection.cursor()
    cur.execute("SELECT * FROM caso")
    firmas = cur.fetchall()
    return render_template('firmas.html', firmas=firmas) """




@app.route('/predict', methods=['POST'])
def predict():
    image_doubtful_path = request.form.get('imageDoubtful')
    image_indubitable_path = request.form.get('imageIndubitable')
    casoid = request.form.get('casoid')
    print("_____+++++++++_________sasasa")
    print(image_doubtful_path)
    print(image_indubitable_path)
    print(casoid)
    imagen1=image_doubtful_path
    imagen2=image_indubitable_path
    basepath = os.path.dirname(__file__)
    image_doubtful_path = os.path.join(basepath, image_doubtful_path.lstrip('/'))
    image_indubitable_path = os.path.join(basepath, image_indubitable_path.lstrip('/'))
    print(f'total {image_doubtful_path}')
    print(f'total2 {image_indubitable_path}')

    if not image_doubtful_path or not image_indubitable_path:
        return '<p>No se subieron ambos archivos (dubitada e indubitable).</p>', 400

    try:
        if not os.path.exists(image_doubtful_path) or not os.path.exists(image_indubitable_path):
            return '<p>Una o ambas imágenes no se encontraron en las rutas proporcionadas.</p>', 404

        # Ejecutar YOLOv7 para detectar características en la firma dubitada
        yolo_weights = 'best.pt'  # Ruta al modelo YOLOv7 entrenado
        process = subprocess.Popen(["python", "yolo/detect.py", '--source', image_doubtful_path, "--weights", yolo_weights], shell=True)
        process.wait()  # Esperar a que el proceso termine
        labels_resultados = []
        with open('labels_resultados.txt', 'r') as f:
            labels_resultados = [line.strip() for line in f.readlines()]

        print("_____________________")
        print(labels_resultados)
        
        # Verificar si YOLO ejecutó correctamente
        print("YOLO ejecutado correctamente, esperando resultados.")

        # Verificar si existe una carpeta en `runs/detect`
        folder_path = 'runs/detect'
        subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
        
        if not subfolders:
            return "Error: No se encontraron subcarpetas en runs/detect.", 500

        latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
        yolo_image_path = os.path.join(folder_path, latest_subfolder, os.path.basename(image_doubtful_path))


        
        # Verifica si la imagen procesada existe
        print(f'Ruta de la imagen procesada por YOLO: {yolo_image_path}')
        if not os.path.exists(yolo_image_path):
            return f"Error: La imagen procesada por YOLO no se encontró en {yolo_image_path}.", 500

        # Procesamiento adicional de las firmas con el modelo de verificación de firmas
        img_doubtful = cv2.imread(image_doubtful_path)
        img_doubtful = cv2.resize(img_doubtful, (224, 224))
        img_doubtful = img_doubtful.astype('float32') / 255.0
        #img_doubtful = img_doubtful / 255.0
        #img_doubtful = np.expand_dims(img_doubtful, axis=0)

        img_indubitable = cv2.imread(image_indubitable_path)
        img_indubitable = cv2.resize(img_indubitable, (224, 224))
        img_indubitable = img_indubitable.astype('float32') / 255.0
        #img_indubitable = img_indubitable / 255.0
        #img_indubitable = np.expand_dims(img_indubitable, axis=0)

        prediction = siamese_model.predict([np.expand_dims(img_doubtful, axis=0), np.expand_dims(img_indubitable, axis=0)])
        similarity_score = prediction[0][0] * 10  # Multiplicar por 100 para obtener el porcentaje


        # Realizar predicciones con el modelo de verificación de firmas
        #prediction_doubtful = model.predict(img_doubtful)
        #prediction_indubitable = model.predict(img_indubitable)

        #print("predicciones")
        #print(prediction_doubtful)
        #print(prediction_indubitable)


        # Comparación de resultados entre ambas predicciones
        #similarity_score = 1 - np.abs(prediction_doubtful - prediction_indubitable)
        #similarity_score_value = similarity_score[0][0]

        similarity_score_value = similarity_score

        threshold = 50.0  # Umbral para definir la autenticidad
        if similarity_score_value >= threshold:
            result = 'LA FIRMA ES GENUINA'
        else:
            result = 'LA FIRMA ES FALSA'

        #percentage = similarity_score_value * 100

        cur = mySQL.connection.cursor()
        cur.execute("SELECT * FROM caso WHERE activo = 1")
        casos = cur.fetchall()
        
      
        yolo_image_path = yolo_image_path.replace('\\', '/')

        casos=''
        
        # Renderizar el template HTML con el mensaje y la imagen de YOLOv7
        return render_template('spocometria.html', result=result, percentage=similarity_score_value, yolo_image=yolo_image_path,casos=casos,labels_resultados=labels_resultados,imagen1=imagen1,imagen2=imagen2,casoid=casoid)

    except Exception as e:
        return f'<p>Error al procesar las imágenes: {str(e)}</p>', 500



# Ruta para servir la imagen procesada por YOLOv7
@app.route('/show_yolo_image/<filename>')
def show_yolo_image(filename):
    yolo_output_dir = 'runs/detect'
    
    try:
        subfolders = [f for f in os.listdir(yolo_output_dir) if os.path.isdir(os.path.join(yolo_output_dir, f))]
        latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(yolo_output_dir, x)))
        
        # Construir la ruta completa del archivo
        image_path = os.path.join(yolo_output_dir, latest_subfolder, filename)
        
        # Imprimir el path que se está intentando acceder
        print(f"Buscando la imagen en: {image_path}")
        
        if os.path.exists(image_path):
            return send_from_directory(os.path.join(yolo_output_dir, latest_subfolder), filename)
        else:
            return f"Archivo {filename} no encontrado en {image_path}", 404

    except Exception as e:
        return f"Error al buscar la imagen procesada: {str(e)}", 500

@app.route('/mostrar_imagen_procesada/<ruta_c>/<filename>')
def mostrar_imagen_procesada(ruta_c, filename):
    yolo_output_dir = 'resultados_firmas'
    print('-'*100)
    print('entro a la ruta pa mostrar imagen')
    
    try:
        
        # Construir la ruta completa del archivo
        image_path = os.path.join(yolo_output_dir, ruta_c, filename)
        
        # Imprimir el path que se está intentando acceder
        print(f"Buscando la imagen en: {image_path}")
        
        if os.path.exists(image_path):
            return send_from_directory(os.path.join(yolo_output_dir, ruta_c), filename)
        else:
            return f"Archivo {filename} no encontrado en {image_path}", 404

    except Exception as e:
        return f"Error al buscar la imagen procesada: {str(e)}", 500

@app.route('/ver/caso/<id>', methods=['GET'])
def ver_caso(id):
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    conexion = mySQL.connection
    cur = conexion.cursor()

    cur.execute("SELECT * FROM caso WHERE id_caso = %s", (id,))
    
    caso = cur.fetchone()
    cur.execute("SELECT * FROM resultados WHERE caso = %s", (id,))
    
    resultados = cur.fetchone()
    cur.close()

    detalles = None

    if resultados:
        valores = str(resultados['detalle'])[1:len(resultados['detalle'])-1].replace("'", "")
        valores = valores.split(',')
        detalles = [item.split() for item in valores]
        resultados['ruta_imagen'] = str(resultados['ruta_imagen']).replace('\\', '/').split('/')
        resultados['ruta_carpeta'] = str(resultados['ruta_imagen'][1])
        resultados['ruta_imagen'] = str(resultados['ruta_imagen'][2])
        print(detalles)
        print(resultados['ruta_imagen'])

        

    return render_template('ver_caso.html', caso=caso, resultados=resultados, detalles = detalles)

@app.route('/editar/caso/<id>', methods=['POST'])
def editar_caso(id):
    print(id)
    id_usuario_modificado = session['id_usuario']
    nombre_caso = request.form['nombre_caso']
    descripcion_caso = request.form['descripcion']
    cur = mySQL.connection.cursor()
    cur.execute('UPDATE caso SET nombre_caso = %s, descripcion = %s, id_usuario_modificado = %s WHERE id_caso = %s', (nombre_caso, descripcion_caso, id_usuario_modificado, id))
    mySQL.connection.commit()

    return redirect(url_for('listar_casos'))

@app.route('/borrar/caso/<id>', methods=['GET'])
def borrar_caso(id):
    print(id)
    cur = mySQL.connection.cursor()
    cur.execute('UPDATE caso SET activo = 0 WHERE id_caso = %s', (id))
    mySQL.connection.commit()
    return redirect(url_for('listar_casos'))

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)