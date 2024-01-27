
import datetime
from bson import ObjectId
from flask import Flask, jsonify, request, session
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import jwt 

app = Flask(__name__)
app.config['MONGO_URI']='mongodb://localhost:27017/pythondb'
PyMongo(app)
mongo = PyMongo(app)
bcrypt = Bcrypt(app)  # Inicializar Bcrypt con tu aplicación
app.config['SECRET_KEY'] = 'dsdd4353'

CORS(app)

db = mongo.db.users
dbt = mongo.db.task


#generar token
def generate_token(email):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token válido por 1 hora
    payload = {
        'email': email,
        'exp': expiration_time
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token



#crear usuario
@app.route('/users', methods=['POST'])
def createUser():
    user_data = {
        'name': request.json.get('name'),
        'email': request.json.get('email'),
        'password': bcrypt.generate_password_hash(request.json.get('password')).decode('utf-8')
        
    }
    

    result = db.insert_one(user_data)
    inserted_id = result.inserted_id
    print(str(inserted_id))
    
    return jsonify({'id': str(inserted_id), 'message': 'User created successfully'})

#Crear Tareas
@app.route('/task', methods=['POST'])
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


#inicio de sesion
@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')  # Obtener el email desde la solicitud JSON
    password = request.json.get('password')  # Obtener la contraseña desde la solicitud JSON

    if not email or not password:
        return jsonify({'mensaje': 'El email y la contraseña son obligatorios'}), 400

    usuario = db.find_one({'email': email})

    if usuario and bcrypt.check_password_hash(usuario['password'], password):
        user_id = str(usuario['_id'])
        token = generate_token({'user_id': str(usuario['_id']), 'email': usuario['email']})
        session['email'] = usuario['email']
        return jsonify({'token': token, 'mensaje': 'Inicio de sesión exitoso','email':email, 'user_id':user_id,
                        'status':'ok'}), 200
    else:
        return jsonify({'mensaje': 'Credenciales inválidas'}), 401

 #Usuarios //
@app.route('/users', methods=['GET'])
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

#mostrar usuarios
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

#eliminar usuario
@app.route('/user/<id>', methods=['DELETE'])
def deleteUser(id):
    db.delete_one({'_id': ObjectId(id)})
    return jsonify({'msg': 'Usuario eliminado'})


#actualizar usuario
@app.route('/user/<id>', methods=['PUT'])
def updateUser(id):
    db.update_one({'_id': ObjectId(id)}, {'$set': {
        'name': request.json['name'],
        'email': request.json['email'],
        'password': request.json['password']
    }})
    
    return jsonify({'message': 'User updated successfully'})

if __name__ == "__main__":
    app.run(debug=True)