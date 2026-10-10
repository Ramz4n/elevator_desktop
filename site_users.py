from imports import *
from werkzeug.security import generate_password_hash

SITE_ACCESS_DEFAULT = '0'


def _is_mariadb_admin(cur):
    """Администратор MariaDB: есть ALL PRIVILEGES на *.* либо GRANT OPTION на *.*."""
    cur.execute("SHOW GRANTS FOR CURRENT_USER()")
    for (grant,) in cur.fetchall():
        g = grant.upper()
        if " ON *.* " in g and ("ALL PRIVILEGES" in g or "WITH GRANT OPTION" in g):
            return True
    return False


class SiteUsersWindow(tk.Toplevel):
    """
    Пользователи сайта (БД site, таблица users). Доступ только администратору MariaDB:
    сначала просим админ-логин/пароль, проверяем права, затем показываем список
    с добавлением / изменением / удалением. Пароль хэшируется так же, как в
    "генерация_паролей.txt" (werkzeug generate_password_hash).
    """

    def __init__(self, default_host="127.0.0.1", default_port=3306):
        super().__init__()
        self.title("Пользователи сайта")
        self.resizable(False, False)
        self.grab_set()
        self.wm_attributes('-topmost', 1)

        self.font_main = ('Calibri', 12)
        self.font_bold = ('Calibri', 12, 'bold')
        self.conn = None
        self.entries = {}
        self.default_host = default_host
        self.default_port = default_port
        self.protocol("WM_DELETE_WINDOW", self._close)

        self._build_login()

    def _close(self):
        if self.conn is not None:
            try:
                self.conn.close()
            except mariadb.Error:
                pass
        self.destroy()

    def _center(self):
        self.update_idletasks()
        self.geometry(f"+{(self.winfo_screenwidth() - self.winfo_width()) // 2}"
                      f"+{(self.winfo_screenheight() - self.winfo_height()) // 2}")

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()
        self.entries = {}

    def _field(self, parent, row, key, label, default="", show=None):
        tk.Label(parent, text=label, font=self.font_main).grid(row=row, column=0, padx=10, pady=4, sticky='w')
        e = tk.Entry(parent, font=self.font_main, width=28, show=show)
        e.insert(0, default)
        e.grid(row=row, column=1, padx=10, pady=4, sticky='w')
        self.entries[key] = e
        return e

    # ---------- вход администратора ----------
    def _build_login(self):
        self._clear()
        frame = tk.Frame(self, padx=16, pady=16)
        frame.pack()
        tk.Label(frame, text="Вход администратора MariaDB", font=self.font_bold) \
            .grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky='w')
        self._field(frame, 1, "host", "Хост MariaDB:", str(self.default_host))
        self._field(frame, 2, "port", "Порт:", str(self.default_port))
        self._field(frame, 3, "user", "Админ-логин:", "root")
        pw = self._field(frame, 4, "password", "Админ-пароль:", "", show="*")
        tk.Button(frame, text="Войти", font=self.font_bold, bg='#d7efd7', command=self._login) \
            .grid(row=5, column=0, columnspan=2, pady=(10, 0))
        pw.bind('<Return>', lambda e: self._login())
        self._center()

    def _login(self):
        v = {k: e.get().strip() for k, e in self.entries.items()}
        if not v["password"]:
            mb.showwarning("Внимание", "Введите админ-пароль.", parent=self)
            return
        try:
            port = int(v["port"])
        except ValueError:
            mb.showwarning("Внимание", "Порт должен быть числом.", parent=self)
            return
        try:
            conn = mariadb.connect(host=v["host"], port=port, user=v["user"],
                                   password=v["password"], connect_timeout=5)
            cur = conn.cursor()
            if not _is_mariadb_admin(cur):
                conn.close()
                mb.showerror("Нет доступа",
                             "Этот пользователь не является администратором MariaDB.", parent=self)
                return
            create_site_db(cur)
            conn.commit()
        except mariadb.Error as e:
            mb.showerror("Ошибка подключения", f"Не удалось войти:\n{e}", parent=self)
            return
        self.conn = conn
        self._build_list()

    # ---------- список пользователей ----------
    def _build_list(self):
        self._clear()
        frame = tk.Frame(self, padx=12, pady=12)
        frame.pack()

        self.tree = ttk.Treeview(frame, columns=("id", "username", "access"), show="headings",
                                 height=14, selectmode="browse")
        for col, text_, w in (("id", "ID", 50), ("username", "Логин", 220), ("access", "Доступ", 70)):
            self.tree.heading(col, text=text_)
            self.tree.column(col, width=w, anchor='w')
        self.tree.grid(row=0, column=0, columnspan=3)

        tk.Button(frame, text="Добавить", font=self.font_main, command=self._add) \
            .grid(row=1, column=0, pady=(10, 0), sticky='ew')
        tk.Button(frame, text="Изменить", font=self.font_main, command=self._edit) \
            .grid(row=1, column=1, pady=(10, 0), sticky='ew')
        tk.Button(frame, text="Удалить", font=self.font_main, command=self._delete) \
            .grid(row=1, column=2, pady=(10, 0), sticky='ew')

        self._reload()
        self._center()

    def _reload(self):
        self.tree.delete(*self.tree.get_children())
        try:
            cur = self.conn.cursor()
            cur.execute(f"SELECT id, username, access FROM `{SITE_DB_NAME}`.users ORDER BY id")
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
        except mariadb.Error as e:
            mb.showerror("Ошибка", f"Не удалось загрузить пользователей:\n{e}", parent=self)

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            mb.showwarning("Внимание", "Выберите пользователя в списке.", parent=self)
            return None
        return self.tree.item(sel[0], "values")

    # ---------- диалог добавления / изменения ----------
    def _user_dialog(self, title, username="", access=SITE_ACCESS_DEFAULT, password_required=True):
        """Возвращает (username, password|'' , access) либо None."""
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()
        dlg.wm_attributes('-topmost', 1)
        frame = tk.Frame(dlg, padx=16, pady=16)
        frame.pack()
        ents = {}
        rows = (("username", "Логин:", username, None),
                ("password", "Пароль:" if password_required else "Новый пароль:", "", "*"),
                ("access", "Доступ (1 символ):", access, None))
        for i, (key, label, default, show) in enumerate(rows):
            tk.Label(frame, text=label, font=self.font_main).grid(row=i, column=0, padx=8, pady=4, sticky='w')
            e = tk.Entry(frame, font=self.font_main, width=26, show=show)
            e.insert(0, default)
            e.grid(row=i, column=1, padx=8, pady=4)
            ents[key] = e
        if not password_required:
            tk.Label(frame, text="(пустой пароль — оставить прежний)", font=('Calibri', 10), fg='gray30') \
                .grid(row=3, column=0, columnspan=2, sticky='w')

        result = {}

        def ok():
            u = ents["username"].get().strip()
            p = ents["password"].get()
            a = ents["access"].get().strip()
            if not u or len(u) > 50:
                mb.showwarning("Внимание", "Логин обязателен (до 50 символов).", parent=dlg)
                return
            if password_required and not p:
                mb.showwarning("Внимание", "Введите пароль.", parent=dlg)
                return
            if len(a) != 1:
                mb.showwarning("Внимание", "Доступ — ровно один символ.", parent=dlg)
                return
            result["v"] = (u, p, a)
            dlg.destroy()

        tk.Button(frame, text="Сохранить", font=self.font_bold, bg='#d7efd7', command=ok) \
            .grid(row=4, column=0, columnspan=2, pady=(10, 0))
        dlg.update_idletasks()
        dlg.geometry(f"+{self.winfo_rootx() + 40}+{self.winfo_rooty() + 40}")
        self.wait_window(dlg)
        return result.get("v")

    def _username_taken(self, username, exclude_id=None):
        cur = self.conn.cursor()
        cur.execute(f"SELECT id FROM `{SITE_DB_NAME}`.users WHERE username = ?", (username,))
        return any(str(r[0]) != str(exclude_id) for r in cur.fetchall())

    def _add(self):
        data = self._user_dialog("Добавить пользователя на сайт")
        if not data:
            return
        username, password, access = data
        try:
            if self._username_taken(username):
                mb.showwarning("Внимание", f"Логин «{username}» уже существует.", parent=self)
                return
            cur = self.conn.cursor()
            cur.execute(f"INSERT INTO `{SITE_DB_NAME}`.users (username, password, access) VALUES (?, ?, ?)",
                        (username, generate_password_hash(password), access))
            self.conn.commit()
        except mariadb.Error as e:
            mb.showerror("Ошибка", f"Не удалось добавить:\n{e}", parent=self)
            return
        self._reload()

    def _edit(self):
        row = self._selected()
        if not row:
            return
        uid, old_name, old_access = row
        data = self._user_dialog("Изменить пользователя", old_name, old_access, password_required=False)
        if not data:
            return
        username, password, access = data
        try:
            if self._username_taken(username, exclude_id=uid):
                mb.showwarning("Внимание", f"Логин «{username}» уже существует.", parent=self)
                return
            cur = self.conn.cursor()
            if password:
                cur.execute(f"UPDATE `{SITE_DB_NAME}`.users SET username=?, password=?, access=? WHERE id=?",
                            (username, generate_password_hash(password), access, uid))
            else:
                cur.execute(f"UPDATE `{SITE_DB_NAME}`.users SET username=?, access=? WHERE id=?",
                            (username, access, uid))
            self.conn.commit()
        except mariadb.Error as e:
            mb.showerror("Ошибка", f"Не удалось изменить:\n{e}", parent=self)
            return
        self._reload()

    def _delete(self):
        row = self._selected()
        if not row:
            return
        uid, name, _ = row
        if not askyesno("Удаление", f"Удалить пользователя «{name}» с сайта?", parent=self):
            return
        try:
            cur = self.conn.cursor()
            cur.execute(f"DELETE FROM `{SITE_DB_NAME}`.users WHERE id=?", (uid,))
            self.conn.commit()
        except mariadb.Error as e:
            mb.showerror("Ошибка", f"Не удалось удалить:\n{e}", parent=self)
            return
        self._reload()
