from flask import Blueprint, jsonify, request, abort, current_app, url_for
from packages import db, models, utils
from sqlalchemy.exc import IntegrityError
import bcrypt
import logging 
from packages.auth import requires_auth, requires_admin

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('', methods=['POST'])
@requires_auth
def create_user():
    db_connection = current_app.config['DB_CONNECTION']  # Acessando configurações da aplicação
    data = request.get_json()

    required_fields = ['username', 'password', 'birthdate'] # birthdate agora é obrigatório
    error, status_code = utils.validate_package_data(data, required_fields)
    if error:
        abort(status_code, description=error)

    # validações adicionais
    if not utils.validate_username(data['username']): # valida o formato do username
        abort(400, description="Formato de nome de usuário inválido. Use apenas letras, números, pontos e underscores.")
    if len(data['password']) < 8: # valida o tamanho da senha
         abort(400, description="A senha deve ter pelo menos 8 caracteres.")


    # Criptografa a senha
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())


    with db_connection.session_scope() as session:
        try:  # Verifica se o nome de usuário já existe
            existing_user = session.query(models.User).filter_by(username=data['username']).first()
            if existing_user:
                abort(409, description="Nome de usuário já existe.")

            new_user = models.User(
                username=data['username'],
                password_hash=hashed_password.decode('utf-8'),  # salva senha hasheada
                birthdate=data['birthdate']

            )
            session.add(new_user)
            session.commit()

            return jsonify({'message': 'Usuário criado com sucesso', 'id': new_user.id}), 201

        except IntegrityError:
            abort(409, description="Nome de usuário já existe.") # erro 409 Conflito
        except Exception as e:
             logging.exception("Erro ao criar usuário: %s", e)

             abort(500, description=f"Erro ao criar usuário: {str(e)}")

@users_bp.route('/<int:user_id>', methods=['PUT']) # Atualiza informações do usuário
@requires_auth
def update_user(user_id):
    db_connection = current_app.config['DB_CONNECTION']
    data = request.get_json()


    if request.user_id != user_id and not utils.is_admin(request.user_id, db_connection): # verifica se é o mesmo usuário ou admin
        abort(403, description="Você só pode editar seu próprio perfil (ou precisa ser admin).")


    allowed_fields = ["username", "password", "birthdate"]
    with db_connection.session_scope() as session:  # garante que a sessão seja fechada
        user = session.query(models.User).filter_by(id=user_id).first()


        if not user:  # verifica se o usuário existe

            abort(404, description="Usuário não encontrado")


        if 'username' in data and not utils.validate_username(data['username']): # valida formato de username
            abort(400, description="Formato de nome de usuário inválido. Use apenas letras, números, pontos e underscores.")
        if 'password' in data and len(data['password']) < 8:  # valida tamanho da senha
            abort(400, description="A senha deve ter pelo menos 8 caracteres.")

        try: # verifica se o novo username já existe

             if 'username' in data and session.query(models.User).filter_by(username=data['username']).filter(models.User.id != user_id).first():
                abort(409, description="Nome de usuário já existe.")


        except IntegrityError:
            abort(409, description="Nome de usuário já existe.")


        for field in allowed_fields:  # Itera apenas pelos campos permitidos
            if field in data:
                if field == 'password':  # Hasheia a senha se ela for atualizada
                     hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
                     setattr(user, 'password_hash', hashed_password.decode('utf-8'))
                else:
                    setattr(user, field, data[field])



        try:
             session.commit()
             return jsonify({'message': 'Usuário atualizado com sucesso'}), 200

        except Exception as e:  # Trata erros de banco de dados e outros erros
             logging.exception("Erro ao atualizar o usuário: %s", e)

             abort(500, description=f"Erro ao atualizar o usuário: {e}")

@users_bp.route('/<int:user_id>', methods=['GET'])  # Obtém informações de um usuário
@requires_auth
def get_user(user_id):
    db_connection = current_app.config['DB_CONNECTION']


    if request.user_id != user_id and not utils.is_admin(request.user_id, db_connection):  # Verifica permissões
        abort(403, description="Você não tem permissão para ver este perfil.")


    with db_connection.session_scope() as session:

        user = session.query(models.User).filter_by(id=user_id).first()


        if not user:

             abort(404, description="Usuário não encontrado")  # Retorna 404 se o usuário não existir

        user_dict = user.to_dict()

        if not utils.is_admin(request.user_id, db_connection):  # Remove informações sensíveis para não-admins
            user_dict.pop('password_hash', None)  # Remove 'password_hash', se presente

        return jsonify(user_dict)

@users_bp.route('', methods=['GET']) # Lista todos os usuários (apenas para administradores)
@requires_auth
@requires_admin
def list_users():
    db_connection = current_app.config['DB_CONNECTION']


    with db_connection.session_scope() as session:

        query = session.query(models.User)

        return utils.paginate(query, request=request, url_for=url_for)

@users_bp.route('/<int:user_id>', methods=['DELETE']) # Exclui um usuário (apenas para administradores)
@requires_auth
@requires_admin
def delete_user(user_id):

    db_connection = current_app.config['DB_CONNECTION']


    with db_connection.session_scope() as session:

        user = session.query(models.User).filter_by(id=user_id).first()


        if not user:  # Verifica se o usuário existe

            abort(404, description="Usuário não encontrado")



        try:
            session.delete(user)

            session.commit()
            return jsonify({'message': 'Usuário excluído com sucesso'}), 200


        except Exception as e:  # Trata erros de banco de dados

             logging.exception("Erro ao excluir o usuário: %s", e)

             abort(500, description=f"Erro ao excluir o usuário: {e}")

@users_bp.route('/login', methods=['POST'])  # Login do usuário (gera token JWT)
def login():
    db_connection = current_app.config['DB_CONNECTION']
    data = request.get_json()


    if not data or not data.get('username') or not data.get('password'):  # Valida dados de entrada

        abort(400, description="Nome de usuário e senha são obrigatórios.")


    user_id = utils.authenticate(data['username'], data['password'], db_connection)


    if user_id:
        token = utils.generate_token(user_id, current_app.config['SECRET_KEY'], JWT_ALGORITHM) # gera token JWT
        return jsonify({'token': token}), 200
    else:
        abort(401, description="Credenciais inválidas.") # erro 401 Unauthorized

        