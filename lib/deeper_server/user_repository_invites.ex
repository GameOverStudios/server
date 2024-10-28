defmodule DeeperServer.UserRepositoryInvite do
  use Ecto.Schema
  import Ecto.Changeset

  schema "user_repository_invites" do
    field :accepted, :boolean
    field :invited_user_id, :integer
    field :invite_code, :string
    field :repository_id, :integer
    field :user_id, :integer

    timestamps()
  end

  @doc false
  def changeset(user_repository_invite, attrs) do
    user_repository_invite
    |> cast(attrs, [:accepted, :invited_user_id, :invite_code, :repository_id, :user_id])
    |> validate_required([:invited_user_id, :repository_id, :invite_code])
    |> validate_length(:invite_code, max: 255)
  end
end
