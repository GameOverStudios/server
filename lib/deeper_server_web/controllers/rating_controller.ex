defmodule DeeperServerWeb.RatingController do
  use DeeperServerWeb, :controller
  alias DeeperServer.Rating
  alias DeeperServer.Repo

  @doc """
  Lista todos os ratings.

  Retorna uma lista de ratings em formato JSON.
  """
  @spec index(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def index(conn, _params) do
    ratings = Repo.all(Rating)
    json(conn, ratings)
  end

  @doc """
  Cria um novo rating.

  Recebe os parâmetros do rating e tenta inseri-lo no banco de dados.
  Retorna o rating criado ou uma mensagem de erro.
  """
  @spec create(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def create(conn, params) do
    changeset = Rating.changeset(%Rating{}, params)

    case Repo.insert(changeset) do
      {:ok, rating} ->
        conn
        |> put_status(:created)
        |> json(rating)

      {:error, changeset} ->
        conn
        |> put_status(:unprocessable_entity)
        |> json(%{errors: changeset.errors})
    end
  end

  @doc """
  Mostra um rating específico pelo ID.

  Retorna o rating encontrado ou uma mensagem de erro se não for encontrado.
  """
  @spec show(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def show(conn, %{"id" => id}) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "Rating not found"})

      rating ->
        json(conn, rating)
    end
  end

  @doc """
  Atualiza um rating existente.

  Recebe os novos parâmetros e atualiza o rating correspondente.
  Retorna o rating atualizado ou uma mensagem de erro.
  """
  @spec update(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def update(conn, %{"id" => id} = params) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "Rating not found"})

      rating ->
        changeset = Rating.changeset(rating, params)

        case Repo.update(changeset) do
          {:ok, updated_rating} ->
            json(conn, updated_rating)

          {:error, changeset} ->
            conn
            |> put_status(:unprocessable_entity)
            |> json(%{errors: changeset.errors})
        end
    end
  end

  @doc """
  Deleta um rating existente pelo ID.

  Retorna uma mensagem de confirmação ou um erro se o rating não for encontrado.
  """
  @spec delete(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def delete(conn, %{"id" => id}) do
    case fetch_by_id(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{error: "Rating not found"})

      rating ->
        Repo.delete(rating)
        conn
        |> put_status(:no_content)
        |> json(%{message: "Rating deleted successfully"})
    end
  end

  @spec fetch_by_id(any()) :: Rating.t() | nil
  defp fetch_by_id(id) do
    Repo.get(Rating, id)
  end
end
