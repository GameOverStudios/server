defmodule DeeperServerWeb.Router do
  use DeeperServerWeb, :router

  pipeline :browser do
    plug :accepts, ["html"]
    plug :fetch_session
    plug :fetch_live_flash
    plug :put_root_layout, html: {DeeperServerWeb.Layouts, :root}
    plug :protect_from_forgery
    plug :put_secure_browser_headers
  end

  pipeline :api do
    plug :accepts, ["json"]
  end

  scope "/", DeeperServerWeb do
    pipe_through :browser

    get "/", PageController, :home
  end

  scope "/api", DeeperServerWeb do
    pipe_through :api

    # Rotas para Developers
    resources "/developers", DeveloperController

    # Rotas para Package Dependencies
    resources "/package_dependencies", PackageDependencyController

    # Rotas para Package Repositories
    resources "/package_repositories", PackageRepositoryController

    # Rotas para Packages
    resources "/packages", PackageController

    # Rotas para Ratings
    resources "/ratings", RatingController

    # Rotas para Repositories
    resources "/repositories", RepositoryController

    # Rotas para User Repository Invites
    resources "/user_repository_invites", UserRepositoryInviteController

    # Rotas para Users
    resources "/users", UserController
  end

  # Enable LiveDashboard and Swoosh mailbox preview in development
  if Application.compile_env(:deeper_server, :dev_routes) do
    # If you want to use the LiveDashboard in production, you should put
    # it behind authentication and allow only admins to access it.
    # If your application does not have an admins-only section yet,
    # you can use Plug.BasicAuth to set up some basic authentication
    # as long as you are also using SSL (which you should anyway).
    import Phoenix.LiveDashboard.Router

    scope "/dev" do
      pipe_through :browser

      live_dashboard "/dashboard", metrics: DeeperServerWeb.Telemetry
      forward "/mailbox", Plug.Swoosh.MailboxPreview
    end
  end
end
