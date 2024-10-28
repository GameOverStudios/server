defmodule DeeperServerWeb.PageController do
  use DeeperServerWeb, :controller

  @doc """
  Renderiza a página inicial da aplicação.

  A página inicial geralmente é personalizada, portanto, não usa o layout padrão.
  """
  def home(conn, _params) do
    render(conn, :home, layout: false)
  end

  # Se você quiser adicionar uma resposta JSON para um endpoint futuro, considere isso:
  # def api_home(conn, _params) do
  #   json(conn, %{message: "Welcome to the API!"})
  # end
end
