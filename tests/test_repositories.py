# tests/test_repositories.py
import unittest
import sys
sys.path.append('../packages')

from packages import db, models, utils, cloud_storage
from packages.routes_repositories import bp as repositories_bp
from flask import Flask, jsonify, request, send_from_directory, abort, make_response, url_for, redirect
import json
from unittest.mock import patch

class TestRepositories(unittest.TestCase):

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
        self.app.register_blueprint(repositories_bp)
        self.app.config['DB_CONNECTION'] = self.db_connection

        self.client = self.app.test_client()

    def tearDown(self):
        """Limpa o banco de dados após cada teste."""
        self.db_connection.close_connection()

    def test_create_repository(self):
        """Verifica se a rota POST /api/repositories cria um novo repositório."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            response = self.client.post('/api/repositories', data=json.dumps({'name': 'TestRepo', 'network_type': 'clearnet'}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 201)
            self.assertIsNotNone(response.get_json().get('id'))
            # Verifica se o repositório foi criado no banco de dados
            new_repo = self.db_connection.fetchone_dict("SELECT * FROM repositories WHERE name = 'TestRepo'")
            self.assertIsNotNone(new_repo)

    def test_list_repositories(self):
        """Verifica se a rota GET /api/repositories lista todos os repositórios."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            # Crie um repositório de teste
            self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
            response = self.client.get('/api/repositories', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIsNotNone(data.get('items'))

    def test_get_repository(self):
        """Verifica se a rota GET /api/repositories/<int:repository_id> retorna um repositório específico."""
        with self.app.app_context():
            # Crie um repositório de teste
            self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
            repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            response = self.client.get(f'/api/repositories/{repository_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['name'], 'TestRepo')

    def test_update_repository(self):
        """Verifica se a rota PUT /api/repositories/<int:repository_id> atualiza um repositório."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            # Crie um repositório de teste
            self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
            repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
            response = self.client.put(f'/api/repositories/{repository_id}', data=json.dumps({'name': 'UpdatedRepo'}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            # Verifica se o repositório foi atualizado no banco de dados
            updated_repo = self.db_connection.fetchone_dict("SELECT * FROM repositories WHERE name = 'UpdatedRepo'")
            self.assertIsNotNone(updated_repo)

    def test_delete_repository(self):
        """Verifica se a rota DELETE /api/repositories/<int:repository_id> exclui um repositório."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            # Crie um repositório de teste
            self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
            repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
            response = self.client.delete(f'/api/repositories/{repository_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            # Verifica se o repositório foi excluído do banco de dados
            deleted_repo = self.db_connection.fetchone_dict("SELECT * FROM repositories WHERE name = 'TestRepo'")
            self.assertIsNone(deleted_repo)

    def test_generate_invite(self):
        """Verifica se a rota POST /api/invites/generate/<int:repository_id> gera um novo convite."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')  # Token de um administrador
            # Crie um repositório de teste
            self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
            repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
            response = self.client.post(f'/api/invites/generate/{repository_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 201)
            self.assertIsNotNone(response.get_json().get('invite_code'))
            # Verifica se o convite foi criado no banco de dados
            new_invite = self.db_connection.fetchone_dict(f"SELECT * FROM user_repository_invites WHERE repository_id = {repository_id}")
            self.assertIsNotNone(new_invite)

    def test_generate_invite_invalid_repository(self):
        """Verifica se a rota POST /api/invites/generate/<int:repository_id> retorna um erro 404 para um repositório inválido."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')  # Token de um administrador
            response = self.client.post('/api/invites/generate/999', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 404)

    def test_list_invites(self):
        """Verifica se a rota GET /api/invites/list/<int:repository_id> lista convites de um repositório."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')  # Token de um administrador
            # Crie um repositório e alguns convites
            self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
            repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
            self.db_connection.execute_query("INSERT INTO user_repository_invites (repository_id, invite_code) VALUES (?, 'invite1')", (repository_id,))
            self.db_connection.execute_query("INSERT INTO user_repository_invites (repository_id, invite_code) VALUES (?, 'invite2')", (repository_id,))
            response = self.client.get(f'/api/invites/list/{repository_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIsNotNone(data.get('items'))
            self.assertGreaterEqual(len(data['items']), 2)

    def test_revoke_invite(self):
        """Verifica se a rota DELETE /api/invites/<invite_code> revoga um convite."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')  # Token de um administrador
            # Crie um convite de teste
            self.db_connection.execute_query("INSERT INTO user_repository_invites (repository_id, invite_code) VALUES (1, 'testinvite')")
            invite_code = 'testinvite'
            response = self.client.delete(f'/api/invites/{invite_code}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            # Verifica se o convite foi removido do banco de dados
            revoked_invite = self.db_connection.fetchone_dict(f"SELECT * FROM user_repository_invites WHERE invite_code = '{invite_code}'")
            self.assertIsNone(revoked_invite)

    def test_revoke_invite_invalid_invite(self):
        """Verifica se a rota DELETE /api/invites/<invite_code> retorna um erro 404 para um convite inválido."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')  # Token de um administrador
            response = self.client.delete('/api/invites/invalidinvite', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 404)