from imports import *

class Menu_errors:
    def __init__(self, tree, clipboard, lojnaya, error, delete, time_to, open_comment, edit):
        self.tree = tree
        self.clipboard = clipboard
        self.lojnaya = lojnaya
        self.error = error
        self.delete = delete
        self.time_to = time_to
        self.open_comment = open_comment
        self.edit = edit
    def show_menu(self, event):
        menu = tk.Menu(self.tree, tearoff=False, font=20)
        self.add_error_menu(menu)
        self.add_editing_menu(menu)
        self.add_other_menu(menu)
        menu.post(event.x_root, event.y_root)

    def add_error_menu(self, menu):
        settings_menu = tk.Menu(tearoff=False, font=20)
        error_codes = [
            "ошибка а0", "ошибка a2", "ошибка 43", "ошибка 44", "ошибка 45",
            "ошибка 46", "ошибка 48", "ошибка 49", "ошибка 50", "ошибка 52",
            "ошибка 53", "ошибка 56", "ошибка 57", "ошибка 58", "ошибка 59",
            "ошибка 60", "ошибка 64", "ошибка 67", "ошибка 70", "ошибка 71",
            "ошибка 96", "ошибка 99", "Частотник", "До наладчика",
            "Ревизия/инспекция", "Аварийная блокировка"
        ]
        for error in error_codes:
            settings_menu.add_command(label=error, command=lambda e=error: self.error(e))

        menu.add_cascade(label="Ошибка", command=lambda: self.error("Ошибка"), menu=settings_menu)

    def add_editing_menu(self, menu):
        menu.add_command(label="Копировать заявку", command=self.clipboard)
        menu.add_command(label="Редактировать", command=lambda: self.edit("Редактировать"))
        menu.add_command(label="Отметить Время", command=lambda: self.time_to("Отметить Время"))
        menu.add_command(label="Комментировать", command=lambda: self.open_comment("Комментировать"))
        menu.add_separator()

    def add_other_menu(self, menu):
        menu.add_command(label="Ложная Заявка", command=lambda: self.lojnaya("На момент осмотра, лифт находился в работе"))
        menu.add_command(label="Отсутствие электроэнергии", command=lambda: self.error("Отсутствие электроэнергии"))
        menu.add_command(label="Пожарная сигнализация", command=lambda: self.error("Пожарная сигнализация"))
        menu.add_command(label="Вандальные действия", command=lambda: self.error("Вандальные действия"))
        menu.add_separator()
        menu.add_command(label="Удалить Заявку", command=lambda: self.delete("Удалить Заявку"))


