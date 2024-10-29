alias DeeperServer.Repo
alias DeeperServer.Listener

# Exemplos de listeners (ajuste portas e protocolos conforme necessário)
listeners = [
  %{name: "listener_tcp_1", port: 5555, protocol_module: :DeeperServer.Protocols.Echo, ssl: false}, # Átomo com dois pontos
  %{name: "listener_ssl_1", port: 5556, protocol_module: :DeeperServer.Protocols.EchoSSL, ssl: true, certfile: "cert.pem", keyfile: "key.pem"} # Átomo com dois pontos
  # Adicione mais listeners aqui...
]

Enum.each(listeners, fn listener ->
  # Verifica se o listener já existe antes de inseri-lo (para evitar erros)
  case Repo.get_by(Listener, name: listener.name) do
    nil ->
      changeset = Listener.changeset(%Listener{}, listener) # Cria o changeset a partir do schema

      case Repo.insert(changeset) do
        {:ok, _listener} -> IO.puts("Listener #{listener.name} criado com sucesso.")
        {:error, changeset} -> IO.puts("Erro ao criar listener #{listener.name}: #{inspect(changeset.errors)}")
      end
    _existing_listener -> IO.puts("Listener #{listener.name} já existe. Pulando.")
  end
end)
