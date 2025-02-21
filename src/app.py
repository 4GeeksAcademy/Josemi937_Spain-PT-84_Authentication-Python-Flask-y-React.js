"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from api.utils import APIException, generate_sitemap
from api.models import db, User
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from flask_cors import CORS

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

from flask_bcrypt import Bcrypt



ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../public/')
app = Flask(__name__)
app.url_map.strict_slashes = False

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_KEY")
jwt = JWTManager(app)

bcrypt = Bcrypt(app)

CORS(app)


db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)


setup_admin(app)


setup_commands(app)


app.register_blueprint(api, url_prefix='/api')



@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code




@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')


@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0
    return response


@app.route('/register', methods=['POST'])
def register():
    body = request.get_json(silent=True)
    if body == None:
        return jsonify({'msg': 'Debes enviar informacion en el body: name, surname,email y password'}),400
    if 'email' not in body:
        return jsonify({'msg': 'El campo email es obligatorio'}),400
    if 'password' not in body:
        return jsonify({'msg': 'El campo password es obligatorio'}), 400
    user = User.query.filter_by(email=body['email']).first()
    if user is not None:
        return jsonify ({'msg': f'El correo {body["email"]} ya ha sido registrado'}),400 
    new_user = User()
    new_user.email = body['email']
    new_user.password = bcrypt.generate_password_hash(body['password']).decode('utf-8')
    new_user.is_active = True
    db.session.add(new_user)  
    db.session.commit()
    return jsonify ({'msg': 'Nuevo usuario creado con exito!'}), 201


@app.route('/login', methods=['POST'])
def login():
    body = request.get_json(silent=True)
    if body == None:
        return jsonify({'msg': 'Debes enviar informacion en el body: email y password'}),400
    if 'email' not in body:
        return jsonify({'msg': 'El campo email es obligatorio'}),400
    if 'password' not in body:
        return jsonify({'msg': 'El campo password es obligatorio'}), 400
        
    user = User.query.filter_by(email=body['email']).first()
    print(user)
    check_password = bcrypt.check_password_hash(user.password, body['password'])
    if user is None or check_password == False:
        return jsonify({'msg': 'Correo o contraseña invalido'}),401
    access_token = create_access_token(identity=user.email)
    return jsonify({'token': access_token})


@app.route('/private', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'msg': 'ok', 'user': current_user})



if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
