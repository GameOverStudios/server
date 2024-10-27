import jwt
from datetime import datetime, timedelta
import bcrypt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import logging
import pytz
import re
from flask import jsonify, request
from packages import models
import secrets

# Use um fuso horário UTC para datetime
UTC = pytz.utc

def is_admin(user_id, db_connection):
    """Verifica se o usuário é administrador."""
    with db_connection.session_scope() as session: # usar session_scope garante que a sessão seja fechada corretamente
        admin_role_id = session.execute("SELECT id FROM roles WHERE name = 'admin'").scalar_one_or_none()

        if not admin_role_id: # A função retorna False se não existir role de 'admin'
            return False

        user_role = session.execute(
            """
            SELECT role_id FROM user_roles WHERE user_id = :user_id
            """, {"user_id": user_id}
        ).scalar_one_or_none() # apenas um resultado

        return user_role == admin_role_id

def authenticate(username, password, db_connection):
    """Autentica o usuário."""
    with db_connection.session_scope() as session:
        user = session.query(models.User).filter_by(username=username).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return user.id # Retorna o ID do usuário

    return None  # Retorna None se a autenticação falhar


def generate_token(user_id, secret_key, algorithm):
    """Gera um JWT."""
    payload = {'user_id': user_id, 'exp': datetime.now(tz=UTC) + timedelta(days=1)}
    token = jwt.encode(payload, secret_key, algorithm=algorithm)

    return token


def decode_token(token, secret_key, algorithm):
    """Decodifica um JWT."""

    payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    return payload['user_id']


def load_public_key(public_key_string):

    try:
        public_key = serialization.load_pem_public_key(
            public_key_string.encode(),
            backend=default_backend()
        )

        return public_key

    except (ValueError, TypeError) as e:
        logging.error(f"Erro ao carregar a chave pública: {e}")

        return None


def verify_signature(public_key, signature, data):

    try:
        signature_bytes = bytes.fromhex(signature)  # Converter a assinatura de hexadecimal para bytes
        public_key.verify(
            signature_bytes,
            data.encode(), # Converter o dado para bytes antes de verificar a assinatura.
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()

        )
        return True

    except Exception as e:
        logging.error(f"Erro na verificação da assinatura: {e}")
        return False


def generate_invite_code():
    return secrets.token_urlsafe(16)


def validate_username(username):
    """Valida o formato do nome de usuário."""

    pattern = r"^[a-zA-Z0-9._]+$" # Apenas letras, números, pontos e underscores

    if re.match(pattern, username):
        return True # Nome de usuário válido

    return False


def paginate(query, args=(), per_page=20, request=None, url_for=None):
    """Função auxiliar para paginação."""
    page = int(request.args.get('page', 1))
    offset = (page - 1) * per_page


    total_items = query.count() # Usando SQLAlchemy para contagem
    items = query.limit(per_page).offset(offset).all()
    items = [item.to_dict() for item in items] # Converte cada item para dicionário

    # Gera links para a próxima e página anterior (se existirem)
    next_page_url = None

    prev_page_url = None

    if page * per_page < total_items:

        next_page_url = url_for(request.endpoint, page=page + 1, **request.args)

    if page > 1:
         prev_page_url = url_for(request.endpoint, page=page - 1, **request.args)


    return jsonify({
       'items': items,
       'total': total_items,
       'page': page,
        'per_page': per_page,
        'next_page': next_page_url,
        'prev_page': prev_page_url
    })

def filter_packages(query, repository_id=None, network_type=None, approved_status=None): # Função específica para filtrar pacotes
    if repository_id:
        query = query.filter(models.Package.repositories.any(id=repository_id))

    if network_type:
        query = query.join(models.PackageRepository).join(models.Repository).filter(models.Repository.network_type == network_type)


    if approved_status is not None:
         if approved_status: # Se buscando pacotes aprovados
            query = query.filter(models.Package.approved == True)

         else: # Se buscando pacotes NÃO aprovados
             query = query.filter(models.Package.approved == False)
    return query

def validate_package_data(data, required_fields):
    if not data:
        return "Dados ausentes", 400


    if not all(field in data for field in required_fields):  # Verifica todos os campos ao mesmo tempo
        missing_fields = set(required_fields) - set(data.keys())  # Calcula os campos ausentes
        return f"Campos obrigatórios ausentes: {', '.join(missing_fields)}", 400


    return None, None  # Retorna None se tudo estiver OK