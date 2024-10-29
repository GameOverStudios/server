defmodule DeeperServer.ListenerSupervisor do
  use Supervisor

  alias DeeperServer.Repo
  alias DeeperServer.Listener

  require Logger

  def start_link(args) do
    Supervisor.start_link(__MODULE__, args, name: __MODULE__)
  end

  def init(_) do
    children = create_listeners_from_db()
    Supervisor.init(children, strategy: :one_for_one)
  end

  defp create_listeners_from_db() do
    Repo.all(Listener)
    |> Enum.map(&create_listener_child_spec/1)
  end

  defp create_listener_child_spec(listener) do
    name = String.to_atom(listener.name)
    protocol_module_string = listener.protocol_module

    try do
      protocol_module = String.to_existing_atom(protocol_module_string)

      opts = [port: listener.port]
      transport =
        if listener.ssl do
          opts = Keyword.merge(opts, certfile: listener.certfile, keyfile: listener.keyfile)
          :ranch_ssl
        else
          :ranch_tcp
        end

      # Retorna apenas o child_spec do Ranch
      :ranch.child_spec(name, transport, opts, protocol_module, [])

    rescue
      ArgumentError ->
        Logger.error("Módulo de protocolo inválido: #{protocol_module_string}")
        IO.puts("Módulo de protocolo inválido: #{protocol_module_string}") # Mostrar no console
        {:error, :invalid_protocol_module}
    end
  end

  # Adicione estas funções para iniciar/parar dinamicamente e registrar eventos de log
  def start_listener(listener_data) do
    spec = create_listener_child_spec(listener_data)
    case Supervisor.start_child(__MODULE__, spec) do
      {:ok, pid} ->
        Logger.info("Listener iniciado com sucesso: #{inspect(pid)}")
        IO.puts("Listener iniciado com sucesso: #{inspect(pid)}") # Mostrar no console
      {:error, reason} ->
        Logger.error("Falha ao iniciar listener: #{inspect(reason)}")
        IO.puts("Falha ao iniciar listener: #{inspect(reason)}") # Mostrar no console
    end
  end

  def stop_listener(listener_name) do
    case Supervisor.terminate_child(__MODULE__, String.to_atom(listener_name)) do
      :ok ->
        Logger.info("Listener #{listener_name} parado com sucesso.")
        IO.puts("Listener #{listener_name} parado com sucesso.") # Mostrar no console
      {:error, reason} ->
        Logger.error("Falha ao parar listener #{listener_name}: #{inspect(reason)}")
        IO.puts("Falha ao parar listener #{listener_name}: #{inspect(reason)}") # Mostrar no console
    end
  end
end
