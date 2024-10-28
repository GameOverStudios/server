defmodule DeeperServer.Repo.Migrations.CreateInitialTables do
  use Ecto.Migration

  def change do
    # Tabela: users
    create table(:users) do
      add :username, :string, null: false
      add :password_hash, :string, null: false
      add :birthdate, :date
      add :inserted_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP"), null: false
      add :updated_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP"), null: false
    end

    # Tabela: developers
    create table(:developers) do
      add :user_id, references(:users), null: false
      add :public_key, :text
      add :inserted_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP")
      add :updated_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP")
    end

    # Tabela: packages
    create table(:packages) do
      add :name, :string, null: false
      add :version, :string, null: false
      add :release, :string
      add :patch, :string
      add :maps, :string
      add :description, :text
      add :icon_url, :string
      add :screenshot_urls, :string
      add :trailer_url, :string
      add :download_size, :integer
      add :hash_package, :string, null: false
      add :hash_metadata, :string, null: false
      add :public_key, :text, null: false
      add :signature, :text, null: false
      add :release_date, :utc_datetime
      add :age_rating, :string
      add :tags, :string
      add :average_rating, :float
      add :rating_count, :integer
      add :is_active, :boolean
      add :approved, :boolean
      add :inserted_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP"), null: false
      add :updated_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP"), null: false
    end

    # Tabela: ratings
    create table(:ratings) do
      add :package_id, references(:packages), null: false
      add :user_id, references(:users), null: false
      add :rating, :integer, null: false
      add :comment, :text
      add :inserted_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP"), null: false
      add :updated_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP"), null: false
    end

    # Tabela: comments
    create table(:comments) do
      add :rating_id, references(:ratings), null: false
      add :user_id, references(:users), null: false
      add :comment, :text, null: false
      add :inserted_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP"), null: false
      add :updated_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP"), null: false
    end

    # Tabela: repositories
    create table(:repositories) do
      add :name, :string, null: false
      add :url, :string
      add :network_type, :string, null: false
      add :min_age, :integer
      add :is_official, :boolean
      add :approved, :boolean
      add :allow_clearnet, :boolean
      add :allow_deepnet, :boolean
      add :allow_darknet, :boolean
      add :allow_zeronet, :boolean
      add :global_approval, :boolean
      add :approve_clearnet, :boolean
      add :approve_deepnet, :boolean
      add :approve_darknet, :boolean
      add :approve_zeronet, :boolean
      add :inserted_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP")
      add :updated_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP")
    end

    # Tabela: package_dependencies
    create table(:package_dependencies) do
      add :package_id, references(:packages), null: false
      add :dependency_id, references(:packages), null: false
      add :dependency_type, :string
      add :version_required, :string
    end

    # Tabela: package_repositories
    create table(:package_repositories) do
      add :package_id, references(:packages), null: false
      add :repository_id, references(:repositories), null: false
      add :download_url, :string
      add :download_type, :string, null: false
    end

    # Tabela: user_repository_invites
    create table(:user_repository_invites) do
      add :user_id, references(:users)
      add :invited_user_id, references(:users)
      add :repository_id, references(:repositories), null: false
      add :invite_code, :string, null: false
      add :accepted, :boolean
      add :inserted_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP"), null: false
      add :updated_at, :utc_datetime, default: fragment("CURRENT_TIMESTAMP"), null: false

      unique_index(:user_repository_invites, [:invite_code])
    end
  end
end
