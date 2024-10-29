defmodule TodosWeb.TodoController do
  use TodosWeb, :controller

  alias TodosWeb.FallbackController
  alias Todos.Todolist

  action_fallback FallbackController

  def index(conn, _params) do
    todos = Todolist.list_todos()
    render(conn, :index, todos: todos)
  end

  def show(conn, %{"id" => id}) do
    todo = Todolist.get_todo!(id)
    render(conn, :show, todo: todo)
  end

  def create(conn, %{"todo" => todo_params} = params) do
    IO.inspect(params)
    with {:ok, todo} <- Todolist.create_todo(todo_params) do
      conn
      |> put_status(:created)
      |> put_resp_header("location", ~p"/api/todos/#{todo}")
      |> render(:show, todo: todo)
    end
  end

  def update(conn, %{"id" => id, "todo" => todo_params}) do
    todo = Todolist.get_todo!(id)

    with {:ok, %Todolist.Todo{} = todo} <- Todolist.update_todo(todo, todo_params) do
      render(conn, :show, todo: todo)
    end
  end

  def delete(conn, %{"id" => id}) do
    todo = Todolist.get_todo!(id)

    with {:ok, %Todolist.Todo{}} <- Todolist.delete_todo(todo) do
      send_resp(conn, :no_content, "")
    end
  end
end
