defmodule DeeperServer.Protocols.EchoSSL do
  @behaviour :ranch_protocol
  @timeout 5000

  require Logger

  def start_link(ref, transport, opts, _protocol_opts) do
    {:ok, spawn_link(__MODULE__, :init, [ref, transport, opts])}
  end

  def init(ref, transport, _opts) do
    {:ok, socket} = :ranch.handshake(ref)
    loop(socket, transport)
  end

  defp loop(socket, transport) do
    case transport.recv(socket, 0, @timeout) do
      {:ok, data} ->
        transport.send(socket, data)
        loop(socket, transport)
      {:error, :closed} ->
        Logger.info("Conexão SSL fechada.")
        :ok
      {:error, reason} ->
        Logger.error("Erro na conexão SSL: #{inspect(reason)}")
        :error
    end
  end
end
