import flet as ft
import httpx

API_URL = "http://127.0.0.1:8000"

class ToDoApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "ToDo App"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO)
        self.page.scroll = ft.ScrollMode.ALWAYS
        self.token = None
        self.tasks = []

        self.login_view()

    # ---------------- LOGIN ----------------
    def login_view(self):
        self.logo = ft.Image(src="https://cdn-icons-png.flaticon.com/256/7590/7590241.png", width=250, height=250)
        self.username = ft.TextField(label="Username", expand=True)
        self.password = ft.TextField(label="Password", password=True, can_reveal_password=True, expand=True)
        self.message = ft.Text("", color=ft.Colors.RED)

        login_btn = ft.ElevatedButton(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.LOGIN),
                        ft.Text(value="Login", weight=ft.FontWeight.BOLD), 
                    ]
                ),
                margin=10,
            ),
            on_click=self.login  
        )

        signup_btn = ft.ElevatedButton(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.PERSON),
                        ft.Text(value="Criar Conta", weight=ft.FontWeight.BOLD),
                    ]
                ),
                margin=10,
            ),
            on_click=self.signup_popup
        )

        self.page.controls.clear()
        self.page.add(
            ft.Column(
                controls=[
                    self.logo,
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

    # ---------------- SIGNUP POPUP ----------------
    def signup_popup(self, e):
        self.signup_username = ft.TextField(label="Novo usuário")
        self.signup_password = ft.TextField(label="Senha", password=True, can_reveal_password=True)
        self.signup_message = ft.Text("", color=ft.Colors.RED)

        create_btn = ft.ElevatedButton("Criar", on_click=self.create_account)
        cancel_btn = ft.TextButton("Cancelar", on_click=lambda e: self.close_signup())

        self.signup_dialog = ft.AlertDialog(
            title=ft.Text("Criar Conta"),
            content=ft.Column([self.signup_username, self.signup_password, self.signup_message]),
            actions=[create_btn, cancel_btn]
        )

        self.page.dialog = self.signup_dialog
        self.signup_username.value = ""
        self.signup_password.value = ""
        self.signup_message.value = ""
        self.page.open(self.signup_dialog)

    def create_account(self, e):
        username = self.signup_username.value.strip()
        password = self.signup_password.value.strip()
        if not username or not password:
            self.signup_message.value = "Preencha todos os campos!"
            self.page.update()
            return

        try:
            response = httpx.post(f"{API_URL}/auth/signup", json={"username": username, "password": password})
            if response.status_code == 200:
                # login automático
                token_resp = httpx.post(
                    f"{API_URL}/auth/login",
                    data={"username": username, "password": password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if token_resp.status_code == 200:
                    self.token = token_resp.json()["access_token"]
                    self.close_signup()
                    self.load_todo_view()
                else:
                    self.signup_message.value = "Erro ao logar automaticamente"
            else:
                self.signup_message.value = f"Erro: {response.json().get('detail')}"
        except Exception as ex:
            self.signup_message.value = f"Erro de conexão: {ex}"
        self.page.update()

    def close_signup(self):
        self.page.dialog.open = False
        self.page.update()

    # ---------------- LOGIN ACTION ----------------
    def login(self, e):
        username = self.username.value.strip()
        password = self.password.value.strip()
        if not username or not password:
            self.message.value = "Preencha todos os campos!"
            self.page.update()
            return

        try:
            response = httpx.post(
                f"{API_URL}/auth/login",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.load_todo_view()
            else:
                self.message.value = "Usuário ou senha incorretos."
        except Exception as ex:
            self.message.value = f"Erro de conexão: {ex}"
        self.page.update()

    # ---------------- TODO VIEW ----------------
    def load_todo_view(self):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = httpx.get(f"{API_URL}/users/me", headers=headers)
            if resp.status_code == 200:
                username = resp.json().get("username", "Usuário")
            else:
                username = "Usuário"
        except Exception as ex:
            print(f"Erro ao buscar usuário: {ex}")
            username = "Usuário"

        user_name_text = ft.Text(
            value=f"Tarefas de, {username}!",
            weight=ft.FontWeight.BOLD,
            size=18
        )

        logout_btn = ft.IconButton(
            icon=ft.Icons.LOGOUT,
            icon_color=ft.Colors.RED,
            tooltip="Sair",
            on_click=self.logout
        )

        self.task_input = ft.TextField(hint_text="Nova tarefa", expand=True)
        add_btn = ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=ft.Colors.GREEN, on_click=self.add_task)
        self.tasks_container = ft.Column()

        self.tabs = ft.Tabs(
            selected_index=0,
            on_change=self.tabs_changed,
            tabs=[
                ft.Tab(text="Todas"),
                ft.Tab(text="Em andamento"),
                ft.Tab(text="Finalizadas"),
            ],
            expand=1
        )

        self.page.controls.clear()
        self.page.add(
            ft.Column(
                controls=[
                    ft.Row([user_name_text, logout_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([self.task_input, add_btn], spacing=10),
                    self.tabs,
                    self.tasks_container
                ],
                expand=True
            )
        )
        self.refresh_tasks()

    def tabs_changed(self, e):
        index = e.control.selected_index
        if index == 0:
            self.refresh_tasks()
        elif index == 1:
            self.refresh_tasks(status="incomplete")
        elif index == 2:
            self.refresh_tasks(status="complete")

    def refresh_tasks(self, status=None):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            params = {"status": status} if status else {}
            response = httpx.get(f"{API_URL}/tasks/", headers=headers, params=params)
            if response.status_code == 200:
                self.tasks = response.json()
                self.update_tasks_ui()

                # Atualiza contagem das abas
                all_resp = httpx.get(f"{API_URL}/tasks/", headers=headers)
                incomplete_resp = httpx.get(f"{API_URL}/tasks/", headers=headers, params={"status": "incomplete"})
                complete_resp = httpx.get(f"{API_URL}/tasks/", headers=headers, params={"status": "complete"})

                if all_resp.status_code == 200:
                    self.tabs.tabs[0].text = f"Todos ({len(all_resp.json())})"
                if incomplete_resp.status_code == 200:
                    self.tabs.tabs[1].text = f"Em andamento ({len(incomplete_resp.json())})"
                if complete_resp.status_code == 200:
                    self.tabs.tabs[2].text = f"Finalizados ({len(complete_resp.json())})"

                self.page.update()

        except Exception as ex:
            self.tasks_container.controls.clear()
            self.tasks_container.controls.append(ft.Text(f"Erro ao buscar tasks: {ex}", color=ft.Colors.RED))
            self.page.update()

    def update_tasks_ui(self):
        self.tasks_container.controls.clear()

        for t in self.tasks:
            # campo de texto da tarefa
            task_field = ft.TextField(
                value=t["name"],
                expand=True,
                border=ft.InputBorder.NONE,
                read_only=True
            )

            # checkbox de status
            cb = ft.Checkbox(
                value=t["status"] == "complete",
                on_change=lambda e, task=t: self.toggle_status(e, task)
            )

            # botão editar
            def toggle_edit(e, task=t, field=task_field):
                if field.read_only:
                    field.read_only = False
                    field.border = ft.InputBorder.OUTLINE
                    e.control.icon = ft.Icons.SAVE
                else:
                    field.read_only = True
                    field.border = ft.InputBorder.NONE
                    e.control.icon = ft.Icons.EDIT
                    self.edit_task(task["id"], field.value)
                self.page.update()

            edit_btn = ft.IconButton(
                icon=ft.Icons.EDIT,
                icon_color=ft.Colors.BLUE,
                tooltip="Editar",
                on_click=toggle_edit
            )

            del_btn = ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color=ft.Colors.RED,
                tooltip="Excluir",
                on_click=lambda e, task_id=t["id"]: self.delete_task(task_id)
            )

            self.tasks_container.controls.append(
                ft.Card(
                    content=ft.Row(
                        [cb, task_field, edit_btn, del_btn],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    elevation=2,
                    margin=5,
                )
                
            )

        self.page.update()

    def edit_task(self, task_id, new_name):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = httpx.put(
                f"{API_URL}/tasks/{task_id}",
                json={"name": new_name},
                headers=headers
            )
            if response.status_code == 200:
                self.refresh_tasks()
        except Exception as ex:
            print(f"Erro ao editar task: {ex}")

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
    
    def logout(self, e):
        self.token = None
        self.tasks = []
        self.login_view()

def main(page: ft.Page):
    ToDoApp(page)

ft.app(target=main, assets_dir='assets', view=ft.WEB_BROWSER)
