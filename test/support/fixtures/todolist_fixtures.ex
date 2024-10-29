defmodule Todos.TodolistFixtures do
  @defaults %{done: false, title: "Walk the dog."}

  def todo_fixture(attrs \\ %{}) do
    {:ok, todo} =
        attrs
        |> Enum.into(@defaults)
        |> Todos.Todolist.create_todo()

    todo
  end
end
