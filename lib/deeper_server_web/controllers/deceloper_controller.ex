defmodule DeeperServerWeb.DeveloperController do
  use DeeperServerWeb, :controller
  alias DeeperServer.Developer
  alias DeeperServer.Repo

  @spec index(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def index(conn, _params) do
    developers = Repo.all(Developer)
    json(conn, developers)
  end

  @spec create(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def create(conn, params) do
    params = Map.take(params, [:name, :email, :skills]) # Ajuste conforme os campos do seu Developer

    changeset = Developer.changeset(%Developer{}, params)

    case Repo.insert(changeset) do
      {:ok, developer} ->
        conn
        |> put_status(:created)
        |> json(%{status: "success", developer: developer})

      {:error, changeset} ->
        conn
        |> put_status(:unprocessable_entity)
        |> json(%{status: "error", errors: changeset.errors})
    end
  end

  @spec show(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def show(conn, %{"id" => id}) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{status: "error", message: "Developer not found"})

      developer ->
        json(conn, %{status: "success", developer: developer})
    end
  end

  @spec update(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def update(conn, %{"id" => id} = params) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{status: "error", message: "Developer not found"})

      developer ->
        changeset = Developer.changeset(developer, params)

        case Repo.update(changeset) do
          {:ok, updated_developer} ->
            json(conn, %{status: "success", developer: updated_developer})

          {:error, changeset} ->
            conn
            |> put_status(:unprocessable_entity)
            |> json(%{status: "error", errors: changeset.errors})
        end
    end
  end

  @spec delete(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def delete(conn, %{"id" => id}) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{status: "error", message: "Developer not found"})

      developer ->
        case Repo.delete(developer) do
          {:ok, _} ->
            conn
            |> put_status(:no_content)
            |> json(%{status: "success", message: "Developer deleted successfully"})

          {:error, _} ->
            conn
            |> put_status(:internal_server_error)
            |> json(%{status: "error", message: "Failed to delete developer"})
        end
    end
  end

  @spec fetch_by_id(any()) :: Developer.t() | nil
  defp fetch_by_id(id) do
    Repo.get(Developer, id)
  end
end
