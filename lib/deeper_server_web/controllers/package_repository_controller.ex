defmodule DeeperServerWeb.PackageRepositoryController do
  use DeeperServerWeb, :controller
  alias DeeperServer.PackageRepository
  alias DeeperServer.Repo

  @spec index(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def index(conn, _params) do
    repositories = Repo.all(Repository)
    json(conn, %{status: "success", repositories: repositories})
  end

  @spec create(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def create(conn, params) do
    params = Map.take(params, [:repository_id, :package_id]) # Ajuste conforme os campos do seu PackageRepository

    changeset = PackageRepository.changeset(%PackageRepository{}, params)

    case Repo.insert(changeset) do
      {:ok, package_repository} ->
        conn
        |> put_status(:created)
        |> json(%{status: "success", package_repository: package_repository})

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
        |> json(%{status: "error", message: "PackageRepository not found"})

      package_repository ->
        json(conn, %{status: "success", package_repository: package_repository})
    end
  end

  @spec update(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def update(conn, %{"id" => id} = params) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{status: "error", message: "PackageRepository not found"})

      package_repository ->
        changeset = PackageRepository.changeset(package_repository, params)

        case Repo.update(changeset) do
          {:ok, updated_package_repository} ->
            json(conn, %{status: "success", package_repository: updated_package_repository})

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
        |> json(%{status: "error", message: "PackageRepository not found"})

      package_repository ->
        case Repo.delete(package_repository) do
          {:ok, _} ->
            conn
            |> put_status(:no_content)
            |> json(%{status: "success", message: "PackageRepository deleted successfully"})

          {:error, _} ->
            conn
            |> put_status(:internal_server_error)
            |> json(%{status: "error", message: "Failed to delete PackageRepository"})
        end
    end
  end

  @spec fetch_by_id(any()) :: PackageRepository.t() | nil
  defp fetch_by_id(id) do
    Repo.get(PackageRepository, id)
  end
end
