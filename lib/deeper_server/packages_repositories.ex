defmodule DeeperServer.PackageRepository do
  use Ecto.Schema
  import Ecto.Changeset

  schema "package_repositories" do
    field :download_type, :string
    field :download_url, :string
    field :package_id, :integer
    field :repository_id, :integer

    timestamps()
  end

  @doc false
  def changeset(package_repository, attrs) do
    package_repository
    |> cast(attrs, [:download_type, :download_url, :package_id, :repository_id])
    |> validate_required([:download_type, :download_url, :package_id, :repository_id])
    |> validate_length(:download_type, max: 255)  # Limite opcional para download_type
    |> validate_length(:download_url, max: 255)   # Limite opcional para download_url
  end
end
