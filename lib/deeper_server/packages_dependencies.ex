defmodule DeeperServer.PackageDependency do
  use Ecto.Schema
  import Ecto.Changeset

  schema "package_dependencies" do
    field :dependency_id, :integer
    field :dependency_type, :string
    field :package_id, :integer
    field :version_required, :string

    timestamps()
  end

  @doc false
  def changeset(package_dependency, attrs) do
    package_dependency
    |> cast(attrs, [:dependency_id, :dependency_type, :package_id, :version_required])
    |> validate_required([:dependency_id, :dependency_type, :package_id, :version_required])
    |> validate_length(:dependency_type, max: 255)  # Limite opcional para dependency_type
    |> validate_length(:version_required, max: 255)  # Limite opcional para version_required
  end
end
