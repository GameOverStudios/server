defmodule DeeperServerWeb.PackageController do
  use DeeperServerWeb, :controller
  alias DeeperServer.Package
  alias DeeperServer.Repo

  @spec index(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def index(conn, _params) do
    packages = Repo.all(Package)
    json(conn, %{status: "success", packages: packages})
  end

  @spec create(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def create(conn, params) do
    params = Map.take(params, [:name, :description, :version]) # Ajuste conforme os campos do seu Package

    changeset = Package.changeset(%Package{}, params)

    case Repo.insert(changeset) do
      {:ok, package} ->
        conn
        |> put_status(:created)
        |> json(%{status: "success", package: package})

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
        |> json(%{status: "error", message: "Package not found"})

      package ->
        json(conn, %{status: "success", package: package})
    end
  end

  @spec update(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def update(conn, %{"id" => id} = params) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{status: "error", message: "Package not found"})

      package ->
        changeset = Package.changeset(package, params)

        case Repo.update(changeset) do
          {:ok, updated_package} ->
            json(conn, %{status: "success", package: updated_package})

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
        |> json(%{status: "error", message: "Package not found"})

      package ->
        case Repo.delete(package) do
          {:ok, _} ->
            conn
            |> put_status(:no_content)
            |> json(%{status: "success", message: "Package deleted successfully"})

          {:error, _} ->
            conn
            |> put_status(:internal_server_error)
            |> json(%{status: "error", message: "Failed to delete package"})
        end
    end
  end

  @spec fetch_by_id(any()) :: Package.t() | nil
  defp fetch_by_id(id) do
    Repo.get(Package, id)
  end
end
