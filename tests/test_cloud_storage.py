# tests/test_cloud_storage.py
import unittest
import sys
sys.path.append('../packages')

from packages import cloud_storage
from unittest.mock import patch
from google.cloud import storage
import os
import hashlib

# Configuração do Cloud Storage (opcional)
BUCKET_NAME = os.environ.get('CLOUD_STORAGE_BUCKET')  # Nome do bucket do Google Cloud Storage (opcional)
UPLOAD_FOLDER = 'uploads'  # Diretório local temporário para upload (opcional)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class TestCloudStorage(unittest.TestCase):

    @patch('google.cloud.storage.Client')
    def test_upload_file(self, mock_client):
        """Verifica se a função upload_file envia um arquivo para o Cloud Storage."""
        mock_bucket = mock_client.return_value.bucket.return_value
        mock_blob = mock_bucket.blob.return_value
        file = open('tests/test_file.txt', 'rb')
        filename = 'test_file.txt'
        upload_url = cloud_storage.upload_file(file, filename, BUCKET_NAME)
        mock_blob.upload_from_string.assert_called_once_with(file.read(), content_type=file.content_type)
        file.close()
        self.assertEqual(upload_url, f"gs://{BUCKET_NAME}/{filename}")

    @patch('google.cloud.storage.Client')
    def test_download_file(self, mock_client):
        """Verifica se a função download_file baixa um arquivo do Cloud Storage."""
        mock_bucket = mock_client.return_value.bucket.return_value
        mock_blob = mock_bucket.blob.return_value
        mock_blob.download_as_string.return_value = b'TestFileContent'
        filename = 'TestFile.txt'
        file_content = cloud_storage.download_file(filename, BUCKET_NAME)
        mock_blob.download_as_string.assert_called_once()
        self.assertEqual(file_content, b'TestFileContent')

    @patch('google.cloud.storage.Client')
    def test_delete_file(self, mock_client):
        """Verifica se a função delete_file exclui um arquivo do Cloud Storage."""
        mock_bucket = mock_client.return_value.bucket.return_value
        mock_blob = mock_bucket.blob.return_value
        filename = 'TestFile.txt'
        cloud_storage.delete_file(filename, BUCKET_NAME)
        mock_blob.delete.assert_called_once()

    @patch('google.cloud.storage.Client')
    def test_generate_download_url(self, mock_client):
        """Verifica se a função generate_download_url gera uma URL pública para download de um arquivo."""
        mock_bucket = mock_client.return_value.bucket.return_value
        mock_blob = mock_bucket.blob.return_value
        mock_blob.generate_signed_url.return_value = 'https://storage.googleapis.com/test-bucket/TestFile.txt'
        filename = 'TestFile.txt'
        download_url = cloud_storage.generate_download_url(filename, BUCKET_NAME)
        mock_blob.generate_signed_url.assert_called_once_with(expiration=3600, method='GET')
        self.assertEqual(download_url, 'https://storage.googleapis.com/test-bucket/TestFile.txt')

    def test_upload_file_local(self):
        """Verifica se a função upload_file_local salva um arquivo no servidor local."""
        file = open('tests/test_file.txt', 'rb')
        filename = 'test_file.txt'
        filepath = cloud_storage.upload_file_local(file, filename)
        file.close()
        self.assertTrue(os.path.exists(filepath))

    def test_download_file_local(self):
        """Verifica se a função download_file_local baixa um arquivo do servidor local."""
        filename = 'test_file.txt'
        file_content = cloud_storage.download_file_local(filename)
        self.assertIsNotNone(file_content)

    def test_delete_file_local(self):
        """Verifica se a função delete_file_local exclui um arquivo do servidor local."""
        filename = 'test_file.txt'
        cloud_storage.delete_file_local(filename)
        self.assertFalse(os.path.exists(os.path.join(UPLOAD_FOLDER, filename)))

    def test_generate_download_url_local(self):
        """Verifica se a função generate_download_url_local gera uma URL para download de um arquivo local."""
        filename = 'test_file.txt'
        download_url = cloud_storage.generate_download_url_local(filename)
        self.assertEqual(download_url, f"/uploads/{filename}")

    def test_generate_filename(self):
        """Verifica se a função generate_filename gera um nome de arquivo único."""
        file = open('tests/test_file.txt', 'rb')
        filename = cloud_storage.generate_filename(file)
        self.assertIsNotNone(filename)
        self.assertTrue(filename.startswith(hashlib.sha256(file.read()).hexdigest()))
        file.close()

    def test_generate_filename_with_prefix(self):
        """Verifica se a função generate_filename gera um nome de arquivo com prefixo."""
        file = open('tests/test_file.txt', 'rb')
        filename = cloud_storage.generate_filename(file, prefix='test')
        self.assertTrue(filename.startswith('test_'))
        file.close()