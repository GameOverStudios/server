from flask import Blueprint, jsonify, request, abort, url_for, current_app, send_file
from packages import db, models, utils, cloud_storage
from sqlalchemy.exc import IntegrityError
import os
import hashlib
import json
import logging 
from packages.auth import requires_auth, requires_admin

packages_bp = Blueprint('packages', __name__, url_prefix='/api/packages')

@packages_bp.route('', methods=['GET'])  # Lista pacotes (com paginação e filtros)
@requires_auth
def list_packages():
    db_connection = current_app.config['DB_CONNECTION']
    repository_id = request.args.get('repository_id')
    network_type = request.args.get('network_type')
    approved_status_str = request.args.get('approved') # pode ser "true", "false" ou None (para ambos)

    approved_status = None

    if approved_status_str:
        approved_status = approved_status_str.lower() == 'true'

    with db_connection.session_scope() as session:
        query = session.query(models.Package)
        query = utils.filter_packages(query, repository_id, network_type, approved_status)
        return utils.paginate(query, request=request, url_for=url_for)

@packages_bp.route('/<int:package_id>', methods=['GET']) # Detalhes de um pacote específico
@requires_auth
def get_package(package_id):
    db_connection = current_app.config['DB_CONNECTION']
    with db_connection.session_scope() as session:
        package = session.query(models.Package).filter_by(id=package_id).first()


        if not package:

            abort(404, description="Pacote não encontrado")  # Retorna 404 com mensagem descritiva

        return jsonify(package.to_dict())

@packages_bp.route('', methods=['POST'])  # Cria um novo pacote (upload)
@requires_auth
def create_package():  # alterado para create_package
    CLOUD_STORAGE_ENABLED = current_app.config.get('CLOUD_STORAGE_ENABLED')
    db_connection = current_app.config['DB_CONNECTION']

    if 'file' not in request.files: # verifica se foi enviado um arquivo
        abort(400, description="Nenhum arquivo enviado.")


    file = request.files['file']
    if file.filename == '':  # verifica se o arquivo tem nome
         abort(400, description="Nome do arquivo ausente.")


    if not request.is_json:  # Verifica se a requisição contém dados JSON
        abort(400, description="Metadados ausentes (JSON).")


    try:  # para erros de JSON
        metadata = request.get_json()

    except Exception as e:  # Lidar com erro de JSON inválido

        abort(400, description=f"Erro ao analisar JSON: {str(e)}")

    required_fields = ['name', 'version', 'public_key', 'signature']
    error, status_code = utils.validate_package_data(metadata, required_fields) # Valida os metadados

    if error:
        abort(status_code, description=error)


    if not utils.verify_signature(utils.load_public_key(metadata['public_key']), metadata['signature'], json.dumps(metadata, sort_keys=True)):
        abort(400, description="Assinatura inválida.")


    with db_connection.session_scope() as session:
        # Calcula o hash SHA256 do PACOTE
        file_hash = hashlib.sha256(file.read()).hexdigest()
        file.seek(0)  # Retorna para o início para salvar o pacote


        try: # Calcula hash dos metadados

             metadata_hash = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()

        except Exception as e:
            abort(400, description=f"Erro ao calcular hash dos metadados: {str(e)}")

        try:
            filename = file_hash + os.path.splitext(file.filename)[1] # Nome do arquivo no Cloud Storage
            download_url = cloud_storage.upload_file(file, filename, current_app.config['CLOUD_STORAGE_BUCKET'])

        except Exception as e:

            logging.exception("Erro ao enviar o arquivo para o Cloud Storage: %s", e) # Log mais detalhado
            abort(500, description=f"Erro ao fazer upload do arquivo: {str(e)}")


        try:
            new_package = models.Package(
                 name=metadata['name'],
                version=metadata['version'],
                release=metadata.get('release'),
                patch=metadata.get('patch'),
                maps=metadata.get('maps'),
                description=metadata.get('description'),
                icon_url=metadata.get('icon_url'),
                screenshot_urls=metadata.get('screenshot_urls'),
                trailer_url=metadata.get('trailer_url'),
                download_size=file.content_length,
                hash_package=file_hash, # adicionado hash do pacote
                hash_metadata=metadata_hash, # adicionado hash dos metadados
                public_key=metadata['public_key'],
                signature=metadata['signature'],
                release_date=metadata.get('release_date'),
                 age_rating=metadata.get('age_rating'),
                 tags=metadata.get('tags'),
                average_rating=metadata.get('average_rating'),

            )

            session.add(new_package)
            session.flush() # garante que o pacote tenha um ID antes de adicionar ao repositório


            # Relaciona o pacote com o repositório
            repository_id = request.form.get('repository_id')
            if repository_id:
                try:
                    repository_id = int(repository_id)
                    repository = session.query(models.Repository).filter_by(id=repository_id).first()


                    if not repository:
                        abort(404, description="Repositório não encontrado")


                    new_package_repository = models.PackageRepository(
                         package_id=new_package.id, # ID gerado automaticamente pelo banco de dados
                         repository_id=repository_id,
                         download_url=download_url,
                         download_type=current_app.config.get('DOWNLOAD_TYPE', 'http') # busca do config, padrão 'http'
                     )
                    session.add(new_package_repository)
                except ValueError:
                    abort(400, description="ID do repositório inválido.")



            session.commit()

            return jsonify({'message': 'Pacote criado com sucesso', 'package_id': new_package.id}), 201


        except IntegrityError as e: # nome e versão duplicados

            abort(409, description=f"Conflito: {e.orig}") # Erro 409 Conflict


        except Exception as e:  # Trata outros erros

            logging.exception("Erro ao criar pacote: %s", e) # Log mais detalhado

            abort(500, description=f"Erro ao criar pacote: {str(e)}")

@packages_bp.route('/<int:package_id>', methods=['PUT'])  # Atualiza um pacote
@requires_auth
@requires_admin
def update_package(package_id):
    db_connection = current_app.config['DB_CONNECTION']
    data = request.get_json()


    with db_connection.session_scope() as session:
        package = session.query(models.Package).filter_by(id=package_id).first()


        if not package:
             abort(404, description="Pacote não encontrado")


        allowed_fields = [  # Define os campos que podem ser alterados
             "name", "version", "release", "patch", "maps", "description", "icon_url", "screenshot_urls", "trailer_url",
            "download_size", "release_date", "age_rating", "tags", "average_rating", "is_active", "approved"  # Adicionado 'approved'
         ]

        for field in allowed_fields:  # Itera apenas pelos campos permitidos
            if field in data:
                setattr(package, field, data[field])


        try:
            session.commit()
            return jsonify({'message': 'Pacote atualizado com sucesso'}), 200


        except IntegrityError as e:
             abort(409, description=str(e)) # erro 409 Conflito

        except Exception as e: # outros erros de banco de dados
            logging.exception("Erro ao atualizar pacote: %s", e)

            abort(500, description=f"Erro ao atualizar pacote: {str(e)}")

@packages_bp.route('/<int:package_id>', methods=['DELETE'])  # Exclui um pacote
@requires_auth
@requires_admin
def delete_package(package_id):
    db_connection = current_app.config['DB_CONNECTION']
    CLOUD_STORAGE_ENABLED = current_app.config.get('CLOUD_STORAGE_ENABLED') # Verifica se Cloud Storage está ativado
    CLOUD_STORAGE_BUCKET = current_app.config.get('CLOUD_STORAGE_BUCKET') # Nome do bucket (se aplicável)

    with db_connection.session_scope() as session:
        package = session.query(models.Package).filter_by(id=package_id).first()


        if not package:

            abort(404, description="Pacote não encontrado")



        try:
            package_filename = package.hash_package + os.path.splitext(package.name)[1] # nome do arquivo usando o hash

            if CLOUD_STORAGE_ENABLED: # verifica se deve ser excluído do Cloud Storage

                cloud_storage.delete_file(package_filename, CLOUD_STORAGE_BUCKET) # nome do bucket




            session.delete(package) # exclui os relacionamentos e o pacote
            session.commit()  # confirma as alterações no banco de dados
            return jsonify({'message': 'Pacote excluído com sucesso'}), 200


        except Exception as e: # outros erros de banco de dados, ou do Cloud Storage
            logging.exception("Erro ao excluir pacote: %s", e) # Log detalhado do erro, incluindo traceback
            abort(500, description=f"Erro ao excluir pacote: {str(e)}")

@packages_bp.route('/<int:package_id>/download', methods=['GET'])  # Download de um pacote
@requires_auth # Autenticação necessária para download
def download_package(package_id):

    CLOUD_STORAGE_ENABLED = current_app.config.get('CLOUD_STORAGE_ENABLED')

    db_connection = current_app.config['DB_CONNECTION']

    with db_connection.session_scope() as session:  # garante que a sessão seja fechada
        package_repository = session.query(models.PackageRepository).filter_by(package_id=package_id).first()


        if not package_repository:

            abort(404, description="URL de download do pacote não encontrada") # pacote não existe neste repositório



        if CLOUD_STORAGE_ENABLED:
            try:
                package = session.query(models.Package).filter_by(id=package_id).first()

                if not package:
                    abort(404, description="Pacote não encontrado")

                package_filename = package.hash_package + os.path.splitext(package.name)[1]

                file_stream = cloud_storage.download_file(package_filename, current_app.config['CLOUD_STORAGE_BUCKET'])  # Nome do bucket

                return send_file(file_stream, as_attachment=True, download_name=package.name)


            except Exception as e:  # Trata exceções do Cloud Storage

                logging.exception("Erro ao baixar pacote do Cloud Storage: %s", e)

                abort(500, description=f"Erro ao baixar pacote: {e}")


        else:  # Se Cloud Storage não estiver ativado
             try:  # Lida com erros de download
                return send_file(package_repository.download_url, as_attachment=True) # send_file se local


             except Exception as e:  # Lidar com erros de download (FileNotFoundError, etc.)
                 logging.exception("Erro ao baixar pacote (local): %s", e)

                 abort(500, description=f"Erro ao baixar pacote: {e}")

@packages_bp.route('/<int:package_id>/dependencies', methods=['POST']) # Adiciona uma dependência a um pacote
@requires_auth
@requires_admin
def add_dependency(package_id):
    db_connection = current_app.config['DB_CONNECTION']

    data = request.get_json()

    required_fields = ['dependency_id', 'dependency_type']
    error, status_code = utils.validate_package_data(data, required_fields)
    if error:

        abort(status_code, description=error)


    with db_connection.session_scope() as session:
        package = session.query(models.Package).filter_by(id=package_id).first()
        dependency = session.query(models.Package).filter_by(id=data['dependency_id']).first()


        if not package:

            abort(404, description="Pacote não encontrado")


        if not dependency:

            abort(404, description="Dependência não encontrada")


        try:
            new_dependency = models.PackageDependency(
                 package_id=package_id,
                dependency_id=data['dependency_id'],  # ID da dependência
                 dependency_type=data['dependency_type'],
                version_required=data.get('version_required') # opcional
            )

            session.add(new_dependency)
            session.commit()

            return jsonify({'message': 'Dependência adicionada com sucesso'}), 201

        except Exception as e: # erros de banco de dados
            logging.exception("Erro ao adicionar dependência: %s", e)

            abort(500, description=f"Erro ao adicionar dependência: {str(e)}")

@packages_bp.route('/<int:package_id>/dependencies', methods=['GET']) # Lista as dependências de um pacote
@requires_auth # Autenticação necessária para download
def list_dependencies(package_id):
    db_connection = current_app.config['DB_CONNECTION']
    with db_connection.session_scope() as session:
        package = session.query(models.Package).filter_by(id=package_id).first()

        if not package:

            abort(404, description="Pacote não encontrado")


        dependencies = [
            dep.to_dict() for dep in package.dependencies
        ]

        return jsonify(dependencies), 200

@packages_bp.route('/search', methods=['GET']) # Busca por pacotes (com filtros)
@requires_auth
def search_packages():
    db_connection = current_app.config['DB_CONNECTION']

    name = request.args.get('name')
    tags = request.args.get('tags')
    age_rating = request.args.get('age_rating')
    repository_id = request.args.get('repository_id')  # Adiciona filtro por repositório

    with db_connection.session_scope() as session:
        query = session.query(models.Package)

        if name:
            query = query.filter(models.Package.name.ilike(f"%{name}%"))

        if tags:
            tags_list = tags.split(',')

            for tag in tags_list:
                 query = query.filter(models.Package.tags.ilike(f"%{tag.strip()}%"))


        if age_rating:

            query = query.filter(models.Package.age_rating == age_rating)


        if repository_id:  # Aplica filtro por repositório se fornecido

           try:

                repository_id = int(repository_id)

                query = query.filter(models.Package.repositories.any(id=repository_id))

           except ValueError: # Lidar com erro se o ID não for um inteiro

               abort(400, description="ID do repositório inválido.")



        return utils.paginate(query, request=request, url_for=url_for)

def replicate_package(package_id, origin_repository_id):

    """
    Replica um pacote para os espelhos do repositório de origem.
    """

    db_connection = current_app.config['DB_CONNECTION']
    CLOUD_STORAGE_ENABLED = current_app.config.get('CLOUD_STORAGE_ENABLED') # Verifica Cloud Storage

    with db_connection.session_scope() as session:

        origin_repository = session.query(models.Repository).filter_by(id=origin_repository_id).first()

        package = session.query(models.Package).filter_by(id=package_id).first()


        if not origin_repository:
             abort(404, description="Repositório de origem não encontrado")

        if not package:
             abort(404, description="Pacote não encontrado")


        mirrors = origin_repository.mirrors

        for mirror in mirrors:
            try:
                existing_package = session.query(models.PackageRepository).filter_by(package_id=package_id, repository_id=mirror.id).first()

                if existing_package:  # Pacote já existe no espelho - evita a criação duplicada
                     continue  # Pula para o próximo espelho




                new_package_repository = models.PackageRepository(

                    package=package,  # Adiciona o pacote diretamente
                    repository=mirror,  # Adiciona o repositório espelho diretamente
                    download_url=cloud_storage.generate_download_url(package.hash_package, current_app.config['CLOUD_STORAGE_BUCKET']), # URL do Cloud Storage
                    download_type=current_app.config.get('DOWNLOAD_TYPE', 'http')
                )

                session.add(new_package_repository)

            except Exception as e:  # captura erros de replicação para cada espelho individualmente
                logging.exception(f"Erro ao replicar pacote para o espelho {mirror.name}: %s", e)  # Log mais informativo
                # Aqui você poderia adicionar lógica para tentar novamente a replicação mais tarde, registrar o erro em um banco de dados separado, etc.


        session.commit() # Salva as alterações no banco de dados


        return jsonify({'message': 'Pacote replicado para espelhos com sucesso.'}), 200
    
