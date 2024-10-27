from functools import wraps
from flask import request
import logging
from flask import jsonify, request, make_response
from functools import wraps
from packages import db, utils

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        
        JWT_ALGORITHM = 'HS256'

        token = request.headers.get('Authorization')
        if not token:
            return make_response(jsonify({'message': 'Authentication required (Token)'}), 401)

        try:
            user_id = utils.decode_token(token, app.config['SECRET_KEY'], JWT_ALGORITHM)
            request.user_id = user_id  # Armazena user_id para outras funções
        except Exception as e:
            logging.error(f"Erro de autenticação: {e}")
            return jsonify({'message': 'Invalid or expired token'}), 401

        return f(*args, **kwargs)
    return decorated

def requires_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not utils.is_admin(request.user_id, db.get_db()):
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function