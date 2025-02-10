from imports import *

class Afternoon_statistic(tk.Toplevel):
    def __init__(self, parent, db_config):
        super().__init__(parent)
        self.db_config = db_config
        self.visual()

    def visual(self):
        self.title('Статистика за день')
        self.geometry('700x400+300+300')
        self.resizable(False, False)

        self.calendar = DateEntry(self, locale='ru_RU', font=1)
        self.calendar.bind("<<DateEntrySelected>>", self.print_info)
        self.calendar.pack(side=tk.TOP, anchor=tk.NW)

        self.label_info_bd = tk.Label(borderwidth=1, width=50, height=10, relief="raised", text="",
                                      font='Times 12')

        self.tree2 = ttk.Treeview(self, style="mystyle.Treeview",
                                  columns=('Город', 'Застр', 'Неиспр', 'Кол_во'),
                                  height=12, show='headings')
        self.tree2.column('Город', width=100, anchor=tk.CENTER, stretch=True)
        self.tree2.column('Застр', width=100, anchor=tk.CENTER, stretch=True)
        self.tree2.column('Неиспр', width=100, anchor=tk.CENTER, stretch=True)
        self.tree2.column('Кол_во', width=90, anchor=tk.CENTER, stretch=True)

        self.tree2.heading('Город', text='Город')
        self.tree2.heading('Застр', text='Застрев')
        self.tree2.heading('Неиспр', text='Неиспр')
        self.tree2.heading('Кол_во', text='Кол-во')
        self.tree2.pack(side="left", fill="both", expand=True)
        self.label_info_bd.pack(side=tk.TOP)
        date_obj = datetime.datetime.now()
        self.print_info(date_obj.strftime('%d.%m.%Y'))

    def print_info(self, event):
        self.selected_date = self.calendar.get_date()
        self.selected_date_str = self.selected_date.strftime('%d.%m.%Y')
        try:
            with closing(self.db_config.connect()) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''SELECT g.город as Город,
                                    SUM(CASE WHEN z.Причина = 'Застревание' THEN 1 ELSE 0 END) as Застр,
                                    SUM(CASE WHEN z.Причина IN ('Остановлен', 'Неисправность') THEN 1 ELSE 0 END) as Неиспр,
                                    SUM(CASE WHEN z.Причина IN ('Остановлен', 'Неисправность', 'Застревание') THEN 1 ELSE 0 END) as Кол_во
                                    FROM {self.db_config.data['table_zayavki']} z
                                    JOIN {self.db_config.data['table_goroda']} g ON z.id_город = g.id
                                    WHERE DATE_FORMAT(FROM_UNIXTIME(z.Дата_заявки), '%d.%m.%Y') = ?
                                    GROUP BY Город;''',
                               (self.selected_date_str,))
                data = cursor.fetchall()  # Получаем данные из запроса
                [self.tree2.delete(i) for i in self.tree2.get_children()]  # Очищаем treeview
                for row in data:  # Используем переменную data для вставки
                    self.tree2.insert('', 'end', values=row)  # Вставляем данные в treeview
                connection.commit()
        except mariadb.Error as e:
            messagebox.showinfo('Информация', f"Ошибка при работе с базой данных: {e}")


    def is_open(self):
        return self.winfo_exists()

    def show(self):
        if self.is_open():
            self.deiconify()  # Показываем окно, если оно скрыто
            self.focus_force()

