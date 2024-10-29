defmodule TodosWeb.Router do
  use TodosWeb, :router

  pipeline :api do
    plug :accepts, ["json"]
  end

  scope "/api", TodosWeb do
    pipe_through :api

    get "/todos", TodoController, :index
    get "/todos/:id", TodoController, :show
    post "/todos", TodoController, :create
    put "/todos/:id", TodoController, :update
    delete "/todos/:id", TodoController, :delete
  end

  # Enable LiveDashboard in development
  if Application.compile_env(:todos, :dev_routes) do
    # If you want to use the LiveDashboard in production, you should put
    # it behind authentication and allow only admins to access it.
    # If your application does not have an admins-only section yet,
    # you can use Plug.BasicAuth to set up some basic authentication
    # as long as you are also using SSL (which you should anyway).
    import Phoenix.LiveDashboard.Router

    scope "/dev" do
      pipe_through [:fetch_session, :protect_from_forgery]

      live_dashboard "/dashboard", metrics: TodosWeb.Telemetry
    end
  end
end
