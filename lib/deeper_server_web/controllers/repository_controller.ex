defmodule DeeperServerWeb.RepositoryController do
  use DeeperServerWeb, :controller
  alias DeeperServer.Repository
  alias DeeperServer.Repo

  @doc """
  Lista todos os repositórios.

  Retorna uma lista de repositórios em formato JSON.
  """
  @spec index(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def index(conn, _params) do
    repositories = Repo.all(Repository)
    json(conn, repositories)
  end

  @doc """
  Cria um novo repositório.

  Recebe os parâmetros do repositório e tenta inseri-lo no banco de dados.
  Retorna o repositório criado ou uma mensagem de erro.
  """
  @spec create(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def create(conn, params) do
    changeset = Repository.changeset(%Repository{}, params)

    case Repo.insert(changeset) do
      {:ok, repository} ->
        conn
        |> put_status(:created)
        |> json(repository)

      {:error, changeset} ->
        conn
        |> put_status(:unprocessable_entity)
        |> json(%{errors: changeset.errors})
    end
  end

  @doc """
  Mostra um repositório específico pelo ID.

  Retorna o repositório encontrado ou uma mensagem de erro se não for encontrado.
  """
  @spec show(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def show(conn, %{"id" => id}) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "Repository not found"})

      repository ->
        json(conn, repository)
    end
  end

  @doc """
  Atualiza um repositório existente.

  Recebe os novos parâmetros e atualiza o repositório correspondente.
  Retorna o repositório atualizado ou uma mensagem de erro.
  """
  @spec update(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def update(conn, %{"id" => id} = params) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "Repository not found"})

      repository ->
        changeset = Repository.changeset(repository, params)

        case Repo.update(changeset) do
          {:ok, updated_repository} ->
            json(conn, updated_repository)

          {:error, changeset} ->
            conn
            |> put_status(:unprocessable_entity)
            |> json(%{errors: changeset.errors})
        end
    end
  end

  @doc """
  Deleta um repositório existente pelo ID.

  Retorna uma mensagem de confirmação ou um erro se o repositório não for encontrado.
  """
  @spec delete(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def delete(conn, %{"id" => id}) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "Repository not found"})

      repository ->
        case Repo.delete(repository) do
          {:ok, _} ->
            conn
            |> put_status(:no_content)
            |> json(%{message: "Repository deleted successfully"})

          {:error, _} ->
            conn
            |> put_status(:unprocessable_entity)
            |> json(%{error: "Failed to delete repository"})
        end
    end
  end

  @spec fetch_by_id(String.t()) :: Repository.t() | nil
  defp fetch_by_id(id) do
    Repo.get(Repository, id)
  end
end
