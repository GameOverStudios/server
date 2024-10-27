# tests/test_invites.py
import unittest
import sys
sys.path.append('../packages')

from packages import db, models, utils, cloud_storage
from packages.routes_invites import bp as invites_bp
from flask import Flask, jsonify, request, send_from_directory, abort, make_response, url_for, redirect
import json
from unittest.mock import patch

class TestInvites(unittest.TestCase):

    def setUp(self):
        """Configura a conexão com o banco de dados para os testes."""
        self.db_connection = db.DatabaseConnection('sqlite:///test_db.sqlite')
        self.db_connection.create_tables()

    def tearDown(self):
        """Limpa o banco de dados após cada teste."""
        self.db_connection.close_connection()

    def test_accept_invite(self):
        """Verifica se a rota POST /api/invites/<invite_code>/accept aceita um convite."""
        with patch('packages.routes_invites.utils.generate_token') as mock_generate_token:
            mock_generate_token.return_value = 'test_token'
            with patch('packages.routes_invites.utils.is_admin') as mock_is_admin:
                mock_is_admin.return_value = False  # Simulando usuário não administrador
                with self.app.app_context():
                    # Crie um repositório e um convite
                    self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
                    repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
                    self.db_connection.execute_query("INSERT INTO user_repository_invites (repository_id, invite_code) VALUES (?, 'testinvite')", (repository_id,))
                    invite_code = 'testinvite'
                    response = self.client.post(f'/api/invites/{invite_code}/accept', headers={'Authorization': f'Bearer test_token'})
                    self.assertEqual(response.status_code, 200)
                    # Verifica se o convite foi aceito
                    accepted_invite = self.db_connection.fetchone_dict(f"SELECT * FROM user_repository_invites WHERE invite_code = '{invite_code}'")
                    self.assertTrue(accepted_invite['accepted'])
                    # Verifica se o usuário foi adicionado ao repositório como desenvolvedor
                    developer_in_repo = self.db_connection.fetchone_dict(f"SELECT COUNT(*) AS count FROM repository_developers WHERE repository_id = {repository_id} AND developer_id = (SELECT id FROM developers WHERE user_id = 2)")['count']
                    self.assertEqual(developer_in_repo, 1)

    def test_accept_invite_invalid_invite(self):
        """Verifica se a rota POST /api/invites/<invite_code>/accept retorna um erro 404 para um convite inválido."""
        with patch('packages.routes_invites.utils.generate_token') as mock_generate_token:
            mock_generate_token.return_value = 'test_token'
            with self.app.app_context():
                response = self.client.post('/api/invites/invalidinvite/accept', headers={'Authorization': f'Bearer test_token'})
                self.assertEqual(response.status_code, 404)

    def test_generate_invite(self):
        """Verifica se a rota POST /api/invites/generate/<int:repository_id> gera um novo convite."""
        with patch('packages.routes_invites.utils.generate_token') as mock_generate_token:
            mock_generate_token.return_value = 'test_token'
            with patch('packages.routes_invites.utils.is_admin') as mock_is_admin:
                mock_is_admin.return_value = True  # Simulando usuário administrador
                with self.app.app_context():
                    # Crie um repositório de teste
                    self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
                    repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
                    response = self.client.post(f'/api/invites/generate/{repository_id}', headers={'Authorization': f'Bearer test_token'})
                    self.assertEqual(response.status_code, 201)
                    self.assertIsNotNone(response.get_json().get('invite_code'))
                    # Verifica se o convite foi criado no banco de dados
                    new_invite = self.db_connection.fetchone_dict(f"SELECT * FROM user_repository_invites WHERE repository_id = {repository_id}")
                    self.assertIsNotNone(new_invite)

    def test_generate_invite_invalid_repository(self):
        """Verifica se a rota POST /api/invites/generate/<int:repository_id> retorna um erro 404 para um repositório inválido."""
        with patch('packages.routes_invites.utils.generate_token') as mock_generate_token:
            mock_generate_token.return_value = 'test_token'
            with self.app.app_context():
                response = self.client.post('/api/invites/generate/999', headers={'Authorization': f'Bearer test_token'})
                self.assertEqual(response.status_code, 404)

    def test_list_invites(self):
        """Verifica se a rota GET /api/invites/list/<int:repository_id> lista convites de um repositório."""
        with patch('packages.routes_invites.utils.generate_token') as mock_generate_token:
            mock_generate_token.return_value = 'test_token'
            with patch('packages.routes_invites.utils.is_admin') as mock_is_admin:
                mock_is_admin.return_value = True  # Simulando usuário administrador
                with self.app.app_context():
                    # Crie um repositório e alguns convites
                    self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
                    repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
                    self.db_connection.execute_query("INSERT INTO user_repository_invites (repository_id, invite_code) VALUES (?, 'invite1')", (repository_id,))
                    self.db_connection.execute_query("INSERT INTO user_repository_invites (repository_id, invite_code) VALUES (?, 'invite2')", (repository_id,))
                    response = self.client.get(f'/api/invites/list/{repository_id}', headers={'Authorization': f'Bearer test_token'})
                    self.assertEqual(response.status_code, 200)
                    data = response.get_json()
                    self.assertIsNotNone(data.get('items'))
                    self.assertGreaterEqual(len(data['items']), 2)

    def test_revoke_invite(self):
        """Verifica se a rota DELETE /api/invites/<invite_code> revoga um convite."""
        with patch('packages.routes_invites.utils.generate_token') as mock_generate_token:
            mock_generate_token.return_value = 'test_token'
            with patch('packages.routes_invites.utils.is_admin') as mock_is_admin:
                mock_is_admin.return_value = True  # Simulando usuário administrador
                with self.app.app_context():
                    # Crie um convite de teste
                    self.db_connection.execute_query("INSERT INTO user_repository_invites (repository_id, invite_code) VALUES (1, 'testinvite')")
                    invite_code = 'testinvite'
                    response = self.client.delete(f'/api/invites/{invite_code}', headers={'Authorization': f'Bearer test_token'})
                    self.assertEqual(response.status_code, 200)
                    # Verifica se o convite foi removido do banco de dados
                    revoked_invite = self.db_connection.fetchone_dict(f"SELECT * FROM user_repository_invites WHERE invite_code = '{invite_code}'")
                    self.assertIsNone(revoked_invite)

    def test_revoke_invite_invalid_invite(self):
        """Verifica se a rota DELETE /api/invites/<invite_code> retorna um erro 404 para um convite inválido."""
        with patch('packages.routes_invites.utils.generate_token') as mock_generate_token:
            mock_generate_token.return_value = 'test_token'
            with self.app.app_context():
                response = self.client.delete('/api/invites/invalidinvite', headers={'Authorization': f'Bearer test_token'})
                self.assertEqual(response.status_code, 404)