defmodule DeeperServer.Repo do
  use Ecto.Repo,
    otp_app: :deeper_server,
    adapter: Ecto.Adapters.SQLite3
end
