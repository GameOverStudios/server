defmodule DeeperServer.Rating do
  use Ecto.Schema
  import Ecto.Changeset

  schema "ratings" do
    field :comment, :string
    field :package_id, :integer
    field :rating, :integer
    field :user_id, :integer

    timestamps()
  end

  @doc false
  def changeset(rating, attrs) do
    rating
    |> cast(attrs, [:comment, :package_id, :rating, :user_id])
    |> validate_required([:package_id, :rating, :user_id])
    |> validate_length(:comment, max: 255)
    |> validate_number(:rating, greater_than_or_equal_to: 0, less_than_or_equal_to: 5)
  end
end
