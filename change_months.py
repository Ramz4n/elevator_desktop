from imports import *

class Change_months():
    def __init__(self, text, db_tables, db_manager, enabled, session, month_label, year_label, list_months, tree, month_index, year_index):
        self.tree = tree
        self.enabled = enabled
        self.db_tables = db_tables
        self.db_manager = db_manager
        self.text = text
        self.session = session
        self.month_label = month_label
        self.year_label = year_label
        self.list_months = list_months
        self.month_index = month_index
        self.year_index = year_index
        self.table_zayavki = self.db_tables["table_zayavki"]
        self.table_workers = self.db_tables["table_workers"]
        self.table_street = self.db_tables["table_street"]
        self.table_goroda = self.db_tables["table_goroda"]
        self.table_doma = self.db_tables["table_doma"]
        self.table_padik = self.db_tables["table_padik"]
        self.change_months()


    def change_months(self):
        type_button = self.session
        if type_button in ('all', 'line_close', 'started'):
            self.update_month_index()
            query = self.build_query(type_button)
            self.execute_query(query)
        else:
            self.show_error_message()

    def update_month_index(self):
        if self.text == "forward":
            self.month_index = (self.month_index + 1) % 12
            self.month_label.config(text=self.list_months[self.month_index])
            if self.month_index == 0:
                self.year_index = (self.year_index + 1) % 100
                self.year_label.config(text=self.year_index)
        elif self.text == "backward":
            self.month_index = (self.month_index - 1) % 12
            self.month_label.config(text=self.list_months[self.month_index])
            if self.month_index == 11:
                self.year_index = (self.year_index - 1) % 100
                self.year_label.config(text=self.year_index)

    def build_query(self, type_button):
        base_query = f'''
            SELECT z.Номер_заявки,
                   FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%y, %H:%i') AS Дата_заявки,
                   w.ФИО AS Диспетчер,
                   g.город AS Город,
                   CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                   тип_лифта,
                   причина,
                   m1.ФИО as Принял,
                   m2.ФИО as Исполнил,
                   FROM_UNIXTIME(дата_запуска, '%d.%m.%y, %H:%i') AS Дата_запуска,
                   комментарий,
                   z.id
            FROM {self.table_zayavki} z
            JOIN {self.table_workers} w ON z.id_диспетчер = w.id
            JOIN {self.table_goroda} g ON z.id_город = g.id
            JOIN {self.table_street} s ON z.id_улица = s.id
            JOIN {self.table_doma} d ON z.id_дом = d.id
            JOIN {self.table_padik} p ON z.id_подъезд = p.id
            JOIN {self.table_workers} m1 ON z.id_механик = m1.id
            LEFT JOIN {self.table_workers} m2 ON z.id_исполнитель = m2.id
        '''
        query = self.add_filter_to_query(base_query, type_button)
        query += self.add_date_and_order_to_query()
        return query

    def add_filter_to_query(self, query, type_button):
        if type_button == 'all':
            query += ' WHERE z.Причина <> "Линейная"'
        elif type_button == 'line_close':
            query += ' WHERE Дата_запуска > 100 AND Причина = "Линейная"'
        elif type_button == 'started':
            query += ' WHERE Причина="Остановлен" AND Дата_запуска is not Null'
        return query

    def add_date_and_order_to_query(self):
        return f'''
            AND FROM_UNIXTIME(Дата_заявки, '%m') = '{str(self.month_index + 1).zfill(2)}'
            AND FROM_UNIXTIME(Дата_заявки, '%y') = '{str(self.year_index)}'
            AND z.pc_id = {self.enabled}
            ORDER BY z.id;
        '''

    def execute_query(self, query):
        try:
            # Создаем новое соединение для выполнения запроса
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor()
                cursor.execute(query)
                self.update_treeview(cursor.fetchall())
                connection.commit()
                self.tree.yview_moveto(1.0)
        except mariadb.Error as e:
            print(e)
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")


    def update_treeview(self, rows):
        [self.tree.delete(i) for i in self.tree.get_children()]
        for row in rows:
            self.insert_row_into_treeview(row)

    def insert_row_into_treeview(self, row):
        if row[-3] is None and row[-5] == 'Остановлен':
            self.tree.insert('', 'end', values=tuple(row), tags=('Red.Treeview',))
        elif row[-3] is None and row[-5] in ('Неисправность', 'Застревание'):
            self.tree.insert('', 'end', values=tuple(row), tags=('Blue.Treeview',))
        elif row[-3] is not None and row[-5] == 'Остановлен':
            self.tree.insert('', 'end', values=tuple(row), tags=('Green.Treeview',))
        elif row[-3] is not None and row[-5] == 'Линейная':
            self.tree.insert('', 'end', values=tuple(row), tags=('Violet.Treeview',))
        else:
            self.tree.insert('', 'end', values=tuple(row))

    def show_error_message(self):
        msg = "Этот раздел уже имеет все месяцы с заявками"
        showerror("Ошибка!", msg)
