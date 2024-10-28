defmodule DeeperServer.User do
  use Ecto.Schema
  import Ecto.Changeset

  schema "users" do
    field :birthdate, :date
    field :password_hash, :string
    field :username, :string

    timestamps()
  end

  @doc false
  def changeset(user, attrs) do
    user
    |> cast(attrs, [:birthdate, :password_hash, :username])
    |> validate_required([:username, :password_hash])
    |> validate_length(:username, max: 255)
    |> validate_birthdate() # Se você quiser adicionar uma validação para a data de nascimento
  end

  defp validate_birthdate(changeset) do
    if get_field(changeset, :birthdate) do
      # Exemplo: verifique se a data de nascimento indica que o usuário tem pelo menos 18 anos
      if Date.diff(Date.utc_today(), get_field(changeset, :birthdate)) < 6574 do
        add_error(changeset, :birthdate, "User must be at least 18 years old.")
      else
        changeset
      end
    else
      changeset
    end
  end
end
