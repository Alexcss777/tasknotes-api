import datetime
from functools import wraps
from bson import ObjectId
from flask import Flask, jsonify, request, session
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import jwt 
from flask import current_app

# Define la aplicación Flask antes de configurar app.config
app = Flask(__name__)

# Configura la URI de conexión a MongoDB Atlas
app.config['MONGO_URI'] = 'mongodb+srv://alexcslaguna:alexcss77@clustertest.oxtpjng.mongodb.net/mydatabase?retryWrites=true&w=majority&appName=clustertest'

# Inicializa PyMongo con la configuración de la aplicación
mongo = PyMongo(app)

# Inicializa otros componentes
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'dsdd4353'

# Habilita CORS
CORS(app)

# Definir las colecciones
db = mongo.db.users
dbt = mongo.db.task

# Probar la conexión y crear colecciones automáticamente
try:
    print("Acceso a MongoDB exitoso.")

    # Crear la colección 'users' si no existe
    if not db.find_one():
        db.insert_one({'init': 'create users collection'})
        print("Colección 'users' creada.")

    # Crear la colección 'task' si no existe
    if not dbt.find_one():
        dbt.insert_one({'init': 'create task collection'})
        print("Colección 'task' creada.")

    print("Conexión a MongoDB establecida correctamente y colecciones verificadas.")
except Exception as e:
    print(f"Error al conectar con MongoDB: {e}")

# Generar token
def generate_token(email):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token válido por 1 hora
    payload = {
        'email': email,
        'exp': expiration_time
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'mensaje': 'Token faltante'}), 401

        try:
            # Decodificar el token
            decoded_token = jwt.decode(token.split(" ")[1], current_app.config['SECRET_KEY'], algorithms=['HS256'])
            # Puedes almacenar la información del usuario en 'decoded_token' y usarla en la función protegida
        except jwt.ExpiredSignatureError:
            return jsonify({'mensaje': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'mensaje': 'Token inválido'}), 401

        return f(*args, **kwargs)

    return decorated

# Crear usuario
@app.route('/users', methods=['POST'])
def createUser():
    email = request.json.get('email')
    usuario = db.find_one({'email': email})
    print(usuario)
    if usuario is None:
        user_data = {
            'name': request.json.get('name'),
            'email': request.json.get('email'),
            'password': bcrypt.generate_password_hash(request.json.get('password')).decode('utf-8')
        }
        result = db.insert_one(user_data)
        inserted_id = result.inserted_id
        print(str(inserted_id))
        return jsonify({'mensaje': 'User created successfully'})
    else:
        return jsonify({'mensaje': 'Este email ya esta registrado'}), 401

# Crear tareas
@app.route('/task', methods=['POST'])
@token_required
def createTask():
    task_data = {
        'name': request.json.get('name'),
        'idUser': request.json.get('idUser'),
        'date': request.json.get('date'),
        'description': request.json.get('description')
    }
    result = dbt.insert_one(task_data)
    inserted_id = result.inserted_id
    print(str(inserted_id))
    return jsonify({'id': str(inserted_id), 'message': 'tarea created successfully'})

# Obtener tareas
@app.route('/tasks/<id>', methods=['GET'])
def getTasks(id):
    print(f"Buscando tareas para el usuario con id: {id}")
    tasks = dbt.find({'idUser': id})

    task_list = [{
        '_id': str(ObjectId(task['_id'])),
        'name': task['name'],
        'idUser': task['idUser'],
        'date': task['date'], 
        'description': task['description']
    } for task in tasks]

    print(f"Número de tareas encontradas: {len(task_list)}")
    return jsonify(task_list)

# Eliminar tareas 
@app.route('/tasks/<id>', methods=['DELETE'])
@token_required
def deleteTask(id):
    dbt.delete_one({'_id': ObjectId(id)})
    return jsonify({'msg': 'tarea eliminada'})

# Actualizar tarea
@app.route('/tasks/<id>', methods=['PUT'])
@token_required
def updateTask(id):
    dbt.update_one({'_id': ObjectId(id)}, {'$set': {
        'name': request.json['name'],
        'date': request.json['date'],
        'description': request.json['description']
    }})
    return jsonify({'message': 'Tarea actualizada exitosamente'})

# Obtener tarea por su ID
@app.route('/task/<id>', methods=['GET'])
@token_required
def getTaskId(id):
    task = dbt.find_one({'_id': ObjectId(id)})
    print(task)
    return jsonify({
        '_id': str(ObjectId(task['_id'])),
        'name': task['name'],
        'idUser': task['idUser'],
        'date': task['date'], 
        'description': task['description']
    })

# Inicio de sesión
@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')  # Obtener el email desde la solicitud JSON
    password = request.json.get('password')  # Obtener la contraseña desde la solicitud JSON

    if not email or not password:
        return jsonify({'mensaje': 'El email y la contraseña son obligatorios'}), 400

    usuario = db.find_one({'email': email})

    if usuario and bcrypt.check_password_hash(usuario['password'], password):
        user_id = str(usuario['_id'])
        name = str(usuario['name'])
        token = generate_token({'user_id': str(usuario['_id']), 'email': usuario['email']})
        session['email'] = usuario['email']
        return jsonify({'token': token, 'mensaje': 'Inicio de sesión exitoso','email':email, 'user_id':user_id,
                        'name':name,'status':'ok'}), 200
    elif usuario is None:
        encontrado = False
        return jsonify({ 'encontrado': encontrado}), 401
    else:
        return jsonify({'mensaje': 'Credenciales inválidas'}), 401

# Obtener usuarios
@app.route('/users', methods=['GET'])
@token_required
def getUsers():
    users = []
    for doc in db.find():
        user = {
            '_id': str(doc['_id']),
            'name': doc['name'],
            'email': doc['email'],
            'password': doc['password']  
        }
        users.append(user)
    return jsonify(users)

# Obtener usuario por ID
@app.route('/user/<id>', methods=['GET'])
def getUser(id):
    user = db.find_one({'_id': ObjectId(id)})
    print(user)
    return jsonify({
        '_id': str(ObjectId(user['_id'])),
        'name': user['name'],
        'email': user['email'],
        'password': user['password'] 
    })

# Eliminar usuario
@app.route('/user/<id>', methods=['DELETE'])
def deleteUser(id):
    db.delete_one({'_id': ObjectId(id)})
    return jsonify({'msg': 'Usuario eliminado'})

# Actualizar usuario
@app.route('/user/<id>', methods=['PUT'])
def updateUser(id):
    db.update_one({'_id': ObjectId(id)}, {'$set': {
        'name': request.json['name'],
        'email': request.json['email'],
        'password': request.json['password']
    }})
    return jsonify({'message': 'Usuario actualizado exitosamente'})

if __name__ == "__main__":
    app.run(debug=True)
