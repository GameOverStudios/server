import os
import logging
from flask import Flask, jsonify, request, make_response, url_for
from datetime import timedelta
from functools import wraps
import pytz
from packages import db, utils  
from packages.cloud_storage import UPLOAD_FOLDER
from flask_jwt_extended import JWTManager  
from packages.routes_users import users_bp
from packages.routes_packages import packages_bp
from packages.routes_repositories import repositories_bp
from packages.routes_ratings import ratings_bp
from packages.routes_invites import invites_bp  

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('app.log'),
                              logging.StreamHandler()])

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sua_chave_secreta_jwt') # Usar variável de ambiente, ou um valor padrão
app.config['DATABASE_URI'] = os.environ.get('DATABASE_URI')
app.config['CLOUD_STORAGE_ENABLED'] = os.environ.get('CLOUD_STORAGE_ENABLED', 'False').lower() == 'true'
app.config['CLOUD_STORAGE_BUCKET'] = os.environ.get('CLOUD_STORAGE_BUCKET')  # Nome do bucket (se aplicável)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # Utiliza o upload folder definido no módulo de Cloud Storage.
app.config["JWT_SECRET_KEY"] = app.config['SECRET_KEY']
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
app.config["JWT_ALGORITHM"] = "HS256"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_db.sqlite'

UTC = pytz.utc
JWT_ALGORITHM = 'HS256' 

def create_app():    
    jwt = JWTManager(app)
    db.init_app(app)
    with app.app_context():
        db.db_connection = db.DatabaseConnection('sqlite:///test_db.sqlite')
        db.db_connection.create_tables()

    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(packages_bp, url_prefix='/api/packages')
    app.register_blueprint(repositories_bp, url_prefix='/api/repositories')
    app.register_blueprint(ratings_bp, url_prefix='/api/ratings')
    app.register_blueprint(invites_bp, url_prefix='/api/invites')

    @app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    @app.errorhandler(500)
    def internal_server_error(error):
        logging.exception("Erro interno do servidor: %s", error)  # Log mais detalhado
        return make_response(jsonify({'error': 'Internal Server Error'}), 500)

    @app.teardown_appcontext
    def close_db(error):
        db.close_connection(error)

    @app.before_request
    def log_request_info():
        logging.info(f"Requisição recebida: {request.method} {request.path}")

    def authenticate(username, password):
        return utils.authenticate(username, password, db.get_db())

    def requires_admin(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
           if not utils.is_admin(request.user_id, db.get_db()):
               return jsonify({'error': 'Admin privileges required'}), 403
           return f(*args, **kwargs)
        return decorated_function

    def paginate(query, args=(), per_page=20):
        return utils.paginate(query, args, per_page, request, url_for)

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "OK"}), 200

    app.run(debug=True, host='0.0.0.0') # host='0.0.0.0' torna o app acessível externamente na rede

    return app

if __name__ == '__main__':
    app = create_app()