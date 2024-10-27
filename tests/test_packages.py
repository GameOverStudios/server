# tests/test_routes_packages.py
import unittest
import sys
sys.path.append('../packages')

from packages import db, models, utils, cloud_storage
from packages.routes_packages import bp as packages_bp
from flask import Flask, jsonify, request, send_from_directory, abort, make_response, url_for, redirect
import json
from unittest.mock import patch

class TestPackages(unittest.TestCase):

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
        self.app.register_blueprint(packages_bp)
        self.app.config['DB_CONNECTION'] = self.db_connection

        self.client = self.app.test_client()

    def tearDown(self):
        """Limpa o banco de dados após cada teste."""
        self.db_connection.close_connection()

    def test_create_package(self):
        """Verifica se a rota POST /api/packages cria um novo pacote."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            # Simule um arquivo e metadados
            file = (b'TestPackageContent', 'TestPackage.pak')
            metadata = {
                'name': 'TestPackage',
                'version': '1.0.0',
                'public_key': 'public_key',
                'signature': 'signature'
            }
            metadata_json = json.dumps(metadata, sort_keys=True).encode()
            signature = hashlib.sha256(metadata_json).hexdigest()  # Crie uma assinatura fictícia
            metadata['signature'] = signature
            response = self.client.post('/api/packages', data=json.dumps(metadata), content_type='application/json', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 201)
            self.assertIsNotNone(response.get_json().get('package_id'))
            # Verifica se o pacote foi criado no banco de dados
            new_package = self.db_connection.fetchone_dict("SELECT * FROM packages WHERE name = 'TestPackage'")
            self.assertIsNotNone(new_package)

    def test_create_package_duplicate(self):
        """Verifica se a rota POST /api/packages retorna um erro 400 para um pacote com nome e versão já existentes."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            # Crie um pacote de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            response = self.client.post('/api/packages', data=json.dumps({'name': 'TestPackage', 'version': '1.0.0', 'public_key': 'public_key', 'signature': 'signature'}), content_type='application/json', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 400)

    def test_get_package(self):
        """Verifica se a rota GET /api/packages/<int:package_id> retorna um pacote específico."""
        with self.app.app_context():
            # Crie um pacote de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            response = self.client.get(f'/api/packages/{package_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['name'], 'TestPackage')

    def test_update_package(self):
        """Verifica se a rota PUT /api/packages/<int:package_id> atualiza um pacote."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            # Crie um pacote de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            response = self.client.put(f'/api/packages/{package_id}', data=json.dumps({'name': 'UpdatedPackage'}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            # Verifica se o pacote foi atualizado no banco de dados
            updated_package = self.db_connection.fetchone_dict("SELECT * FROM packages WHERE name = 'UpdatedPackage'")
            self.assertIsNotNone(updated_package)

    def test_delete_package(self):
        """Verifica se a rota DELETE /api/packages/<int:package_id> exclui um pacote."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            # Crie um pacote de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            response = self.client.delete(f'/api/packages/{package_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            # Verifica se o pacote foi excluído do banco de dados
            deleted_package = self.db_connection.fetchone_dict("SELECT * FROM packages WHERE name = 'TestPackage'")
            self.assertIsNone(deleted_package)

    def test_add_dependency(self):
        """Verifica se a rota POST /api/packages/<int:package_id>/dependencies adiciona uma dependência a um pacote."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            # Crie dois pacotes
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage1', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage2', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage1'")['id']
            dependency_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage2'")['id']
            response = self.client.post(f'/api/packages/{package_id}/dependencies', data=json.dumps({'dependency_id': dependency_id, 'dependency_type': 'runtime'}), headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 201)
            # Verifica se a dependência foi adicionada
            dependency_in_package = self.db_connection.fetchone_dict(f"SELECT COUNT(*) AS count FROM package_dependencies WHERE package_id = {package_id} AND dependency_id = {dependency_id}")['count']
            self.assertEqual(dependency_in_package, 1)

    def test_list_dependencies(self):
        """Verifica se a rota GET /api/packages/<int:package_id>/dependencies lista as dependências de um pacote."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            # Crie um pacote e uma dependência
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestDependency', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            dependency_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestDependency'")['id']
            # Adicione a dependência ao pacote
            self.db_connection.execute_query("INSERT INTO package_dependencies (package_id, dependency_id, dependency_type) VALUES (?, ?, 'runtime')", (package_id, dependency_id))
            response = self.client.get(f'/api/packages/{package_id}/dependencies', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(len(data), 1)  # Verifica se há uma dependência na lista

    def test_search_packages(self):
        """Verifica se a rota GET /api/packages/search busca pacotes com filtros."""
        with self.app.app_context():
            token = utils.generate_token(1, self.app.config['SECRET_KEY'], 'HS256')
            # Crie alguns pacotes
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage1', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage2', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            response = self.client.get('/api/packages/search?name=TestPackage', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(len(data['items']), 1)

    def test_replicate_package(self):
        """Verifica se a função replicate_package replica um pacote para os espelhos."""
        with self.app.app_context():
            # Crie um pacote e um repositório com espelho
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
            self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('MirrorRepo', 'clearnet')")
            self.db_connection.execute_query("INSERT INTO repository_mirrors (main_repository_id, mirror_repository_id) VALUES (1, 2)")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            origin_repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
            # Chama a função replicate_package
            response = self.client.post(f'/api/packages/{package_id}/replicate?origin_repository_id={origin_repository_id}', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(response.status_code, 200)
            # Verifica se o pacote foi replicado para o espelho
            mirrored_package = self.db_connection.fetchone_dict(f"SELECT COUNT(*) AS count FROM package_repositories WHERE package_id = {package_id} AND repository_id = 2")['count']
            self.assertEqual(mirrored_package, 1)