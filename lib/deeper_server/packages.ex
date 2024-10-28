defmodule DeeperServer.Package do
  use Ecto.Schema
  import Ecto.Changeset

  schema "packages" do
    field :age_rating, :string
    field :approved, :boolean
    field :average_rating, :float
    field :description, :string
    field :download_size, :integer
    field :hash_metadata, :string
    field :hash_package, :string
    field :icon_url, :string
    field :is_active, :boolean
    field :name, :string
    field :patch, :string
    field :public_key, :string
    field :rating_count, :integer
    field :release, :string
    field :release_date, :naive_datetime
    field :screenshot_urls, :string
    field :signature, :string
    field :tags, :string
    field :trailer_url, :string
    field :version, :string
    field :maps, :string

    timestamps()
  end

  @doc false
  def changeset(package, attrs) do
    package
    |> cast(attrs, [:age_rating, :approved, :description, :download_size, :hash_metadata, :hash_package, :icon_url, :is_active, :name, :patch, :public_key, :rating_count, :release, :release_date, :screenshot_urls, :signature, :tags, :trailer_url, :version, :maps])
    |> validate_required([:name, :version, :hash_package, :hash_metadata, :public_key, :is_active, :approved])
    |> validate_length(:name, max: 255)
    |> validate_length(:version, max: 255)
    |> validate_length(:release, max: 255)
    |> validate_length(:patch, max: 255)
    |> validate_length(:hash_package, max: 255)
    |> validate_length(:hash_metadata, max: 255)
    |> validate_length(:icon_url, max: 255)
    |> validate_length(:screenshot_urls, max: 255)
    |> validate_length(:trailer_url, max: 255)
    |> validate_length(:tags, max: 255)
    |> validate_length(:maps, max: 255)
  end
end
