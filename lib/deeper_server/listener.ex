defmodule DeeperServer.Listener do
  use Ecto.Schema
  import Ecto.Changeset


  schema "listeners" do
    field :name, :string
    field :port, :integer
    field :protocol_module, :string
    field :ssl, :boolean
    field :certfile, :string
    field :keyfile, :string

    timestamps()
  end

  @doc false
  def changeset(listener, attrs) do
    listener
    |> cast(attrs, [:name, :port, :protocol_module, :ssl, :certfile, :keyfile])
    |> validate_required([:name, :port, :protocol_module, :ssl])
  end
end
