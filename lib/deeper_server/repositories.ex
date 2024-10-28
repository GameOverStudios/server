defmodule DeeperServer.Repository do
  use Ecto.Schema
  import Ecto.Changeset

  schema "repositories" do
    field :allow_clearnet, :boolean
    field :allow_darknet, :boolean
    field :allow_deepnet, :boolean
    field :allow_zeronet, :boolean
    field :approve_clearnet, :boolean
    field :approve_darknet, :boolean
    field :approve_deepnet, :boolean
    field :approve_zeronet, :boolean
    field :global_approval, :boolean
    field :is_official, :boolean
    field :min_age, :integer
    field :name, :string
    field :network_type, :string
    field :url, :string

    timestamps()
  end

  @doc false
  def changeset(repository, attrs) do
    repository
    |> cast(attrs, [
      :allow_clearnet, :allow_darknet, :allow_deepnet, :allow_zeronet,
      :approve_clearnet, :approve_darknet, :approve_deepnet, :approve_zeronet,
      :global_approval, :is_official, :min_age, :name, :network_type, :url
    ])
    |> validate_required([:name, :network_type])
    |> validate_length(:name, max: 255)
    |> validate_length(:network_type, max: 255)
    |> validate_length(:url, max: 255)
  end
end
