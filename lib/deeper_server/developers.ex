defmodule DeeperServer.Developer do
  use Ecto.Schema
  import Ecto.Changeset

  schema "developers" do
    field :public_key, :string
    field :user_id, :integer

    # timestamps() adiciona automaticamente os campos :inserted_at e :updated_at
    timestamps()
  end

  @doc false
  def changeset(developer, attrs) do
    developer
    |> cast(attrs, [:public_key, :user_id])
    |> validate_required([:public_key, :user_id])
    |> validate_length(:public_key, max: 255)  # Se desejar limitar o tamanho da chave pública
  end
end
