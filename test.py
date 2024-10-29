import requests

BASE_URL = "http://localhost:4000/api/todos"

def list_todos():
    response = requests.get(BASE_URL)
    return response.json()

def create_todo(name):
    response = requests.post(BASE_URL, json={"todo": {"title": name}})
    return response.json()

def update_todo(todo_id, name):
    response = requests.put(f"{BASE_URL}/{todo_id}", json={"todo": {"title": name}})
    return response.json()

def delete_todo(todo_id):
    response = requests.delete(f"{BASE_URL}/{todo_id}")
    return response.status_code

if __name__ == "__main__":
    # Listar todos
    print("Lista de Todos:", list_todos())

    # Adicionar um novo todo
    new_todo = create_todo("Novo Todo")
    print("Todo criado:", new_todo)

    # Atualizar um todo existente
    updated_todo = update_todo(new_todo['id'], "Todo Atualizado")
    print("Todo atualizado:", updated_todo)

    # Excluir um todo
    status_code = delete_todo(new_todo['id'])
    print("Status da exclusão:", status_code)