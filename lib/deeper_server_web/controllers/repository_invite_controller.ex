defmodule DeeperServerWeb.UserRepositoryInviteController do
  use DeeperServerWeb, :controller
  alias DeeperServer.{Repo, UserRepositoryInvite}

  @doc """
  Lista todos os convites de repositórios de usuários.

  Retorna uma lista de convites em formato JSON.
  """
  @spec index(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def index(conn, _params) do
    user_repository_invites = Repo.all(UserRepositoryInvite)
    json(conn, user_repository_invites)
  end

  @doc """
  Cria um novo convite para repositório de usuário.

  Recebe os parâmetros do convite e tenta inseri-lo no banco de dados.
  Retorna o convite criado ou uma mensagem de erro.
  """
  @spec create(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def create(conn, params) do
    changeset = UserRepositoryInvite.changeset(%UserRepositoryInvite{}, params)

    case Repo.insert(changeset) do
      {:ok, user_repository_invite} ->
        conn
        |> put_status(:created)
        |> json(user_repository_invite)

      {:error, changeset} ->
        conn
        |> put_status(:unprocessable_entity)
        |> json(%{errors: changeset.errors})
    end
  end

  @doc """
  Mostra um convite de repositório de usuário específico pelo ID.

  Retorna o convite encontrado ou uma mensagem de erro se não for encontrado.
  """
  @spec show(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def show(conn, %{"id" => id}) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "UserRepositoryInvite not found"})

      user_repository_invite ->
        json(conn, user_repository_invite)
    end
  end

  @doc """
  Atualiza um convite de repositório de usuário existente.

  Recebe os novos parâmetros e atualiza o convite correspondente.
  Retorna o convite atualizado ou uma mensagem de erro.
  """
  @spec update(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def update(conn, %{"id" => id} = params) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "UserRepositoryInvite not found"})

      user_repository_invite ->
        changeset = UserRepositoryInvite.changeset(user_repository_invite, params)

        case Repo.update(changeset) do
          {:ok, updated_invite} ->
            json(conn, updated_invite)

          {:error, changeset} ->
            conn
            |> put_status(:unprocessable_entity)
            |> json(%{errors: changeset.errors})
        end
    end
  end

  @doc """
  Deleta um convite de repositório de usuário existente pelo ID.

  Retorna uma mensagem de confirmação ou um erro se o convite não for encontrado.
  """
  @spec delete(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def delete(conn, %{"id" => id}) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "UserRepositoryInvite not found"})

      user_repository_invite ->
        Repo.delete(user_repository_invite)
        conn
        |> put_status(:no_content)
        |> json(%{message: "UserRepositoryInvite deleted successfully"})
    end
  end

  @spec fetch_by_id(any()) :: UserRepositoryInvite.t() | nil
  defp fetch_by_id(id) do
    Repo.get(UserRepositoryInvite, id)
  end
end
