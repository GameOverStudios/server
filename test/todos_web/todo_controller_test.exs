defmodule TodosWeb.TodoControllerTest do
  use TodosWeb.ConnCase

  import Todos.TodolistFixtures

  setup %{conn: conn} do
    {:ok, conn: put_req_header(conn, "accept", "application/json")}
  end

  describe "index" do
    test "lists all todos (empty)", %{conn: conn} do
      conn = get(conn, ~p"/api/todos")
      assert json_response(conn, 200) == []
    end
  end

  describe "index with setup" do
    setup [:setup_todo]

    test "lists all todos (setup)", %{conn: conn, todo: todo} do
      conn = get(conn, ~p"/api/todos")
      expected_todo = %{"id" => todo.id, "title" => todo.title, "done" => todo.done}
      assert [^expected_todo] = json_response(conn, 200)
    end
  end

  describe "create todo" do
    test "responds with a todo when data is valid", %{conn: conn} do
      # given
      attrs = %{title: "Walk the dog.", done: false}

      # when
      conn = post(conn, ~p"/api/todos", todo: attrs)

      # then
      assert %{"id" => id} = json_response(conn, 201)
      conn = get(conn, ~p"/api/todos/#{id}")

      assert %{"id" => ^id, "done" => false, "title" => "Walk the dog."} =
               json_response(conn, 200)
    end
  end

  defp setup_todo(_) do
    todo = todo_fixture()
    %{todo: todo}
  end
end
