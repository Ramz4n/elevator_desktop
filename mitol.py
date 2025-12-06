from imports import *

class Main(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        root.title("Восток")
        root.state("zoomed")
        root.resizable(False, True)
        self.session = Session()
        self.db_manager = DataBaseManager()
        self.tables = self.db_manager.db_tables()
        self.workers = self.tables['table_workers']
        self.goroda = self.tables['table_goroda']
        self.zayavki = self.tables['table_zayavki']
        self.street = self.tables['table_street']
        self.doma = self.tables['table_doma']
        self.padik = self.tables['table_padik']
        self.lifts = self.tables['table_lifts']
        self.main()
        self.afternoon_statistic_window = None


    def main(self):
        with open('config.json', 'r') as file:
            data = json.loads(file.read())

        self.pc_id = data['pc_id']
        m = Menu(root)
        root.config(menu=m)
        fm = Menu(m, font=20)
        m.add_cascade(label="МЕНЮ", menu=fm)
        fm.add_command(label="Открыть в экселе", command=self.open_bd_to_excel)
        fm.add_command(label="Дневная статистика", command=self.afternoon_statistic)
        # =======1 ОСНОВНОЙ TOOLBAR====================================================================
        toolbar_general = tk.Frame(borderwidth=1, relief="raised")
        toolbar_general.pack(side=tk.TOP, fill=tk.X)
        # ===============================№1 ДИСПЕТЧЕРА===========================================================
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''select id, ФИО from {self.workers} where Должность="Диспетчер" and is_active = 1 order by ФИО''')
                data_workers = cursor.fetchall()
        except:
            mb.showerror("Ошибка", "Нет подключения к базе данных")
            sys.exit()
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''select w.id, w.ФИО from {self.zayavki} z
                        JOIN {self.workers} w ON z.id_диспетчер = w.id
                        where pc_id={self.pc_id}
                        ORDER BY z.id DESC LIMIT 1''')
                data_worker = cursor.fetchone()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

        # Создаем toolbar для диспетчеров
        toolbar_dispetcher = tk.Frame(toolbar_general, borderwidth=1, relief="raised")
        toolbar_dispetcher.pack(side=tk.LEFT, fill=tk.Y)

        label_dispetcher = tk.Label(toolbar_dispetcher, borderwidth=1, width=21, relief="raised", text="Диспетчер", font='Calibri 16 bold')
        label_dispetcher.pack(side=tk.TOP, fill=tk.X)

        self.canvas_dispetcher = tk.Canvas(toolbar_dispetcher, width=100)
        y_scrollbar_dispetcher = ttk.Scrollbar(toolbar_dispetcher, orient="vertical", command=self.canvas_dispetcher.yview)
        scrollable_frame_dispetcher = ttk.Frame(self.canvas_dispetcher)

        scrollable_frame_dispetcher.bind(
                            "<Configure>",
                            lambda e: self.canvas_dispetcher.configure(
                                scrollregion=self.canvas_dispetcher.bbox("all")))
        self.canvas_dispetcher.create_window((0, 0), window=scrollable_frame_dispetcher, anchor="nw")
        self.canvas_dispetcher.configure(yscrollcommand=y_scrollbar_dispetcher.set)

        self.canvas_dispetcher.pack(side="left", fill="both", expand=True)
        y_scrollbar_dispetcher.pack(side="right", fill="y")

        # Привязка событий колесика мыши только к Canvas
        self.canvas_dispetcher.bind("<MouseWheel>", self._on_mousewheel2)
        self.canvas_dispetcher.bind("<Button-4>", self._on_mousewheel2)
        self.canvas_dispetcher.bind("<Button-5>", self._on_mousewheel2)

        self.workers_dict = {disp['ФИО']: disp['id'] for disp in data_workers}

        # Устанавливаем значение для StringVar
        self.disp = tk.StringVar(value=data_worker['ФИО'] if data_worker else '')
        self.disp.trace("w", self.on_select_disp)

        for disp in data_workers:
            radiobutton = tk.Radiobutton(scrollable_frame_dispetcher, font=('Calibri', 16), text=disp['ФИО'],
                                         variable=self.disp,
                                         value=disp['ФИО'])
            radiobutton.pack(anchor="w")
            radiobutton.bind("<MouseWheel>", self._on_mousewheel2)
            radiobutton.bind("<Button-4>", self._on_mousewheel2)
            radiobutton.bind("<Button-5>", self._on_mousewheel2)

        # =======2 ГОРОДА===========================================================================
        toolbar_city = tk.Frame(toolbar_general, borderwidth=1, relief="raised")
        toolbar_city.pack(side=tk.LEFT, fill=tk.Y)

        try:
            with closing(self.db_manager.connect()) as connection2:
                cursor = connection2.cursor(dictionary=True)
                cursor.execute(f"select id, город from {self.goroda}")
                data_cities = cursor.fetchall()
        except mariadb.Error as e:
            messagebox.showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
            return

        default_town = data_cities[0] if data_cities else ''

        label_city = tk.Label(toolbar_city, borderwidth=1, width=21, relief="raised", text="Город", font='Calibri 16 bold')
        label_city.pack(side=tk.TOP, fill=tk.X)

        self.canvas_city = tk.Canvas(toolbar_city, width=100)
        y_scrollbar_city = ttk.Scrollbar(toolbar_city, orient="vertical", command=self.canvas_city.yview)
        scrollable_frame_city = ttk.Frame(self.canvas_city)

        scrollable_frame_city.bind(
            "<Configure>",
            lambda e: self.canvas_city.configure(
                scrollregion=self.canvas_city.bbox("all")
            )
        )
        self.canvas_city.create_window((0, 0), window=scrollable_frame_city, anchor="nw")
        self.canvas_city.configure(yscrollcommand=y_scrollbar_city.set)

        self.canvas_city.pack(side="left", fill="both", expand=True)
        y_scrollbar_city.pack(side="right", fill="y")

        # Привязка событий колесика мыши только к Canvas
        self.canvas_city.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas_city.bind("<Button-4>", self._on_mousewheel)
        self.canvas_city.bind("<Button-5>", self._on_mousewheel)

        self.value_city = tk.StringVar(value=default_town['город'] if default_town else '')
        self.value_city.trace("w", self.on_select_city)

        for city in data_cities:
            radiobutton = tk.Radiobutton(scrollable_frame_city, font=('Calibri', 16), text=city['город'],
                                         variable=self.value_city,
                                         value=city['город'])
            radiobutton.pack(anchor="w")
            radiobutton.bind("<MouseWheel>", self._on_mousewheel)
            radiobutton.bind("<Button-4>", self._on_mousewheel)
            radiobutton.bind("<Button-5>", self._on_mousewheel)
        # =======3 БЛОК АДРЕСОВ========================================================================
        toolbar_addresses = tk.Frame(toolbar_general, borderwidth=1, relief="raised")
        toolbar_addresses.pack(side=tk.LEFT, fill=tk.Y)

        label_addresses = tk.Label(toolbar_addresses, borderwidth=1, width=21, relief="raised", text="Адрес", font='Calibri 16 bold')
        frame_addresses = tk.Frame()
        self.value_address = tk.StringVar()
        self.entry_addresses = tk.Entry(toolbar_addresses, textvariable=self.value_address, width=33)
        self.entry_addresses.bind('<KeyRelease>', self.check_input_address)
        label_addresses.pack(side=tk.TOP, fill=tk.X)
        self.entry_addresses.pack(side=tk.TOP, expand=True, fill=tk.X)

        self.listbox_values = tk.Variable()
        self.listbox_addresses = tk.Listbox(toolbar_addresses, listvariable=self.listbox_values, width=25, font='Calibri 16')
        self.listbox_addresses.bind('<<ListboxSelect>>', self.on_change_selection_address)

        # Создаем горизонтальный скроллбар
        x_scrollbar_addresses = tk.Scrollbar(toolbar_addresses, orient=tk.HORIZONTAL)
        x_scrollbar_addresses.pack(side=tk.BOTTOM, fill=tk.X)

        # Связываем скроллбар с Listbox
        self.listbox_addresses.config(xscrollcommand=x_scrollbar_addresses.set)
        x_scrollbar_addresses.config(command=self.listbox_addresses.xview)

        # Создаем вертикальный скроллбар
        y_scrollbar_addresses = tk.Scrollbar(toolbar_addresses, orient=tk.VERTICAL)
        y_scrollbar_addresses.pack(side=tk.RIGHT, fill=tk.Y)

        # Связываем скроллбар с Listbox
        self.listbox_addresses.config(yscrollcommand=y_scrollbar_addresses.set)
        y_scrollbar_addresses.config(command=self.listbox_addresses.yview)

        self.listbox_addresses.pack(side=tk.TOP, expand=True)
        frame_addresses.pack(side=tk.LEFT, anchor=tk.NW, expand=True)
        # ======4 БЛОК КОД С ТИПАМИ ЛИФТОВ==================================================================
        toolbar_type_lifts = tk.Frame(toolbar_general, borderwidth=1, relief="raised")
        toolbar_type_lifts.pack(side=tk.LEFT, fill=tk.Y)
        label_type_lifts = tk.Label(toolbar_type_lifts, borderwidth=1, width=12, relief="raised", text="Тип лифта", font='Calibri 16 bold')
        frame_type_lifts = tk.Frame()
        self.value_type_lifts = tk.StringVar()
        self.entry_type_lifts = tk.Entry(toolbar_type_lifts, textvariable=self.value_type_lifts, width=18)
        self.entry_type_lifts.bind('<KeyRelease>', self.check_input_lifts)
        label_type_lifts.pack(side=tk.TOP, fill=tk.X)
        self.entry_type_lifts.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.listbox_values_type = tk.Variable()
        self.listbox_type = tk.Listbox(toolbar_type_lifts, listvariable=self.listbox_values_type, width=14, font='Calibri 16')
        self.listbox_type.bind('<<ListboxSelect>>', self.on_change_selection_lift)

        # Создаем горизонтальный скроллбар
        x_scrollbar_type_lifts = tk.Scrollbar(toolbar_type_lifts, orient=tk.HORIZONTAL)
        x_scrollbar_type_lifts.pack(side=tk.BOTTOM, fill=tk.X)

        # Связываем скроллбар с Listbox
        self.listbox_type.config(xscrollcommand=x_scrollbar_type_lifts.set)
        x_scrollbar_type_lifts.config(command=self.listbox_type.xview)

        self.listbox_type.pack(side=tk.TOP, expand=True, fill=tk.X)
        frame_type_lifts.pack(side=tk.LEFT, anchor=tk.NW, expand=True, fill=tk.X)
        # ======5 БЛОК ПРИЧИНА ОСТАНОВКИ ============================================
        toolbar_prichina = tk.Frame(toolbar_general, borderwidth=1, relief="raised")
        toolbar_prichina.pack(side=tk.LEFT, fill=tk.Y)
        frame_prichina = tk.Frame()
        label_prichina = tk.Label(toolbar_prichina, borderwidth=1, width=14, relief="raised", text="Причина", font='Calibri 16 bold')
        label_prichina.pack(fill=tk.X)
        self.list_prichina = ['Неисправность', 'Застревание', 'Остановлен', 'Связь', 'Линейная', 'Т.О.', 'УК']
        self.value_prichina = tk.StringVar(value='?')
        for pr in self.list_prichina:
            btn_prichina = tk.Radiobutton(toolbar_prichina, text=pr, value=pr, variable=self.value_prichina, font='Calibri  16')
            btn_prichina.pack(anchor=tk.NW, expand=True)
        frame_prichina.pack(side=tk.LEFT, anchor=tk.NW, expand=True)
        # ======6 БЛОК FIO МЕХАНИКА =====================================================
        toolbar_fio_meh = tk.Frame(toolbar_general, borderwidth=1, relief="raised")
        toolbar_fio_meh.pack(side=tk.LEFT, fill=tk.Y)
        label_fio_meh = tk.Label(toolbar_fio_meh, borderwidth=1, width=18, relief="raised", text="ФИО механика", font='Calibri  16 bold')
        frame_fio_meh = tk.Frame()
        self.value_in_entry_fio_meh = tk.StringVar(value='')
        self.entry_fio_meh = tk.Entry(toolbar_fio_meh, textvariable=self.value_in_entry_fio_meh, width=28)
        self.entry_fio_meh.bind('<KeyRelease>', self.parsing_fio_into_listbox)
        label_fio_meh.pack(side=tk.TOP, fill=tk.X)
        self.entry_fio_meh.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.values_listbox_fio_meh = tk.Variable()
        self.listbox_fio_meh = tk.Listbox(toolbar_fio_meh, width=21, listvariable=self.values_listbox_fio_meh, font='Calibri 16')
        self.listbox_fio_meh.bind('<<ListboxSelect>>', self.on_change_selection_fio)

        # Создаем горизонтальный скроллбар
        x_scrollbar_fio_meh = tk.Scrollbar(toolbar_fio_meh, orient=tk.HORIZONTAL)
        x_scrollbar_fio_meh.pack(side=tk.BOTTOM, fill=tk.X)

        # Связываем скроллбар с Listbox
        self.listbox_fio_meh.config(xscrollcommand=x_scrollbar_fio_meh.set)
        x_scrollbar_fio_meh.config(command=self.listbox_fio_meh.xview)

        # Создаем вертикальный скроллбар
        y_scrollbar_fio_meh = tk.Scrollbar(toolbar_fio_meh, orient=tk.VERTICAL)
        y_scrollbar_fio_meh.pack(side=tk.RIGHT, fill=tk.Y)

        # Связываем скроллбар с Listbox
        self.listbox_fio_meh.config(yscrollcommand=y_scrollbar_fio_meh.set)
        y_scrollbar_fio_meh.config(command=self.listbox_fio_meh.yview)

        self.listbox_fio_meh.pack(side=tk.TOP, expand=True, fill=tk.X)
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f"select id, ФИО from {self.workers} where Должность = 'Механик' order by ФИО")
                self.data_meh = cursor.fetchall()
            for d in self.data_meh:
                self.data_meh_name = f"{d['ФИО']}"
                self.data_meh_id = f"{d['id']}"
                self.listbox_fio_meh.insert(tk.END, self.data_meh_name)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        frame_fio_meh.pack(side=tk.LEFT, anchor=tk.NW, expand=True)

        # ================КНОПКИ========================================================
        helv36 = tkFont.Font(family='Helvetica', size=10, weight=tkFont.BOLD)
        general_tool_button = tk.Frame(toolbar_general, borderwidth=1, relief="raised")
        general_tool_button.pack(side=tk.LEFT, fill=tk.X, anchor=tk.W)
        btn_open_dialog = tk.Button(general_tool_button, text='Добавить заявку', command=self.check_values_from_listboxes, bg='#d7d8e0', compound=tk.LEFT, width=19, height=1, font=helv36)
        btn_open_dialog.pack(side=tk.TOP)
        btn_refresh = tk.Button(general_tool_button, text='Обновить', bg='#d7d8e0', compound=tk.TOP, command=lambda: self.event_of_button('all'), width=19, font=helv36)
        btn_refresh.pack(side=tk.TOP)
        btn_search = tk.Button(general_tool_button, text='Поиск адреса', bg='#d7d8e0', compound=tk.TOP, command=lambda: Search(), width=19, font=helv36)
        btn_search.pack(side=tk.TOP)
        # =================КНОПКИ========================================================
        btn_stop = tk.Button(general_tool_button, text='Остановленные лифты', bg='#FFB3AB', compound=tk.TOP, command=lambda: self.event_of_button('stopped'), width=19, font=helv36)
        btn_stop.pack(side=tk.TOP)
        btn_open_ = tk.Button(general_tool_button, text='Незакрытые заявки', bg='#4897FF', compound=tk.TOP, command=lambda: self.event_of_button('open'), width=19, font=helv36)
        btn_open_.pack(side=tk.TOP)
        btn_start = tk.Button(general_tool_button, text='Запущенные лифты', bg='#00AD0E', compound=tk.TOP, command=lambda: self.event_of_button('started'), width=19, font=helv36)
        btn_start.pack(side=tk.TOP)
        #=====================================================================================
        self.is_on = True
        self.enabled = IntVar()
        self.enabled.set(self.pc_id)
        self.my_label = Label(general_tool_button,
                         text="Мои заявки",
                         fg="green",
                         font=("Helvetica", 10))
        self.my_label.pack()
        self.on = PhotoImage(file="on.png")
        self.off = PhotoImage(file="off.png")
        self.on_button = Button(general_tool_button, image=self.off, bd=0, command=self.switch)
        self.on_button.pack()
        btn_lineyka_close = tk.Button(general_tool_button, text='Линейные закрытые', compound=tk.TOP,
                              command=lambda: self.event_of_button('line_close'), width=19, font=helv36, bg='#BE81FF')
        btn_lineyka_close.pack(side=tk.TOP)
        btn_lineyka_open = tk.Button(general_tool_button, text='Линейные открытые', compound=tk.TOP,
                                command=lambda: self.event_of_button('line_open'), width=19, font=helv36)
        btn_lineyka_open.pack(side=tk.TOP)
        btn_svyaz = tk.Button(general_tool_button, text='Связь', compound=tk.TOP,
                                     command=lambda: self.event_of_button('svyaz'), width=19, font=helv36)
        btn_svyaz.pack(side=tk.TOP)
        btn_uk = tk.Button(general_tool_button, text='Заявки УК', compound=tk.TOP,
                              command=lambda: self.event_of_button('uk'), width=19, font=helv36)
        btn_uk.pack(side=tk.TOP)
        # === ПЕРЕЛИСТЫВАНИЕ БД ПО МЕСЯЦАМ=====================================================================
        self.months = ["Январь", "Февраль", "Март", "Апрель",
                       "Май", "Июнь", "Июль", "Август",
                       "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

        toolbar_btn_month = tk.Frame(root)
        toolbar_btn_month.pack(fill='x', pady=10)

        # Слева: entry_num_zayavki - поиск по номеру заявки
        self.values_num_zayavki = tk.Variable()
        self.entry_num_zayavki = tk.Entry(toolbar_btn_month, width=5, font=('Helvetica', 14), textvariable=self.values_num_zayavki)
        self.entry_num_zayavki.pack(side='left', padx=1)
        btn_num_zayavki = tk.Button(toolbar_btn_month, text='🔍', compound=tk.TOP,
                                     command=lambda: self.event_of_button('num'), width=3, font=helv36)
        btn_num_zayavki.pack(side='left')

        # Центр: отдельный фрейм для кнопок и меток
        center_frame = tk.Frame(toolbar_btn_month)
        center_frame.pack(side='left', expand=True)

        # Кнопка "Предыдущий месяц"
        btn_refresh_backward = tk.Button(center_frame, text='Предыдущий месяц', bg='#d7d8e0', compound=tk.CENTER,
                                         command=lambda: self.change_months("backward"), width=19, font='helv36')
        btn_refresh_backward.grid(row=0, column=0, padx=5)

        # Метка месяца
        self.month_label = Label(center_frame, text='', font='Calibri 16 bold')
        self.month_label.grid(row=0, column=1, padx=5)

        # Метка года
        self.year_label = Label(center_frame, text='', font='Calibri 16 bold')
        self.year_label.grid(row=0, column=2, padx=5)

        # Кнопка "Следующий месяц"
        btn_refresh_forward = tk.Button(center_frame, text='Следующий месяц', bg='#d7d8e0', compound=tk.CENTER,
                                        command=lambda: self.change_months("forward"), width=19, font='helv36')
        btn_refresh_forward.grid(row=0, column=3, padx=5)


        # =======ВИЗУАЛ БАЗЫ ДАННЫХ =========================================================================
        style = ttk.Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0, font=('Helvetica', 16), rowheight=23)
        style.configure("mystyle.Treeview.Heading", font=('Helvetica', 16, 'bold'))
        style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])
        self.tree = ttk.Treeview(self, style="mystyle.Treeview",
        columns=('ID', 'date', 'dispetcher', 'town', 'adress', 'type_lift', 'prichina', 'fio', 'ispolnitel', 'date_to_go', 'comment', 'id2'),
                                 height=50, show='headings')
        self.tree.column('ID', width=60, anchor=tk.CENTER, stretch=False)
        self.tree.column('date', width=165, anchor=tk.W, stretch=False)
        self.tree.column('dispetcher', width=120, anchor=tk.W, stretch=False)
        self.tree.column('town', width=120, anchor=tk.W, stretch=False)
        self.tree.column('adress', width=280, anchor=tk.W, stretch=False)
        self.tree.column('type_lift', width=90, anchor=tk.W, stretch=False)
        self.tree.column('prichina', width=130, anchor=tk.W, stretch=False)
        self.tree.column('fio', width=170, anchor=tk.W, stretch=False)
        self.tree.column('ispolnitel', width=170, anchor=tk.W, stretch=False)
        self.tree.column('date_to_go', width=185, anchor=tk.CENTER, stretch=False)
        self.tree.column("comment", width=1000, anchor=tk.W, stretch=True)
        self.tree.column("id2", width=0, anchor=tk.CENTER, stretch=tk.NO)
        self.tree.column('#0', stretch=False)


        self.tree.heading('ID', text='№')
        self.tree.heading('date', text='Дата заявки')
        self.tree.heading('dispetcher', text='Диспетчер')
        self.tree.heading('town', text='Город')
        self.tree.heading('adress', text='Адрес')
        self.tree.heading('type_lift', text='Тип')
        self.tree.heading('prichina', text='Причина')
        self.tree.heading('fio', text='Принял')
        self.tree.heading('ispolnitel', text='Исполнил')
        self.tree.heading('date_to_go', text='Дата устранения')
        self.tree.heading('comment', text='Комментарий', anchor=tk.W)
        self.tree.heading('id2', text='')


        # Создаем экземпляр класса Menu_errors и передаем ему виджет tree
        self.menu_errors = Menu_errors(self.tree, self.clipboard, self.lojnaya, self.error,
                                       self.delete, self.time_to, self.open_comment, self.edit)

        # Привязываем событие правой кнопки мыши к методу show_menu
        self.tree.bind("<Button-3>", self.menu_errors.show_menu)

        y_scrollbar_treeview = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.tree.configure(yscrollcommand=y_scrollbar_treeview.set)
        y_scrollbar_treeview.config(command=self.tree.yview)
        y_scrollbar_treeview.pack(side="right", fill="both")

        x_scrollbar_treeview = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.tree.configure(xscrollcommand=x_scrollbar_treeview.set)
        x_scrollbar_treeview.config(command=self.tree.xview)
        x_scrollbar_treeview.pack(side="bottom", fill="both")

        self.tree.pack(side="left", fill="both")
        self.on_select_city()
        self.event_of_button('all')
        Tooltip(self.tree)

    def choose_ispolnitel(self):
        # Создаем экземпляр класса Add_ispolnitel
        win = Choose_ispolnitel(self.db_manager)
        self.wait_window(win)  # ← САМЫЙ ГЛАВНЫЙ МОМЕНТ
        return win.selected_mechanic

    def change_months(self, direction):
        print(f"Смена месяца: {direction}")  # заглушка для логики смены месяца

    def label_center_switch_name(self, name, color):
        self.label_center.configure(text=f'{name}', bg=f'{color}')

    def get_last_column_value(self):
        try:
            selected_item_id = self.tree.selection()[0]  # получаем выбранный элемент
            value = self.tree.set(selected_item_id, "id2")  # список имён колонок
            return value
        except Exception as e:
            print(f"Ошибка при получении значения последней колонки: {e}")
            return None

    def clipboard(self):
        if self.tree.selection():
            try:
                request_id = self.get_last_column_value()

                with closing(self.db_manager.connect()) as connection:
                    cursor = connection.cursor()
                    cursor.execute(f'''SELECT z.Номер_заявки,
                                       FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%y, %H:%i') AS Дата_заявки,
                                       g.город AS Город,
                                       CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                       тип_лифта,
                                       причина,
                                       комментарий
                                     FROM {self.zayavki} z
                                     JOIN {self.goroda} g ON z.id_город = g.id
                                     JOIN {self.street} s ON z.id_улица = s.id
                                     JOIN {self.doma} d ON z.id_дом = d.id
                                     JOIN {self.padik} p ON z.id_подъезд = p.id
                                     JOIN {self.workers} m ON z.id_механик = m.id
                                     WHERE z.id=?''', [request_id])

                    result = cursor.fetchone()
                    if result:
                        result_str = (
                            f"№: {result[0]}\n" 
                            f"Дата: {result[1]}\n"  
                            f"Город: {result[2]}\n" 
                            f"Адрес: {result[3]}\n" 
                            f"Лифт: {result[4]}\n" 
                            f"Причина: {result[5]}\n"  
                            f"Комментарий: {result[6]}"
                        )
                        self.clipboard_clear()
                        self.clipboard_append(result_str)
                        connection.commit()
                    else:
                        mb.showinfo('Информация', 'Нет данных для выбранного элемента.')
            except mariadb.Error as e:
                showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        else:
            mb.showerror('Вы не выбрали строку')

    def afternoon_statistic(self):
        if self.afternoon_statistic_window is None or not self.afternoon_statistic_window.is_open():
            self.afternoon_statistic_window = Afternoon_statistic(self, self.db_manager, self.enabled.get())
        else:
            self.afternoon_statistic_window.show()

    def _on_mousewheel(self, event):
        self.canvas_city.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel2(self, event):
        self.canvas_dispetcher.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_select_city(self, *args):
        self.selected_city = self.value_city.get()
        self.obnov()

    def on_select_disp(self, *args):
        selected_disp = self.disp.get()
        self.selected_disp_id = self.workers_dict.get(selected_disp)

    def switch(self):
        pc = {1, 2}
        if self.is_on:
            self.on_button.config(image=self.on)
            self.my_label.config(text="Чужие заявки", fg="red")
            self.pc_id = (self.enabled.get() % len(pc)) + 1
            self.enabled.set(self.pc_id)
            self.event_of_button(f'{self.session.get("type_button")}')
            self.is_on = False
        else:
            self.on_button.config(image=self.off)
            self.my_label.config(text="Мои заявки", fg="green")
            self.pc_id = (self.enabled.get() % len(pc))  + 1
            self.enabled.set(self.pc_id)
            self.event_of_button(f'{self.session.get("type_button")}')
            self.is_on = True

    # ===РЕДАКТИРОВАТЬ========================================================================
    def edit(self, event):
        if self.tree.selection():
            try:
                with closing(self.db_manager.connect()) as connection:
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute(f'''SELECT z.id,
                                       FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%y, %H:%i') AS Дата_заявки,
                                       w.ФИО AS Диспетчер,
                                       g.город AS Город,
                                       CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                       тип_лифта,
                                       причина,
                                       m1.ФИО as Принял,
                                       m2.ФИО as Исполнил,
                                       FROM_UNIXTIME(дата_запуска, '%d.%m.%y, %H:%i') AS дата_запуска,
                                       комментарий
                                FROM {self.zayavki} z
                                JOIN {self.workers} w ON z.id_диспетчер = w.id
                                JOIN {self.goroda} g ON z.id_город = g.id
                                JOIN {self.street} s ON z.id_улица = s.id
                                JOIN {self.doma} d ON z.id_дом = d.id
                                JOIN {self.padik} p ON z.id_подъезд = p.id
                                JOIN {self.workers} m1 ON z.id_механик = m1.id
                                LEFT JOIN {self.workers} m2 ON z.id_исполнитель = m2.id
                                     where z.id=?''',
                                   (self.get_last_column_value(),))
                    rows = cursor.fetchall()
                    Edit(rows)
            except mariadb.Error as e:
                showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        else:
            mb.showerror("Ошибка","Строка для редактирования не выбрана")
            return

    # ===ВСТАВКА ВРЕМЕНИ В БД=======================================================================
    def time_to(self, event):
        try:
            selected_id = self.get_last_column_value()
        except:
            mb.showerror("Ошибка", "Строка не выбрана")
            return

        # Проверяем, есть ли время запуска
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    f"SELECT Дата_запуска, id_исполнитель FROM {self.zayavki} WHERE id=?",
                    [selected_id])
                info = cursor.fetchone()

        except mariadb.Error as e:
            showinfo("Информация", f"Ошибка при работе с базой данных: {e}")
            return

        # === ЕСЛИ ВРЕМЯ УЖЕ ЕСТЬ ===
        if info and info[0] is not None and info[1] is None:
            answer = mb.askyesno("Внимание", "Время уже указано.\nВставить исполнителя?")
            if answer:
                mech = self.choose_ispolnitel()
                if mech:
                    self.add_ispolnitel(mech["id"], selected_id)
                    self.event_of_button(self.session.get("type_button"))
                    self.show_temporary_message("Информация", "Исполнитель добавлен!")
            return
        elif info and info[0] is not None and info[1] is not None:
            showinfo("Информация", f"Время и исполнитель уже отмечены. Для дальнейшего изменения зайдите в раздел редактирования!")
            return

        # Теперь ставим время
        try:
            self.id_mechanic = self.choose_ispolnitel()
            # Извлекаем id из словаря, если self.id_mechanic не None
            id_ispolnitel = self.id_mechanic["id"] if self.id_mechanic else None

            date_str = datetime.datetime.now().strftime("%d.%m.%y, %H:%M")
            time_obj = datetime.datetime.strptime(date_str, time_format)
            unix_time = int(time_obj.timestamp())

            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    f"UPDATE {self.zayavki} SET Дата_запуска=?, id_исполнитель=? WHERE ID=?",
                    [unix_time, id_ispolnitel, selected_id]
                )
                connection.commit()

            self.event_of_button(self.session.get("type_button"))
            self.show_temporary_message("Информация", "Время отмечено!")

        except mariadb.Error as e:
            showinfo("Информация", f"Ошибка при работе с базой данных: {e}")

    # ===ДОБАВЛЕНИЕ ИСПОЛНИТЕЛЯ=====================================================================
    def add_ispolnitel(self, id_ispolnitel, selected_id):
        with closing(self.db_manager.connect()) as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"UPDATE {self.zayavki} SET id_исполнитель=? WHERE ID=?",
                [id_ispolnitel, selected_id])
            connection.commit()


    # ===УДАЛЕНИЕ СТРОКИ=====================================================================
    def delete(self, event):
        if self.tree.selection():
            result = askyesno(title="Подтвержение операции", message="УДАЛИТЬ строчку?")
            if result:
                try:
                    with closing(self.db_manager.connect()) as connection:
                        cursor = connection.cursor()
                        id_value = self.get_last_column_value()
                        cursor.execute(f'''UPDATE {self.zayavki} 
                                            SET pc_id = NULL
                                            WHERE ID = ?''', (id_value,))
                        connection.commit()
                except mariadb.Error as e:
                    showinfo('Информация', f"Ошибка удаления записи: {e}")
            else:
                showinfo("Результат", "Операция отменена")
        else:
            mb.showerror(
                "Ошибка",
                "Строка не выбрана")
            return
        self.event_of_button(f'{self.session.get("type_button")}')

    # ===ОТМЕТИТЬ ЛОЖНУЮ==============================================================================
    def lojnaya(self, event):
        date_ = (datetime.datetime.now(tz=None)).strftime("%d.%m.%y, %H:%M")
        time_obj = datetime.datetime.strptime(date_, time_format)
        unix_time = int(time_obj.timestamp())
        if self.tree.selection():
            try:
                with closing(self.db_manager.connect()) as connection:
                    cursor = connection.cursor()
                    cursor.execute(f'''UPDATE {self.zayavki} set Дата_запуска=?, Комментарий=? WHERE ID=?''',
                                   [unix_time, f'{event}', self.get_last_column_value()])
                    connection.commit()
            except mariadb.Error as e:
                showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        else:
            mb.showerror("Ошибка","Строка не выбрана")
            return
        self.event_of_button(f'{self.session.get("type_button")}')
        msg = f"Запись отредактирована!"
        self.show_temporary_message('Информация', msg)

    # ===ОТМЕТИТЬ ОШИБКУ==============================================================================
    def error(self, event):
        if self.tree.selection():
            try:
                with closing(self.db_manager.connect()) as connection:
                    cursor = connection.cursor()
                    cursor.execute(f'''UPDATE {self.zayavki} set Комментарий=? WHERE ID=?''',
                                   [f'{event}', self.get_last_column_value()])
                    connection.commit()
            except mariadb.Error as e:
                showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        else:
            mb.showerror("Ошибка", "Строка не выбрана")
            return
        self.event_of_button(f'{self.session.get("type_button")}')
        msg = f"Запись отредактирована!"
        self.show_temporary_message('Информация', msg)

    # ===ФУНКЦИЯ КОММЕНТИРОВАНИЯ==================================================
    def open_comment(self, event):
        if self.tree.selection():
            try:
                with closing(self.db_manager.connect()) as connection:
                    cursor = connection.cursor()
                    item_id = self.get_last_column_value()
                    cursor.execute(f'''select Комментарий from {self.zayavki} WHERE ID=?''', (item_id,))
                    connection.commit()
                    now = cursor.fetchone()
                    Comment(now)
            except mariadb.Error as e:
                showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        else:
            mb.showerror("Ошибка","Строка не выбрана")
            return

    def change_months(self, text):
        changer = Change_months(text, self.tables, self.db_manager, self.enabled.get(), self.session.get("type_button"),
                                self.month_label, self.year_label, self.months, self.tree, self.current_month_index,
                                self.current_year_index)
        self.current_month_index = changer.month_index
        self.current_year_index = changer.year_index

    def query(self):
        return f'''SELECT z.Номер_заявки,
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
                   FROM {self.zayavki} z
                   JOIN {self.workers} w ON z.id_диспетчер = w.id
                   JOIN {self.goroda} g ON z.id_город = g.id
                   JOIN {self.street} s ON z.id_улица = s.id
                   JOIN {self.doma} d ON z.id_дом = d.id
                   JOIN {self.padik} p ON z.id_подъезд = p.id
                   JOIN {self.workers} m1 ON z.id_механик = m1.id
                   LEFT JOIN {self.workers} m2 ON z.id_исполнитель = m2.id'''


    def event_of_button(self, type_button, town=None, address=None, calendar1=None, calendar2=None, callback=None):
        self.current_month_index = int((datetime.datetime.now(tz=None)).strftime("%m")) - 1
        self.current_year_index = int((datetime.datetime.now(tz=None)).strftime("%y"))
        self.month_label.config(text=self.months[self.current_month_index])
        self.tree.tag_configure("Green.Treeview", foreground="#06B206")
        self.tree.tag_configure("Red.Treeview", foreground="red")
        self.tree.tag_configure("Blue.Treeview", foreground="#1437FF")
        self.tree.tag_configure("Violet.Treeview", foreground="#7B00B4")

        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                query = self.query()

                end = f''' AND FROM_UNIXTIME(Дата_заявки, '%m') = '{str(self.current_month_index + 1).zfill(2)}'
                                AND FROM_UNIXTIME(Дата_заявки, '%y') = '{str(self.current_year_index)}' AND z.pc_id = {self.enabled.get()}
                                order by z.id;'''

                order = f''' AND z.pc_id = {self.enabled.get()}
                                order by z.id;'''

                if type_button == 'all':
                    self.session.delete("type_button")
                    self.session.set("type_button", "all")
                    query += ' WHERE NOT z.Причина in ("Линейная", "Связь")'
                    query += end
                    self.entry_num_zayavki.delete(0, tk.END)
                elif type_button == 'stopped':
                    self.session.delete("type_button")
                    self.session.set("type_button", "stopped")
                    query += ' WHERE Причина="Остановлен" AND Дата_запуска is Null'
                    query += order
                    self.entry_num_zayavki.delete(0, tk.END)
                elif type_button == 'open':
                    self.session.delete("type_button")
                    self.session.set("type_button", "open")
                    query += ' WHERE Дата_запуска is Null AND not Причина IN ("Остановлен", "Линейная", "Связь", "УК")'
                    query += order
                    self.entry_num_zayavki.delete(0, tk.END)
                elif type_button == 'line_open':
                    self.session.delete("type_button")
                    self.session.set("type_button", "line_open")
                    query += ' WHERE Дата_запуска is Null AND Причина IN ("Линейная", "Т.О.")'
                    query += order
                    self.entry_num_zayavki.delete(0, tk.END)
                elif type_button == 'line_close':
                    self.session.delete("type_button")
                    self.session.set("type_button", "line_close")
                    query += ' WHERE Дата_запуска > 100 AND Причина IN ("Линейная", "Т.О.")'
                    query += end
                    self.entry_num_zayavki.delete(0, tk.END)
                elif type_button == 'started':
                    self.session.delete("type_button")
                    self.session.set("type_button", "started")
                    query += ' where Причина="Остановлен" AND Дата_запуска is not Null'
                    query += end
                    self.entry_num_zayavki.delete(0, tk.END)
                elif type_button == 'svyaz':
                    self.session.delete("type_button")
                    self.session.set("type_button", "svyaz")
                    query += ' where Причина="Связь" AND Дата_запуска is Null'
                    query += order
                    self.entry_num_zayavki.delete(0, tk.END)
                elif type_button == 'uk':
                    self.session.delete("type_button")
                    self.session.set("type_button", "uk")
                    query += ' where Причина="УК" AND Дата_запуска is Null'
                    query += order
                    self.entry_num_zayavki.delete(0, tk.END)
                elif type_button == 'num':
                    value = self.values_num_zayavki.get()
                    if not value.strip():
                        self.session.delete("type_button")
                        self.session.set("type_button", "all")
                        query += ' WHERE NOT z.Причина in ("Линейная", "Связь")'
                        query += end
                    else:
                        self.session.delete("type_button")
                        self.session.set("type_button", "num")
                        query += f' where z.Номер_заявки = {value}'
                        query += order
                elif type_button == 'search':
                    self.entry_num_zayavki.delete(0, tk.END)
                    self.session.delete("type_button")
                    self.session.set("type_button", "search")
                    if address:
                        query += f'''  WHERE CONCAT(s.улица, ', ', d.номер, ', ', p.номер) LIKE "%{address}%"'''
                    if calendar1 and calendar2:
                        time_obj2 = datetime.datetime.strptime(calendar2, '%d.%m.%y')
                        unix_time2 = int(time_obj2.timestamp()) + 86400
                        time_obj1 = datetime.datetime.strptime(calendar1, '%d.%m.%y')
                        unix_time1 = int(time_obj1.timestamp())
                        query += f''' and Дата_заявки BETWEEN "{unix_time1}" and "{unix_time2}"'''
                    query += order
                cursor.execute(query)

                [self.tree.delete(i) for i in self.tree.get_children()]
                for row in cursor.fetchall():
                    # заменяем None -> ""
                    row = {k: ("" if v is None else v) for k, v in row.items()}

                    if not row["Дата_запуска"] and row["причина"] == "Остановлен":
                        self.tree.insert('', 'end', values=tuple(row.values()), tags=('Red.Treeview',))
                    elif not row["Дата_запуска"] and row["причина"] in ('Неисправность', 'Застревание'):
                        self.tree.insert('', 'end', values=tuple(row.values()), tags=('Blue.Treeview',))
                    elif row["Дата_запуска"] and row["причина"] == "Остановлен":
                        self.tree.insert('', 'end', values=tuple(row.values()), tags=('Green.Treeview',))
                    elif row["Дата_запуска"] and row["причина"] == "Линейная":
                        self.tree.insert('', 'end', values=tuple(row.values()), tags=('Violet.Treeview',))
                    else:
                        self.tree.insert('', 'end', values=tuple(row.values()))

                connection.commit()
                self.tree.yview_moveto(1.0)
                if callback:
                    callback()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    # ===Открытие файла excel================================================================
    def open_bd_to_excel(self):
        if self.tree.selection():
            selected_items = self.tree.selection()
            selected_ids = [self.tree.item(item, 'values')[-1] for item in selected_items]
            selected_id_str = ', '.join([f'"{id}"' for id in selected_ids])
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor()
                sql_query = f'''SELECT z.Номер_заявки,
                                       FROM_UNIXTIME(z.Дата_заявки, '%d.%m.%y, %H:%i') AS Дата_заявки,
                                       w.ФИО AS Диспетчер,
                                       g.город AS Город,
                                       CONCAT(s.улица, ', ', d.номер, ', ', p.номер) AS Адрес,
                                       Тип_лифта,
                                       Причина,
                                       m.ФИО as Механик,
                                       FROM_UNIXTIME(дата_запуска, '%d.%m.%y, %H:%i') AS Дата_запуска,
                                       Комментарий
                                FROM {self.zayavki} z
                                JOIN {self.workers} w ON z.id_диспетчер = w.id
                                JOIN {self.goroda} g ON z.id_город = g.id
                                JOIN {self.street} s ON z.id_улица = s.id
                                JOIN {self.doma} d ON z.id_дом = d.id
                                JOIN {self.padik} p ON z.id_подъезд = p.id
                                JOIN {self.workers} m ON z.id_механик = m.id 
                                        WHERE z.id in ({selected_id_str})'''
                cursor.execute(sql_query)
                data = cursor.fetchall()
                df = pd.DataFrame(data, columns=[i[0] for i in cursor.description])
                Excel(df)
        else:
            msg = f"Нужно выделить одну или несколько строк, которые нужно вставить в excel"
            mb.showerror("Ошибка!", msg)

    # ===РЕДАКТИРОВАНИЕ ДАННЫХ В БД===================================================================
    def update_record(self, data, dispetcher, town, street, house, padik, type_lift, lift_id, prichina, fio_meh, fio_ispolnitel, date_to_go, comment, callback):
        try:
            date_object = datetime.datetime.strptime(data, time_format)
            if date_to_go == None or date_to_go == '':
                date_to_go = None
                self.value_to_edit = (int(date_object.timestamp()),
                        dispetcher, town, street, house,
                        padik, type_lift, prichina, fio_meh, fio_ispolnitel,
                        date_to_go, comment, lift_id, self.get_last_column_value())
            else:
                try:
                    date_object2 = datetime.datetime.strptime(date_to_go, time_format)
                    self.value_to_edit = (int(date_object.timestamp()),
                            dispetcher, town, street, house,
                            padik, type_lift, prichina, fio_meh, fio_ispolnitel,
                        int(date_object2.timestamp()), comment, lift_id, self.get_last_column_value())
                except ValueError:
                    msg = "Введите дату в формате ДД.ММ.ГГГГ, ЧЧ:ММ или нажмите на нужную заявку, а потом на кнопку 'Отметить время'"
                    mb.showerror("Ошибка", msg)
                    return
        except ValueError:
            msg = "Введите дату в формате ДД.ММ.ГГГГ, ЧЧ:ММ или нажмите на нужную заявку, а потом на кнопку 'Отметить время'"
            mb.showerror("Ошибка", msg)
            return
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''UPDATE {self.zayavki} SET 
                                        Дата_заявки = ?, 
                                        id_Диспетчер = ?, 
                                        id_город = ?, 
                                        id_улица = ?, 
                                        id_дом = ?, 
                                        id_подъезд = ?, 
                                        тип_лифта = ?, 
                                        Причина = ?, 
                                        id_Механик = ?, 
                                        id_исполнитель = ?,
                                        Дата_запуска = ?, 
                                        Комментарий = ?,
                                        id_лифт = ?
                                    WHERE ID = ?;''',
                               self.value_to_edit)
                connection.commit()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.event_of_button(f'{self.session.get("type_button")}')
        msg = f"Запись отредактирована!"
        self.show_temporary_message('Информация', msg)
        if callback:
            callback()

    def comment(self, comment, callback):
        '''
        Добавление комментария через ПКМ.
        '''
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''UPDATE {self.zayavki} SET Комментарий=? WHERE ID=?''',
                               (comment, self.get_last_column_value()))
                connection.commit()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.event_of_button(f'{self.session.get("type_button")}')
        if callback:
            callback()
        msg = f"Комментарий добавлен!"
        self.show_temporary_message('Информация', msg)

    def obnov(self):
        '''
        ОБНОВЛЕНИЕ СТРОК ФИО И АДРЕСА И ЛИФТА В ЛИСТБОКСАХ ПОСЛЕ ДОБАВЛЕНИЯ ЗАЯВКИ.
        '''
        self.entry_addresses.delete(0, tk.END)
        self.entry_type_lifts.delete(0, tk.END)
        self.entry_fio_meh.delete(0, tk.END)
        self.tree.yview_moveto(1)
        self.check_input_address()
        self.parsing_fio_into_listbox()

    def parsing_fio_into_listbox(self, _event=None):
        '''
        Парсинг ФИО из БД фамилий в listbox.
        '''
        selected_fio = self.entry_fio_meh.get().lower()
        names = []
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f"select id, ФИО from {self.workers} where Должность = 'Механик' order by ФИО")
                self.data_meh = cursor.fetchall()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        for i in self.data_meh:
            names.append(''.join(i['ФИО']))
        if selected_fio == '':
            self.values_listbox_fio_meh.set(names)
        else:
            data_fio = [item7 for item7 in names if item7.lower().startswith(selected_fio)]
            self.values_listbox_fio_meh.set(data_fio)

    def on_change_selection_fio(self, event):
        '''
        Вставка выбранного ФИО из парсинга в строку.
        '''
        selection_fio = event.widget.curselection()
        if selection_fio:
            selected_index = selection_fio[0]
            selected_name = event.widget.get(selected_index)
            for mechanic in self.data_meh:
                if selected_name == mechanic['ФИО']:
                    self.selected_meh_id = mechanic['id']
                    break
            self.value_in_entry_fio_meh.set(selected_name)
            self.parsing_fio_into_listbox()

    def check_input_lifts(self, _event=None):
        '''
        ПАРСИНГ ТИПА ЛИФТОВ ИЗ СПИСКА ЛИФТОВ В ЛИСТБОКС.
        '''
        selected_address = self.data3
        types = []
        street, home, entrance = selected_address.split(', ')
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''SELECT Тип_лифта
                                    FROM {self.lifts}
                                    JOIN {self.padik} ON {self.lifts}.id_подъезд = {self.padik}.id
                                    JOIN {self.doma} ON {self.lifts}.id_дом = {self.doma}.id
                                    JOIN {self.street} ON {self.doma}.id_улица = {self.street}.id
                                    JOIN {self.goroda} ON {self.street}.id_город = {self.goroda}.id
                                    WHERE {self.goroda}.город = "{self.selected_city}" AND {self.street}.улица = "{street}"
                                    and {self.doma}.номер = "{home}" and {self.padik}.номер = "{entrance}" 
                                    order BY {self.street}.улица, {self.doma}.номер, {self.padik}.номер''')
                data_lifts = cursor.fetchall()
                for lift in data_lifts:
                    lift_str = f"{lift['Тип_лифта']}"
                    types.append(lift_str)
                    self.listbox_type.insert(tk.END, lift_str)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        if self.value_type_lifts.get() == '':
            self.listbox_values_type.set(types)
            self.entry_type_lifts.delete(0, tk.END)
        else:
            data2 = [item for item in types if
                    self.value_type_lifts.get().lower() in item.lower()]
            self.listbox_values_type.set(data2)

    def check_input_address(self, _event=None):
        '''
        ПАРСИНГ АДРЕСОВ ИЗ БД В ЛИСТБОКС.
        '''
        self.listbox_type.delete(0, tk.END)
        names = []
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''
                        SELECT {self.street}.Улица, {self.doma}.Номер AS дом, {self.padik}.Номер AS подъезд
                        FROM {self.street}
                        JOIN {self.doma} ON {self.street}.id = {self.doma}.id_улица
                        JOIN {self.lifts} ON {self.doma}.id = {self.lifts}.id_дом
                        JOIN {self.padik} ON {self.lifts}.id_подъезд = {self.padik}.id
                        JOIN {self.goroda} ON {self.street}.id_город = {self.goroda}.id
                        WHERE {self.goroda}.Город = '{self.selected_city}' AND {self.doma}.is_active = 1
                        group BY {self.street}.Улица, {self.doma}.Номер, {self.padik}.Номер
						ORDER BY {self.street}.Улица, {self.doma}.Номер, {self.padik}.Номер''')
                data_streets = cursor.fetchall()
                for d in data_streets:
                    address_str = f"{d['Улица']}, {d['дом']}, {d['подъезд']}"
                    names.append(address_str)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        if self.entry_addresses.get().lower() == '':
            self.listbox_values.set(names)
            self.entry_type_lifts.delete(0, tk.END)
        else:
            data = [item for item in names if self.entry_addresses.get().lower() in item.lower()]
            self.listbox_values.set(data)
            self.on_change_selection_address

    def on_change_selection_lift(self, event):
        '''
        ВСТАВКА ЛИФТА ИЗ ПАРСИНГА В ЛИСТБОКС.
        '''
        self.selection = event.widget.curselection()
        if self.selection:
            self.index4 = self.selection[0]
            self.data4 = event.widget.get(self.index4)
            self.value_type_lifts.set(self.data4)
        self.check_input_lifts()

    def on_change_selection_address(self, event):
        '''
        ВСТАВКА АДРЕСА В СТРОКУ ПРИ НАЖАТИИ НА НЕГО ИЗ ПАРСИНГА В ЛИСТБОКС.
        '''
        self.selection = event.widget.curselection()
        if self.selection:
            self.index3 = self.selection[0]
            self.data3 = event.widget.get(self.index3)
            self.value_address.set(self.data3)
            self.check_input_address()
        self.check_input_lifts()
    # --------------------------------------------------------------
    def check_lineyki(self, adres_info_lift):

        return False

    def check_values_from_listboxes(self):
        """
    Проверяет значения, введенные пользователем в интерфейсе, после нажатия на кнопку "Добавить заявку".
    Эта функция выполняет проверку данных, введенных пользователем,
    и вызывает метод для вставки данных в базу данных, если все данные корректны.
    Args:
        self: Экземпляр класса, в котором определена эта функция.
    Process:
        1. Собирает данные из полей ввода: город, адрес, тип лифта, причина остановки и ФИО механика.
        2. Проверяет длину каждого значения. Если длина меньше 2 символов, выводит сообщение об ошибке.
        3. Если все значения корректны, вызывает метод `sql_insert()` для добавления заявки в базу данных.
    Used Methods:
        - self.value_city.get(): Получает значение из поля ввода города.
        - self.value_address.get(): Получает значение из поля ввода адреса.
        - self.value_type_lifts.get(): Получает значение из поля ввода типа лифта.
        - self.value_prichina.get(): Получает значение из поля ввода причины остановки.
        - self.value_in_entry_fio_meh.get(): Получает значение из поля ввода ФИО механика.
        - mb.showerror(): Выводит диалоговое окно с сообщением об ошибке.
        - self.sql_insert(): Выполняет вставку данных в базу данных.
    Note:
        - Функция предполагает, что все необходимые методы и атрибуты определены в классе, к которому она принадлежит.
        - Используется для валидации данных перед их сохранением в базу данных.
        """

        data_string_values = {'Город': self.value_city.get(),
                              'Адрес': self.value_address.get(),
                              'Тип лифта': self.value_type_lifts.get(),
                              'Причина остановки': self.value_prichina.get(),
                              'ФИО механика': self.value_in_entry_fio_meh.get()}

        for key, value in data_string_values.items():
            if len(data_string_values[key]) < 2:
                mb.showerror("Ошибка", f"Введите данные в строке: {key}")
                return
        self.check_similar_info_into_bd(data_string_values)

    def check_similar_info_into_bd(self, data_string_values):
        """
    В эту функцию поступают данные заявки, которую только что ввёл диспетчер.
    После получения данных, делается запрос в БД и проверяется, есть ли такая же заявка в БД.
    Args:
        data_string_values: информация(заявка) введённая диспетчером.
    Process:
        1. Пступают данные 'data_string_values'.
        2. Делается запрос в БД.
        3. Создается переменная 'check_info', которая принимает в себя данные из БД.
        4. Проверяется условие, если данные в переменной 'check_info' есть, значит длина будет > 1, значит такая
        заявка есть -> вывести ошибку. Иначе запустить функцию self.sql_insert().
        """
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor()
                query = self.query()
                end = f''' WHERE g.город = "{data_string_values['Город']}"
                            AND s.улица = "{data_string_values['Адрес'].split(',')[0].strip()}"
                            AND d.номер = "{data_string_values['Адрес'].split(',')[1].strip()}"
                            AND p.номер = "{data_string_values['Адрес'].split(',')[2].strip()}"
                            AND z.тип_лифта = "{data_string_values['Тип лифта']}"
                            AND z.причина = "{data_string_values['Причина остановки']}"
                            AND z.дата_запуска IS NULL AND pc_id is not NULL'''
                query += end
                cursor.execute(query)
                check_info = cursor.fetchall()
                if len(check_info) < 1:
                    self.sql_insert()
                else:
                    mb.showerror("Ошибка", f"Такая заявка уже существует! Её номер №{check_info[0][0]} от {check_info[0][1]}")
                    self.obnov()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")


    def take_address_from_listbox(self):
        """
        Получает id_улицы, id_дома, id_подъезда и id_лифта для дальнейшего заноса этих id в Базу.
        """
        parts_of_address = self.value_address.get().split(',')
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''SELECT 
                                {self.goroda}.id AS goroda_id, 
                                {self.street}.id AS street_id, 
                                {self.doma}.id AS doma_id, 
                                {self.padik}.id AS padik_id, 
                                {self.lifts}.id as id_лифт
                                FROM {self.lifts}
                                JOIN {self.padik} ON {self.lifts}.id_подъезд = {self.padik}.id
                                JOIN {self.doma} ON {self.lifts}.id_дом = {self.doma}.id
                                JOIN {self.street} ON {self.doma}.id_улица = {self.street}.id
                                JOIN {self.goroda} ON {self.street}.id_город = {self.goroda}.id
                                WHERE {self.goroda}.город = "{self.selected_city}" 
                                AND {self.street}.улица = "{parts_of_address[0].strip()}" 
                                AND {self.doma}.номер = "{parts_of_address[1].strip()}" 
                                AND {self.padik}.номер = "{parts_of_address[2].strip()}" and тип_лифта="{self.value_type_lifts.get()}";''')
                data_id_lift = cursor.fetchall()
                return data_id_lift
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    def check_last_maxnumber(self):
        """
        Проверяет последний номер заявки и добавляет для будущей заявки +1 к номеру.
        """
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''SELECT COALESCE(MAX(Номер_заявки), 0) FROM {self.zayavki}
                    WHERE DATE_FORMAT(FROM_UNIXTIME(`Дата_заявки`), '%y-%m') = ?''',
                    ((datetime.datetime.now()).strftime('%y-%m'),))
                number_application = cursor.fetchone()[0]
                return number_application + 1
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    def sql_insert(self):
        """
        Добавляет заявку в БД.
        Variables:
        |data_lifts|: берёт значения(id_улица, id_дом, id_подъезд, id_лифт) из функции self.take_address_from_listbox().
        |number_application|: берёт из функции(self.check_last_maxnumber()) последний номер последней
                              заявки актуального месяца из БД и делает +1.
        |self.on_select_disp()|: передаёт id диспетчера в эту функцию.
        """
        data_id_lift = self.take_address_from_listbox()
        number_application = self.check_last_maxnumber()
        self.on_select_disp()
        date_ = (datetime.datetime.now(tz=None)).strftime("%d.%m.%y, %H:%M")
        time_obj = datetime.datetime.strptime(date_, time_format)
        unix_time = int(time_obj.timestamp())

        town, street, home, entrance, lift_id = data_id_lift[0]

        values = (number_application, unix_time, self.selected_disp_id,
               town, street, home, entrance, self.entry_type_lifts.get(),
            self.value_prichina.get(), None, self.selected_meh_id,
               '', lift_id, self.pc_id)
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor()
                cursor.execute(f'''INSERT INTO {self.zayavki} (
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
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''',(values))
                connection.commit()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных123: {e}")

        msg = f"Запись успешно добавлена! Её порядковый номер - {number_application}"
        self.show_temporary_message('Информация', msg)
        self.event_of_button(f"{self.session.get('type_button')}")
        self.obnov()

    def show_temporary_message(self, title, message, duration=3000, fade_duration=1000):
        """
        Показывает всплывающее окно с сообщением, которое затухает и закрывается через заданное время.
        Args:
        |title|: Заголовок окна.
        |message|: Сообщение для отображения.
        |duration|: Время в миллисекундах, через которое начнется затухание (по умолчанию 3000 мс = 3 секунды).
        |fade_duration|: Время затухания в миллисекундах (по умолчанию 1000 мс = 1 секунда).
        """
        # Создаем новое окно для сообщения
        message_window = tk.Toplevel()
        message_window.title(title)

        # Убираем стандартную верхнюю панель
        message_window.overrideredirect(True)

        # Устанавливаем цвет фона окна
        message_window.configure(bg='lightyellow')

        # Создаем собственную панель заголовка
        title_bar = tk.Frame(message_window, bg='darkblue', relief='raised', bd=2)
        title_bar.pack(fill=tk.X)

        # Устанавливаем шрифт
        title_font = tkfont.Font(family="Helvetica", size=14, weight="bold")
        message_font = tkfont.Font(family="Helvetica", size=12, weight="bold")

        # Добавляем заголовок в панель
        title_label = tk.Label(title_bar, text=title, bg='darkblue', fg='white', font=title_font)
        title_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Добавляем кнопку закрытия
        close_button = tk.Button(title_bar, text='×', bg='darkblue', fg='white', font=title_font,
                                 command=message_window.destroy)
        close_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Устанавливаем сообщение в окне
        label = tk.Label(message_window, text=message, bg='lightyellow', fg='darkblue', font=message_font)
        label.pack(pady=20, padx=20)

        # Обновляем окно, чтобы получить точные размеры
        message_window.update_idletasks()

        # Получаем размеры экрана
        screen_width = message_window.winfo_screenwidth()
        screen_height = message_window.winfo_screenheight()

        # Получаем фактические размеры окна
        window_width = message_window.winfo_width()
        window_height = message_window.winfo_height()

        # Вычисляем координаты для размещения окна по центру
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        # Устанавливаем позицию окна
        message_window.geometry(f'+{x}+{y}')

        # Устанавливаем прозрачность окна
        message_window.attributes("-alpha", 1.0)

        def fade_out():
            # Уменьшаем прозрачность окна до полного исчезновения
            alpha = message_window.attributes("-alpha")
            if alpha > 0:
                alpha -= 0.05
                message_window.attributes("-alpha", alpha)
                message_window.after(fade_duration // 20, fade_out)
            else:
                message_window.destroy()

        # Запускаем затухание через заданное время
        message_window.after(duration, fade_out)

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

        # Проверяем, наведена ли мышь на другую ячейку
        if row_id != self.last_row_id or column_id != self.last_column_id:
            self.last_row_id = row_id
            self.last_column_id = column_id
            self.hide_tooltip()

            # Получаем имя колонки по column_id (например "#3" → "comment")
            try:
                col_index = int(column_id.replace('#', '')) - 1
                col_name = self.widget["columns"][col_index]
            except (ValueError, IndexError):
                col_name = None

            # Проверяем, это ли колонка "comment"
            if row_id and col_name == "comment":
                comment_text = self.widget.set(row_id, col_name)
                if comment_text:  # показываем только если есть текст
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
        screen_height = self.widget.winfo_toplevel().winfo_screenheight()
        tooltip_width = 400  # Ширина подсказки
        tooltip_height = 400
        if x + tooltip_width > screen_width:
            x = self.widget.winfo_rootx() + event.x - tooltip_width  # Сдвигаем по координате х
        if y + tooltip_height > screen_height:
            y = self.widget.winfo_rooty() + event.y - tooltip_height + 280 # Сдвигаем по координате y


        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=text, background="yellow", wraplength=tooltip_width, font=(None, 15))
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window is not None:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# ====ВЫЗОВ ФУНКЦИЙ МЕНЮ РЕДАКТИРОВАНИЯ==================================================================
class Edit(tk.Toplevel):
    def __init__(self, rows):
        self.rows = rows
        super().__init__(root)
        self.db_manager = DataBaseManager()
        self.tables = self.db_manager.db_tables()
        self.workers = self.tables['table_workers']
        self.goroda = self.tables['table_goroda']
        self.zayavki = self.tables['table_zayavki']
        self.street = self.tables['table_street']
        self.doma = self.tables['table_doma']
        self.padik = self.tables['table_padik']
        self.lifts = self.tables['table_lifts']
        self.init_edit()
        self.view = app

    def init_edit(self):
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
        label_fio_meh = tk.Label(self, text='Принял:', font=font12)
        label_fio_meh.place(x=20, y=230)
        label_fio_meh = tk.Label(self, text='Исполнил:', font=font12)
        label_fio_meh.place(x=20, y=260)
        label_data2 = tk.Label(self, text='Дата устранения:', font=font12)
        label_data2.place(x=20, y=290)
        label_comment = tk.Label(self, text='Комментарий:', font=font12)
        label_comment.place(x=20, y=320)
#===============================================================================================
        self.text_entry_data = tk.StringVar(value=self.rows[0]['Дата_заявки'])
        self.calen1 = tk.Entry(self, textvariable=self.text_entry_data, font=font10)
        self.calen1.place(x=200, y=50)
#================================================================================================
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f"SELECT id, ФИО FROM {self.workers} WHERE Должность = 'Диспетчер'")
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
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f"select id, город from {self.goroda}")
                data_towns = cursor.fetchall()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.town_to_id = {i['город']: i['id'] for i in data_towns}

        town_d = [i['город'] for i in data_towns]
        g1 = [j for j in town_d]
        g1.insert(0, self.rows[0]['Город'])
        self.combobox_town = ttk.Combobox(self, values=list(dict.fromkeys(g1)), font=font10, state='readonly')
        self.combobox_town.current(0)
        self.combobox_town.place(x=200, y=110)
        self.combobox_town.bind("<<ComboboxSelected>>", self.on_town_select)
#=============================================================================================
        self.get_street_after_change_town(self.combobox_town.get())

        adres_list = [i['Адрес'] for i in self.adreses]
        self.selected_address = tk.StringVar(value=self.rows[0]['Адрес'])
        self.address_combobox = ttk.Combobox(self, textvariable=self.selected_address, font=font10, width=30, state='readonly')
        adres_list.insert(0, self.rows[0]['Адрес'])
        self.address_combobox['values'] = adres_list
        self.address_combobox.place(x=200, y=140)
        self.address_combobox.bind("<<ComboboxSelected>>", self.on_address_select)
        self.street_name, self.house, self.entrance = self.address_combobox.get().split(', ')

#=============================================================================================
        self.selected_type = tk.StringVar(value=self.rows[0]['тип_лифта'])
        self.combobox_lift = ttk.Combobox(self, textvariable=self.selected_type, font=font10, state='readonly')
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''
                    SELECT {self.lifts}.тип_лифта
                    FROM {self.lifts}
                    JOIN {self.padik} ON {self.lifts}.id_подъезд = {self.padik}.id
                    JOIN {self.doma} ON {self.lifts}.id_дом = {self.doma}.id
                    JOIN {self.street} ON {self.doma}.id_улица = {self.street}.id
                    JOIN {self.goroda} ON {self.street}.id_город = {self.goroda}.id
                    WHERE {self.goroda}.город = "{self.combobox_town.get()}"
                      AND {self.street}.улица = "{self.street_name}"
                      AND {self.doma}.номер = "{self.house}"
                      AND {self.padik}.номер = "{self.entrance}"''')

                data_lifts = cursor.fetchall()
                self.add_type_lifts = [lift['тип_лифта'] for lift in data_lifts]
                # Обновление значений комбобокса с типами лифтов
                self.combobox_lift['values'] = self.add_type_lifts
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.combobox_lift.place(x=200, y=170)
#==============================================================================================
        self.combobox_stop = ttk.Combobox(self, values=list(dict.fromkeys(
                    [self.rows[0]['причина'], 'Неисправность', 'Застревание', 'Остановлен', 'Линейная', 'Связь', 'Т.О.', 'УК'])), font=font10, state='readonly')
        self.combobox_stop.current(0)
        self.combobox_stop.place(x=200, y=200)
#==============================================================================================
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f"select ФИО, id from {self.workers} where Должность = 'Механик' order by ФИО")
                read = cursor.fetchall()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.meh_to_id = {i['ФИО']: i['id'] for i in read}
        meh = [i['ФИО'] for i in read]
        meh.insert(0, self.rows[0]['Принял'])
        self.combobox_meh = ttk.Combobox(self, values=list(dict.fromkeys(meh)), font=font10, state='readonly')
        self.combobox_meh.current(0)
        self.combobox_meh.place(x=200, y=230)
# ==============================================================================================
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f"select ФИО, id from {self.workers} where Должность = 'Механик' order by ФИО")
                read = cursor.fetchall()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.ispolnitel_to_id = {i['ФИО']: i['id'] for i in read}
        ispolnitel = [i['ФИО'] for i in read]
        ispolnitel.insert(0, self.rows[0]['Исполнил'])
        self.combobox_ispolnitel = ttk.Combobox(self, values=list(dict.fromkeys(ispolnitel)), font=font10, state='readonly')
        self.combobox_ispolnitel.current(0)
        self.combobox_ispolnitel.place(x=200, y=260)
#====================================================================================
        self.text_entry_zapusk = tk.StringVar(value=self.rows[0]['дата_запуска'])
        self.calen2 = tk.Entry(self, textvariable=self.text_entry_zapusk, font=font10)
        self.calen2.place(x=200, y=290)
#=======================================================================================
        self.text_entry_comment = tk.StringVar(value=self.rows[0]['комментарий'])
        self.entry_comment = tk.Entry(self, textvariable=self.text_entry_comment, font=font10)
        self.entry_comment.place(x=200, y=320)
        btn_cancel = ttk.Button(self, text='Отменить', command=self.destroy)
        btn_cancel.place(x=300, y=380)
        self.btn_ok = ttk.Button(self, text='Сохранить', command=self.save_and_close)
        self.btn_ok.place(x=200, y=380)

    def get_street_after_change_town(self, town, street=None, home=None, entrance=None, elevator=None):
        """
        Поиск адресов заданного города.
        |town|: аргумент - заданный город.
        |type town|: str.
        |return|: Вывод словарей: self.street_to_id, self.house_to_id, self.padik_to_id.
        |rtype|: dict.
        """
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''SELECT
                                    {self.goroda}.id as goroda_id,
                                    {self.goroda}.город,
                                    CONCAT({self.street}.улица, ', ', {self.doma}.номер, ', ', {self.padik}.номер) as Адрес,
                                    {self.street}.id as street_id,
                                    {self.street}.улица as улица,
                                    {self.doma}.id as doma_id,
                                    {self.doma}.номер as дом,
                                    {self.padik}.id as padik_id,
                                    {self.padik}.номер as подъезд
                                FROM {self.goroda}
                                JOIN {self.street} ON {self.goroda}.id = {self.street}.id_город
                                JOIN {self.doma} ON {self.street}.id = {self.doma}.id_улица
                                JOIN {self.lifts} ON {self.doma}.id = {self.lifts}.id_дом
                                JOIN {self.padik} ON {self.lifts}.id_подъезд = {self.padik}.id
                                WHERE {self.goroda}.город = '{town}';''')
                self.adreses = cursor.fetchall()
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
        self.street_to_id = {i['улица']: i['street_id'] for i in self.adreses}
        self.house_to_id = {i['дом']: i['doma_id'] for i in self.adreses}
        self.padik_to_id = {i['подъезд']: i['padik_id'] for i in self.adreses}

    def get_home_after_change_street(self):
        pass
    def on_unmap(self, event):
        # Отменяем сворачивание дочернего окна
        self.deiconify()

    def deiconify(self):
        if self.state() == 'iconic':
            self.state('normal')

    def on_town_select(self, event):
        selected_town = self.combobox_town.get()
        # Запрос к базе данных для получения типов лифтов на основе выбранного адреса
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''SELECT CONCAT({self.street}.улица, ', ', CAST({self.doma}.номер AS CHAR), ', ', CAST({self.padik}.номер AS CHAR)) AS Адрес
                    FROM {self.goroda}
                    JOIN {self.street} ON {self.goroda}.id = {self.street}.id_город
                    JOIN {self.doma} ON {self.street}.id = {self.doma}.id_улица
                    JOIN {self.lifts} ON {self.doma}.id = {self.lifts}.id_дом
                    JOIN {self.padik} ON {self.lifts}.id_подъезд = {self.padik}.id
                    WHERE {self.goroda}.город = "{self.combobox_town.get()}"
                    group BY {self.street}.Улица, {self.doma}.Номер, {self.padik}.Номер
                    order by {self.street}.улица, {self.doma}.номер, {self.padik}.номер''')
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
        self.street_name, self.house, self.entrance = self.address_combobox.get().split(', ')
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''SELECT {self.lifts}.тип_лифта
                                FROM {self.lifts}
                                JOIN {self.padik} ON {self.lifts}.id_подъезд = {self.padik}.id
                                JOIN {self.doma} ON {self.lifts}.id_дом = {self.doma}.id
                                JOIN {self.street} ON {self.doma}.id_улица = {self.street}.id
                                JOIN {self.goroda} ON {self.street}.id_город = {self.goroda}.id
                                WHERE {self.goroda}.город = "{self.combobox_town.get()}" AND {self.street}.улица = "{self.street_name}"
                                and {self.doma}.номер = "{self.house}" and {self.padik}.номер = "{self.entrance}"''')
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
            self.get_street_after_change_town(self.combobox_town.get())
            town_name = self.combobox_town.get()
            street_name, home_name, padik_name = self.address_combobox.get().split(',')
            lift_name = self.combobox_lift.get()
            self.all_id_address = self.get_all_id_address(town_name.strip(), street_name.strip(), home_name.strip(),
                                                     padik_name.strip(), lift_name.strip())
            return self.all_id_address

    def get_all_id_address(self, town, street, home, entrance, lift):
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''SELECT 
                      goroda.id AS goroda_id,
                      street.id AS street_id,
                      doma.id AS home_id,
                      padik.id AS padik_id,
                      lifts.id AS lifts_id
                      FROM goroda
                      JOIN street ON goroda.id = street.id_город
                      JOIN doma ON street.id = doma.id_улица
                      JOIN lifts ON doma.id = lifts.id_дом
                      JOIN padik ON lifts.id_подъезд = padik.id
                      WHERE goroda.город = ? AND street.Улица= ?
                      AND doma.Номер= ? AND padik.Номер= ? AND lifts.Тип_лифта= ?
                    ''', (town, street, home, entrance, lift),)
                data_all_id_address = cursor.fetchall()
            return data_all_id_address
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

    def get_selected_meh_id(self):
        selected_meh_fio = self.combobox_meh.get()
        selected_meh_id = self.meh_to_id.get(selected_meh_fio)
        return selected_meh_id

    def get_selected_ispolnitel_id(self):
        selected_ispolnitel_fio = self.combobox_ispolnitel.get()
        selected_ispolnitel_id = self.ispolnitel_to_id.get(selected_ispolnitel_fio)
        if selected_ispolnitel_id == 'None':
            return None
        else:
            return selected_ispolnitel_id

    def is_data_changed(self):
        original_data = self.rows[0]

        current_data = {
            'Дата_заявки': self.calen1.get(),
            'Диспетчер': self.dispetcher.get(),
            'Город': self.combobox_town.get(),
            'Адрес': self.address_combobox.get(),
            'тип_лифта': self.selected_type.get(),
            'причина': self.combobox_stop.get(),
            'Принял': self.combobox_meh.get(),
            'Исполнил': self.combobox_ispolnitel.get(),
            'дата_запуска': self.calen2.get(),
            'комментарий': self.entry_comment.get()
        }

        # Проверяем, изменились ли какие-либо значения
        for key, value in current_data.items():
            if str(original_data[key]) != str(value):
                return True
        return False

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

        # Проверяем, изменились ли данные
        if not self.is_data_changed():
            self.destroy()  # Просто закрываем окно, если ничего не изменилось
            return

        self.view.update_record(self.calen1.get(),
                                self.get_selected_dispetcher_id(),
                                self.get_selected_town_id(),
                                self.get_selected_adres_id()[0]['street_id'],
                                self.get_selected_adres_id()[0]['home_id'],
                                self.get_selected_adres_id()[0]['padik_id'],
                                self.selected_type.get(),
                                self.get_selected_adres_id()[0]['lifts_id'],
                                self.combobox_stop.get(),
                                self.get_selected_meh_id(),
                                self.get_selected_ispolnitel_id(),
                                self.calen2.get(),
                                self.entry_comment.get(),
                                self.destroy())

class Search(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.db_manager = DataBaseManager()
        self.tables = self.db_manager.db_tables()
        self.workers = self.tables['table_workers']
        self.goroda = self.tables['table_goroda']
        self.zayavki = self.tables['table_zayavki']
        self.street = self.tables['table_street']
        self.doma = self.tables['table_doma']
        self.padik = self.tables['table_padik']
        self.lifts = self.tables['table_lifts']
        self.init_search()
        self.view = app

    def init_search(self):
        self.title('Поиск')
        self.geometry('600x400+400+300')
        self.resizable(False, False)
        self.wm_attributes('-topmost', 1)
        self.bind('<Unmap>', self.on_unmap)

        toolbar_city = tk.Frame(self, borderwidth=1, relief="raised")
        toolbar_city.pack(side=tk.LEFT, fill=tk.Y)

        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f"select id, город from {self.goroda}")
                data_towns = cursor.fetchall()
        except mariadb.Error as e:
            messagebox.showinfo('Информация', f"Ошибка при работе с базой данных: {e}")
            return

        default_town = data_towns[0] if data_towns else ''

        self.label_city = tk.Label(toolbar_city, borderwidth=1, width=21, relief="raised", text="Город", font='Calibri 14 bold')
        self.label_city.pack(side=tk.TOP)

        self.canvas = tk.Canvas(toolbar_city, width=100)
        self.scrollbar = ttk.Scrollbar(toolbar_city, orient="vertical", command=self.canvas.yview)
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

        self.value_city = tk.StringVar(value=default_town['город'] if default_town else '')
        self.value_city.trace("w", self.on_select_city)

        for town in data_towns:
            radiobutton = tk.Radiobutton(self.scrollable_frame, font=('Calibri', 14), text=town['город'],
                                         variable=self.value_city,
                                         value=town['город'])
            radiobutton.pack(anchor="w")
            radiobutton.bind("<MouseWheel>", self._on_mousewheel)
            radiobutton.bind("<Button-4>", self._on_mousewheel)
            radiobutton.bind("<Button-5>", self._on_mousewheel)
#================================================================================================================
        toolbar_addresses = tk.Frame(self, borderwidth=1, relief="raised")
        toolbar_addresses.pack(side=tk.LEFT, fill=tk.Y)
        label_adres = tk.Label(toolbar_addresses, borderwidth=1, relief='raised', width=21, text='Адрес', font='Calibri 14 bold')
        label_adres.pack(side=tk.TOP)

        toolbar6 = tk.Frame(self, borderwidth=1, relief="raised")
        toolbar6.pack(side=tk.LEFT, fill=tk.Y)
        label_data = tk.Label(toolbar6, borderwidth=1, relief='raised', width=21, text='Дата', font='Calibri 14 bold')
        label_data.pack()
        label_c = tk.Label(toolbar6, text='с', font='Calibri 15 bold')
        label_c.pack()
        self.calendar1 = DateEntry(toolbar6, locale='ru_RU', font=1, date_pattern='dd.mm.yy')
        self.calendar1.bind("<<DateEntrySelected>>")
        self.calendar1.pack()
        label_po = tk.Label(toolbar6, text='по', font='Calibri 15 bold')
        label_po.pack()
        self.calendar2 = DateEntry(toolbar6, locale='ru_RU', font=1, date_pattern='dd.mm.yy')
        self.calendar2.bind("<<DateEntrySelected>>")
        self.calendar2.pack()

        self.frame_search = tk.Frame(borderwidth=1)
        self.entry_text_address = tk.StringVar()
        self.entry_for_address = tk.Entry(toolbar_addresses, textvariable=self.entry_text_address, width=33)
        self.entry_for_address.bind('<KeyRelease>', self.check_input_address)
        self.entry_for_address.pack()
        self.value_addresses = tk.Variable()

        # Создаем горизонтальный скроллбар
        self.scrollbar_x = tk.Scrollbar(toolbar_addresses, orient=tk.HORIZONTAL)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.listbox_addresses = tk.Listbox(toolbar_addresses, listvariable=self.value_addresses, height=15, width=25, font='Calibri 12')
        self.listbox_addresses.bind('<<ListboxSelect>>', self.on_change_selection_11)
        self.listbox_addresses.pack()
        # Связываем скроллбар с Listbox
        self.listbox_addresses.config(xscrollcommand=self.scrollbar_x.set)
        self.scrollbar_x.config(command=self.listbox_addresses.xview)
        self.selected_city = self.value_city.get()
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''SELECT
                                    {self.goroda}.id as goroda_id,
                                    {self.goroda}.город,
                                    {self.street}.id as street_id,
                                    {self.street}.улица,
                                    {self.doma}.id as doma_id,
                                    {self.doma}.номер as дом,
                                    {self.padik}.id as padik_id,
                                    {self.padik}.номер as подъезд
                                FROM {self.goroda}
                                JOIN {self.street} ON {self.goroda}.id = {self.street}.id_город
                                JOIN {self.doma} ON {self.street}.id = {self.doma}.id_улица
                                JOIN {self.lifts} ON {self.doma}.id = {self.lifts}.id_дом
                                JOIN {self.padik} ON {self.lifts}.id_подъезд = {self.padik}.id
                                WHERE {self.goroda}.город = '{self.selected_city}'
                                GROUP BY {self.goroda}.id, {self.street}.улица, {self.doma}.номер, {self.padik}.номер
                                ORDER BY {self.goroda}.id, {self.street}.улица, {self.doma}.номер, {self.padik}.номер;''')
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
        btn_search.bind('<Button-1>', lambda event: (self.view.event_of_button('search', self.value_city, self.entry_for_address.get(), self.calendar1.get(), self.calendar2.get(), self.destroy())))

    def on_unmap(self, event):
        self.deiconify()  # Отменяем сворачивание дочернего окна

    def deiconify(self):
        if self.state() == 'iconic':
            self.state('normal')

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_select_city(self, *args):
        self.selected_city = self.value_city.get()
        # Очистить Listbox перед добавлением новых улиц
        self.listbox_addresses.delete(0, tk.END)
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''SELECT {self.street}.Улица, 
                        {self.doma}.Номер AS дом, 
                        {self.padik}.Номер AS подъезд
                        FROM {self.street}
                        JOIN {self.doma} ON {self.street}.id = {self.doma}.id_улица
                        JOIN {self.lifts} ON {self.doma}.id = {self.lifts}.id_дом
                        JOIN {self.padik} ON {self.lifts}.id_подъезд = {self.padik}.id
                        JOIN {self.goroda} ON {self.street}.id_город = {self.goroda}.id
                        WHERE {self.goroda}.Город = '{self.selected_city}' AND {self.doma}.is_active = 1
                        group BY {self.street}.Улица, {self.doma}.Номер, {self.padik}.Номер
						ORDER BY {self.street}.Улица, {self.doma}.Номер, {self.padik}.Номер''')
                self.data_streets = cursor.fetchall()
                for d in self.data_streets:
                    self.address_str = f"{d['Улица']}, {d['дом']}, {d['подъезд']}"
                    self.listbox_addresses.insert(tk.END, self.address_str)
        except mariadb.Error as e:
            showinfo('Информация', f"Ошибка при работе с базой данных: {e}")

        # =========================================================================
    def check_input_address(self, _event=None):
        self.selected_city = self.value_city.get()
        changed_address = self.entry_text_address.get().lower()
        names = []
        try:
            with closing(self.db_manager.connect()) as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f'''SELECT {self.street}.Улица, 
                        {self.doma}.Номер AS дом, 
                        {self.padik}.Номер AS подъезд
                        FROM {self.street}
                        JOIN {self.doma} ON {self.street}.id = {self.doma}.id_улица
                        JOIN {self.lifts} ON {self.doma}.id = {self.lifts}.id_дом
                        JOIN {self.padik} ON {self.lifts}.id_подъезд = {self.padik}.id
                        JOIN {self.goroda} ON {self.street}.id_город = {self.goroda}.id
                        WHERE {self.goroda}.Город = '{self.selected_city}'
                        group BY {self.street}.Улица, {self.doma}.Номер, {self.padik}.Номер
						ORDER BY {self.street}.Улица, {self.doma}.Номер, {self.padik}.Номер''')
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
        self.geometry('700x400+300+300')
        self.resizable(False, False)
        self.wm_attributes('-topmost', 1)
        self.bind('<Unmap>', self.on_unmap)

        self.t = Text(self, height=14, width=50, font=16)
        self.t.insert(tk.END, self.now[0])
        self.t.place(x=10, y=10)

        style = ttk.Style()
        style.configure("BigFont.TButton", font=('Helvetica', 16))
        style.configure("Green.TButton", foreground="green", background="#50C878", font='Calibri 12')
        style.configure("Red.TButton", foreground="red", background="#FCA195", font='Calibri 12')

        self.btn_micro = ttk.Button(self, text='Сказать\U0001f3a4', command=self.on_microfon_button_click, width=9, style="BigFont.TButton")
        self.btn_micro.place(x=565, y=8)

        # Метка для инструкций, расположенная под кнопкой
        self.instruction_label = ttk.Label(self, text='', wraplength=300)
        self.instruction_label.place(x=575, y=40)  # Положение метки под кнопкой

        button_cancel = ttk.Button(self, text='Отменить', command=self.destroy, style="Red.TButton", width=30)
        button_cancel.place(x=300, y=340)

        button_search = ttk.Button(self, text='Сохранить', command=self.save_and_close, style="Green.TButton", width=30)
        button_search.place(x=10, y=340)

        self.t.bind("<Button-3>", self.show_menu)
        self.t.bind_all("<Control-v>", self.paste_text)

    def on_unmap(self, event):
        self.deiconify()  # Отменяем сворачивание дочернего окна

    def on_microfon_button_click(self):
        if self.is_recording:
            return

        self.is_recording = True
        self.btn_micro.config(text='Говорите...')
        self.instruction_label.config(text='Говорите', foreground='red', font='16')
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
        self.view.comment(self.t.get("1.0", tk.END).strip(), self.destroy)


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
    time_format = "%d.%m.%y, %H:%M"
    root = tk.Tk()
    app = Main(root)
    app.pack()
    root.title("Электронный журнал")
    root.geometry("1920x1080")
    # root.iconphoto(False, tk.PhotoImage(file='icon.png'))
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


