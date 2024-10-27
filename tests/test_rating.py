# tests/test_rating.py
import unittest
import sys
sys.path.append('../packages')

from packages import db, models, utils, cloud_storage
from packages.routes_ratings import bp as ratings_bp
from flask import Flask, jsonify, request, send_from_directory, abort, make_response, url_for, redirect
import json
from unittest.mock import patch

class TestRatings(unittest.TestCase):

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
        self.app.register_blueprint(ratings_bp)
        self.app.config['DB_CONNECTION'] = self.db_connection

        self.client = self.app.test_client()

    def tearDown(self):
        """Limpa o banco de dados após cada teste."""
        self.db_connection.close_connection()

    def test_create_rating(self):
        """Verifica se a rota POST /api/ratings/<int:package_id> cria uma nova avaliação para um pacote."""
        with self.app.app_context():
            # Crie um pacote de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            response = self.client.post(f'/api/ratings/{package_id}', data=json.dumps({'rating': 4, 'comment': 'Great package!'}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 201)
            self.assertIsNotNone(response.get_json().get('id'))
            # Verifica se a avaliação foi criada no banco de dados
            new_rating = self.db_connection.fetchone_dict(f"SELECT * FROM ratings WHERE package_id = {package_id} AND rating = 4")
            self.assertIsNotNone(new_rating)

    def test_create_rating_invalid_rating(self):
        """Verifica se a rota POST /api/ratings/<int:package_id> retorna um erro 400 para uma avaliação inválida."""
        with self.app.app_context():
            # Crie um pacote de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            response = self.client.post(f'/api/ratings/{package_id}', data=json.dumps({'rating': 7}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 400)

    def test_create_rating_duplicate(self):
        """Verifica se a rota POST /api/ratings/<int:package_id> retorna um erro 409 para uma avaliação duplicada."""
        with self.app.app_context():
            # Crie um pacote e uma avaliação de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 4)", (package_id, 1))
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            response = self.client.post(f'/api/ratings/{package_id}', data=json.dumps({'rating': 4}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 409)

    def test_list_ratings(self):
        """Verifica se a rota GET /api/ratings/<int:package_id> lista avaliações de um pacote."""
        with self.app.app_context():
            # Crie um pacote e algumas avaliações de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 4)", (package_id, 1))
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 3)", (package_id, 1))
            response = self.client.get(f'/api/ratings/{package_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIsNotNone(data.get('items'))
            self.assertGreaterEqual(len(data['items']), 2)

    def test_update_rating(self):
        """Verifica se a rota PUT /api/ratings/<int:rating_id> atualiza uma avaliação."""
        with self.app.app_context():
            # Crie uma avaliação de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 4)", (package_id, 1))
            rating_id = self.db_connection.fetchone_dict("SELECT id FROM ratings WHERE package_id = ?", (package_id,))['id']
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            response = self.client.put(f'/api/ratings/{rating_id}', data=json.dumps({'rating': 5}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            # Verifica se a avaliação foi atualizada no banco de dados
            updated_rating = self.db_connection.fetchone_dict(f"SELECT * FROM ratings WHERE id = {rating_id}")
            self.assertEqual(updated_rating['rating'], 5)

    def test_update_rating_invalid_rating(self):
        """Verifica se a rota PUT /api/ratings/<int:rating_id> retorna um erro 400 para uma avaliação inválida."""
        with self.app.app_context():
            # Crie uma avaliação de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 4)", (package_id, 1))
            rating_id = self.db_connection.fetchone_dict("SELECT id FROM ratings WHERE package_id = ?", (package_id,))['id']
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            response = self.client.put(f'/api/ratings/{rating_id}', data=json.dumps({'rating': 7}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 400)

    def test_update_rating_unauthorized(self):
        """Verifica se a rota PUT /api/ratings/<int:rating_id> retorna um erro 403 para um usuário não autorizado."""
        with self.app.app_context():
            # Crie uma avaliação de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 4)", (package_id, 1))
            rating_id = self.db_connection.fetchone_dict("SELECT id FROM ratings WHERE package_id = ?", (package_id,))['id']
            token = utils.generate_token(2, self.app.config['SECRET_KEY'], 'HS256')  # Token de um usuário diferente
            response = self.client.put(f'/api/ratings/{rating_id}', data=json.dumps({'rating': 5}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 403)

    def test_delete_rating(self):
        """Verifica se a rota DELETE /api/ratings/<int:rating_id> exclui uma avaliação."""
        with self.app.app_context():
            # Crie uma avaliação de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 4)", (package_id, 1))
            rating_id = self.db_connection.fetchone_dict("SELECT id FROM ratings WHERE package_id = ?", (package_id,))['id']
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            response = self.client.delete(f'/api/ratings/{rating_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            # Verifica se a avaliação foi excluída do banco de dados
            deleted_rating = self.db_connection.fetchone_dict(f"SELECT * FROM ratings WHERE id = {rating_id}")
            self.assertIsNone(deleted_rating)

    def test_delete_rating_unauthorized(self):
        """Verifica se a rota DELETE /api/ratings/<int:rating_id> retorna um erro 403 para um usuário não autorizado."""
        with self.app.app_context():
            # Crie uma avaliação de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 4)", (package_id, 1))
            rating_id = self.db_connection.fetchone_dict("SELECT id FROM ratings WHERE package_id = ?", (package_id,))['id']
            token = utils.generate_token(2, self.app.config['SECRET_KEY'], 'HS256')  # Token de um usuário diferente
            response = self.client.delete(f'/api/ratings/{rating_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 403)

    def test_create_comment(self):
        """Verifica se a rota POST /api/ratings/<int:rating_id>/comments adiciona um comentário a uma avaliação."""
        with self.app.app_context():
            # Crie uma avaliação de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 4)", (package_id, 1))
            rating_id = self.db_connection.fetchone_dict("SELECT id FROM ratings WHERE package_id = ?", (package_id,))['id']
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            response = self.client.post(f'/api/ratings/{rating_id}/comments', data=json.dumps({'comment': 'This is a great comment!'}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 201)
            self.assertIsNotNone(response.get_json().get('id'))
            # Verifica se o comentário foi criado no banco de dados
            new_comment = self.db_connection.fetchone_dict(f"SELECT * FROM comments WHERE rating_id = {rating_id} AND comment = 'This is a great comment!'")
            self.assertIsNotNone(new_comment)

    def test_create_comment_unauthorized(self):
        """Verifica se a rota POST /api/ratings/<int:rating_id>/comments retorna um erro 403 para um usuário não autorizado."""
        with self.app.app_context():
            # Crie uma avaliação de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 4)", (package_id, 1))
            rating_id = self.db_connection.fetchone_dict("SELECT id FROM ratings WHERE package_id = ?", (package_id,))['id']
            token = utils.generate_token(2, self.app.config['SECRET_KEY'], 'HS256')  # Token de um usuário diferente
            response = self.client.post(f'/api/ratings/{rating_id}/comments', data=json.dumps({'comment': 'This is a comment!'}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 403)

    def test_list_comments(self):
        """Verifica se a rota GET /api/ratings/<int:rating_id>/comments lista comentários de uma avaliação."""
        with self.app.app_context():
            # Crie uma avaliação e alguns comentários de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 4)", (package_id, 1))
            rating_id = self.db_connection.fetchone_dict("SELECT id FROM ratings WHERE package_id = ?", (package_id,))['id']
            self.db_connection.execute_query("INSERT INTO comments (rating_id, user_id, comment) VALUES (?, ?, 'Comment 1')", (rating_id, 1))
            self.db_connection.execute_query("INSERT INTO comments (rating_id, user_id, comment) VALUES (?, ?, 'Comment 2')", (rating_id, 1))
            response = self.client.get(f'/api/ratings/{rating_id}/comments', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIsNotNone(data.get('items'))
            self.assertGreaterEqual(len(data['items']), 2)