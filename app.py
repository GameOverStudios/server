from flask import Flask
from packages import db, models  # Importe suas classes do banco de dados 
from packages.routes_users import users_bp
from packages.routes_packages import packages_bp
from packages.routes_ratings import ratings_bp
from packages.routes_invites import invites_bp
from config import Config  # Importe as configurações da sua aplicação

''' 
    sudo apt-get install python3-flask
    pip install Flask  # Framework Flask
    pip install bcrypt  # Para hash de senhas
    pip install flask-cors  # Para permitir requisições CORS
    pip install flask-jwt-extended  # Para autenticação JWT
    pip install flask-sqlalchemy  # Para integração com banco de dados
    pip install google-cloud-storage  # Para Cloud Storage (opcional)
    pip install python-jose  # Para trabalhar com JWT
    pip install requests  # Para fazer requisições HTTP
    pip install itsdangerous  # Para segurança
    pip install werkzeug  # Para ferramentas da web
    flask run

    python3 -m unittest discover
    
'''
app = Flask(__name__)
app.config.from_object(Config)  # Configure as configurações

db.init_app(app)  # Inicializa a conexão com o banco de dados

# ... Registrar os blueprints da aplicação
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(packages_bp, url_prefix='/api/packages')
app.register_blueprint(ratings_bp, url_prefix='/api/ratings')
app.register_blueprint(invites_bp, url_prefix='/api/invites')

if __name__ == '__main__':
    app.run(debug=True)  # Executa o servidor