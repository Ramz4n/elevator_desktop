from imports import *

class Choose_ispolnitel(tk.Toplevel):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager

        # Получаем список механиков из БД
        self.mechanics_list = self.get_mechanics()
        self.filtered_list = self.mechanics_list.copy()
        self.init_ispolnitel()

    def init_ispolnitel(self):
        self.title("Выбор исполнителя")
        self.geometry("300x400+500+200")
        self.resizable(False, False)
        # self.bind('<Unmap>', self.on_unmap)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Поле ввода для поиска
        tk.Label(self, text="Выберите исполнителя из списка:").pack(pady=5)
        self.search_var = tk.StringVar()
        self.entry_search = tk.Entry(self, textvariable=self.search_var)
        self.entry_search.pack(fill=tk.X, padx=10)
        self.entry_search.bind("<KeyRelease>", self.filter_list)

        # Listbox с фамилиями
        self.listbox = tk.Listbox(self, height=15, font=("Calibri", 12))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.listbox.bind("<Double-Button-1>", self.select_mechanic)

        # Заполнить Listbox
        self.update_listbox()

        # Выбранный механик
        self.selected_mechanic = None

    def on_close(self):
        if messagebox.askyesno("Подтверждение", "Закрыть без выбора?"):
            self.selected_mechanic = None  # Сбрасываем выбор
            self.destroy()  # Закрываем окно

    # def on_unmap(self, event):
    #     # Разворачиваем окно, если оно было свёрнуто
    #     if self.state() == 'iconic':
    #         self.state('normal')
    #     # Отменяем событие сворачивания
    #     return "break"
    #
    # def deiconify(self):
    #     if self.state() == 'iconic':
    #         self.state('normal')

    def get_mechanics(self):
        """Получает список механиков из базы в виде [{'ФИО': ..., 'id': ...}, ...]"""
        mechanics = []
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f"SELECT ФИО, id FROM workers "
                               f"WHERE Должность = 'Механик' ORDER BY ФИО")
                mechanics = cursor.fetchall()
        except Exception as e:
            tk.messagebox.showerror("Ошибка", f"Не удалось загрузить механиков:\n{e}")
        return mechanics

    def update_listbox(self):
        """Обновляет Listbox на основе self.filtered_list"""
        self.listbox.delete(0, tk.END)
        for mech in self.filtered_list:
            self.listbox.insert(tk.END, mech['ФИО'])

    def filter_list(self, event=None):
        """Фильтрует фамилии по введенной строке"""
        query = self.search_var.get().lower()
        if query == "":
            self.filtered_list = self.mechanics_list.copy()
        else:
            self.filtered_list = [m for m in self.mechanics_list if m['ФИО'].lower().startswith(query)]
        self.update_listbox()

    def select_mechanic(self, event=None):
        index = self.listbox.curselection()
        if index:
            self.selected_mechanic = self.filtered_list[index[0]]
            self.destroy()  # Закрываем окно
