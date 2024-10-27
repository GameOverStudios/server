# tests/test_models.py
import unittest
import sys
sys.path.append('../packages')

from packages import db, models, utils
from datetime import datetime, timedelta
import bcrypt
from flask import Flask
from unittest.mock import patch

class TestModels(unittest.TestCase):

    def setUp(self):
        """Configura a conexão com o banco de dados para os testes."""
        self.app = Flask(__name__)
        self.app.config['DATABASE_URI'] = 'sqlite:///test_db.sqlite'
        self.db_connection = db.DatabaseConnection(self.app.config['DATABASE_URI'])
        self.db_connection.create_tables()

    def tearDown(self):
        """Limpa o banco de dados após cada teste."""
        self.db_connection.close_connection()

    def test_create_package(self):
        """Verifica se o modelo Package cria um novo pacote."""
        with self.app.app_context():
            package = models.Package(name='TestPackage', version='1.0.0', hash_package='hash_package', hash_metadata='hash_metadata', public_key='public_key', signature='signature')
            self.db_connection.session.add(package)
            self.db_connection.session.commit()
            self.assertIsNotNone(package.id)

    def test_create_repository(self):
        """Verifica se o modelo Repository cria um novo repositório."""
        with self.app.app_context():
            repository = models.Repository(name='TestRepo', network_type='clearnet')
            self.db_connection.session.add(repository)
            self.db_connection.session.commit()
            self.assertIsNotNone(repository.id)

    def test_create_rating(self):
        """Verifica se o modelo Rating cria uma nova avaliação."""
        with self.app.app_context():
            # Crie um pacote de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            rating = models.Rating(package_id=package_id, user_id=1, rating=4)
            self.db_connection.session.add(rating)
            self.db_connection.session.commit()
            self.assertIsNotNone(rating.id)

    def test_create_comment(self):
        """Verifica se o modelo Comment cria um novo comentário."""
        with self.app.app_context():
            # Crie uma avaliação de teste
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature')")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO ratings (package_id, user_id, rating) VALUES (?, ?, 4)", (package_id, 1))
            rating_id = self.db_connection.fetchone_dict("SELECT id FROM ratings WHERE package_id = ?", (package_id,))['id']
            comment = models.Comment(rating_id=rating_id, user_id=1, comment='This is a comment!')
            self.db_connection.session.add(comment)
            self.db_connection.session.commit()
            self.assertIsNotNone(comment.id)

    def test_create_developer(self):
        """Verifica se o modelo Developer cria um novo desenvolvedor."""
        with self.app.app_context():
            developer = models.Developer(user_id=1, repository_id=1, role='developer')
            self.db_connection.session.add(developer)
            self.db_connection.session.commit()
            self.assertIsNotNone(developer.id)

    def test_create_user_repository_invite(self):
        """Verifica se o modelo UserRepositoryInvite cria um novo convite."""
        with self.app.app_context():
            # Crie um repositório de teste
            self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
            repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
            invite = models.UserRepositoryInvite(repository_id=repository_id, invite_code='testinvite')
            self.db_connection.session.add(invite)
            self.db_connection.session.commit()
            self.assertIsNotNone(invite.id)

    def test_create_package_repository(self):
        """Verifica se o modelo PackageRepository cria uma nova associação de pacote a repositório."""
        with self.app.app_context():
            # Crie um pacote e um repositório
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature, approved) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature', 1)")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            self.db_connection.execute_query("INSERT INTO repositories (name, network_type) VALUES ('TestRepo', 'clearnet')")
            repository_id = self.db_connection.fetchone_dict("SELECT id FROM repositories WHERE name = 'TestRepo'")['id']
            package_repo = models.PackageRepository(package_id=package_id, repository_id=repository_id)
            self.db_connection.session.add(package_repo)
            self.db_connection.session.commit()
            self.assertIsNotNone(package_repo.id)

    def test_create_package_version(self):
        """Verifica se o modelo PackageVersion cria uma nova versão de um pacote."""
        with self.app.app_context():
            # Crie um pacote
            self.db_connection.execute_query("INSERT INTO packages (name, version, hash_package, hash_metadata, public_key, signature, approved) VALUES ('TestPackage', '1.0.0', 'hash_package', 'hash_metadata', 'public_key', 'signature', 1)")
            package_id = self.db_connection.fetchone_dict("SELECT id FROM packages WHERE name = 'TestPackage'")['id']
            package_version = models.PackageVersion(package_id=package_id, version='1.1.0', hash_package='hash_package', hash_metadata='hash_metadata', public_key='public_key', signature='signature', approved=True)
            self.db_connection.session.add(package_version)
            self.db_connection.session.commit()
            self.assertIsNotNone(package_version.id)