from flask import Flask, flash, render_template, request, redirect, session, Response, url_for, send_from_directory, send_from_directory, abort
from flask_mysqldb import MySQL, MySQLdb
from werkzeug.utils import secure_filename
from datetime import datetime
import numpy as np
import cv2
import os
from tensorflow.keras.models import load_model
import subprocess
import torch
import shutil
""" from pymysql.cursors import DictCursor  # Importación adicional necesaria """

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
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# INICIO DE SESION (INICIO)

@app.route('/acceso-login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        _user = request.form['user']
        _password = request.form['password']
        
        cur = mySQL.connection.cursor()
        cur.execute('SELECT * FROM usuario WHERE usuario = %s AND password = %s', (_user, _password,))
        account = cur.fetchone()

        if account:
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

@app.route('/logout', methods=['POST'])
def logout():
    # Eliminar las variables de sesión al cerrar sesión
    session.pop('logueado', None)
    session.pop('id_usuario', None)
    session.pop('nombre', None)
    session.pop('apellido', None)
    # Redirigir al login después de cerrar sesión
    return redirect(url_for('login'))  # Esto debe ser el nombre de la función de vista

# INICIO DE SESION (FIN)


# USUARIOS REGISTRO EDITAR ELIMINAR (INICIO)

@app.route('/usuarios')
def usuarios():
    conexion = mySQL.connection
    cur = conexion.cursor()

    # Solo obtener los usuarios activos
    cur.execute("SELECT * FROM usuario WHERE activo = 1")
    usuarios = cur.fetchall()
    cur.close()

    return render_template('usuarios.html', Usuarios=usuarios)        

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

        # Validación de imagen subida
        imagen = request.files['imagen']
        imagen_filename = None
        if imagen and allowed_file(imagen.filename):
            imagen_filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename))

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

        # Insertar los datos en la tabla `usuario`, incluyendo la imagen, sexo, y fecha
        cur = mySQL.connection.cursor()
        cur.execute("""
            INSERT INTO usuario (nombre, apellido, edad, ci, telefono, email, usuario, password, sexo, imagen, fecha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nombre, apellido, edad, cedula, celular, email, user, password, sexo, imagen_filename, fecha_actual))
        mySQL.connection.commit()
        flash('Usuario creado exitosamente', 'success')

        return redirect(url_for('usuarios'))
  # Redirige a la página 'usuarios.html'


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

    # Obtener la imagen (si se proporciona una nueva)
    imagen = request.files['imagen']
    imagen_actual = request.form['imagen_actual']  # Imagen actual

    # Comprobar si el usuario ha subido una nueva imagen
    if imagen.filename != '':
        # Guardar la imagen en la carpeta 'Users_Profile'
        imagen.save(os.path.join('static/Users_Profile', imagen.filename))
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
    if request.method == 'POST':
        # Verifica si el usuario está logueado
        if 'id_usuario' not in session:
            flash('Debes iniciar sesión para agregar un caso.', 'error')
            return redirect(url_for('login'))

        # Capturando los datos del formulario
        tipo_caso = request.form['tipo_caso']
        nombre_caso = request.form['nombre_caso']
        descripcion = request.form['descripcion']
        departamento = request.form['departamento']
        
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

        # Insertar los datos en la tabla `caso`
        cur = mySQL.connection.cursor()
        cur.execute("""
            INSERT INTO caso (usuario_id, tipo_caso, nombre_caso, descripcion, departamento, fecha, f_dubitada, f_indubitada)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (usuario_id, tipo_caso, nombre_caso, descripcion, departamento, fecha_actual, f_dubitada_filename, f_indubitada_filename))
        mySQL.connection.commit()

        flash('Caso agregado exitosamente', 'success')
        return redirect(url_for('listar_casos'))

    # Si es GET, solo renderiza el formulario de nuevo caso
    return render_template('nuevo_caso.html')

@app.route('/listar_casos')
def listar_casos():
    cur = mySQL.connection.cursor()
    cur.execute("SELECT * FROM caso")
    casos = cur.fetchall()
    return render_template('list_casos.html', casos=casos)

# CREACION DE CASOS Y LISTADO DE CASOSO (FIN)

# Rutas para la aplicación
""" @app.route('/firmas')
def signature_verification():
    return render_template('/firmas.html') """

@app.route('/firmas')
def signatures():
    return render_template('/firmas.html')

""" @app.route('/listar_casos_c')
def listar_casos_c():
    cur = mySQL.connection.cursor()
    cur.execute("SELECT * FROM caso")
    firmas = cur.fetchall()
    return render_template('firmas.html', firmas=firmas) """


@app.route('/predict', methods=['POST'])
def predict():
    file_dubitada = request.files.get('imageDoubtful')
    file_indubitable = request.files.get('imageIndubitable')

    if not file_dubitada or not file_indubitable:
        return '<p>No se subieron ambos archivos (dubitada e indubitable).</p>', 400

    try:
        # Guardar las imágenes cargadas
        basepath = os.path.dirname(__file__)
        dubitada_path = os.path.join(basepath, 'uploads', secure_filename(file_dubitada.filename))
        indubitable_path = os.path.join(basepath, 'uploads', secure_filename(file_indubitable.filename))
        file_dubitada.save(dubitada_path)
        file_indubitable.save(indubitable_path)

        # Comprobar la ruta de la imagen guardada
        print(f'Ruta de la imagen dubitada: {dubitada_path}')
        
        # Ejecutar YOLOv7 para detectar características en la firma dubitada
        yolo_weights = 'best.pt'  # Ruta al modelo YOLOv7 entrenado
        process = subprocess.Popen(["python", "yolo/detect.py", '--source', dubitada_path, "--weights", yolo_weights], shell=True)
        process.wait()  # Esperar a que el proceso termine
        
        # Verificar si YOLO ejecutó correctamente
        print("YOLO ejecutado correctamente, esperando resultados.")

        # Verificar si existe una carpeta en `runs/detect`
        folder_path = 'runs/detect'
        subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
        
        if not subfolders:
            return "Error: No se encontraron subcarpetas en runs/detect.", 500

        latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
        yolo_image_path = os.path.join(folder_path, latest_subfolder, file_dubitada.filename)

        # Verifica si la imagen procesada existe
        print(f'Ruta de la imagen procesada por YOLO: {yolo_image_path}')
        if not os.path.exists(yolo_image_path):
            return f"Error: La imagen procesada por YOLO no se encontró en {yolo_image_path}.", 500

        # Procesamiento adicional de las firmas con el modelo de verificación de firmas
        img_dubitada = cv2.imread(dubitada_path)
        img_dubitada = cv2.resize(img_dubitada, (224, 224))
        img_dubitada = img_dubitada / 255.0
        img_dubitada = np.expand_dims(img_dubitada, axis=0)

        img_indubitable = cv2.imread(indubitable_path)
        img_indubitable = cv2.resize(img_indubitable, (224, 224))
        img_indubitable = img_indubitable / 255.0
        img_indubitable = np.expand_dims(img_indubitable, axis=0)

        # Realizar predicciones con el modelo de verificación de firmas
        prediction_dubitada = model.predict(img_dubitada)
        prediction_indubitable = model.predict(img_indubitable)

        # Comparación de resultados entre ambas predicciones
        similarity_score = 1 - np.abs(prediction_dubitada - prediction_indubitable)
        similarity_score_value = similarity_score[0][0]

        threshold = 0.5  # Umbral para definir la autenticidad
        if similarity_score_value >= threshold:
            result = 'LA FIRMA ES GENUINA'
        else:
            result = 'LA FIRMA ES FALSA'

        percentage = similarity_score_value * 100
        
        # Renderizar el template HTML con el mensaje y la imagen de YOLOv7
        return render_template('firmas.html', result=result, percentage=percentage, yolo_image=yolo_image_path)

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


if __name__ == '__main__':
    app.run(debug=True)
