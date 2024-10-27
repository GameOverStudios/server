from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from packages.db import Base

# ... (outros imports que você possa precisar)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    birthdate = Column(Date)
    created_at = Column(DateTime, nullable=False, server_default='now()')
    updated_at = Column(DateTime, nullable=False, server_default='now()')

    # Relacionamentos
    developer = relationship("Developer", backref="user") # backref p/ acesso do outro lado
    ratings = relationship("Rating", backref="user")

    def __repr__(self):
        return f"<User {self.username}>"



class Developer(Base):
   __tablename__ = 'developers'
   id = Column(Integer, primary_key=True, autoincrement=True)
   user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
   public_key = Column(Text) # chave pública longa
   created_at = Column(DateTime, server_default='now()')
   updated_at = Column(DateTime, server_default='now()')
   
   # Relacionamentos
   repositories = relationship('Repository', secondary='repository_developers', back_populates='developers')
   
   def __repr__(self):
        return f"<Developer {self.id} (User: {self.user_id})>"


class Repository(Base):
   __tablename__ = 'repositories'
   id = Column(Integer, primary_key=True, autoincrement=True)
   name = Column(String, unique=True, nullable=False)
   url = Column(String)
   network_type = Column(String, nullable=False)  # clearnet, deepnet, etc.
   min_age = Column(Integer)
   is_official = Column(Boolean, default=False)
   approved = Column(Boolean, default=False)
   allow_clearnet = Column(Boolean, default=True)
   allow_deepnet = Column(Boolean, default=False)
   allow_darknet = Column(Boolean, default=False)
   allow_zeronet = Column(Boolean, default=False)
   global_approval = Column(Boolean, default=True) # Determina se este repositório aceita pacotes sem aprovação
   approve_clearnet = Column(Boolean, default=True)
   approve_deepnet = Column(Boolean, default=True)
   approve_darknet = Column(Boolean, default=True)
   approve_zeronet = Column(Boolean, default=True)
   created_at = Column(DateTime, server_default='now()')
   updated_at = Column(DateTime, server_default='now()')
   
   # Relacionamentos
   packages = relationship("Package", secondary="package_repositories", back_populates="repositories")
   developers = relationship('Developer', secondary='repository_developers', back_populates='repositories')
   invites = relationship("UserRepositoryInvite", backref="repository") # para os invites
   
   
   def __repr__(self):
       return f"<Repository {self.name}>"



class Package(Base):
    __tablename__ = 'packages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    release = Column(String)
    patch = Column(String)
    maps = Column(String)  #  mapas para jogos (se aplicável)
    description = Column(Text)
    icon_url = Column(String)
    screenshot_urls = Column(String)  #  URLs separadas por vírgula
    trailer_url = Column(String)
    download_size = Column(Integer)  #  em bytes
    hash_package = Column(String, nullable=False)
    hash_metadata = Column(String, nullable=False)
    public_key = Column(Text, nullable=False) # chave pública para verificação
    signature = Column(Text, nullable=False) # assinatura digital
    release_date = Column(DateTime)
    age_rating = Column(String)
    tags = Column(String)
    average_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True) # Para ativar/desativar pacotes
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, server_default='now()')
    updated_at = Column(DateTime, nullable=False, server_default='now()')

    # Relacionamentos
    repositories = relationship("Repository", secondary="package_repositories", back_populates="packages")
    ratings = relationship("Rating", backref="package")
    dependencies = relationship("PackageDependency", foreign_keys="PackageDependency.package_id", backref="package")

    def __repr__(self):
       return f"<Package {self.name} v{self.version}>"


class PackageRepository(Base):
    __tablename__ = 'package_repositories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    package_id = Column(Integer, ForeignKey('packages.id'), nullable=False)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    download_url = Column(String)  # URL completo para download
    download_type = Column(String, nullable=False, default='http') # Tipo de download (http, torrent, etc.)


class PackageDependency(Base):
    __tablename__ = 'package_dependencies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    package_id = Column(Integer, ForeignKey('packages.id'), nullable=False)
    dependency_id = Column(Integer, ForeignKey('packages.id'), nullable=False)  # Referencia a outro pacote
    dependency_type = Column(String)  # Tipo de dependência
    version_required = Column(String)  # Versão da dependência


class Rating(Base):
    __tablename__ = 'ratings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    package_id = Column(Integer, ForeignKey('packages.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default='now()')

    comments = relationship("Comment", backref="rating")  # Relacionamento com Comment

    def __repr__(self):
       return f"<Rating {self.rating} (User: {self.user_id}, Package: {self.package_id})>"


class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rating_id = Column(Integer, ForeignKey('ratings.id'), nullable=False) # adicionado relacionamento com ratings
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default='now()')

    def __repr__(self):
        return f"<Comment {self.comment[:20]}...>"

class UserRepositoryInvite(Base):
    __tablename__ = "user_repository_invites"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id')) # Convite de UM usuário PARA outro
    invited_user_id = Column(Integer, ForeignKey('users.id')) # Referencia ao user que foi convidado

    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    invite_code = Column(String, unique=True, nullable=False)  # Código único do convite
    accepted = Column(Boolean, default=False)  # Se o convite foi aceito
    created_at = Column(DateTime, server_default='now()')