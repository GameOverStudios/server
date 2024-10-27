from flask import Blueprint, jsonify, request, abort, url_for
from packages import db, models, utils, cloud_storage
from sqlalchemy.exc import IntegrityError
import logging 
from flask import Blueprint, jsonify, request, abort, url_for, current_app 
from packages.auth import requires_auth, requires_admin

bp_repositories = Blueprint('repositories', __name__, url_prefix='/api/repositories')  # Define o blueprint

@bp_repositories.route('', methods=['GET']) # Lista todos os repositórios
@requires_auth
def get_repositories():

    db_connection = current_app.config['DB_CONNECTION']

    with db_connection.session_scope() as session:
        query = session.query(models.Repository)
        return utils.paginate(query, request=request, url_for=url_for)

@bp_repositories.route('/<int:repository_id>', methods=['GET']) # Detalhes de um repositório específico
@requires_auth
def get_repository(repository_id):

    db_connection = current_app.config['DB_CONNECTION']

    with db_connection.session_scope() as session:
        repository = session.query(models.Repository).filter_by(id=repository_id).first()

        if not repository:

            abort(404, description="Repositório não encontrado")

        return jsonify(repository.to_dict())

@bp_repositories.route('', methods=['POST'])  # Cria um novo repositório
@requires_auth
@requires_admin
def create_repository():
    db_connection = current_app.config['DB_CONNECTION']
    data = request.get_json()

    required_fields = ['name', 'network_type']
    error, status_code = utils.validate_package_data(data, required_fields)

    if error:
        abort(status_code, description=error) # Retorna erro 400 se dados inválidos


    with db_connection.session_scope() as session:  # garante que a sessão seja fechada corretamente, mesmo com erros
        try:

            new_repository = models.Repository(**data)  # Cria o objeto repositório com os dados validados

            session.add(new_repository)
            session.commit()

            return jsonify({'message': 'Repositório criado com sucesso', 'id': new_repository.id}), 201

        except IntegrityError:

            abort(409, description="Já existe um repositório com esse nome.") # Conflito

        except Exception as e:  # erros genéricos de banco de dados
            logging.exception("Erro ao criar repositório: %s", e)
            abort(500, description=f"Erro ao criar repositório: {str(e)}") # Erro interno do servidor

@bp_repositories.route('/<int:repository_id>', methods=['PUT'])  # Atualiza um repositório
@requires_auth
@requires_admin
def update_repository(repository_id):
    db_connection = current_app.config['DB_CONNECTION']

    data = request.get_json()

    with db_connection.session_scope() as session:
        repository = session.query(models.Repository).filter_by(id=repository_id).first()


        if not repository:
            abort(404, description="Repositório não encontrado")



        for field, value in data.items():
            setattr(repository, field, value)  # Define cada atributo com o novo valor recebido


        try:
            session.commit()
            return jsonify({'message': 'Repositório atualizado com sucesso'}), 200

        except IntegrityError as e:  # Tratar erros de integridade (e.g., nome duplicado)
            abort(409, description=str(e))

        except Exception as e: # erros de banco de dados
           logging.exception("Erro ao atualizar repositório: %s", e)

           abort(500, description=f"Erro ao atualizar repositório: {str(e)}")

@bp_repositories.route('/<int:repository_id>', methods=['DELETE']) # Exclui um repositório
@requires_auth
@requires_admin
def delete_repository(repository_id):
    db_connection = current_app.config['DB_CONNECTION']


    with db_connection.session_scope() as session:
        try:

            repository = session.query(models.Repository).filter_by(id=repository_id).first()

            if not repository:

                 abort(404, description="Repositório não encontrado")


            session.delete(repository)
            session.commit()

            return jsonify({'message': 'Repositório excluído com sucesso'}), 200

        except Exception as e: # Erros de banco de dados
             logging.exception("Erro ao excluir repositório: %s", e)

             abort(500, description=f"Erro ao excluir repositório: {str(e)}")

@bp_repositories.route('/<int:repository_id>/developers', methods=['POST']) # Adiciona um desenvolvedor a um repositório
@requires_auth
@requires_admin
def add_developer(repository_id):
    db_connection = current_app.config['DB_CONNECTION']
    data = request.get_json()

    if not data or 'developer_id' not in data:
        abort(400, description="ID do desenvolvedor é obrigatório.")

    developer_id = data['developer_id']

    with db_connection.session_scope() as session:
        repository = session.query(models.Repository).filter_by(id=repository_id).first()
        developer = session.query(models.Developer).filter_by(id=developer_id).first()


        if not repository:
            abort(404, description="Repositório não encontrado")


        if not developer:
            abort(404, description="Desenvolvedor não encontrado")


        try:  # previne adicionar um desenvolvedor repetidamente
            if developer not in repository.developers:  # Verifica se a associação já existe
                 repository.developers.append(developer) # Adiciona o desenvolvedor à lista
                 session.commit()  # Salva as alterações
                 return jsonify({'message': 'Desenvolvedor adicionado ao repositório com sucesso'}), 201
            else:
                return jsonify({'message': 'Desenvolvedor já está associado ao repositório'}), 200 # ou 409 Conflict


        except Exception as e: # outros erros de banco de dados
            logging.exception("Erro ao adicionar desenvolvedor ao repositório: %s", e)
            abort(500, description=f"Erro ao adicionar desenvolvedor ao repositório: {str(e)}")

@bp_repositories.route('/<int:repository_id>/developers/<int:developer_id>', methods=['DELETE']) # Remove um desenvolvedor de um repositório
@requires_auth
@requires_admin
def remove_developer(repository_id, developer_id):
    db_connection = current_app.config['DB_CONNECTION']

    with db_connection.session_scope() as session:
        repository = session.query(models.Repository).filter_by(id=repository_id).first()
        developer = session.query(models.Developer).filter_by(id=developer_id).first()

        if not repository:
            abort(404, description="Repositório não encontrado")

        if not developer:
             abort(404, description="Desenvolvedor não encontrado")

        try:

            if developer in repository.developers:
                repository.developers.remove(developer)
                session.commit()
                return jsonify({'message': 'Desenvolvedor removido do repositório com sucesso'}), 200
            else:
                return jsonify({'message': 'Desenvolvedor não está associado a este repositório'}), 404  # ou 200 OK


        except Exception as e: # erros de banco de dados
             logging.exception("Erro ao remover desenvolvedor do repositório: %s", e)
             abort(500, description=f"Erro ao remover desenvolvedor do repositório: {str(e)}")

@bp_repositories.route('/<int:repository_id>/mirrors', methods=['POST']) # Adiciona um espelho a um repositório
@requires_auth
@requires_admin
def add_mirror(repository_id):
    db_connection = current_app.config['DB_CONNECTION']

    data = request.get_json()

    if not data or 'mirror_repository_id' not in data:
        abort(400, description="ID do repositório espelho é obrigatório.")


    mirror_repository_id = data['mirror_repository_id']

    with db_connection.session_scope() as session:
        repository = session.query(models.Repository).filter_by(id=repository_id).first()
        mirror_repository = session.query(models.Repository).filter_by(id=mirror_repository_id).first()


        if not repository:

             abort(404, description="Repositório não encontrado")


        if not mirror_repository:
            abort(404, description="Repositório espelho não encontrado")


        try:
            repository.mirrors.append(mirror_repository)
            session.commit()
            return jsonify({'message': 'Espelho adicionado ao repositório com sucesso'}), 201


        except IntegrityError: # Se o espelho já existir
            abort(409, description="Este repositório já está espelhado.")

        except Exception as e:  # outros erros de banco de dados
            logging.exception("Erro ao adicionar espelho ao repositório: %s", e)

            abort(500, description=f"Erro ao adicionar espelho ao repositório: {str(e)}")

@bp_repositories.route('/<int:repository_id>/mirrors/<int:mirror_repository_id>', methods=['DELETE']) # Remove um espelho de um repositório
@requires_auth
@requires_admin
def remove_mirror(repository_id, mirror_repository_id):

    db_connection = current_app.config['DB_CONNECTION']

    with db_connection.session_scope() as session:
        repository = session.query(models.Repository).filter_by(id=repository_id).first()

        mirror_repository = session.query(models.Repository).filter_by(id=mirror_repository_id).first()


        if not repository:

            abort(404, description="Repositório não encontrado")


        if not mirror_repository:

            abort(404, description="Repositório espelho não encontrado")



        try:
            if mirror_repository in repository.mirrors:
                repository.mirrors.remove(mirror_repository)
                session.commit()
                return jsonify({'message': 'Espelho removido do repositório com sucesso'}), 200
            else:

                return jsonify({'message': 'Este repositório não está espelhado para o repositório especificado.'}), 404 # ou 200 OK se preferir


        except Exception as e:
            logging.exception("Erro ao remover espelho do repositório: %s", e)

            abort(500, description=f"Erro ao remover espelho do repositório: {str(e)}")

@bp_repositories.route('/<int:repository_id>/config', methods=['PUT'])  # Configura um repositório (exemplo)
@requires_auth
@requires_admin
def configure_repository(repository_id):

    """
    Configura as opções de um repositório, como aprovação de pacotes, tipos de rede permitidos, etc.
    """

    db_connection = current_app.config['DB_CONNECTION']
    data = request.get_json()

    allowed_fields = ['allow_clearnet', 'allow_deepnet', 'allow_darknet', 'allow_zeronet', 'approved', 'global_approval', 'approve_clearnet', 'approve_deepnet', 'approve_darknet', 'approve_zeronet']


    with db_connection.session_scope() as session:
        repository = session.query(models.Repository).filter_by(id=repository_id).first()


        if not repository:

             abort(404, description="Repositório não encontrado")



        for field in allowed_fields: # itera os campos permitidos
            if field in data:
                setattr(repository, field, data[field])


        try:
            session.commit()
            return jsonify({"message": "Repositório configurado com sucesso"}), 200

        except Exception as e: # erros de banco de dados

             logging.exception("Erro ao configurar o repositório: %s", e)
             abort(500, description=f"Erro ao configurar o repositório: {str(e)}")

@bp_repositories.route('/<int:repository_id>/developers', methods=['GET'])
@requires_auth
def list_developers(repository_id):
    db_connection = current_app.config['DB_CONNECTION']
    with db_connection.session_scope() as session:
        repository = session.query(models.Repository).filter_by(id=repository_id).first()
        if not repository:
            abort(404, description="Repositório não encontrado")

        developers = [dev.to_dict() for dev in repository.developers]  # Usa o relacionamento para obter os desenvolvedores
        return jsonify(developers), 200
    
@bp_repositories.route('/<int:repository_id>/mirrors', methods=['GET'])
@requires_auth
def list_mirrors(repository_id):
    db_connection = current_app.config['DB_CONNECTION']

    with db_connection.session_scope() as session:
        repository = session.query(models.Repository).filter_by(id=repository_id).first()
        if not repository:

            abort(404, description="Repositório não encontrado")

        mirrors = [mirror.to_dict() for mirror in repository.mirrors]
        return jsonify(mirrors), 200
    
@bp_repositories.route('/search', methods=['GET'])
@requires_auth
def search_repositories():
    db_connection = current_app.config['DB_CONNECTION']
    name = request.args.get('name')
    network_type = request.args.get('network_type')

    with db_connection.session_scope() as session:
        query = session.query(models.Repository)

        if name:
            query = query.filter(models.Repository.name.ilike(f"%{name}%"))  # Busca por nome (case-insensitive)


        if network_type:
            query = query.filter(models.Repository.network_type == network_type)

        return utils.paginate(query, request=request, url_for=url_for)
    
@bp_repositories.route('/<int:repository_id>/status', methods=['PUT'])
@requires_auth
@requires_admin
def update_repository_status(repository_id):
    db_connection = current_app.config['DB_CONNECTION']
    data = request.get_json()

    if not data or 'is_active' not in data:  # Verifica se 'is_active' está presente nos dados
        abort(400, description="Campo 'is_active' é obrigatório.")


    with db_connection.session_scope() as session:  # garante que a sessão seja fechada
        repository = session.query(models.Repository).filter_by(id=repository_id).first()

        if not repository:
            abort(404, description="Repositório não encontrado")

        repository.is_active = data['is_active']
        session.commit()

        return jsonify({'message': 'Status do repositório atualizado com sucesso'}), 200
