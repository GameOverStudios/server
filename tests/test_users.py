# tests/test_users.py
import unittest
import sys
sys.path.append('../packages')

from packages import db, models, utils, cloud_storage
from packages.routes_users import bp as users_bp
from flask import Flask, jsonify, request, send_from_directory, abort, make_response, url_for, redirect
import json
from unittest.mock import patch

class TestUsers(unittest.TestCase):

    def setUp(self):
        """Configura a aplicação Flask e a conexão com o banco de dados para os testes."""
        self.app = Flask(__name__)
        self.app.config['DATABASE_URI'] = 'sqlite:///test_db.sqlite'  # Use um banco de dados de teste
        self.app.config['SECRET_KEY'] = 'your_secret_key'
        self.app.config['CLOUD_STORAGE_ENABLED'] = False # Desativa o Cloud Storage nos testes
        self.app.config['CLOUD_STORAGE_BUCKET'] = 'your_bucket_name' # Se Cloud Storage estiver ativado, defina o nome do bucket.

        # Inicializa a conexão com o banco de dados
        self.db_connection = db.DatabaseConnection(self.app.config['DATABASE_URI'])
        self.db_connection.create_tables()  # Cria as tabelas se elas não existirem

        # Registra o blueprint para a aplicação
        self.app.register_blueprint(users_bp)
        self.app.config['DB_CONNECTION'] = self.db_connection

        self.client = self.app.test_client()

    def tearDown(self):
        """Limpa o banco de dados após cada teste."""
        self.db_connection.close_connection()

    def test_create_user(self):
        """Verifica se a rota POST /api/users cria um novo usuário."""
        with self.app.app_context():
            response = self.client.post('/api/users', data=json.dumps({'username': 'TestUser', 'email': 'test@example.com', 'password': 'password'}), headers={'Authorization': 'Bearer test_token'}) # Token de um administrador
            self.assertEqual(response.status_code, 201)
            self.assertIsNotNone(response.get_json().get('id'))
            # Verifica se o usuário foi criado no banco de dados
            new_user = self.db_connection.fetchone_dict("SELECT * FROM users WHERE username = 'TestUser'")
            self.assertIsNotNone(new_user)

    def test_create_user_duplicate_username(self):
        """Verifica se a rota POST /api/users retorna um erro 409 para um nome de usuário duplicado."""
        with self.app.app_context():
            # Crie um usuário de teste
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser', 'test@example.com', 'password')")
            response = self.client.post('/api/users', data=json.dumps({'username': 'TestUser', 'email': 'test2@example.com', 'password': 'password'}), headers={'Authorization': 'Bearer test_token'}) # Token de um administrador
            self.assertEqual(response.status_code, 409)

    def test_create_user_duplicate_email(self):
        """Verifica se a rota POST /api/users retorna um erro 409 para um email duplicado."""
        with self.app.app_context():
            # Crie um usuário de teste
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser', 'test@example.com', 'password')")
            response = self.client.post('/api/users', data=json.dumps({'username': 'TestUser2', 'email': 'test@example.com', 'password': 'password'}), headers={'Authorization': 'Bearer test_token'}) # Token de um administrador
            self.assertEqual(response.status_code, 409)

    def test_login(self):
        """Verifica se a rota POST /api/login efetua login de um usuário."""
        with self.app.app_context():
            # Crie um usuário de teste
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser', 'test@example.com', 'password')")
            response = self.client.post('/api/login', data=json.dumps({'username': 'TestUser', 'password': 'password'}))
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.get_json().get('token'))

    def test_login_invalid_credentials(self):
        """Verifica se a rota POST /api/login retorna um erro 401 para credenciais inválidas."""
        with self.app.app_context():
            response = self.client.post('/api/login', data=json.dumps({'username': 'TestUser', 'password': 'wrongpassword'}))
            self.assertEqual(response.status_code, 401)

    def test_get_user(self):
        """Verifica se a rota GET /api/users/<int:user_id> retorna informações de um usuário."""
        with self.app.app_context():
            # Crie um usuário de teste
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser', 'test@example.com', 'password')")
            user_id = self.db_connection.fetchone_dict("SELECT id FROM users WHERE username = 'TestUser'")['id']
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            response = self.client.get(f'/api/users/{user_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['username'], 'TestUser')

    def test_update_user(self):
        """Verifica se a rota PUT /api/users/<int:user_id> atualiza informações de um usuário."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256') # Token de um administrador
            # Crie um usuário de teste
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser', 'test@example.com', 'password')")
            user_id = self.db_connection.fetchone_dict("SELECT id FROM users WHERE username = 'TestUser'")['id']
            response = self.client.put(f'/api/users/{user_id}', data=json.dumps({'username': 'UpdatedUser', 'email': 'updated@example.com'}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            # Verifica se o usuário foi atualizado no banco de dados
            updated_user = self.db_connection.fetchone_dict("SELECT * FROM users WHERE username = 'UpdatedUser'")
            self.assertIsNotNone(updated_user)

    def test_update_user_duplicate_username(self):
        """Verifica se a rota PUT /api/users/<int:user_id> retorna um erro 409 para um nome de usuário duplicado."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256') # Token de um administrador
            # Crie dois usuários de teste
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser', 'test@example.com', 'password')")
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser2', 'test2@example.com', 'password')")
            user_id = self.db_connection.fetchone_dict("SELECT id FROM users WHERE username = 'TestUser'")['id']
            response = self.client.put(f'/api/users/{user_id}', data=json.dumps({'username': 'TestUser2'}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 409)

    def test_update_user_duplicate_email(self):
        """Verifica se a rota PUT /api/users/<int:user_id> retorna um erro 409 para um email duplicado."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256') # Token de um administrador
            # Crie dois usuários de teste
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser', 'test@example.com', 'password')")
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser2', 'test2@example.com', 'password')")
            user_id = self.db_connection.fetchone_dict("SELECT id FROM users WHERE username = 'TestUser'")['id']
            response = self.client.put(f'/api/users/{user_id}', data=json.dumps({'email': 'test2@example.com'}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 409)

    def test_update_user_unauthorized(self):
        """Verifica se a rota PUT /api/users/<int:user_id> retorna um erro 403 para um usuário não autorizado."""
        with self.app.app_context():
            # Crie um usuário de teste
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser', 'test@example.com', 'password')")
            user_id = self.db_connection.fetchone_dict("SELECT id FROM users WHERE username = 'TestUser'")['id']
            token = utils.generate_token(2, self.app.config['SECRET_KEY'], 'HS256')  # Token de um usuário diferente
            response = self.client.put(f'/api/users/{user_id}', data=json.dumps({'username': 'UpdatedUser'}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 403)

    def test_delete_user(self):
        """Verifica se a rota DELETE /api/users/<int:user_id> exclui um usuário."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256') # Token de um administrador
            # Crie um usuário de teste
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser', 'test@example.com', 'password')")
            user_id = self.db_connection.fetchone_dict("SELECT id FROM users WHERE username = 'TestUser'")['id']
            response = self.client.delete(f'/api/users/{user_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            # Verifica se o usuário foi excluído do banco de dados
            deleted_user = self.db_connection.fetchone_dict("SELECT * FROM users WHERE username = 'TestUser'")
            self.assertIsNone(deleted_user)

    def test_delete_user_unauthorized(self):
        """Verifica se a rota DELETE /api/users/<int:user_id> retorna um erro 403 para um usuário não autorizado."""
        with self.app.app_context():
            # Crie um usuário de teste
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser', 'test@example.com', 'password')")
            user_id = self.db_connection.fetchone_dict("SELECT id FROM users WHERE username = 'TestUser'")['id']
            token = utils.generate_token(2, self.app.config['SECRET_KEY'], 'HS256')  # Token de um usuário diferente
            response = self.client.delete(f'/api/users/{user_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 403)

    def test_get_user_by_username(self):
        """Verifica se a rota GET /api/users/username/<string:username> recupera informações de um usuário por nome de usuário."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            # Crie um usuário de teste
            self.db_connection.execute_query("INSERT INTO users (username, email, password) VALUES ('TestUser', 'test@example.com', 'password')")
            response = self.client.get('/api/users/username/TestUser', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['username'], 'TestUser')