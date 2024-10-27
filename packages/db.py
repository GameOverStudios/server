from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging

# Cria a base para os modelos
Base = declarative_base()

# Cria a instância do SQLAlchemy
db = SQLAlchemy()

def init_app(app):
    """Configura o SQLAlchemy com a aplicação Flask."""
    db.init_app(app)
    # ... (outras configurações do banco de dados, se necessário)

def get_db():
    """Cria e retorna uma conexão com o banco de dados."""
    engine = create_engine(app.config['DATABASE_URI'], echo=False) # echo=True para logs SQL
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Session = scoped_session(session_factory)
    session = Session()
    return session

def close_connection(error=None):
    """Fecha a conexão com o banco de dados."""
    logging.info("Fechando conexão com o banco de dados.")
    db.session.close() 
    # ... (sua lógica para fechar a conexão)

# Classe DatabaseConnection (pode ser removida se estiver usando SQLAlchemy)
class DatabaseConnection:
    """(Classe opcional) Classe para gerenciar a conexão com o banco de dados."""
    def __init__(self, db_uri):
         self.engine = create_engine(db_uri, echo=False)  # echo=True para logs SQL
         self.session_factory = sessionmaker(bind=self.engine)
         self.Session = scoped_session(self.session_factory)
         self.session = self.Session()

    def create_tables(self):
        """Cria as tabelas no banco de dados."""
        try:
            Base.metadata.create_all(self.engine)
            print("Tabelas criadas com sucesso!")
        except Exception as e:
            print(f"Erro ao criar as tabelas: {e}")

    def execute_query(self, query, params=None):
        """Executa uma consulta SQL."""
        try:
            result = self.session.execute(text(query), params)
            self.session.commit()  # necessário para INSERT, UPDATE, DELETE
            return result
        except Exception as e:
            self.session.rollback()
            raise

    def fetchall_dict(self, query, params=None):
        """Retorna todos os resultados como uma lista de dicionários."""
        result = self.execute_query(query, params)
        return [dict(row) for row in result.fetchall()]

    def fetchone_dict(self, query, params=None):
        """Retorna o primeiro resultado como um dicionário."""
        result = self.execute_query(query, params)
        row = result.fetchone()
        return dict(row) if row else None

    def close_connection(self, exception=None):
        """Fecha a conexão com o banco de dados."""
        if exception:  # faz rollback se houve uma exceção
            self.session.rollback()
        self.Session.remove()
        if self.engine:
            self.engine.dispose()