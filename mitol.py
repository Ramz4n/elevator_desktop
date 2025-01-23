from imports import *

class Main(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        root.title("МиТОЛ")
        root.state("zoomed")
        root.resizable(False, True)
        self.init_main()
        self.view_records()


    def init_main(self):
        with open('config.json', 'r') as file:
            data = json.loads(file.read())

        self.pc_id = data['pc_id']
        m = Menu(root)
        root.config(menu=m)
        fm = Menu(m, font=20)
        m.add_cascade(label="МЕНЮ", menu=fm)
        fm.add_command(label="Открыть в экселе", command=self.open_bd_to_excel)
        # =======1 ОСНОВНОЙ TOOLBAR====================================================================
        toolbar2 = tk.Frame(borderwidth=1, relief="raised")
        toolbar2.pack(side=tk.TOP, fill=tk.X)
        # ==========================================================================================
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f'''select id, ФИО from {table_workers} where Должность="Диспетчер" order by ФИО''')
                data_workers = cursor.fetchall()
        except:
            mb.showerror("Ошибка","Нет подключения к базе данных")
            sys.exit()
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f'''select w.ФИО from {table_zayavki} z
                JOIN {table_workers} w ON z.id_диспетчер = w.id
                where pc_id={self.pc_id}
                ORDER BY z.id DESC LIMIT 1''')
                data_worker = cursor.fetchone()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.disp_to_id = {i['ФИО'] for i in data_workers}
        first_element = next(iter(self.disp_to_id), None)
        if data_worker is None:
            data = first_element
        else:
            data = data_worker['ФИО']
        toolbar3 = tk.Frame(toolbar2, borderwidth=1, relief="raised")
        toolbar3.pack(side=tk.LEFT, fill=tk.Y)
        self.disp = tk.StringVar(value=data)
        self.label3 = tk.Label(toolbar3, borderwidth=1, width=18, relief="raised", text="Диспетчер", font='Calibri 16 bold')
        frame3 = tk.Frame(toolbar3)
        self.label3.pack(side=tk.TOP, fill=tk.X)
        for d in data_workers:
            lang_btn3 = tk.Radiobutton(toolbar3, text=d['ФИО'], value=d, variable=self.disp, font='Calibri  16')
            lang_btn3.pack(anchor=tk.NW, expand=True)
            if d['ФИО'] == self.disp.get():
                lang_btn3.select()
            else:
                lang_btn3.deselect()
        frame3.pack(side=tk.LEFT, anchor=tk.NW, expand=True)
        # =======2 ГОРОДА===========================================================================
        toolbar4 = tk.Frame(toolbar2, borderwidth=1, relief="raised")
        toolbar4.pack(side=tk.LEFT, fill=tk.Y)

        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port,
                                         database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f"select id, город from {table_goroda}")
                data_towns = cursor.fetchall()
        except mariadb.Error as e:
            messagebox.showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
            return

        default_town = data_towns[0] if data_towns else ''

        self.label2 = tk.Label(toolbar4, borderwidth=1, width=21, relief="raised", text="Город", font='Calibri 16 bold')
        self.label2.pack(side=tk.TOP, fill=tk.X)

        self.canvas = tk.Canvas(toolbar4, width=100)
        self.scrollbar = ttk.Scrollbar(toolbar4, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Привязка событий колесика мыши только к Canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

        self.city = tk.StringVar(value=default_town['город'] if default_town else '')
        self.city.trace("w", self.on_select_city)

        for town in data_towns:
            radiobutton = tk.Radiobutton(self.scrollable_frame, font=('Calibri', 16), text=town['город'],
                                         variable=self.city,
                                         value=town['город'])
            radiobutton.pack(anchor="w")
            radiobutton.bind("<MouseWheel>", self._on_mousewheel)
            radiobutton.bind("<Button-4>", self._on_mousewheel)
            radiobutton.bind("<Button-5>", self._on_mousewheel)
        # =======3 БЛОК АДРЕСОВ========================================================================
        toolbar5 = tk.Frame(toolbar2, borderwidth=1, relief="raised")
        toolbar5.pack(side=tk.LEFT, fill=tk.Y)

        self.label3 = tk.Label(toolbar5, borderwidth=1, width=21, relief="raised", text="Адрес", font='Calibri 16 bold')
        self.frame3 = tk.Frame()
        self.entry_text3 = tk.StringVar()
        self.entry3 = tk.Entry(toolbar5, textvariable=self.entry_text3, width=33)
        self.entry3.bind('<KeyRelease>', self.check_input_address)
        self.label3.pack(side=tk.TOP, fill=tk.X)
        self.entry3.pack(side=tk.TOP, expand=True, fill=tk.X)

        self.listbox_values = tk.Variable()
        self.listbox = tk.Listbox(toolbar5, listvariable=self.listbox_values, width=25, font='Calibri 16')
        self.listbox.bind('<<ListboxSelect>>', self.on_change_selection_address)

        # Создаем горизонтальный скроллбар
        self.scrollbar_x = tk.Scrollbar(toolbar5, orient=tk.HORIZONTAL)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Связываем скроллбар с Listbox
        self.listbox.config(xscrollcommand=self.scrollbar_x.set)
        self.scrollbar_x.config(command=self.listbox.xview)

        self.listbox.pack(side=tk.TOP, expand=True)
        self.frame3.pack(side=tk.LEFT, anchor=tk.NW, expand=True)
        # ======4 БЛОК КОД С ТИПАМИ ЛИФТОВ==================================================================
        toolbar6 = tk.Frame(toolbar2, borderwidth=1, relief="raised")
        toolbar6.pack(side=tk.LEFT, fill=tk.Y)
        self.label4 = tk.Label(toolbar6, borderwidth=1, width=12, relief="raised", text="Тип лифта", font='Calibri 16 bold')
        self.frame4 = tk.Frame()
        self.entry_text4 = tk.StringVar()
        self.entry4 = tk.Entry(toolbar6, textvariable=self.entry_text4, width=18)
        self.entry4.bind('<KeyRelease>', self.check_input_lifts)
        self.label4.pack(side=tk.TOP, fill=tk.X)
        self.entry4.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.listbox_values_type = tk.Variable()
        self.listbox_type = tk.Listbox(toolbar6, listvariable=self.listbox_values_type, width=14, font='Calibri 16')
        self.listbox_type.bind('<<ListboxSelect>>', self.on_change_selection_lift)

        # Создаем горизонтальный скроллбар
        self.scrollbar_x = tk.Scrollbar(toolbar6, orient=tk.HORIZONTAL)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Связываем скроллбар с Listbox
        self.listbox_type.config(xscrollcommand=self.scrollbar_x.set)
        self.scrollbar_x.config(command=self.listbox_type.xview)

        self.listbox_type.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.frame4.pack(side=tk.LEFT, anchor=tk.NW, expand=True, fill=tk.X)
        # ======5 БЛОК ПРИЧИНА ОСТАНОВКИ ============================================
        toolbar7 = tk.Frame(toolbar2, borderwidth=1, relief="raised")
        toolbar7.pack(side=tk.LEFT, fill=tk.Y)
        frame5 = tk.Frame()
        label5 = tk.Label(toolbar7, borderwidth=1, width=14, relief="raised", text="Причина", font='Calibri 16 bold')
        label5.pack(fill=tk.X)
        self.prichina = ['Неисправность', 'Застревание', 'Остановлен', 'Связь', 'Линейная']
        self.prich5 = tk.StringVar(value='?')
        for pr in self.prichina:
            lang_btn3 = tk.Radiobutton(toolbar7, text=pr, value=pr, variable=self.prich5, font='Calibri  16')
            lang_btn3.pack(anchor=tk.NW, expand=True)
        frame5.pack(side=tk.LEFT, anchor=tk.NW, expand=True)
        # ======6 БЛОК FIO МЕХАНИКА =====================================================
        toolbar9 = tk.Frame(toolbar2, borderwidth=1, relief="raised")
        toolbar9.pack(side=tk.LEFT, fill=tk.Y)
        self.label7 = tk.Label(toolbar9, borderwidth=1, width=18, relief="raised", text="ФИО механика", font='Calibri  16 bold')
        self.frame7 = tk.Frame()
        self.entry_text7 = tk.StringVar(value='')
        self.entry7 = tk.Entry(toolbar9, textvariable=self.entry_text7, width=28)
        self.entry7.bind('<KeyRelease>', self.check_input_fio)
        self.label7.pack(side=tk.TOP, fill=tk.X)
        self.entry7.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.listbox_values7 = tk.Variable()
        self.listbox7 = tk.Listbox(toolbar9, width=21, listvariable=self.listbox_values7, font='Calibri 16')
        self.listbox7.bind('<<ListboxSelect>>', self.on_change_selection_fio)

        # Создаем горизонтальный скроллбар
        self.scrollbar_x = tk.Scrollbar(toolbar9, orient=tk.HORIZONTAL)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Связываем скроллбар с Listbox
        self.listbox7.config(xscrollcommand=self.scrollbar_x.set)
        self.scrollbar_x.config(command=self.listbox7.xview)

        self.listbox7.pack(side=tk.TOP, expand=True, fill=tk.X)
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f"select id, ФИО from {table_workers} where Должность = 'Механик' order by ФИО")
                self.data_meh = cursor.fetchall()
            for d in self.data_meh:
                self.data_meh_name = f"{d['ФИО']}"
                self.data_meh_id = f"{d['id']}"
                self.listbox7.insert(tk.END, self.data_meh_name)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.frame7.pack(side=tk.LEFT, anchor=tk.NW, expand=True)
        # =======NEW TOOLBAR==============================================================
        toolbar = tk.Frame(bd=2, borderwidth=1, relief="raised")
        toolbar.pack(side=tk.TOP, fill=tk.X, anchor=tk.N)
        helv36 = tkFont.Font(family='Helvetica', size=10, weight=tkFont.BOLD)
        # ================КНОПКИ========================================================
        tool1 = tk.Frame(toolbar, borderwidth=1, relief="raised")
        tool1.pack(side=tk.LEFT, fill=tk.X, anchor=tk.W)
        btn_open_dialog = tk.Button(tool1, text='Добавить заявку', command=self.sql_insert, bg='#d7d8e0', compound=tk.LEFT, width=14, height=1, font=helv36)
        btn_open_dialog.pack(side=tk.TOP)
        btn_refresh = tk.Button(tool1, text='Обновить', bg='#d7d8e0', compound=tk.TOP, command=self.view_records, width=14, font=helv36)
        btn_refresh.pack(side=tk.BOTTOM)
        btn_search = tk.Button(tool1, text='Поиск адреса', bg='#d7d8e0', compound=tk.TOP, command=self.open_search_dialog, width=14, font=helv36)
        btn_search.pack(side=tk.TOP)
        # =================КНОПКИ========================================================
        tool3 = tk.Frame(toolbar, borderwidth=1, relief="raised")
        tool3.pack(side=tk.LEFT, fill=tk.X, anchor=tk.W)
        btn_start = tk.Button(tool3, text='Запущенные лифты', bg='#00AD0E', compound=tk.TOP,command=self.start_lift, width=19, font=helv36)
        btn_start.pack(side=tk.BOTTOM)
        btn_stop = tk.Button(tool3, text='Остановленные лифты', bg='#FFB3AB', compound=tk.TOP,command=self.stop_lift, width=19, font=helv36)
        btn_stop.pack(side=tk.TOP)
        btn_open_ = tk.Button(tool3, text='Незакрытые заявки', bg='#4897FF', compound=tk.TOP,command=self.non_start_lift, width=19, font=helv36)
        btn_open_.pack(side=tk.BOTTOM)
        #=====================================================================================
        tool4 = tk.Frame(toolbar)
        tool4.pack(side=tk.LEFT, fill=tk.X, anchor=tk.W)
        tool5 = tk.Frame(toolbar, borderwidth=1, relief="raised")
        tool5.pack(side=tk.LEFT, fill=tk.X, anchor=tk.W)
        self.is_on = True
        self.enabled = IntVar()
        self.enabled.set(self.pc_id)
        self.my_label = Label(tool4,
                         text="Мои заявки",
                         fg="green",
                         font=("Helvetica", 10))
        self.my_label.pack()
        self.on = PhotoImage(file="on.png")
        self.off = PhotoImage(file="off.png")
        self.on_button = Button(tool4, image=self.off, bd=0, command=self.switch)
        self.on_button.pack()
        btn_lineyka_close = tk.Button(tool5, text='Линейные закрытые', compound=tk.TOP,
                              command=self.close_line_lift, width=19, font=helv36, bg='#BE81FF')
        btn_lineyka_close.pack(side=tk.BOTTOM)
        btn_lineyka_open = tk.Button(tool5, text='Линейные открытые', compound=tk.TOP,
                                command=self.open_line_lift, width=19, font=helv36)
        btn_lineyka_open.pack(side=tk.BOTTOM)
        # === ПЕРЕЛИСТЫВАНИЕ БД ПО МЕСЯЦАМ=====================================================================
        self.months = ["Январь", "Февраль", "Март", "Апрель",
                       "Май", "Июнь", "Июль", "Август",
                       "Сентябрь","Октябрь","Ноябрь", "Декабрь"]
        btn_refresh = tk.Button(toolbar, text='Следующий месяц', bg='#d7d8e0', compound=tk.RIGHT, command=self.update_forward, width=19, font=helv36)
        btn_refresh.pack(side=tk.RIGHT)
        self.year_label = Label(toolbar, text='', font='Calibri 16 bold')
        self.year_label.pack(side=tk.RIGHT)
        self.month_label = Label(toolbar, text='', font='Calibri 16 bold')
        self.month_label.pack(side=tk.RIGHT)
        btn_refresh = tk.Button(toolbar, text='Предыдущий месяц', bg='#d7d8e0', compound=tk.RIGHT, command=self.update_backward, width=19, font=helv36)
        btn_refresh.pack(side=tk.RIGHT)
        # =======ИНФО СПРАВА О ПОДСЧЁТАХ============================================================================
        self.calendar = DateEntry(toolbar2, locale='ru_RU', font=1)
        self.calendar.bind("<<DateEntrySelected>>", self.print_info)
        self.calendar.pack(side=tk.TOP, anchor=tk.NW)
        self.label_info_bd = tk.Label(toolbar2, borderwidth=1, width=50, height=10, relief="raised", text="", font='Times 12')

        self.tree2 = ttk.Treeview(self.label_info_bd, style="mystyle.Treeview", columns=('Город', 'Застр', 'Неиспр', 'Кол_во'),
                                  height=12, show='headings')
        self.tree2.column('Город', width=100, anchor=tk.CENTER)
        self.tree2.column('Застр', width=100, anchor=tk.CENTER)
        self.tree2.column('Неиспр', width=100, anchor=tk.CENTER)
        self.tree2.column('Кол_во', width=90, anchor=tk.CENTER)

        self.tree2.heading('Город', text='Город')
        self.tree2.heading('Застр', text='Застрев')
        self.tree2.heading('Неиспр', text='Неиспр')
        self.tree2.heading('Кол_во', text='Кол-во')
        self.tree2.pack(side="left", fill="both")
        self.label_info_bd.pack(side=tk.TOP)
        # =======ВИЗУАЛ БАЗЫ ДАННЫХ =========================================================================
        style = ttk.Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0, font=('Helvetica', 16), rowheight=23)
        style.configure("mystyle.Treeview.Heading", font=('Helvetica', 16, 'bold'))
        style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])
        self.tree = ttk.Treeview(self, style="mystyle.Treeview",
        columns=('ID', 'date', 'dispetcher', 'town', 'adress', 'type_lift', 'prichina', 'fio', 'date_to_go', 'comment', 'id2'),
                                 height=50, show='headings')
        #self.tree.bind("<Button-3>", self.menu_errors.show_menu)
        self.tree.column('ID', width=50, anchor=tk.CENTER, stretch=False)
        self.tree.column('date', width=185, anchor=tk.W, stretch=False)
        self.tree.column('dispetcher', width=120, anchor=tk.W, stretch=False)
        self.tree.column('town', width=120, anchor=tk.W, stretch=False)
        self.tree.column('adress', width=280, anchor=tk.W, stretch=False)
        self.tree.column('type_lift', width=115, anchor=tk.W, stretch=False)
        self.tree.column('prichina', width=130, anchor=tk.W, stretch=False)
        self.tree.column('fio', width=170, anchor=tk.W, stretch=False)
        self.tree.column('date_to_go', width=185, anchor=tk.W, stretch=False)
        self.tree.column("comment", width=1000, anchor=tk.W, stretch=True)
        self.tree.column("id2", width=0, anchor=tk.CENTER)
        self.tree.column('#0', stretch=False)

        self.tree.heading('ID', text='№')
        self.tree.heading('date', text='Дата заявки')
        self.tree.heading('dispetcher', text='Диспетчер')
        self.tree.heading('town', text='Город')
        self.tree.heading('adress', text='Адрес')
        self.tree.heading('type_lift', text='Тип лифта')
        self.tree.heading('prichina', text='Причина')
        self.tree.heading('fio', text='ФИО механика')
        self.tree.heading('date_to_go', text='Дата запуска')
        self.tree.heading('comment', text='Комментарий', anchor=tk.W)
        self.tree.heading('id2', text='')

        # Создаем экземпляр класса Menu_errors и передаем ему виджет tree
        self.menu_errors = Menu_errors(self.tree, self.clipboard, self.lojnaya, self.error,
                                       self.delete, self.time_to, self.open_comment, self.edit)

        # Привязываем событие правой кнопки мыши к методу show_menu
        self.tree.bind("<Button-3>", self.menu_errors.show_menu)

        self.scrollbar2 = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.tree.configure(yscrollcommand=self.scrollbar2.set)
        self.scrollbar2.config(command=self.tree.yview)
        self.scrollbar2.pack(side="right", fill="both")

        self.scrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.tree.configure(xscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.tree.xview)
        self.scrollbar.pack(side="bottom", fill="both")
        self.tree.pack(side="left", fill="both")
        self.on_select_city()
        Tooltip(self.tree)


    def label_center_switch_name(self, name, color):
        self.label_center.configure(text=f'{name}', bg=f'{color}')

    def clipboard(self):
        if self.tree.selection():
            try:
                selected_item_id = self.tree.selection()[0]  # Получаем ID выбранного элемента
                request_id = self.tree.set(selected_item_id, '#11')  # Получаем значение из колонки #11

                with closing(mariadb.connect(user=user, password=password, host=host, port=port,
                                             database=database)) as connection2:
                    cursor = connection2.cursor()
                    cursor.execute(f'''SELECT z.Номер_заявки,
                                       FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                                       g.город AS Город,
                                       CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                       тип_лифта,
                                       причина,
                                       комментарий
                                     FROM {table_zayavki} z
                                     JOIN {table_goroda} g ON z.id_город = g.id
                                     JOIN {table_street} s ON z.id_улица = s.id
                                     JOIN {table_doma} d ON z.id_дом = d.id
                                     JOIN {table_padik} p ON z.id_подъезд = p.id
                                     JOIN {table_workers} m ON z.id_механик = m.id
                                     WHERE z.id=?''', [request_id])

                    result = cursor.fetchone()  # Получаем первую строку результата
                    if result:  # Проверяем, что результат не None
                        # Создаем строку с метками
                        result_str = (
                            f"№: {result[0]}\n"  # Номер заявки
                            f"Дата: {result[1]}\n"  # Дата заявки
                            f"Город: {result[2]}\n"  # Город
                            f"Адрес: {result[3]}\n"  # Адрес
                            f"Лифт: {result[4]}\n"  # Тип лифта
                            f"Причина: {result[5]}\n"  # Причина
                            f"Комментарий: {result[6]}"  # Комментарий
                        )
                        self.clipboard_clear()  # Очищаем буфер обмена
                        self.clipboard_append(result_str)  # Добавляем результат в буфер обмена
                        connection2.commit()
                    else:
                        mb.showinfo('Информация', 'Нет данных для выбранного элемента.')
            except mariadb.Error as e:
                showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        else:
            mb.showerror('Вы не выбрали строку')

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_select_city(self, *args):
        selected_city = self.city.get()

    def switch(self):
        pc = {1, 2}
        if self.is_on:
            self.on_button.config(image=self.on)
            self.my_label.config(text="Чужие заявки", fg="red")
            self.pc_id = (self.enabled.get() % len(pc)) + 1
            self.enabled.set(self.pc_id)
            self.view_records()
            self.is_on = False
        else:
            self.on_button.config(image=self.off)
            self.my_label.config(text="Мои заявки", fg="green")
            self.pc_id = (self.enabled.get() % len(pc))  + 1
            self.enabled.set(self.pc_id)
            self.view_records()
            self.is_on = True

#ФУНКЦИЯ ПО ПОЛУЧЕНИЮ ГОРОДА И ДАЛЬНЕЙШЕМУ ПАРСИНГУ АДРЕСОВ В ОКОШКО ПО ГОРОДАМ
    def on_select_city(self, *args):
        self.selected_city = self.city.get()
        self.listbox.delete(0, tk.END)
        self.listbox_type.delete(0, tk.END)
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f'''
                    SELECT {table_street}.улица,
                           {table_doma}.номер AS дом,
                           {table_padik}.Номер AS падик
                    FROM {table_goroda}
                    JOIN {table_street} ON {table_goroda}.id = {table_street}.id_город
                    JOIN {table_doma} ON {table_street}.id = {table_doma}.id_улица
                    JOIN {table_lifts} ON {table_doma}.id = {table_lifts}.id_дом
                    JOIN {table_padik} ON {table_lifts}.id_подъезд = {table_padik}.id
                    WHERE {table_goroda}.город = "{self.selected_city}"
                    GROUP BY {table_street}.улица, {table_doma}.номер, {table_padik}.Номер
                    ORDER BY {table_street}.улица, {table_doma}.номер, {table_padik}.Номер;''')
                self.data_streets = cursor.fetchall()
                for d in self.data_streets:
                    self.address_str = f"{d['улица']}, {d['дом']}, {d['падик']}"
                    self.listbox.insert(tk.END, self.address_str)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    # def show_menu(self, event):
    #     menu = tk.Menu(self.tree, tearoff=False, font=20)
    #     settings_menu = tk.Menu(tearoff=False, font=20)
    #     settings_menu.add_command(label="ошибка а0", command=lambda: self.error("ошибка а0"))
    #     settings_menu.add_command(label="ошибка a2", command=lambda: self.error("ошибка a2"))
    #     settings_menu.add_command(label="ошибка 43", command=lambda: self.error("ошибка 43"))
    #     settings_menu.add_command(label="ошибка 44", command=lambda: self.error("ошибка 44"))
    #     settings_menu.add_command(label="ошибка 45", command=lambda: self.error("ошибка 45"))
    #     settings_menu.add_command(label="ошибка 46", command=lambda: self.error("ошибка 46"))
    #     settings_menu.add_command(label="ошибка 48", command=lambda: self.error("ошибка 48"))
    #     settings_menu.add_command(label="ошибка 49", command=lambda: self.error("ошибка 49"))
    #     settings_menu.add_command(label="ошибка 50", command=lambda: self.error("ошибка 50"))
    #     settings_menu.add_command(label="ошибка 52", command=lambda: self.error("ошибка 52"))
    #     settings_menu.add_command(label="ошибка 53", command=lambda: self.error("ошибка 53"))
    #     settings_menu.add_command(label="ошибка 56", command=lambda: self.error("ошибка 56"))
    #     settings_menu.add_command(label="ошибка 57", command=lambda: self.error("ошибка 57"))
    #     settings_menu.add_command(label="ошибка 58", command=lambda: self.error("ошибка 58"))
    #     settings_menu.add_command(label="ошибка 59", command=lambda: self.error("ошибка 59"))
    #     settings_menu.add_command(label="ошибка 60", command=lambda: self.error("ошибка 60"))
    #     settings_menu.add_command(label="ошибка 64", command=lambda: self.error("ошибка 64"))
    #     settings_menu.add_command(label="ошибка 67", command=lambda: self.error("ошибка 67"))
    #     settings_menu.add_command(label="ошибка 70", command=lambda: self.error("ошибка 70"))
    #     settings_menu.add_command(label="ошибка 71", command=lambda: self.error("ошибка 71"))
    #     settings_menu.add_command(label="ошибка 96", command=lambda: self.error("ошибка 96"))
    #     settings_menu.add_command(label="ошибка 99", command=lambda: self.error("ошибка 99"))
    #     settings_menu.add_command(label="Частотник", command=lambda: self.error("Частотник"))
    #     settings_menu.add_command(label="До наладчика", command=lambda: self.error("До наладчика"))
    #     settings_menu.add_command(label="Ревизия/инспекция", command=lambda: self.error("Лифт в ревизии/инспекции"))
    #     settings_menu.add_command(label="Аварийная блокировка", command=lambda: self.error("Аварийная блокировка"))
    #     menu.add_cascade(label="Ошибка", command=lambda: self.error("Ошибка"), menu=settings_menu)
    #     menu.add_command(label="Копировать заявку", command=lambda: self.clipboard())
    #     menu.add_command(label="Редактировать", command=lambda: self.edit("Редактировать"))
    #     menu.add_command(label="Отметить Время", command=lambda: self.time_to("Отметить Время"))
    #     menu.add_command(label="Комментировать", command=lambda: self.open_comment("Комментировать"))
    #     menu.add_separator()
    #     menu.add_command(label="Ложная Заявка", command=lambda: self.lojnaya("Ложная Заявка"))
    #     menu.add_command(label="Отсутствие электроэнергии", command=lambda: self.error("Отсутствие электроэнергии"))
    #     menu.add_command(label="Пожарная сигнализация", command=lambda: self.error("Пожарная сигнализация"))
    #     menu.add_command(label="Вандальные действия", command=lambda: self.error("Вандальные действия"))
    #     menu.add_separator()
    #     menu.add_command(label="Удалить Заявку", command=lambda: self.delete("Удалить Заявку"))
    #     menu.post(event.x_root, event.y_root)

    # ===РЕДАКТИРОВАТЬ========================================================================
    def edit(self, event):
        if self.tree.selection():
            try:
                with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                    cursor = connection2.cursor(dictionary=True)
                    cursor.execute(f'''SELECT z.id,
                                       FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                                       w.ФИО AS Диспетчер,
                                       g.город AS Город,
                                       CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                       тип_лифта,
                                       причина,
                                       m.ФИО,
                                       FROM_UNIXTIME(дата_запуска, '%d.%m.%Y, %H:%i') AS дата_запуска,
                                       комментарий
                                FROM {table_zayavki} z
                                JOIN {table_workers} w ON z.id_диспетчер = w.id
                                JOIN {table_goroda} g ON z.id_город = g.id
                                JOIN {table_street} s ON z.id_улица = s.id
                                JOIN {table_doma} d ON z.id_дом = d.id
                                JOIN {table_padik} p ON z.id_подъезд = p.id
                                JOIN {table_workers} m ON z.id_механик = m.id
                                     where z.id=?''',
                                   (self.tree.set(self.tree.selection()[0], '#11'),))
                    rows = cursor.fetchall()
                    Child(rows)
            except mariadb.Error as e:
                showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        else:
            mb.showerror("Ошибка","Строка для редактирования не выбрана")
            return

    # ===ВСТАВКА ВРЕМЕНИ В БД=======================================================================
    def time_to(self, event):
        date_ = (datetime.datetime.now(tz=None)).strftime("%d.%m.%Y, %H:%M")
        time_obj = datetime.datetime.strptime(date_, time_format)
        unix_time = int(time_obj.timestamp())
        if self.tree.selection():
            try:
                with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                    cursor = connection2.cursor()
                    cursor.execute(f'''SELECT Дата_запуска from {table_zayavki} WHERE id=?''',
                                   [self.tree.set(self.tree.selection()[0], '#11')])
                    info = cursor.fetchone()
                    connection2.commit()
                    if info[0] is None:
                        try:
                            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                                cursor = connection2.cursor()
                                cursor.execute(
                                    f'''UPDATE {table_zayavki} set Дата_запуска=? WHERE ID=?''',
                                    [unix_time, self.tree.set(self.tree.selection()[0], '#11')])
                                connection2.commit()
                        except mariadb.Error as e:
                            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
                    else:
                        mb.showerror("Ошибка","Строка со временем уже заполнена")
                        return
            except mariadb.Error as e:
                showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        else:
            mb.showerror("Ошибка","Строка не выбрана")
            return
        self.view_records()
        msg = f"Время отмечено!"
        mb.showinfo("Информация", msg)

    # ===УДАЛЕНИЕ СТРОКИ=====================================================================
    def delete(self, event):
        if self.tree.selection():
            result = askyesno(title="Подтвержение операции", message="УДАЛИТЬ строчку?")
            if result:
                try:
                    with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                        cursor = connection2.cursor()
                        id_value = self.tree.set(self.tree.selection()[0], '#11')
                        cursor.execute(f'''UPDATE {table_zayavki} 
                                            SET Дата_заявки = NULL,
                                                id_Диспетчер = NULL,
                                                id_город = NULL,
                                                id_улица = NULL,
                                                id_дом = NULL,
                                                id_подъезд = NULL,
                                                тип_лифта = NULL,
                                                Причина = NULL,
                                                Дата_запуска = NULL,
                                                id_Механик = NULL,
                                                Комментарий = NULL,
                                                id_Лифт = NULL,
                                                pc_id = NULL
                                            WHERE ID = ?''', (id_value,))
                        connection2.commit()
                except mariadb.Error as e:
                    showinfo('Информация', f"Ошибка удаления записи: {e}")
            else:
                showinfo("Результат", "Операция отменена")
        else:
            mb.showerror(
                "Ошибка",
                "Строка не выбрана")
            return
        self.view_records()

    # ===ОТМЕТИТЬ ЛОЖНУЮ==============================================================================
    def lojnaya(self, event):
        date_ = (datetime.datetime.now(tz=None)).strftime("%d.%m.%Y, %H:%M")
        time_obj = datetime.datetime.strptime(date_, time_format)
        unix_time = int(time_obj.timestamp())
        if self.tree.selection():
            try:
                with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                    cursor = connection2.cursor()
                    cursor.execute(f'''UPDATE {table_zayavki} set Дата_запуска=?, Комментарий=? WHERE ID=?''',
                                   [unix_time, f'{event}', self.tree.set(self.tree.selection()[0], '#11')])
                    connection2.commit()
            except mariadb.Error as e:
                showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        else:
            mb.showerror("Ошибка","Строка не выбрана")
            return
        self.view_records()
        msg = f"Запись отредактирована!"
        mb.showinfo("Информация", msg)

    # ===ОТМЕТИТЬ ОШИБКУ==============================================================================
    def error(self, event):
        if self.tree.selection():
            try:
                with closing(mariadb.connect(user=user, password=password, host=host, port=port,
                                             database=database)) as connection2:
                    cursor = connection2.cursor()
                    cursor.execute(f'''UPDATE {table_zayavki} set Комментарий=? WHERE ID=?''',
                                   [f'{event}', self.tree.set(self.tree.selection()[0], '#11')])
                    connection2.commit()
            except mariadb.Error as e:
                showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        else:
            mb.showerror("Ошибка", "Строка не выбрана")
            return
        self.view_records()
        msg = f"Запись отредактирована!"
        mb.showinfo("Информация", msg)

    # ===ФУНКЦИЯ КОММЕНТИРОВАНИЯ==================================================
    def open_comment(self, event):
        if self.tree.selection():
            try:
                with closing(mariadb.connect(user=user, password=password, host=host, port=port,
                                             database=database)) as connection2:
                    cursor = connection2.cursor()
                    selected_item_id = self.tree.selection()[0]  # Получаем ID выбранного элемента
                    item_id = self.tree.set(selected_item_id, '#11')
                    cursor.execute(f'''select Комментарий from {table_zayavki} WHERE ID=?''', (item_id,))
                    connection2.commit()
                    now = cursor.fetchone()
                    Comment(now)
            except mariadb.Error as e:
                showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        else:
            mb.showerror("Ошибка","Строка не выбрана")
            return

    def update_forward(self):
        self.current_month_index = (self.current_month_index + 1) % 12
        self.month_label.config(text=self.months[self.current_month_index])
        if self.current_month_index == 0:
            self.current_year_index += 1
            self.year_label.config(text=self.current_year_index)
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''SELECT z.Номер_заявки,
                                   FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                                   w.ФИО AS Диспетчер,
                                   g.город AS Город,
                                   CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                   тип_лифта,
                                   причина,
                                   m.ФИО,
                                   FROM_UNIXTIME(дата_запуска, '%d.%m.%Y, %H:%i') AS Дата_запуска,
                                   комментарий,
                                   z.id
                            FROM {table_zayavki} z
                            JOIN {table_workers} w ON z.id_диспетчер = w.id
                            JOIN {table_goroda} g ON z.id_город = g.id
                            JOIN {table_street} s ON z.id_улица = s.id
                            JOIN {table_doma} d ON z.id_дом = d.id
                            JOIN {table_padik} p ON z.id_подъезд = p.id
                            JOIN {table_workers} m ON z.id_механик = m.id
                                WHERE z.Причина <> "Линейная" and FROM_UNIXTIME(Дата_заявки, '%m') = ?
                                and FROM_UNIXTIME(Дата_заявки, '%Y') = ? and z.pc_id = ?
                                order by z.id;''',
                               (f'{str(self.current_month_index + 1).zfill(2)}', f'{str(self.current_year_index)}', self.enabled.get()))
                [self.tree.delete(i) for i in self.tree.get_children()]
                for row in cursor.fetchall():
                    if row[-3] is None and int((datetime.datetime.strptime(row[1], time_format)).timestamp()) < int(
                            (time.time()) - 86400):
                        self.tree.insert('', 'end', values=tuple(row), tags=('Red.Treeview',))
                    elif row[-3] is None:
                        self.tree.insert('', 'end', values=tuple(row), tags=('Blue.Treeview',))
                    else:
                        self.tree.insert('', 'end', values=tuple(row))
                connection.commit()
                self.tree.yview_moveto(1.0)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    def update_backward(self):
        self.current_month_index = (self.current_month_index - 1) % 12
        self.month_label.config(text=self.months[self.current_month_index])
        if self.current_month_index == 11:
            self.current_year_index -= 1
            self.year_label.config(text=self.current_year_index)
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port,
                                         database=database)) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''SELECT z.Номер_заявки,
                                   FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                                   w.ФИО AS Диспетчер,
                                   g.город AS Город,
                                   CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                   тип_лифта,
                                   причина,
                                   m.ФИО,
                                   FROM_UNIXTIME(дата_запуска, '%d.%m.%Y, %H:%i') AS Дата_запуска,
                                   комментарий,
                                   z.id
                            FROM {table_zayavki} z
                            JOIN {table_workers} w ON z.id_диспетчер = w.id
                            JOIN {table_goroda} g ON z.id_город = g.id
                            JOIN {table_street} s ON z.id_улица = s.id
                            JOIN {table_doma} d ON z.id_дом = d.id
                            JOIN {table_padik} p ON z.id_подъезд = p.id
                            JOIN {table_workers} m ON z.id_механик = m.id
                                WHERE z.Причина <> "Линейная" and FROM_UNIXTIME(Дата_заявки, '%m') = ?
                                and FROM_UNIXTIME(Дата_заявки, '%Y') = ? and z.pc_id = ?
                                order by z.id;''',
                               (f'{str(self.current_month_index + 1).zfill(2)}', f'{str(self.current_year_index)}',
                                self.enabled.get()))
                [self.tree.delete(i) for i in self.tree.get_children()]
                for row in cursor.fetchall():
                    if row[-3] is None and int((datetime.datetime.strptime(row[1], time_format)).timestamp()) < int(
                            (time.time()) - 86400):
                        self.tree.insert('', 'end', values=tuple(row), tags=('Red.Treeview',))
                    elif row[-3] is None:
                        self.tree.insert('', 'end', values=tuple(row), tags=('Blue.Treeview',))
                    else:
                        self.tree.insert('', 'end', values=tuple(row))
                connection.commit()
                self.tree.yview_moveto(1.0)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    def print_info(self, event):
        self.selected_date = self.calendar.get_date()
        self.selected_date_str = self.selected_date.strftime('%d.%m.%Y')
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''SELECT g.город as Город,
                                    SUM(CASE WHEN z.Причина = 'Застревание' THEN 1 ELSE 0 END) as Застр,
                                    SUM(CASE WHEN z.Причина IN ('Остановлен', 'Неисправность') THEN 1 ELSE 0 END) as Неиспр,
                                    SUM(CASE WHEN z.Причина IN ('Остановлен', 'Неисправность', 'Застревание') THEN 1 ELSE 0 END) as Кол_во
                                    FROM {table_zayavki} z
                                    JOIN {table_goroda} g ON z.id_город = g.id
                                    WHERE DATE_FORMAT(FROM_UNIXTIME(z.Дата_заявки), '%d.%m.%Y') = ?
                                    GROUP BY Город;''',
                (self.selected_date_str,))
                [self.tree2.delete(i) for i in self.tree2.get_children()]
                [self.tree2.insert('', 'end', values=row) for row in cursor.fetchall()]
                connection.commit()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    # ===ОСТАНОВЛЕННЫЕ ЛИФТЫ==================================================================================
    def stop_lift(self):
        self.tree.tag_configure("Red.Treeview", foreground="red")
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''SELECT z.Номер_заявки,
                                       FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                                       w.ФИО AS Диспетчер,
                                       g.город AS Город,
                                       CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                       тип_лифта,
                                       причина,
                                       m.ФИО,
                                       FROM_UNIXTIME(дата_запуска, '%d.%m.%Y, %H:%i') AS Дата_запуска,
                                       комментарий,
                                       z.id
                                FROM {table_zayavki} z
                                JOIN {table_workers} w ON z.id_диспетчер = w.id
                                JOIN {table_goroda} g ON z.id_город = g.id
                                JOIN {table_street} s ON z.id_улица = s.id
                                JOIN {table_doma} d ON z.id_дом = d.id
                                JOIN {table_padik} p ON z.id_подъезд = p.id
                                JOIN {table_workers} m ON z.id_механик = m.id
                                WHERE Причина="Остановлен"
                                and Дата_запуска is Null and z.pc_id = ?
                                order by z.id;''', (self.enabled.get(),))
                [self.tree.delete(i) for i in self.tree.get_children()]
                for row in cursor.fetchall():
                    self.tree.insert('', 'end', values=tuple(row), tags=('Red.Treeview',))
                    connection.commit()
                self.tree.yview_moveto(1.0)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    # ===НЕЗАКРЫТЫЕ ЗАЯВКИ==================================================================================
    def non_start_lift(self):
        try:
            self.tree.tag_configure("Blue.Treeview", foreground="#1437FF")
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor()
                cursor.execute(f'''SELECT z.Номер_заявки,
                                       FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                                       w.ФИО AS Диспетчер,
                                       g.город AS Город,
                                       CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                       тип_лифта,
                                       причина,
                                       m.ФИО,
                                       FROM_UNIXTIME(дата_запуска, '%d.%m.%Y, %H:%i') AS Дата_запуска,
                                       комментарий,
                                       z.id
                                FROM {table_zayavki} z
                                JOIN {table_workers} w ON z.id_диспетчер = w.id
                                JOIN {table_goroda} g ON z.id_город = g.id
                                JOIN {table_street} s ON z.id_улица = s.id
                                JOIN {table_doma} d ON z.id_дом = d.id
                                JOIN {table_padik} p ON z.id_подъезд = p.id
                                JOIN {table_workers} m ON z.id_механик = m.id
                                WHERE Дата_запуска is Null and not Причина in ("Остановлен", "Линейная") and z.pc_id = ?
                                order by z.id;''', (self.enabled.get(),))
                [self.tree.delete(i) for i in self.tree.get_children()]
                for row in cursor.fetchall():
                    self.tree.insert('', 'end', values=tuple(row), tags=('Blue.Treeview',))
                self.tree.yview_moveto(1.0)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")


    # ===ОТКРЫТЫЕ ЛИНЕЙНЫЕ ЗАЯВКИ==================================================================================
    def open_line_lift(self):
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port,
                                         database=database)) as connection2:
                cursor = connection2.cursor()
                cursor.execute(f'''SELECT z.Номер_заявки,
                                       FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                                       w.ФИО AS Диспетчер,
                                       g.город AS Город,
                                       CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                       тип_лифта,
                                       причина,
                                       m.ФИО,
                                       FROM_UNIXTIME(дата_запуска, '%d.%m.%Y, %H:%i') AS Дата_запуска,
                                       комментарий,
                                       z.id
                                FROM {table_zayavki} z
                                JOIN {table_workers} w ON z.id_диспетчер = w.id
                                JOIN {table_goroda} g ON z.id_город = g.id
                                JOIN {table_street} s ON z.id_улица = s.id
                                JOIN {table_doma} d ON z.id_дом = d.id
                                JOIN {table_padik} p ON z.id_подъезд = p.id
                                JOIN {table_workers} m ON z.id_механик = m.id
                                WHERE Дата_запуска is Null and Причина = "Линейная" and z.pc_id = ?
                                order by z.id;''', (self.enabled.get(),))
                [self.tree.delete(i) for i in self.tree.get_children()]
                for row in cursor.fetchall():
                    self.tree.insert('', 'end', values=tuple(row), tags=('Orange.Treeview',))
                self.tree.yview_moveto(1.0)

        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    # ===ЗАКРЫТЫЕ ЛИНЕЙНЫЕ ЗАЯВКИ==================================================================================
    def close_line_lift(self):
        try:
            self.tree.tag_configure("Violet.Treeview", foreground="#7B00B4")
            with closing(mariadb.connect(user=user, password=password, host=host, port=port,
                                         database=database)) as connection2:
                cursor = connection2.cursor()
                cursor.execute(f'''SELECT z.Номер_заявки,
                                       FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                                       w.ФИО AS Диспетчер,
                                       g.город AS Город,
                                       CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                       тип_лифта,
                                       причина,
                                       m.ФИО,
                                       FROM_UNIXTIME(дата_запуска, '%d.%m.%Y, %H:%i') AS Дата_запуска,
                                       комментарий,
                                       z.id
                                FROM {table_zayavki} z
                                JOIN {table_workers} w ON z.id_диспетчер = w.id
                                JOIN {table_goroda} g ON z.id_город = g.id
                                JOIN {table_street} s ON z.id_улица = s.id
                                JOIN {table_doma} d ON z.id_дом = d.id
                                JOIN {table_padik} p ON z.id_подъезд = p.id
                                JOIN {table_workers} m ON z.id_механик = m.id
                                WHERE Дата_запуска > 100 and Причина = "Линейная" and z.pc_id = ?
                                order by z.id;''', (self.enabled.get(),))
                [self.tree.delete(i) for i in self.tree.get_children()]
                for row in cursor.fetchall():
                    self.tree.insert('', 'end', values=tuple(row), tags=('Violet.Treeview',))
                self.tree.yview_moveto(1.0)

        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")


    # ===ЗАПУЩЕННЫЕ ЛИФТЫ==================================================================================
    def start_lift(self):
        self.tree.tag_configure("Green.Treeview", foreground="#06B206")
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''SELECT z.Номер_заявки,
                                       FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                                       w.ФИО AS Диспетчер,
                                       g.город AS Город,
                                       CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                       тип_лифта,
                                       причина,
                                       m.ФИО,
                                       FROM_UNIXTIME(дата_запуска, '%d.%m.%Y, %H:%i') AS Дата_запуска,
                                       комментарий,
                                       z.id
                                FROM {table_zayavki} z
                                JOIN {table_workers} w ON z.id_диспетчер = w.id
                                JOIN {table_goroda} g ON z.id_город = g.id
                                JOIN {table_street} s ON z.id_улица = s.id
                                JOIN {table_doma} d ON z.id_дом = d.id
                                JOIN {table_padik} p ON z.id_подъезд = p.id
                                JOIN {table_workers} m ON z.id_механик = m.id
                                where Причина="Остановлен" 
                                and Дата_запуска is not Null and z.pc_id = ?
                                order by z.id;''', (self.enabled.get(),))
                [self.tree.delete(i) for i in self.tree.get_children()]
                for row in cursor.fetchall():
                    self.tree.insert('', 'end', values=row, tags=('Green.Treeview',))
                connection.commit()
                self.tree.yview_moveto(1.0)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    # ===Открытие файла excel================================================================
    def open_bd_to_excel(self):
        if self.tree.selection():
            selected_items = self.tree.selection()
            selected_ids = [self.tree.item(item, 'values')[-1] for item in selected_items]
            selected_id_str = ', '.join([f'"{id}"' for id in selected_ids])
            conn = pymysql.connect(user=user, password=password, host=host, port=port, database=database)
            cursor = conn.cursor()
            sql_query = f'''SELECT z.Номер_заявки,
                                   FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                                   w.ФИО AS Диспетчер,
                                   g.город AS Город,
                                   CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                   Тип_лифта,
                                   Причина,
                                   m.ФИО as Механик,
                                   FROM_UNIXTIME(дата_запуска, '%d.%m.%Y, %H:%i') AS Дата_запуска,
                                   Комментарий
                            FROM {table_zayavki} z
                            JOIN {table_workers} w ON z.id_диспетчер = w.id
                            JOIN {table_goroda} g ON z.id_город = g.id
                            JOIN {table_street} s ON z.id_улица = s.id
                            JOIN {table_doma} d ON z.id_дом = d.id
                            JOIN {table_padik} p ON z.id_подъезд = p.id
                            JOIN {table_workers} m ON z.id_механик = m.id 
                                    WHERE z.id in ({selected_id_str})'''
            cursor.execute(sql_query)
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=[i[0] for i in cursor.description])
            conn.close()
            Excel(df)
        else:
            msg = f"Нужно выделить одну или несколько строк, которые нужно вставить в excel"
            mb.showerror("Ошибка!", msg)

    # ===РЕДАКТИРОВАНИЕ ДАННЫХ В БД===================================================================
    def update_record(self, data, dispetcher, town, street, house, padik, type_lift, prichina, fio_meh, date_to_go, comment):
        try:
            date_object = datetime.datetime.strptime(data, time_format)
            if date_to_go == None or date_to_go == '':
                date_to_go = None
                val1 = (int(date_object.timestamp()),
                        dispetcher, town, street, house,
                        padik, type_lift, prichina, fio_meh,
                        date_to_go, comment)
            else:
                try:
                    date_object2 = datetime.datetime.strptime(date_to_go, time_format)
                    val1 = (int(date_object.timestamp()),
                            dispetcher, town, street, house,
                            padik, type_lift, prichina,fio_meh,
                        int(date_object2.timestamp()), comment)
                except ValueError:
                    msg = "Введите дату в формате ДД.ММ.ГГГГ, ЧЧ:ММ или нажмите на нужную заявку, а потом на кнопку 'Отметить время'"
                    mb.showerror("Ошибка", msg)
                    return
        except ValueError:
            msg = "Введите дату в формате ДД.ММ.ГГГГ, ЧЧ:ММ или нажмите на нужную заявку, а потом на кнопку 'Отметить время'"
            mb.showerror("Ошибка", msg)
            return
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''UPDATE {table_zayavki} z
                                    JOIN {table_workers} w_disp ON z.id_Диспетчер = w_disp.id
                                    JOIN {table_goroda} g ON z.id_город = g.id
                                    JOIN {table_street} s ON z.id_улица = s.id
                                    JOIN {table_doma} d ON z.id_дом = d.id
                                    JOIN {table_padik} p ON z.id_подъезд = p.id
                                    JOIN {table_workers} w_mech ON z.id_Механик = w_mech.id
                                    SET z.Дата_заявки = ?, 
                                        z.id_Диспетчер = ?, 
                                        z.id_город = ?, 
                                        z.id_улица = ?, 
                                        z.id_дом = ?, 
                                        z.id_подъезд = ?, 
                                        z.тип_лифта = ?, 
                                        z.Причина = ?, 
                                        z.id_Механик = ?, 
                                        z.Дата_запуска = ?, 
                                        z.Комментарий = ?
                                    WHERE z.ID = ?;''',
                               (val1 + (self.tree.set(self.tree.selection()[0], '#11'),)))
                connection.commit()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.view_records()
        msg = f"Запись отредактирована!"
        mb.showinfo("Информация", msg)

    # ===ФУНКЦИЯ КНОПКИ ЧЕРЕЗ КОММЕНТИРОВАНИЯ================================================
    def comment(self, comment):
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor()
                cursor.execute(f'''UPDATE {table_zayavki} SET Комментарий=? WHERE ID=?''',
                               (comment, self.tree.set(self.tree.selection()[0], '#11')))
                connection2.commit()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.view_records()
        msg = f"Комментарий добавлен!"
        mb.showinfo("Информация", msg)

    # ===ФУНКЦИЯ ОБНОВЛЕНИЯ ДАННЫХ В TREEVIEW==========================================
    def view_records(self):
        self.current_month_index = int((datetime.datetime.now(tz=None)).strftime("%m")) - 1
        self.current_year_index = int((datetime.datetime.now(tz=None)).strftime("%Y"))
        self.month_label.config(text=self.months[(self.current_month_index) % 12])
        self.year_label.config(text=self.current_year_index)
        self.tree.tag_configure("Red.Treeview", foreground="red")
        self.tree.tag_configure("Blue.Treeview", foreground="#1437FF")
        self.tree.tag_configure("Violet.Treeview", foreground="#7B00B4")
        date_obj = datetime.datetime.now()
        formatted_date = date_obj.strftime('%d.%m.%Y')
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''SELECT
                                        z.Номер_заявки,
                                        FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                                        w.ФИО AS Диспетчер,
                                        g.Город AS Город,
                                        CONCAT(s.Улица, ', ', d.Номер, ', ', p.Номер) AS Адрес,
                                        z.Тип_лифта,
                                        z.Причина,
                                        m.ФИО AS Механик,
                                        FROM_UNIXTIME(z.Дата_запуска, '%d.%m.%Y, %H:%i') AS Дата_запуска,
                                        z.Комментарий,
                                        z.id
                                    FROM {table_zayavki} z
                                    JOIN {table_workers} w ON z.id_диспетчер = w.id
                                    JOIN {table_goroda} g ON z.id_город = g.id
                                    JOIN {table_street} s ON z.id_улица = s.id
                                    JOIN {table_doma} d ON z.id_дом = d.id
                                    JOIN {table_padik} p ON z.id_подъезд = p.id
                                    JOIN {table_workers} m ON z.id_механик = m.id
                                    WHERE z.Причина <> "Линейная" and DATE_FORMAT(FROM_UNIXTIME(z.Дата_заявки), '%m') = ?
                                AND DATE_FORMAT(FROM_UNIXTIME(z.Дата_заявки), '%Y') = ? and z.pc_id = ?
                                order by z.id;''',
                               (f'{str(self.current_month_index + 1).zfill(2)}', f'{str(self.current_year_index)}', self.enabled.get()))
                [self.tree.delete(i) for i in self.tree.get_children()]
                for row in cursor.fetchall():
                    if row[-3] is None and int((datetime.datetime.strptime(row[1], time_format)).timestamp()) < int((time.time()) - 86400):
                        self.tree.insert('', 'end', values=tuple(row), tags=('Red.Treeview',))
                    elif row[-3] is None:
                        self.tree.insert('', 'end', values=tuple(row), tags=('Blue.Treeview',))
                    else:
                        self.tree.insert('', 'end', values=tuple(row))
                self.tree.yview_moveto(1.0)
                connection.commit()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.print_info(formatted_date)

    # ===ФУНКЦИЯ КНОПКИ ПОИСКА ПО АДРЕСУ===============================================
    def search_records(self, town, adress, calendar1, calendar2):
        self.town = town
        self.adress = adress
        self.calendar1 = calendar1
        self.calendar2 = calendar2
        time_obj1 = datetime.datetime.strptime(self.calendar1, '%d.%m.%Y')
        time_obj2 = datetime.datetime.strptime(self.calendar2, '%d.%m.%Y')
        unix_time1 = int(time_obj1.timestamp())
        unix_time2 = int(time_obj2.timestamp()) + 86400
        try:
            conn = mariadb.connect(user=user, password=password, host=host, port=port, database=database)
            cur = conn.cursor()
            cur.execute(f'''SELECT z.Номер_заявки,
                           FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%Y, %H:%i') AS Дата_заявки,
                           w.ФИО AS Диспетчер,
                           g.город AS Город,
                           CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                           тип_лифта,
                           причина,
                           m.ФИО,
                           FROM_UNIXTIME(дата_запуска, '%d.%m.%Y, %H:%i') AS Дата_запуска,
                           комментарий,
                           z.id
                            FROM {table_zayavki} z
                            JOIN {table_workers} w ON z.id_диспетчер = w.id
                            JOIN {table_goroda} g ON z.id_город = g.id
                            JOIN {table_street} s ON z.id_улица = s.id
                            JOIN {table_doma} d ON z.id_дом = d.id
                            JOIN {table_padik} p ON z.id_подъезд = p.id
                            JOIN {table_workers} m ON z.id_механик = m.id
                            WHERE CONCAT(s.улица, ', ', d.номер, ', ', p.номер) LIKE ? 
                            and Дата_заявки BETWEEN "{unix_time1}" and "{unix_time2}"''', (f"%{adress}%",))
            [self.tree.delete(i) for i in self.tree.get_children()]
            for row in cur.fetchall():
                self.tree.insert('', 'end', values=row)
            children = self.tree.get_children()
            if children:
                self.tree.selection_set(children)
                self.tree.focus(children[0])
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        except Exception as e:
            showinfo('Информация', f"Произошла непредвиденная ошибка: {e}")
        else:
            if not self.tree.get_children():
                showinfo('Информация', "Нет заявок")

    def open_search_dialog(self):
        Search()

    # ===ОБНОВЛЕНИЕ СТРОК ФИО И АДРЕСОВ В ЛИСТБОКСАХ============================================
    def obnov(self):
        self.entry3.delete(0, tk.END)
        self.entry4.delete(0, tk.END)
        self.entry7.delete(0, tk.END)
        self.tree.yview_moveto(1)
        self.check_input_address()
        self.check_input_fio()
    # === Парсинг ФИО из списка бд фамилий в listbox ===
    def check_input_fio(self, _event=None):
        value7 = self.entry7.get().lower()
        names = []
        try:
            with closing(
                    mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f"select id, ФИО from {table_workers} where Должность = 'Механик' order by ФИО")
                self.data_meh = cursor.fetchall()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        for i in self.data_meh:
            names.append(''.join(i['ФИО']))
        if value7 == '':
            self.listbox_values7.set(names)
        else:
            data7 = [item7 for item7 in names if item7.lower().startswith(value7)]
            self.listbox_values7.set(data7)

    # === Вставка выбранного ФИО из парсинга в entrybox ===
    def on_change_selection_fio(self, event):
        selection7 = event.widget.curselection()
        if selection7:
            self.index7 = selection7[0]
            self.data7 = event.widget.get(self.index7)
            for d in self.data_meh:
                if self.data7 == d['ФИО']:
                    self.selected_meh_id = d['id']
            self.entry_text7.set(self.data7)
            self.check_input_fio()

    # ===ПАРСИНГ ТИПА ЛИФТОВ ИЗ СПИСКА ЛИФТОВ В ЛИСТБОКС======================
    def check_input_lifts(self, _event=None):
        selected_address = self.data3
        types = []
        street, house, entrance = selected_address.split(', ')
        try:
            with closing(
                    mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f'''SELECT Тип_лифта
                                    FROM {table_lifts}
                                    JOIN {table_padik} ON {table_lifts}.id_подъезд = {table_padik}.id
                                    JOIN {table_doma} ON {table_lifts}.id_дом = {table_doma}.id
                                    JOIN {table_street} ON {table_doma}.id_улица = {table_street}.id
                                    JOIN {table_goroda} ON {table_street}.id_город = {table_goroda}.id
                                    WHERE {table_goroda}.город = "{self.selected_city}" AND {table_street}.улица = "{street}"
                                    and {table_doma}.номер = "{house}" and {table_padik}.номер = "{entrance}" 
                                    order BY {table_street}.улица, {table_doma}.`номер`, {table_padik}.`номер`''')
                data_lifts = cursor.fetchall()
                for lift in data_lifts:
                    lift_str = f"{lift['Тип_лифта']}"
                    types.append(lift_str)
                    self.listbox_type.insert(tk.END, lift_str)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        if self.entry_text4.get() == '':
            self.listbox_values_type.set(types)
            self.entry4.delete(0, tk.END)
        else:
            data2 = [item for item in types if
                    self.entry_text4.get().lower() in item.lower()]
            self.listbox_values_type.set(data2)

    # ===ПАРСИНГ АДРЕСОВ ИЗ СПИСКА АДРЕСОВ В ЛИСТБОКС=========================
    def check_input_address(self, _event=None):
        self.listbox_type.delete(0, tk.END)
        names = []
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f'''
                        SELECT {table_street}.Улица, {table_doma}.Номер AS дом, {table_padik}.Номер AS подъезд
                        FROM {table_street}
                        JOIN {table_doma} ON {table_street}.id = {table_doma}.id_улица
                        JOIN {table_lifts} ON {table_doma}.id = {table_lifts}.id_дом
                        JOIN {table_padik} ON {table_lifts}.id_подъезд = {table_padik}.id
                        JOIN {table_goroda} ON {table_street}.id_город = {table_goroda}.id
                        WHERE {table_goroda}.Город = '{self.selected_city}'
                        group BY {table_street}.`Улица`, {table_doma}.`Номер`, {table_padik}.`Номер`
						ORDER BY {table_street}.`Улица`, {table_doma}.`Номер`, {table_padik}.`Номер`''')
                data_streets = cursor.fetchall()
                for d in data_streets:
                    address_str = f"{d['Улица']}, {d['дом']}, {d['подъезд']}"
                    names.append(address_str)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        if self.entry3.get().lower() == '':
            self.listbox_values.set(names)
            self.entry4.delete(0, tk.END)
        else:
            data = [item for item in names if self.entry3.get().lower() in item.lower()]
            self.listbox_values.set(data)
            self.on_change_selection_address

    # ===ВСТАВКА ЛИФТА ИЗ ПАРСИНГА В ЛИСТБОКС=============================
    def on_change_selection_lift(self, event):
        self.selection = event.widget.curselection()
        if self.selection:
            self.index4 = self.selection[0]
            self.data4 = event.widget.get(self.index4)
            self.entry_text4.set(self.data4)
        self.check_input_lifts()
    # ===ВСТАВКА АДРЕСА ИЗ ПАРСИНГА В ЛИСТБОКС=============================
    def on_change_selection_address(self, event):
        self.selection = event.widget.curselection()
        if self.selection:
            self.index3 = self.selection[0]
            self.data3 = event.widget.get(self.index3)
            self.entry_text3.set(self.data3)
            self.check_input_address()
        self.check_input_lifts()

    # ===ВСТАВКА ГОРОДА ИЗ ПАРСИНГА В ЛИСТБОКС=============================
    def on_change_selection_town(self, event):
        self.selection = event.widget.curselection()
        if self.selection:
            self.index2 = self.selection[0]
            self.data2 = event.widget.get(self.index2)
            self.entry_text2.set(self.data2)
            self.check_input_town()
        #self.check_input_lifts()

    def create_combobox(self, combo_text, town):
        frame = ttk.Frame(borderwidth=1, relief=SOLID, padding=[8, 10])
        label = ttk.Label(self, text=combo_text)
        label.pack(anchor=NW)
        combo = ttk.Combobox(self, values=town)
        combo.pack(anchor=NW, side=LEFT)
        return frame

    # --------------------------------------------------------------
    def select(self):
        self.type_li = self.entry4.get()
        self.adress_excel = self.entry_text3.get()
        self.ala = self.prich5.get()
        fio_excel = self.entry_text7.get()


    def check_lineyki(self, adres_info_lift):

        return False

    def sql_insert(self):
        selected_disp_str = eval(self.disp.get())
        self.selected_disp_id = selected_disp_str['id']
        self.selected_disp_name = selected_disp_str['ФИО']
        date_ = (datetime.datetime.now(tz=None)).strftime("%d.%m.%Y, %H:%M")
        time_obj = datetime.datetime.strptime(date_, time_format)
        unix_time = int(time_obj.timestamp())
        d = (datetime.datetime.now(tz=None)).strftime("%d")
        val2 = [self.selected_disp_name, self.selected_city, self.entry_text3.get(),
                self.entry_text4.get(), self.prich5.get(), self.entry_text7.get()]
        naz = ['Диспетчер', 'Город', 'Адрес', 'Тип лифта', 'Причина остановки', 'ФИО механика']
        for i in range(len(val2)):
            if len(val2[i]) < 2:
                mb.showerror(
                    "Ошибка",
                    f"Введите данные в строке: {naz[i]}")
                return
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection:
                cursor = connection.cursor()
                cursor.execute(f"SELECT COALESCE(MAX(Номер_заявки), 0) FROM {table_zayavki} "
                               f"WHERE DATE_FORMAT(FROM_UNIXTIME(""Дата_заявки), '%Y-%m') = ?",
                    ((datetime.datetime.now()).strftime('%Y-%m'),))
                number_application = cursor.fetchone()[0]
                number_application += 1
                #===========================================
                data = self.entry_text3.get()
                parts = data.split(',')
                try:
                    with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection:
                        cursor = connection.cursor()
                        cursor.execute(f'''SELECT 
                        {table_goroda}.id AS goroda_id, 
                        {table_street}.id AS street_id, 
                        {table_doma}.id AS doma_id, 
                        {table_padik}.id AS padik_id, 
                        {table_lifts}.id as id_лифт
                            FROM {table_lifts}
                            JOIN {table_padik} ON {table_lifts}.id_подъезд = {table_padik}.id
                            JOIN {table_doma} ON {table_lifts}.id_дом = {table_doma}.id
                            JOIN {table_street} ON {table_doma}.id_улица = {table_street}.id
                            JOIN {table_goroda} ON {table_street}.id_город = {table_goroda}.id
                            WHERE {table_goroda}.город = "{self.selected_city}" 
                            AND {table_street}.улица = "{parts[0].strip()}" 
                            AND {table_doma}.номер = "{parts[1].strip()}" 
                            AND {table_padik}.номер = "{parts[2].strip()}" and тип_лифта="{self.entry_text4.get()}";''')
                        data_lifts = cursor.fetchall()
                        if self.check_lineyki(data_lifts):
                            print("точно создать заявку?")
                        else:
                            print('создаём заявку')
                except mariadb.Error as e:
                    showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
                gorod, street, dom, padik, lift_id = data_lifts[0]
                val = (number_application, unix_time, self.selected_disp_id,
                       gorod, street, dom, padik, self.entry4.get(),
                    self.prich5.get(), None, self.selected_meh_id, '', lift_id, self.pc_id)
                try:
                    with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection:
                        cursor = connection.cursor()
                        cursor.execute(f'''INSERT INTO {table_zayavki} (
                                        Номер_заявки,
                                        Дата_заявки,
                                        id_Диспетчер,
                                        id_город,
                                        id_улица,
                                        id_дом,
                                        id_подъезд,
                                        тип_лифта,
                                        Причина,
                                        Дата_запуска,
                                        id_Механик,
                                        Комментарий,
                                        id_Лифт,
                                        pc_id) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''',(val))
                        connection.commit()
                except mariadb.Error as e:
                    showinfo('Информация', f"Ошибка при работе с базой данных123: {e}")
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        msg = f"Запись успешно добавлена! Её порядковый номер - {number_application}"
        mb.showinfo("Информация", msg)
        self.obnov()

    # ======ФУНКЦИЯ СПРОСА О ЗАКРЫТИИ ПРОГРАММЫ=================================================
    def on_closing(self):
        result = askyesno(title="Подтвержение действия", message="Закрыть программу?")
        if result:
            root.destroy()
        else:
            showinfo("Результат", "Действие отменено.")


#====НАВЕДЕНИЕ МЫШКОЙ НА КОММЕНТ=====================================================================
class Tooltip:
    def __init__(self, widget):
        self.widget = widget
        self.tooltip_window = None
        self.widget.bind("<Motion>", self.on_mouse_move)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.last_row_id = None
        self.last_column_id = None

    def on_mouse_move(self, event):
        row_id = self.widget.identify_row(event.y)
        column_id = self.widget.identify_column(event.x)

        if row_id != self.last_row_id or column_id != self.last_column_id:
            self.last_row_id = row_id
            self.last_column_id = column_id
            self.hide_tooltip()

            if row_id and column_id == '#10':  # '#10' это индекс колонки 'comment'
                comment_text = self.widget.item(row_id, 'values')[9]
                self.show_tooltip(event, comment_text)

    def show_tooltip(self, event, text):
        if self.tooltip_window is not None:
            return

        # Создаем всплывающее окно
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)

        # Получаем размеры окна и подсказки
        x = self.widget.winfo_rootx() + event.x
        y = self.widget.winfo_rooty() + event.y + 20  # Смещение вниз

        # Учитываем размеры экрана
        screen_width = self.widget.winfo_toplevel().winfo_screenwidth()
        tooltip_width = 200  # Ширина подсказки
        if x + tooltip_width > screen_width:
            x = self.widget.winfo_rootx() + event.x - tooltip_width - 20  # Сдвигаем влево, если выходит за пределы

        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=text, background="yellow", wraplength=tooltip_width)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window is not None:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# ====ВЫЗОВ ФУНКЦИЙ КНОПОК РЕДАКТИРОВАНИЯ==================================================================
class Child(tk.Toplevel):
    def __init__(self, rows):
        self.rows = rows
        super().__init__(root)
        self.init_child()
        self.view = app

    def init_child(self):
        self.title('Редактировать')
        self.geometry('500x500+0+0')
        self.resizable(False, False)
        self.wm_attributes('-topmost', 1)

        self.bind('<Unmap>', self.on_unmap)

        font10 = tkFont.Font(family='Helvetica', size=10, weight=tkFont.BOLD)
        font12 = tkFont.Font(family='Helvetica', size=12, weight=tkFont.BOLD)

        label_data1 = tk.Label(self, text='Дата заявки:', font=font12)
        label_data1.place(x=20, y=50)
        label_fio_disp = tk.Label(self, text='Диспетчер:', font=font12)
        label_fio_disp.place(x=20, y=80)
        label_town = tk.Label(self, text='Город:', font=font12)
        label_town.place(x=20, y=110)
        label_adres = tk.Label(self, text='Адрес:', font=font12)
        label_adres.place(x=20, y=140)
        label_type_lift = tk.Label(self, text='Тип лифта:', font=font12)
        label_type_lift.place(x=20, y=170)
        label_stop = tk.Label(self, text='Причина остановки:', font=font12)
        label_stop.place(x=20, y=200)
        label_fio_meh = tk.Label(self, text='ФИО механика:', font=font12)
        label_fio_meh.place(x=20, y=230)
        label_data2 = tk.Label(self, text='Дата запуска:', font=font12)
        label_data2.place(x=20, y=260)
        label_comment = tk.Label(self, text='Комментарий:', font=font12)
        label_comment.place(x=20, y=290)
#===============================================================================================
        self.text_entry_data = tk.StringVar(value=self.rows[0]['Дата_заявки'])
        self.calen1 = tk.Entry(self, textvariable=self.text_entry_data, font=font10)
        self.calen1.place(x=200, y=50)
#================================================================================================
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f"SELECT id, ФИО FROM {table_workers} WHERE Должность = 'Диспетчер'")
                read = cursor.fetchall()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        # Создание словаря с соответствием ФИО и ID диспетчеров
        self.fio_to_id = {i['ФИО']: i['id'] for i in read}
        # Получение списка ФИО диспетчеров
        fio_d = [i['ФИО'] for i in read]
        # Вставляем текущего диспетчера в начало списка
        l1 = [j for j in fio_d]
        l1.insert(0, self.rows[0]['Диспетчер'])
        # Создание Combobox с выбором диспетчера
        self.dispetcher = ttk.Combobox(self, values=list(dict.fromkeys(l1)), font=font10, state='readonly')
        self.dispetcher.current(0)
        self.dispetcher.place(x=200, y=80)
#============================================================================================
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f"select id, город from {table_goroda}")
                data_towns = cursor.fetchall()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.town_to_id = {i['город']: i['id'] for i in data_towns}
        # Получение списка ФИО диспетчеров
        town_d = [i['город'] for i in data_towns]
        g1 = [j for j in town_d]
        g1.insert(0, self.rows[0]['Город'])
        self.combobox_town = ttk.Combobox(self, values=list(dict.fromkeys(g1)), font=font10, state='readonly')
        self.combobox_town.current(0)
        self.combobox_town.place(x=200, y=110)
        self.combobox_town.bind("<<ComboboxSelected>>", self.on_town_select)
#=============================================================================================
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f'''SELECT
                                    {table_goroda}.id as goroda_id,
                                    {table_goroda}.город,
                                    CONCAT({table_street}.улица, ', ', {table_doma}.номер, ', ', {table_padik}.номер) as Адрес,
                                    {table_street}.id as street_id,
                                    {table_street}.улица as улица,
                                    {table_doma}.id as doma_id,
                                    {table_doma}.номер as дом,
                                    {table_padik}.id as padik_id,
                                    {table_padik}.номер as подъезд
                                FROM {table_goroda}
                                JOIN {table_street} ON {table_goroda}.id = {table_street}.id_город
                                JOIN {table_doma} ON {table_street}.id = {table_doma}.id_улица
                                JOIN {table_lifts} ON {table_doma}.id = {table_lifts}.id_дом
                                JOIN {table_padik} ON {table_lifts}.id_подъезд = {table_padik}.id
                                WHERE {table_goroda}.город = '{self.combobox_town.get()}'
                                group BY {table_street}.`Улица`, {table_doma}.`Номер`, {table_padik}.`Номер`
                                ORDER BY {table_street}.улица, {table_doma}.номер, {table_padik}.номер;''')
                self.adreses = cursor.fetchall()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.street_to_id = {i['улица']: i['street_id'] for i in self.adreses}
        self.house_to_id = {i['дом']: i['doma_id'] for i in self.adreses}
        self.padik_to_id = {i['подъезд']: i['padik_id'] for i in self.adreses}
        adres_list = [i['Адрес'] for i in self.adreses]
        self.selected_address = tk.StringVar(value=self.rows[0]['Адрес'])
        self.address_combobox = ttk.Combobox(self, textvariable=self.selected_address, font=font10, width=30, state='readonly')
        adres_list.insert(0, self.rows[0]['Адрес'])
        self.address_combobox['values'] = adres_list
        self.address_combobox.place(x=200, y=140)
        self.address_combobox.bind("<<ComboboxSelected>>", self.on_address_select)
        self.street, self.house, self.entrance = self.address_combobox.get().split(', ')

#=============================================================================================
        self.selected_type = tk.StringVar(value=self.rows[0]['тип_лифта'])
        self.combobox_lift = ttk.Combobox(self, textvariable=self.selected_type, font=font10, state='readonly')
        self.street, self.house, self.entrance = self.address_combobox.get().split(', ')
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''SELECT {table_lifts}.тип_лифта
                                    FROM {table_lifts}
                                    JOIN {table_padik} ON {table_lifts}.id_подъезд = {table_padik}.id
                                    JOIN {table_doma} ON {table_lifts}.id_дом = {table_doma}.id
                                    JOIN {table_street} ON {table_doma}.id_улица = {table_street}.id
                                    JOIN {table_goroda} ON {table_street}.id_город = {table_goroda}.id
                                    WHERE {table_goroda}.город = "{self.combobox_town.get()}" AND {table_street}.улица = "{self.street}"
                                    and {table_doma}.номер = "{self.house}" and {table_padik}.номер = "{self.entrance}"''')
                data_lifts = cursor.fetchall()
                self.add_type_lifts = [lift['тип_лифта'] for lift in data_lifts]
                # Обновление значений комбобокса с типами лифтов
                self.combobox_lift['values'] = self.add_type_lifts
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.combobox_lift.place(x=200, y=170)
#==============================================================================================
        self.combobox_stop = ttk.Combobox(self, values=list(dict.fromkeys(
                    [self.rows[0]['причина'], 'Неисправность', 'Застревание', 'Остановлен', 'Линейная', 'Связь'])), font=font10, state='readonly')
        self.combobox_stop.current(0)
        self.combobox_stop.place(x=200, y=200)
#==============================================================================================
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f"select ФИО, id from {table_workers} where Должность = 'Механик' order by ФИО")
                read = cursor.fetchall()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.meh_to_id = {i['ФИО']: i['id'] for i in read}
        meh = [i['ФИО'] for i in read]
        m1 = [j for j in meh]
        m1.insert(0, self.rows[0]['ФИО'])
        self.combobox_meh = ttk.Combobox(self, values=list(dict.fromkeys(m1)), font=font10, state='readonly')
        self.combobox_meh.current(0)
        self.combobox_meh.place(x=200, y=230)
#====================================================================================
        self.text_entry_zapusk = tk.StringVar(value=self.rows[0]['дата_запуска'])
        self.calen2 = tk.Entry(self, textvariable=self.text_entry_zapusk, font=font10)
        self.calen2.place(x=200, y=260)
#=======================================================================================
        self.text_entry_comment = tk.StringVar(value=self.rows[0]['комментарий'])
        self.entry_comment = tk.Entry(self, textvariable=self.text_entry_comment, font=font10)
        self.entry_comment.place(x=200, y=290)
        btn_cancel = ttk.Button(self, text='Отменить', command=self.destroy)
        btn_cancel.place(x=300, y=350)
        self.btn_ok = ttk.Button(self, text='Сохранить', command=self.save_and_close)
        self.btn_ok.place(x=200, y=350)

    def on_unmap(self, event):
        self.deiconify()  # Отменяем сворачивание дочернего окна

    def deiconify(self):
        if self.state() == 'iconic':
            self.state('normal')

    def on_town_select(self, event):
        selected_town = self.combobox_town.get()
        # Запрос к базе данных для получения типов лифтов на основе выбранного адреса
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f'''SELECT CONCAT({table_street}.улица, ', ', CAST({table_doma}.номер AS CHAR), ', ', CAST({table_padik}.номер AS CHAR)) AS Адрес
                    FROM {table_goroda}
                    JOIN {table_street} ON {table_goroda}.id = {table_street}.id_город
                    JOIN {table_doma} ON {table_street}.id = {table_doma}.id_улица
                    JOIN {table_lifts} ON {table_doma}.id = {table_lifts}.id_дом
                    JOIN {table_padik} ON {table_lifts}.id_подъезд = {table_padik}.id
                    WHERE {table_goroda}.город = "{self.combobox_town.get()}"
                    group BY {table_street}.`Улица`, {table_doma}.`Номер`, {table_padik}.`Номер`
                    order by {table_street}.улица, {table_doma}.номер, {table_padik}.номер''')
                self.adreses = cursor.fetchall()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.add_adres = [adres['Адрес'] for adres in self.adreses]
        # Обновление значений комбобокса с типами лифтов
        self.address_combobox['values'] = self.add_adres
        # Сбрасываем текущее выбранное значение типа лифта
        self.selected_address.set('ВЫБРАТЬ АДРЕС')
        self.selected_type.set('ВЫБРАТЬ ЛИФТ')

    def on_address_select(self, event):
        # Запрос к базе данных для получения типов лифтов на основе выбранного адреса
        self.street, self.house, self.entrance = self.address_combobox.get().split(', ')
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''SELECT {table_lifts}.тип_лифта
                                FROM {table_lifts}
                                JOIN {table_padik} ON {table_lifts}.id_подъезд = {table_padik}.id
                                JOIN {table_doma} ON {table_lifts}.id_дом = {table_doma}.id
                                JOIN {table_street} ON {table_doma}.id_улица = {table_street}.id
                                JOIN {table_goroda} ON {table_street}.id_город = {table_goroda}.id
                                WHERE {table_goroda}.город = "{self.combobox_town.get()}" AND {table_street}.улица = "{self.street}"
                                and {table_doma}.номер = "{self.house}" and {table_padik}.номер = "{self.entrance}"''')
                data_lifts = cursor.fetchall()
                self.add_type_lifts = [lift['тип_лифта'] for lift in data_lifts]
                # Обновление значений комбобокса с типами лифтов
                self.combobox_lift['values'] = self.add_type_lifts
                # Сбрасываем текущее выбранное значение типа лифта
                self.selected_type.set('ВЫБРАТЬ ЛИФТ')
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    def get_selected_dispetcher_id(self):
        selected_dispetcher_fio = self.dispetcher.get()
        selected_dispetcher_id = self.fio_to_id.get(selected_dispetcher_fio)
        return selected_dispetcher_id

    def get_selected_town_id(self):
        selected_town = self.combobox_town.get()
        selected_town_id = self.town_to_id.get(selected_town)
        return selected_town_id

    def get_selected_adres_id(self):
        if self.address_combobox.get() == 'ВЫБРАТЬ АДРЕС':
            return self.address_combobox.get()
        else:
            street, house, padik = self.address_combobox.get().split(',')
            selected_street_id = self.street_to_id.get(street.strip())
            selected_house_id = self.house_to_id.get(house.strip())
            selected_padik_id = self.padik_to_id.get(padik.strip())
            return selected_street_id, selected_house_id, selected_padik_id

    def get_selected_meh_id(self):
        selected_meh_fio = self.combobox_meh.get()
        selected_meh_id = self.meh_to_id.get(selected_meh_fio)
        return selected_meh_id

    def save_and_close(self):
        if self.get_selected_adres_id() == 'ВЫБРАТЬ АДРЕС' or self.selected_type.get() == 'ВЫБРАТЬ ЛИФТ':
            self.grab_set()  # Блокируем доступ к другим окнам
            mb.showerror("Ошибка", "Вы не выбрали АДРЕС или ТИП ЛИФТА")
            self.grab_release()  # Разрешаем доступ к другим окнам
            return
        elif self.get_selected_meh_id() is None:
            self.grab_set()  # Блокируем доступ к другим окнам
            mb.showerror("Ошибка", "Вы не выбрали ФИО механика")
            self.grab_release()  # Разрешаем доступ к другим окнам
            return

        self.view.update_record(
            self.calen1.get(),
            self.get_selected_dispetcher_id(),
            self.get_selected_town_id(),
            self.get_selected_adres_id()[0],
            self.get_selected_adres_id()[1],
            self.get_selected_adres_id()[2],
            self.combobox_lift.get(),
            self.combobox_stop.get(),
            self.get_selected_meh_id(),
            self.calen2.get(),
            self.entry_comment.get())
        self.destroy()

class Search(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.init_search()
        self.view = app

    def init_search(self):
        self.title('Поиск')
        self.geometry('600x400+400+300')
        self.resizable(False, False)
        self.wm_attributes('-topmost', 1)
        self.bind('<Unmap>', self.on_unmap)

        toolbar4 = tk.Frame(self, borderwidth=1, relief="raised")
        toolbar4.pack(side=tk.LEFT, fill=tk.Y)

        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port,
                                         database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f"select id, город from {table_goroda}")
                data_towns = cursor.fetchall()
        except mariadb.Error as e:
            messagebox.showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
            return

        default_town = data_towns[0] if data_towns else ''

        self.label_city = tk.Label(toolbar4, borderwidth=1, width=21, relief="raised", text="Город", font='Calibri 14 bold')
        self.label_city.pack(side=tk.TOP)

        self.canvas = tk.Canvas(toolbar4, width=100)
        self.scrollbar = ttk.Scrollbar(toolbar4, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Привязка событий колесика мыши только к Canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

        self.city = tk.StringVar(value=default_town['город'] if default_town else '')
        self.city.trace("w", self.on_select_city)

        for town in data_towns:
            radiobutton = tk.Radiobutton(self.scrollable_frame, font=('Calibri', 14), text=town['город'],
                                         variable=self.city,
                                         value=town['город'])
            radiobutton.pack(anchor="w")
            radiobutton.bind("<MouseWheel>", self._on_mousewheel)
            radiobutton.bind("<Button-4>", self._on_mousewheel)
            radiobutton.bind("<Button-5>", self._on_mousewheel)
#================================================================================================================
        toolbar5 = tk.Frame(self, borderwidth=1, relief="raised")
        toolbar5.pack(side=tk.LEFT, fill=tk.Y)
        label_adres = tk.Label(toolbar5, borderwidth=1, relief='raised', width=21, text='Адрес', font='Calibri 14 bold')
        label_adres.pack(side=tk.TOP)

        toolbar6 = tk.Frame(self, borderwidth=1, relief="raised")
        toolbar6.pack(side=tk.LEFT, fill=tk.Y)
        label_data = tk.Label(toolbar6, borderwidth=1, relief='raised', width=21, text='Дата', font='Calibri 14 bold')
        label_data.pack()
        label_c = tk.Label(toolbar6, text='с', font='Calibri 15 bold')
        label_c.pack()
        self.calendar1 = DateEntry(toolbar6, locale='ru_RU', font=1)
        self.calendar1.bind("<<DateEntrySelected>>")
        self.calendar1.pack()
        label_po = tk.Label(toolbar6, text='по', font='Calibri 15 bold')
        label_po.pack()
        self.calendar2 = DateEntry(toolbar6, locale='ru_RU', font=1)
        self.calendar2.bind("<<DateEntrySelected>>")
        self.calendar2.pack()

        self.frame_search = tk.Frame(borderwidth=1)
        self.entry_text_address = tk.StringVar()
        self.entry_for_address = tk.Entry(toolbar5, textvariable=self.entry_text_address, width=33)
        self.entry_for_address.bind('<KeyRelease>', self.check_input_address)
        self.entry_for_address.pack()
        self.value_addresses = tk.Variable()

        # Создаем горизонтальный скроллбар
        self.scrollbar_x = tk.Scrollbar(toolbar5, orient=tk.HORIZONTAL)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.listbox_addresses = tk.Listbox(toolbar5, listvariable=self.value_addresses, height=15, width=25, font='Calibri 12')
        self.listbox_addresses.bind('<<ListboxSelect>>', self.on_change_selection_11)
        self.listbox_addresses.pack()
        # Связываем скроллбар с Listbox
        self.listbox_addresses.config(xscrollcommand=self.scrollbar_x.set)
        self.scrollbar_x.config(command=self.listbox_addresses.xview)
        self.selected_city = self.city.get()
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f'''SELECT
                                            {table_goroda}.id as goroda_id,
                                            {table_goroda}.город,
                                            {table_street}.id as street_id,
                                            {table_street}.улица,
                                            {table_doma}.id as doma_id,
                                            {table_doma}.номер as дом,
                                            {table_padik}.id as padik_id,
                                            {table_padik}.номер as подъезд
                                        FROM {table_goroda}
                                        JOIN {table_street} ON {table_goroda}.id = {table_street}.id_город
                                        JOIN {table_doma} ON {table_street}.id = {table_doma}.id_улица
                                        JOIN {table_lifts} ON {table_doma}.id = {table_lifts}.id_дом
                                        JOIN {table_padik} ON {table_lifts}.id_подъезд = {table_padik}.id
                                        WHERE {table_goroda}.город = '{self.selected_city}'
                                        GROUP BY {table_goroda}.id, {table_street}.улица, {table_doma}.номер, {table_padik}.номер
                                        ORDER BY {table_goroda}.id, {table_street}.улица, {table_doma}.номер, {table_padik}.номер;''')
                self.data_streets = cursor.fetchall()
                for d in self.data_streets:
                    self.address_str = f"{d['улица']}, {d['дом']}, {d['подъезд']}"
                    self.listbox_addresses.insert(tk.END, self.address_str)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.frame_search.pack(side=tk.LEFT, anchor=tk.NW)
        style = ttk.Style()
        # Создаем стиль для кнопки "Поиск" с зеленым цветом
        style.configure("Green.TButton", foreground="green", background="#50C878", font='Calibri 12')
        # Создаем стиль для кнопки "Закрыть" с красным цветом
        style.configure("Red.TButton", foreground="red", background="#FCA195", font='Calibri 12')
        toolbar7 = tk.Frame(toolbar6, borderwidth=1, relief="raised")
        toolbar7.pack(side=tk.BOTTOM, fill=tk.Y)
        # Создание и размещение кнопки "Закрыть" большого размера справа снизу
        btn_cancel = ttk.Button(toolbar7, text='Закрыть', style="Red.TButton", command=self.destroy, width=20)
        btn_cancel.pack(side=tk.BOTTOM)  # Установить координаты, ширину и высоту
        # Создание и размещение кнопки "Поиск" большого размера слева снизу
        btn_search = ttk.Button(toolbar7, text='Поиск', style="Green.TButton", command=self.destroy, width=20)
        btn_search.pack(side=tk.BOTTOM)  # Установить координаты, ширину и высоту
        btn_search.bind('<Button-1>', lambda event: (self.view.search_records(self.city, self.entry_for_address.get(), self.calendar1.get(), self.calendar2.get())))

    def on_unmap(self, event):
        self.deiconify()  # Отменяем сворачивание дочернего окна

    def deiconify(self):
        if self.state() == 'iconic':
            self.state('normal')

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_select_city(self, *args):
        selected_city = self.city.get()

    def on_select_city(self, *args):
        self.selected_city = self.city.get()
        # Очистить Listbox перед добавлением новых улиц
        self.listbox_addresses.delete(0, tk.END)
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f'''SELECT {table_street}.Улица, {table_doma}.Номер AS дом, {table_padik}.Номер AS подъезд
                        FROM {table_street}
                        JOIN {table_doma} ON {table_street}.id = {table_doma}.id_улица
                        JOIN {table_lifts} ON {table_doma}.id = {table_lifts}.id_дом
                        JOIN {table_padik} ON {table_lifts}.id_подъезд = {table_padik}.id
                        JOIN {table_goroda} ON {table_street}.id_город = {table_goroda}.id
                        WHERE {table_goroda}.Город = '{self.selected_city}'
                        group BY {table_street}.`Улица`, {table_doma}.`Номер`, {table_padik}.`Номер`
						ORDER BY {table_street}.`Улица`, {table_doma}.`Номер`, {table_padik}.`Номер`''')
                self.data_streets = cursor.fetchall()
                for d in self.data_streets:
                    self.address_str = f"{d['Улица']}, {d['дом']}, {d['подъезд']}"
                    self.listbox_addresses.insert(tk.END, self.address_str)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

        # =========================================================================
    def check_input_address(self, _event=None):
        self.selected_city = self.city.get()
        changed_address = self.entry_text_address.get().lower()
        names = []
        try:
            with closing(mariadb.connect(user=user, password=password, host=host, port=port, database=database)) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f'''SELECT {table_street}.Улица, {table_doma}.Номер AS дом, {table_padik}.Номер AS подъезд
                        FROM {table_street}
                        JOIN {table_doma} ON {table_street}.id = {table_doma}.id_улица
                        JOIN {table_lifts} ON {table_doma}.id = {table_lifts}.id_дом
                        JOIN {table_padik} ON {table_lifts}.id_подъезд = {table_padik}.id
                        JOIN {table_goroda} ON {table_street}.id_город = {table_goroda}.id
                        WHERE {table_goroda}.Город = '{self.selected_city}'
                        group BY {table_street}.`Улица`, {table_doma}.`Номер`, {table_padik}.`Номер`
						ORDER BY {table_street}.`Улица`, {table_doma}.`Номер`, {table_padik}.`Номер`''')
                self.data_streets = cursor.fetchall()
                for d in self.data_streets:
                    self.address_str = f"{d['Улица']}, {d['дом']}, {d['подъезд']}"  # Парсим адреса из файла
                    names.append(''.join(self.address_str).strip())
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        if changed_address == '':  # Если поле ввода пустое, показываем все адреса
            self.value_addresses.set(names)
        else:  # Если введено что-то, показываем только подходящие по шаблону адреса
            data = [item for item in names if changed_address in item.lower()]
            self.value_addresses.set(data)

    def on_change_selection_11(self, event):
        self.selection = event.widget.curselection()
        if self.selection:
            self.index3 = self.selection[0]
            self.data3 = event.widget.get(self.index3)
            self.entry_text_address.set(self.data3)
            self.check_input_address()


# ==========================================================================================
class Comment(tk.Toplevel):
    def __init__(self, now):
        super().__init__()
        self.now = now
        self.init_comm()
        self.view = app
        self.speech_recorder = Speech_recorder()
        self.is_recording = False

    def init_comm(self):
        self.title('Комментировать')
        self.geometry('360x230+400+300')
        self.resizable(False, False)

        self.t = Text(self, height=10, width=30)
        self.t.insert(tk.END, self.now[0])
        self.t.place(x=10, y=10)

        self.btn_micro = ttk.Button(self, text='Сказать\U0001f3a4', command=self.on_microfon_button_click, width=12)
        self.btn_micro.place(x=275, y=8)

        # Метка для инструкций, расположенная под кнопкой
        self.instruction_label = ttk.Label(self, text='', wraplength=300)
        self.instruction_label.place(x=275, y=40)  # Положение метки под кнопкой

        button_cancel = ttk.Button(self, text='Отменить', command=self.destroy)
        button_cancel.place(x=135, y=175)

        button_search = ttk.Button(self, text='Сохранить', command=self.save_and_close)
        button_search.place(x=10, y=175)

        self.t.bind("<Button-3>", self.show_menu)
        self.t.bind_all("<Control-v>", self.paste_text)

    def on_microfon_button_click(self):
        if self.is_recording:
            return

        self.is_recording = True
        self.btn_micro.config(text='Говорите...')
        self.instruction_label.config(text='Говорите', foreground='red')
        self.btn_micro.config(state=tk.DISABLED)
        self.update()

        result = self.speech_recorder.speech()
        cleaned_result = result.replace("Не удалось распознать речь", "").strip()

        current_text = self.t.get("1.0", tk.END).strip()

        # Вставляем очищенный результат в текстовое поле
        if cleaned_result:
            if current_text:  # Проверяем, есть ли уже текст
                self.t.insert(tk.END, ' ' + cleaned_result)  # Добавляем пробел перед новым текстом
            else:
                self.t.insert(tk.END, cleaned_result)  # Вставляем текст без пробела

        self.btn_micro.config(state=tk.NORMAL)
        self.btn_micro.config(text='Сказать\U0001f3a4')
        self.instruction_label.config(text='')  # Сбрасываем текст инструкции
        self.is_recording = False

    def save_and_close(self):
        self.view.comment(self.t.get("1.0", tk.END).strip())
        self.destroy()

    def paste_text(self, event=None):
        text_to_paste = self.clipboard_get()
        self.t.insert(tk.INSERT, text_to_paste)

    def show_menu(self, event):
        # Создаем меню
        menu = tk.Menu(self, tearoff=False, font=20)
        menu.add_command(label="Вставить", command=self.paste_text)
        # Показываем меню в указанной позиции
        menu.post(event.x_root, event.y_root)

class Excel():
    def __init__(self, df):
        self.df = df
        self.open_ex()

    def open_ex(self):
        # Экспортировать данные в Excel
        self.df.to_excel('данные.xlsx', index=False)
        process = subprocess.Popen("данные.xlsx", shell=True)
        process.communicate()


if __name__ == "__main__":
    with open('config.json', 'r') as file:
        data = json.loads(file.read())

    host = data['db_host']
    user = data['db_user']
    password = data['db_password']
    port = data['db_port']
    database = data['db_name']
    table_goroda = data['table_goroda']
    table_street = data['table_street']
    table_doma = data['table_doma']
    table_padik = data['table_padik']
    table_lifts = data['table_lifts']
    table_uk = data['table_uk']
    table_zayavki = data['table_zayavki']
    table_workers = data['table_workers']

    time_format = "%d.%m.%Y, %H:%M"

    root = tk.Tk()
    app = Main(root)
    app.pack()
    root.title("Электронный журнал")
    root.geometry("1920x1080")
    root.iconphoto(False, tk.PhotoImage(file='mitol.png'))
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()