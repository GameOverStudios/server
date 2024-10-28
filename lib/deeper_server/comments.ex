defmodule DeeperServer.Comment do
  use Ecto.Schema
  import Ecto.Changeset

  schema "comments" do
    field :comment, :string
    field :rating_id, :integer
    field :user_id, :integer

    # timestamps() adiciona automaticamente os campos :inserted_at e :updated_at
    timestamps()
  end

  @doc false
  def changeset(comment, attrs) do
    comment
    |> cast(attrs, [:comment, :rating_id, :user_id])
    |> validate_required([:comment, :rating_id, :user_id])
    |> validate_length(:comment, max: 255)  # Se desejar limitar o tamanho do comentário
  end
end
