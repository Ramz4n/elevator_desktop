from imports import *


class DataBaseManager:
    def __init__(self):
        with open('config.json', 'r') as file:
            self.data = json.loads(file.read())

    def connect(self):
        try:
            return mariadb.connect(
                user=self.data['db_user'],
                password=self.data['db_password'],
                host=self.data['db_host'],
                port=self.data['db_port'],
                database=self.data['db_name']
            )
        except mariadb.Error as e:
            return f"Ошибка подключения к базе данных: {e}"

    def db_tables(self):
        db_tables = {
            'table_goroda': self.data['table_goroda'],
            'table_zayavki': self.data['table_zayavki'],
            'table_workers': self.data['table_workers'],
            'table_street': self.data['table_street'],
            'table_doma': self.data['table_doma'],
            'table_padik': self.data['table_padik'],
            'table_lifts': self.data['table_lifts']
        }
        return db_tables

    def settings(self):
        settings = {
            'pc_id': self.data['pc_id']
        }