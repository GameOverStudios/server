import os
import hashlib

UPLOAD_FOLDER = 'uploads' # Diretório local temporário para upload (opcional)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def upload_file_local(file, filename):
    """Faz o upload de um arquivo para o servidor local."""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filepath

def download_file_local(filename):
    """Baixa um arquivo do servidor local."""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, 'rb') as f:
        return f.read()

def delete_file_local(filename):
    """Exclui um arquivo do servidor local."""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

def generate_download_url_local(filename):
    """Gera uma URL para download de um arquivo no servidor local."""
    return f"/uploads/{filename}"

def generate_filename(file, prefix=None):
    """Gera um nome de arquivo único com base no hash SHA256 do arquivo."""
    file.seek(0)
    file_hash = hashlib.sha256(file.read()).hexdigest()
    file.seek(0)
    filename = file_hash + os.path.splitext(file.filename)[1]
    if prefix:
        filename = prefix + "_" + filename
    return filename