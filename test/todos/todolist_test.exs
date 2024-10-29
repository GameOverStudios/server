defmodule Todos.TodolistTest do
  use Todos.DataCase
  alias Todos.Todolist

  describe "todos" do
    import Todos.TodolistFixtures

    test "list_todos/0 returns all todos" do
      todo = todo_fixture()
      assert Todolist.list_todos() == [todo]
    end

    test "create_todo/1 with invalid data returns error changeset" do
      invalid_attrs = %{done: nil, title: nil}
      assert {:error, %Ecto.Changeset{}} = Todolist.create_todo(invalid_attrs)
    end
  end
end
