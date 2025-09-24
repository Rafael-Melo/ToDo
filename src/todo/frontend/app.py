import flet as ft
import httpx

API_URL = "http://127.0.0.1:8000"

class ToDoApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "ToDo App"
        self.page.scroll = ft.ScrollMode.ALWAYS
        self.token = None  # JWT token
        self.tasks = []

        self.login_view()

    # ---------------- LOGIN / SIGNUP ----------------
    def login_view(self):
        self.username = ft.TextField(label="Username", expand=True)
        self.password = ft.TextField(label="Password", password=True, can_reveal_password=True, expand=True)
        self.message = ft.Text("", color=ft.Colors.RED)

        login_btn = ft.ElevatedButton("Login", on_click=self.login)
        signup_btn = ft.ElevatedButton("Criar Conta", on_click=self.signup)

        self.page.controls.clear()
        self.page.add(
            ft.Column(
                controls=[
                    self.username,
                    self.password,
                    ft.Row([login_btn, signup_btn], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                    self.message
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            )
        )
        self.page.update()

    async def api_post(self, endpoint, data):
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_URL}{endpoint}", json=data) if endpoint.endswith("/signup") else await client.post(f"{API_URL}{endpoint}", data=data)
            return response

    def login(self, e):
        username = self.username.value.strip()
        password = self.password.value.strip()
        if not username or not password:
            self.message.value = "Preencha todos os campos!"
            self.page.update()
            return

        try:
            response = httpx.post(f"{API_URL}/auth/login", data={"username": username, "password": password})
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.todo_view()
            else:
                self.message.value = "Usuário ou senha incorretos."
                self.page.update()
        except Exception as ex:
            self.message.value = f"Erro de conexão: {ex}"
            self.page.update()

    def signup(self, e):
        username = self.username.value.strip()
        password = self.password.value.strip()
        if not username or not password:
            self.message.value = "Preencha todos os campos!"
            self.page.update()
            return

        try:
            response = httpx.post(f"{API_URL}/auth/signup", json={"username": username, "password": password})
            if response.status_code == 200:
                self.message.value = "Conta criada! Faça login."
            else:
                self.message.value = f"Erro: {response.json().get('detail')}"
            self.page.update()
        except Exception as ex:
            self.message.value = f"Erro de conexão: {ex}"
            self.page.update()

    # ---------------- TODO VIEW ----------------
    def todo_view(self):
        self.task_input = ft.TextField(hint_text="Nova tarefa", expand=True)
        add_btn = ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=self.add_task)
        self.tasks_container = ft.Column()

        self.page.controls.clear()
        self.page.add(
            ft.Column(
                controls=[
                    ft.Row([self.task_input, add_btn], spacing=10),
                    self.tasks_container
                ],
                expand=True
            )
        )
        self.refresh_tasks()

    def refresh_tasks(self):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = httpx.get(f"{API_URL}/tasks/", headers=headers)
            if response.status_code == 200:
                self.tasks = response.json()
                self.update_tasks_ui()
        except Exception as ex:
            self.tasks_container.controls.clear()
            self.tasks_container.controls.append(ft.Text(f"Erro ao buscar tasks: {ex}", color=ft.Colors.RED))
            self.page.update()

    def update_tasks_ui(self):
        self.tasks_container.controls.clear()
        headers = {"Authorization": f"Bearer {self.token}"}

        for t in self.tasks:
            cb = ft.Checkbox(
                label=t["name"],
                value=t["status"] == "complete",
                on_change=lambda e, task=t: self.toggle_status(e, task)
            )
            del_btn = ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color=ft.Colors.RED,
                on_click=lambda e, task_id=t["id"]: self.delete_task(task_id)
            )
            self.tasks_container.controls.append(ft.Row([cb, del_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

        self.page.update()

    def add_task(self, e):
        name = self.task_input.value.strip()
        if not name:
            return
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = httpx.post(f"{API_URL}/tasks/", json={"name": name}, headers=headers)
            if response.status_code == 200:
                self.task_input.value = ""
                self.refresh_tasks()
        except Exception as ex:
            print(f"Erro ao adicionar task: {ex}")

    def delete_task(self, task_id):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = httpx.delete(f"{API_URL}/tasks/{task_id}", headers=headers)
            if response.status_code == 200:
                self.refresh_tasks()
        except Exception as ex:
            print(f"Erro ao deletar task: {ex}")

    def toggle_status(self, e, task):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            new_status = "complete" if e.control.value else "incomplete"
            response = httpx.put(f"{API_URL}/tasks/{task['id']}", json={"status": new_status}, headers=headers)
            if response.status_code == 200:
                self.refresh_tasks()
        except Exception as ex:
            print(f"Erro ao atualizar task: {ex}")


def main(page: ft.Page):
    ToDoApp(page)

ft.app(target=main, view=ft.WEB_BROWSER)

