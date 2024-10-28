defmodule DeeperServerWeb.UserController do
  use DeeperServerWeb, :controller
  alias DeeperServer.{Repo, User}

  @doc """
  Lista todos os usuários.

  Retorna uma lista de usuários em formato JSON.
  """
  @spec index(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def index(conn, _params) do
    users = Repo.all(User)
    json(conn, users)
  end

  @doc """
  Cria um novo usuário.

  Recebe os parâmetros do usuário e tenta inseri-lo no banco de dados.
  Retorna o usuário criado ou uma mensagem de erro.
  """
  @spec create(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def create(conn, params) do
    changeset = User.changeset(%User{}, params)

    case Repo.insert(changeset) do
      {:ok, user} ->
        conn
        |> put_status(:created)
        |> json(user)

      {:error, changeset} ->
        conn
        |> put_status(:unprocessable_entity)
        |> json(%{errors: changeset.errors})
    end
  end

  @doc """
  Mostra um usuário específico pelo ID.

  Retorna o usuário encontrado ou uma mensagem de erro se não for encontrado.
  """
  @spec show(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def show(conn, %{"id" => id}) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "User not found"})

      user ->
        json(conn, user)
    end
  end

  @doc """
  Atualiza um usuário existente.

  Recebe os novos parâmetros e atualiza o usuário correspondente.
  Retorna o usuário atualizado ou uma mensagem de erro.
  """
  @spec update(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def update(conn, %{"id" => id} = params) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "User not found"})

      user ->
        changeset = User.changeset(user, params)

        case Repo.update(changeset) do
          {:ok, updated_user} ->
            json(conn, updated_user)

          {:error, changeset} ->
            conn
            |> put_status(:unprocessable_entity)
            |> json(%{errors: changeset.errors})
        end
    end
  end

  @doc """
  Deleta um usuário existente pelo ID.

  Retorna uma mensagem de confirmação ou um erro se o usuário não for encontrado.
  """
  @spec delete(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def delete(conn, %{"id" => id}) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "User not found"})

      user ->
        Repo.delete(user)
        conn
        |> put_status(:no_content)
        |> json(%{message: "User deleted successfully"})
    end
  end

  @spec fetch_by_id(any()) :: User.t() | nil
  defp fetch_by_id(id) do
    Repo.get(User, id)
  end
end
