defmodule DeeperServerWeb.PackageDependencyController do
  use DeeperServerWeb, :controller
  alias DeeperServer.PackageDependency
  alias DeeperServer.Repo

  @spec index(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def index(conn, _params) do
    package_dependencies = Repo.all(PackageDependency)
    json(conn, %{status: "success", package_dependencies: package_dependencies})
  end

  @spec create(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def create(conn, params) do
    params = Map.take(params, [:package_id, :dependency_id]) # Ajuste conforme os campos do seu PackageDependency

    changeset = PackageDependency.changeset(%PackageDependency{}, params)

    case Repo.insert(changeset) do
      {:ok, package_dependency} ->
        conn
        |> put_status(:created)
        |> json(%{status: "success", package_dependency: package_dependency})

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
        |> json(%{status: "error", message: "PackageDependency not found"})

      package_dependency ->
        json(conn, %{status: "success", package_dependency: package_dependency})
    end
  end

  @spec update(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def update(conn, %{"id" => id} = params) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{status: "error", message: "PackageDependency not found"})

      package_dependency ->
        changeset = PackageDependency.changeset(package_dependency, params)

        case Repo.update(changeset) do
          {:ok, updated_package_dependency} ->
            json(conn, %{status: "success", package_dependency: updated_package_dependency})

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
        |> json(%{status: "error", message: "PackageDependency not found"})

      package_dependency ->
        case Repo.delete(package_dependency) do
          {:ok, _} ->
            conn
            |> put_status(:no_content)
            |> json(%{status: "success", message: "PackageDependency deleted successfully"})

          {:error, _} ->
            conn
            |> put_status(:internal_server_error)
            |> json(%{status: "error", message: "Failed to delete PackageDependency"})
        end
    end
  end

  @spec fetch_by_id(any()) :: PackageDependency.t() | nil
  defp fetch_by_id(id) do
    Repo.get(PackageDependency, id)
  end
end
