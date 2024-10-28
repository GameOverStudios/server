defmodule DeeperServerWeb.CommentController do
  use DeeperServerWeb, :controller
  alias DeeperServer.Comment
  alias DeeperServer.Repo

  @spec index(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def index(conn, _params) do
    comments = Repo.all(Comment)
    json(conn, comments)
  end

  @spec create(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def create(conn, params) do
    params = Map.take(params, [:content, :post_id]) # Ajuste conforme os campos do seu Comment

    changeset = Comment.changeset(%Comment{}, params)

    case Repo.insert(changeset) do
      {:ok, comment} ->
        conn
        |> put_status(:created)
        |> json(%{status: "success", comment: comment})

      {:error, changeset} ->
        conn
        |> put_status(:unprocessable_entity)
        |> json(%{status: "error", errors: changeset.errors})
    end
  end

  @spec show(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def show(conn, %{"id" => id}) do
    case fetch_comment(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{status: "error", message: "Comment not found"})

      comment ->
        json(conn, %{status: "success", comment: comment})
    end
  end

  @spec update(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def update(conn, %{"id" => id} = params) do
    case fetch_comment(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{status: "error", message: "Comment not found"})

      comment ->
        changeset = Comment.changeset(comment, params)

        case Repo.update(changeset) do
          {:ok, updated_comment} ->
            json(conn, %{status: "success", comment: updated_comment})

          {:error, changeset} ->
            conn
            |> put_status(:unprocessable_entity)
            |> json(%{status: "error", errors: changeset.errors})
        end
    end
  end

  @spec delete(Plug.Conn.t(), map()) :: Plug.Conn.t()
  def delete(conn, %{"id" => id}) do
    case fetch_comment(id) do
      nil ->
        conn
        |> put_status(:not_found)
        |> json(%{status: "error", message: "Comment not found"})

      comment ->
        case Repo.delete(comment) do
          {:ok, _} ->
            conn
            |> put_status(:no_content)
            |> json(%{status: "success", message: "Comment deleted successfully"})

          {:error, _} ->
            conn
            |> put_status(:internal_server_error)
            |> json(%{status: "error", message: "Failed to delete comment"})
        end
    end
  end

  @spec fetch_comment(any()) :: Comment.t() | nil
  defp fetch_comment(id) do
    Repo.get(Comment, id)
  end
end
