import unittest
import sys
sys.path.append('../packages')

from packages.db import db
import packages.models as models
import packages.utils as utils
from flask import Flask, jsonify, request, send_from_directory, abort, make_response, url_for, redirect
import bcrypt

class TestUtils(unittest.TestCase):
    
    def setUp(self):
        """Configura a aplicação Flask e a conexão com o banco de dados para os testes."""
        self.app = Flask(__name__)
        self.app.config['DATABASE_URI'] = 'sqlite:///test_db.sqlite'  # Use um banco de dados de teste
        self.app.config['SECRET_KEY'] = 'your_secret_key'
        self.app.config['CLOUD_STORAGE_ENABLED'] = False # Desativa o Cloud Storage nos testes
        self.app.config['CLOUD_STORAGE_BUCKET'] = 'your_bucket_name' # Se Cloud Storage estiver ativado, defina o nome do bucket.

        # Inicializa a conexão com o banco de dados
        utils.setup_db(self.app.config['DATABASE_URI'])  # Use a função utils.setup_db para configurar o banco de dados

        # Importe o blueprint depois de criar a aplicação
        from packages.routes_users import bp as users_bp
        self.app.register_blueprint(users_bp)

        self.app.config['DB_CONNECTION'] = db.get_db()  # Use db.get_db para obter a conexão com o banco de dados

        self.client = self.app.test_client()

    def tearDown(self):
        """Limpa o banco de dados após cada teste."""
        self.db_connection.close_connection()

    def test_is_admin(self):
        """Verifica se a função is_admin retorna True para um usuário administrador."""
        with self.app.app_context():
            # Crie um usuário e atribua a role de administrador
            self.db_connection.execute_query("INSERT INTO users (username, password_hash) VALUES ('adminuser', 'hash')")
            user_id = self.db_connection.fetchone_dict("SELECT id FROM users WHERE username = 'adminuser'")['id']
            self.db_connection.execute_query("INSERT INTO roles (name) VALUES ('admin')")
            role_id = self.db_connection.fetchone_dict("SELECT id FROM roles WHERE name = 'admin'")['id']
            self.db_connection.execute_query("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))
            self.assertTrue(utils.is_admin(user_id, self.db_connection))

    def test_is_admin_not_admin(self):
        """Verifica se a função is_admin retorna False para um usuário que não é administrador."""
        with self.app.app_context():
            # Crie um usuário sem a role de administrador
            self.db_connection.execute_query("INSERT INTO users (username, password_hash) VALUES ('testuser', 'hash')")
            user_id = self.db_connection.fetchone_dict("SELECT id FROM users WHERE username = 'testuser'")['id']
            self.assertFalse(utils.is_admin(user_id, self.db_connection))

    def test_authenticate(self):
        """Verifica se a função authenticate retorna o ID do usuário para credenciais válidas."""
        with self.app.app_context():
            # Crie um usuário de teste
            self.db_connection.execute_query("INSERT INTO users (username, password_hash) VALUES ('testuser', 'hash')")
            user_id = self.db_connection.fetchone_dict("SELECT id FROM users WHERE username = 'testuser'")['id']
            hashed_password = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.db_connection.execute_query("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_password, user_id))
            self.assertEqual(utils.authenticate('testuser', 'password123', self.db_connection), user_id)

    def test_authenticate_invalid_credentials(self):
        """Verifica se a função authenticate retorna None para credenciais inválidas."""
        with self.app.app_context():
            # Crie um usuário de teste
            self.db_connection.execute_query("INSERT INTO users (username, password_hash) VALUES ('testuser', 'hash')")
            self.assertIsNone(utils.authenticate('testuser', 'wrongpassword', self.db_connection))

    def test_generate_token(self):
        """Verifica se a função generate_token gera um token JWT válido."""
        token = utils.generate_token(1, 'your_secret_key', 'HS256')
        self.assertIsNotNone(token)

    def test_decode_token(self):
        """Verifica se a função decode_token decodifica um token JWT válido."""
        token = utils.generate_token(1, 'your_secret_key', 'HS256')
        user_id = utils.decode_token(token, 'your_secret_key', 'HS256')
        self.assertEqual(user_id, 1)

    def test_generate_invite_code(self):
        """Verifica se a função generate_invite_code gera um código de convite aleatório."""
        invite_code = utils.generate_invite_code()
        self.assertIsNotNone(invite_code)

    def test_validate_username(self):
        """Verifica se a função validate_username valida o formato do nome de usuário."""
        self.assertTrue(utils.validate_username('testuser'))
        self.assertTrue(utils.validate_username('test_user'))
        self.assertTrue(utils.validate_username('test1234'))
        self.assertFalse(utils.validate_username('test-user'))
        self.assertFalse(utils.validate_username('test user'))

    def test_paginate(self):
        """Verifica se a função paginate implementa a paginação corretamente."""
        with self.app.app_context():
            # Crie alguns usuários de teste
            for i in range(11):
                self.db_connection.execute_query("INSERT INTO users (username, password_hash) VALUES ('user" + str(i) + "', 'hash')")
            query = self.db_connection.session.query(models.User)
            response = utils.paginate(query, per_page=5, request=request, url_for=url_for)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(len(data['items']), 5)
            self.assertEqual(data['total'], 11)
            self.assertEqual(data['page'], 1)
            self.assertIsNotNone(data['next_page'])

    def test_paginate_next_page(self):
        """Verifica se a função paginate retorna o link para a próxima página."""
        with self.app.app_context():
            # Crie alguns usuários de teste
            for i in range(11):
                self.db_connection.execute_query("INSERT INTO users (username, password_hash) VALUES ('user" + str(i) + "', 'hash')")
            query = self.db_connection.session.query(models.User)
            response = utils.paginate(query, per_page=5, page=2, request=request, url_for=url_for)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(len(data['items']), 5)
            self.assertEqual(data['total'], 11)
            self.assertEqual(data['page'], 2)
            self.assertIsNotNone(data['next_page'])
            self.assertIsNotNone(data['prev_page'])

    def test_paginate_last_page(self):
        """Verifica se a função paginate retorna None para a próxima página na última página."""
        with self.app.app_context():
            # Crie alguns usuários de teste
            for i in range(11):
                self.db_connection.execute_query("INSERT INTO users (username, password_hash) VALUES ('user" + str(i) + "', 'hash')")
            query = self.db_connection.session.query(models.User)
            response = utils.paginate(query, per_page=5, page=3, request=request, url_for=url_for)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(len(data['items']), 1)
            self.assertEqual(data['total'], 11)
            self.assertEqual(data['page'], 3)
            self.assertIsNone(data['next_page'])
            self.assertIsNotNone(data['prev_page'])

    def test_filter_packages(self):
        """Verifica se a função filter_packages filtra pacotes corretamente."""
        with self.app.app_context():
            # Crie' alguns pacotes e repositórios
            self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
            repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature, approved) VALUES ('TestPackage1', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature', 1)")
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature, approved) VALUES ('TestPackage2', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature', 0)")
            self.db_connection.execute_query("INSERT INTO package_repositories (package_id, repository_id) VALUES (1, 1)")
            self.db_connection.execute_query("INSERT INTO package_repositories (package_id, repository_id) VALUES (2, 1)")
            query = self.db_connection.session.query(models.Package)
            # Teste filtrar por repository_id
            filtered_query = utils.filter_packages(query, repository_id=repository_id)
            self.assertEqual(filtered_query.count(), 2)  # Deve haver dois pacotes no repositório
            # Teste filtrar por network_type
            filtered_query = utils.filter_packages(query, network_type='clearnet')
            self.assertEqual(filtered_query.count(), 2)  # Deve haver dois pacotes na rede clearnet
            # Teste filtrar por approved
            filtered_query = utils.filter_packages(query, approved_status=True)
            self.assertEqual(filtered_query.count(), 1)  # Deve haver um pacote aprovado
            filtered_query = utils.filter_packages(query, approved_status=False)
            self.assertEqual(filtered_query.count(), 1)  # Deve haver um pacote não aprovado
            # Teste filtrar por múltiplos critérios
            filtered_query = utils.filter_packages(query, repository_id=repository_id, network_type='clearnet', approved_status=True)
            self.assertEqual(filtered_query.count(), 1)  # Deve haver um pacote aprovado, no repositório e na rede clearnet
    
    def test_validate_package_data(self):
        """Verifica se a função validate_package_data valida os dados do pacote corretamente."""
        # Dados válidos
        data = {'name': 'TestPackage', 'version': '1.0.0', 'public_key': 'public_key', 'signature': 'signature'}
        required_fields = ['name', 'version', 'public_key', 'signature']
        error, status_code = utils.validate_package_data(data, required_fields)
        self.assertIsNone(error)
        self.assertIsNone(status_code)
        # Dados inválidos - campo ausente
        data = {'name': 'TestPackage', 'version': '1.0.0', 'public_key': 'public_key'}
        required_fields = ['name', 'version', 'public_key', 'signature']
        error, status_code = utils.validate_package_data(data, required_fields)
        self.assertEqual(error, "Campos obrigatórios ausentes: signature")
        self.assertEqual(status_code, 400)
        # Dados inválidos - dados ausentes
        data = None
        required_fields = ['name', 'version', 'public_key', 'signature']
        error, status_code = utils.validate_package_data(data, required_fields)
        self.assertEqual(error, "Dados ausentes")
        self.assertEqual(status_code, 400)