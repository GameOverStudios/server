from flask import Blueprint, jsonify, request, abort, current_app, url_for
from packages import db, models, utils
from sqlalchemy.exc import IntegrityError
import logging 
from packages.auth import requires_auth, requires_admin

ratings_bp = Blueprint('ratings', __name__, url_prefix='/api/ratings')

@ratings_bp.route('/<int:package_id>', methods=['POST'])  # Cria uma nova avaliação para um pacote
@requires_auth
def create_rating(package_id):
    db_connection = current_app.config['DB_CONNECTION']
    data = request.get_json()

    required_fields = ['rating']
    error, status_code = utils.validate_package_data(data, required_fields)
    if error:
        abort(status_code, description=error)

    try:
        rating_value = int(data['rating'])
        if not 1 <= rating_value <= 5:
            abort(400, description="A avaliação deve estar entre 1 e 5.")
    except (ValueError, TypeError):
        abort(400, description="Valor de avaliação inválido.")

    with db_connection.session_scope() as session:
        try:
            new_rating = models.Rating(
                package_id=package_id,
                user_id=request.user_id,  # ID do usuário autenticado
                rating=rating_value,
                comment=data.get('comment')  # Comentário opcional
            )
            session.add(new_rating)
            session.flush()  # Para obter o ID da nova avaliação

            # Adiciona comentários, se houver
            comments_data = data.get('comments')
            if comments_data:
                for comment_data in comments_data:
                    new_comment = models.Comment(
                         rating_id=new_rating.id,
                        user_id=request.user_id,
                         comment=comment_data['comment']
                    )
                    session.add(new_comment)



            session.commit() # Atualizar a avaliação média
            utils.update_average_rating(package_id, session) # Função auxiliar
            return jsonify({'message': 'Avaliação criada com sucesso', 'id': new_rating.id}), 201

        except IntegrityError: # Avaliação duplicada
            abort(409, description="Você já avaliou este pacote.")  # Erro 409 Conflict

        except Exception as e:  # Trata outros erros
             logging.exception("Erro ao criar avaliação: %s", e)
             abort(500, description=f"Erro ao criar avaliação: {str(e)}")

@ratings_bp.route('/<int:package_id>', methods=['GET'])  # Lista avaliações de um pacote
def list_ratings(package_id):

    db_connection = current_app.config['DB_CONNECTION']
    with db_connection.session_scope() as session:
        query = session.query(models.Rating).filter_by(package_id=package_id)
        return utils.paginate(query, request=request, url_for=url_for)

@ratings_bp.route('/<int:rating_id>', methods=['PUT'])  # Atualiza uma avaliação
@requires_auth
def update_rating(rating_id):
    db_connection = current_app.config['DB_CONNECTION']
    data = request.get_json()

    allowed_fields = ['rating', 'comment']  # Define os campos permitidos para atualização

    with db_connection.session_scope() as session:
        rating = session.query(models.Rating).filter_by(id=rating_id).first()

        if not rating:
            abort(404, description="Avaliação não encontrada")



        if rating.user_id != request.user_id: # Verifica se é o dono da avaliação

            abort(403, description="Você não tem permissão para editar esta avaliação.")



        for field in allowed_fields: # só atualiza os campos permitidos
            if field in data:
                if field == 'rating':
                     try:

                         rating_value = int(data['rating'])  # Converte para inteiro
                         if 1 <= rating_value <= 5:  # Valida o valor

                            setattr(rating, field, rating_value)

                         else:

                              abort(400, description="A avaliação deve estar entre 1 e 5.") # erro 400 Bad Request

                     except (ValueError, TypeError):  # Se não for um número inteiro

                          abort(400, description="Valor da avaliação inválido.")

                else:
                    setattr(rating, field, data[field])


        try:
            session.commit()
            utils.update_average_rating(rating.package_id, session)  # Atualiza avaliação média após modificação

            return jsonify({'message': 'Avaliação atualizada com sucesso'}), 200


        except Exception as e: # outros erros de banco de dados
            logging.exception("Erro ao atualizar a avaliação: %s", e)

            abort(500, description=f"Erro ao atualizar a avaliação: {e}")

@ratings_bp.route('/<int:rating_id>', methods=['DELETE'])  # Exclui uma avaliação
@requires_auth
def delete_rating(rating_id):
    db_connection = current_app.config['DB_CONNECTION']

    with db_connection.session_scope() as session:
        rating = session.query(models.Rating).filter_by(id=rating_id).first()

        if not rating:
            abort(404, description="Avaliação não encontrada")


        if rating.user_id != request.user_id:

             abort(403, description="Você não tem permissão para excluir esta avaliação.")



        try:

            session.delete(rating)  # Remove os comentários associados em cascata (se configurado no modelo)
            session.commit()
            utils.update_average_rating(rating.package_id, session)  # Atualiza a avaliação média após a exclusão

            return jsonify({'message': 'Avaliação excluída com sucesso'}), 200


        except Exception as e:
            logging.exception("Erro ao excluir a avaliação: %s", e)
            abort(500, description=f"Erro ao excluir a avaliação: {e}")

@ratings_bp.route('/<int:rating_id>/comments', methods=['POST'])  # Adiciona um comentário a uma avaliação
@requires_auth
def create_comment(rating_id):

    db_connection = current_app.config['DB_CONNECTION']
    data = request.get_json()

    if not data or 'comment' not in data:
        abort(400, description="Comentário ausente.")

    with db_connection.session_scope() as session:  # garante que a sessão seja fechada
        rating = session.query(models.Rating).filter_by(id=rating_id).first()

        if not rating:
            abort(404, description="Avaliação não encontrada")

        # verifica se o usuário está comentando na sua propria avaliação ou é admin
        if rating.user_id != request.user_id and not utils.is_admin(request.user_id, db_connection):  # Verifica permissões
            abort(403, description="Você não tem permissão para comentar nesta avaliação.")



        try:
            new_comment = models.Comment(rating_id=rating_id, user_id=request.user_id, comment=data['comment'])
            session.add(new_comment)
            session.commit()
            return jsonify({'message': 'Comentário criado com sucesso', 'id': new_comment.id}), 201


        except Exception as e: # outros erros de banco de dados

            logging.exception("Erro ao criar comentário: %s", e)

            abort(500, description=f"Erro ao criar comentário: {e}")

@ratings_bp.route('/<int:rating_id>/comments', methods=['GET'])  # Lista comentários de uma avaliação
def list_comments(rating_id):

    db_connection = current_app.config['DB_CONNECTION']
    with db_connection.session_scope() as session:

        query = session.query(models.Comment).filter_by(rating_id=rating_id)

        return utils.paginate(query, request=request, url_for=url_for)

def update_average_rating(package_id, session):
    average_rating = session.query(func.avg(models.Rating.rating)).filter_by(package_id=package_id).scalar()
    package = session.query(models.Package).filter_by(id=package_id).first()

    if package:

        package.average_rating = average_rating or 0.0  # Define como 0.0 se não houver avaliações
        session.commit()

