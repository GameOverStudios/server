# priv/repo/seeds.exs

alias DeeperServer.Repo
alias DeeperServer.Package

Repo.insert!(%Package{
  id: 1,
  name: "TestPackage",
  version: "1.0.0",
  hash_package: "hash_package",
  hash_metadata: "hash_metadata",
  public_key: "public_key",
  signature: "signature",
  created_at: NaiveDateTime.utc_now(),
  updated_at: NaiveDateTime.utc_now()
})

# Adicione os outros pacotes da mesma maneira...
