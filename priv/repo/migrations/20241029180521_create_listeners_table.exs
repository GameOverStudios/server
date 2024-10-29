defmodule DeeperServer.Repo.Migrations.CreateListenersTable do
  use Ecto.Migration

  def change do
    create table(:listeners) do
      add :name, :string, null: false, unique: true # Nome único do listener
      add :port, :integer, null: false
      add :protocol_module, :string, null: false  # Módulo do protocolo (Echo ou EchoSSL)
      add :ssl, :boolean, null: false, default: false  # Indica se usa SSL
      add :certfile, :string # Caminho do certificado (se SSL)
      add :keyfile, :string # Caminho da chave (se SSL)

      timestamps()
    end

    create index(:listeners, [:name])

  end
end
