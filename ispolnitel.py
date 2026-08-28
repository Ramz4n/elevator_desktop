from imports import *

class Choose_ispolnitel(tk.Toplevel):
    def __init__(self, db_manager):
        super().__init__()
        # Прячем окно сразу: иначе оно на мгновение показывается в
        # непроинициализированном виде (без geometry) там, где Tk
        # разместило его по умолчанию, и только потом "прыгает" в
        # нужное место -- см. self.deiconify() в init_ispolnitel,
        # вызывается сразу после geometry() (grab_set() ниже не
        # сработает на ещё скрытом окне, поэтому не откладываем
        # deiconify до конца метода, как в Edit/Search/Comment)
        self.withdraw()
        self.db_manager = db_manager

        # Получаем список механиков из БД
        self.mechanics_list = self.get_mechanics()
        self.filtered_list = self.mechanics_list.copy()
        self.init_ispolnitel()

    def init_ispolnitel(self):
        # Создаем затемняющий оверлей
        self.overlay = tk.Toplevel(self.master)
        self.overlay.withdraw()  # см. комментарий у self.withdraw() в __init__
        self.overlay.attributes('-alpha', 0.8)  # Полупрозрачность
        self.overlay.attributes('-topmost', True)
        self.overlay.configure(bg='gray')

        # Получаем размеры и позицию главного окна
        self.master.update_idletasks()
        x = self.master.winfo_x()
        y = self.master.winfo_y()
        width = self.master.winfo_width()
        height = self.master.winfo_height()

        # Размещаем оверлей поверх главного окна
        self.overlay.geometry(f"{width}x{height}+{x}+{y}")
        self.overlay.overrideredirect(True)  # Убираем рамку окна
        self.overlay.deiconify()

        self.title("Выбор исполнителя")
        # Центрируем относительно главного окна вместо фиксированного
        # +500+200 -- иначе при нестандартном положении главного окна
        # диалог мог открыться не по центру или вовсе за пределами экрана
        window_width, window_height = 300, 400
        pos_x = x + width // 2 - window_width // 2
        pos_y = y + height // 2 - window_height // 2
        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        self.resizable(False, False)
        self.attributes('-toolwindow', True)
        self.attributes('-topmost', True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Делаем окно модальным. deiconify() -- сразу, до grab_set():
        # grab_set() не срабатывает на ещё скрытом (withdraw) окне
        self.transient(self.overlay)
        self.deiconify()
        self.grab_set()
        self.focus_set()

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
        if messagebox.askyesno("Подтверждение", "Отметить время без выбора исполнителя?", parent=self):
            self.selected_mechanic = None  # Сбрасываем выбор
            self.overlay.destroy()  # Закрываем оверлей
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
                               f"WHERE Должность = 'Механик' AND is_active = 1 ORDER BY ФИО")
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
            self.overlay.destroy()  # Закрываем оверлей
            self.destroy()  # Закрываем окно
