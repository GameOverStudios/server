from flask import Blueprint, jsonify, request, abort, current_app, url_for
from packages import db, models, utils
from sqlalchemy.exc import IntegrityError
import logging 
from packages.auth import requires_auth, requires_admin

invites_bp = Blueprint('invites', __name__, url_prefix='/api/invites')

@invites_bp.route('/<invite_code>/accept', methods=['POST'])  # Aceitar um convite
@requires_auth
def accept_invite(invite_code):
    db_connection = current_app.config['DB_CONNECTION']

    with db_connection.session_scope() as session:  # garante que a sessão seja fechada
        invite = session.query(models.UserRepositoryInvite).filter_by(invite_code=invite_code, accepted=False).first()

        if not invite:
            abort(404, description="Convite inválido ou já aceito.")

        invite.accepted = True
        invite.invited_user_id = request.user_id # Define o usuário que aceitou o convite

        # Adiciona o usuário como desenvolvedor do repositório, se necessário
        developer = session.query(models.Developer).filter_by(user_id=request.user_id).first()

        if not developer: # Crie um desenvolvedor se ele não existir
           developer = models.Developer(user_id=request.user_id)
           session.add(developer)
           session.flush()  # Para ter o ID

        repository = session.query(models.Repository).filter_by(id=invite.repository_id).first() # Verificar o repositório
        if developer not in repository.developers: # previne desenvolvedor duplicado
             repository.developers.append(developer)



        try:
            session.commit()

            return jsonify({'message': 'Convite aceito com sucesso.'}), 200

        except Exception as e:
            logging.exception("Erro ao aceitar convite: %s", e)
            abort(500, description=f"Erro ao aceitar convite: {e}")

@invites_bp.route('/generate/<int:repository_id>', methods=['POST'])  # Gerar um convite
@requires_auth
@requires_admin # Apenas administradores podem gerar convites
def generate_invite(repository_id):
    db_connection = current_app.config['DB_CONNECTION']

    with db_connection.session_scope() as session:  # garante o fechamento correto da sessão
         repository = session.query(models.Repository).filter_by(id=repository_id).first()
         if not repository:
              abort(404, description="Repositório não encontrado.")
         try:
            invite_code = utils.generate_invite_code()
            new_invite = models.UserRepositoryInvite(
                repository_id=repository_id,
                user_id=request.user_id, # Guarda quem gerou o convite
                invite_code=invite_code

            )

            session.add(new_invite)
            session.commit()

            return jsonify({'message': 'Convite gerado com sucesso.', 'invite_code': invite_code}), 201 # retorna o código

         except IntegrityError:
              abort(409, description="Erro ao gerar convite (código duplicado).")
         except Exception as e:
              logging.exception("Erro ao gerar convite: %s", e)
              abort(500, description=f"Erro ao gerar convite: {str(e)}")

@invites_bp.route('/list/<int:repository_id>', methods=['GET']) # Listar convites de um repositório
@requires_auth
@requires_admin # Apenas administradores podem listar convites
def list_invites(repository_id):

    db_connection = current_app.config['DB_CONNECTION']

    with db_connection.session_scope() as session:  # garante o fechamento correto da sessão
        repository = session.query(models.Repository).filter_by(id=repository_id).first()

        if not repository:
             abort(404, description="Repositório não encontrado.")


        query = session.query(models.UserRepositoryInvite).filter_by(repository_id=repository_id)


        return utils.paginate(query, request=request, url_for=url_for)

@invites_bp.route('/<invite_code>', methods=['DELETE'])  # Revogar um convite (apenas para administradores)
@requires_auth
@requires_admin
def revoke_invite(invite_code):
    db_connection = current_app.config['DB_CONNECTION']
    with db_connection.session_scope() as session:
        invite = session.query(models.UserRepositoryInvite).filter_by(invite_code=invite_code).first()

        if not invite:

            abort(404, description="Convite não encontrado.")



        try:

            session.delete(invite)

            session.commit()
            return jsonify({'message': 'Convite revogado com sucesso.'}), 200

        except Exception as e:  # Trata erros de banco de dados
            logging.exception("Erro ao revogar convite: %s", e)

            abort(500, description=f"Erro ao revogar convite: {e}")