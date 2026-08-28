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
                database=self.data['db_name'],
                connect_timeout=5
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
            'table_lifts': self.data['table_lifts'],
            'table_uk': self.data['table_uk']
        }
        return db_tables

    def ensure_schema(self):
        """
        Создаёт БД, недостающие таблицы и недостающие колонки (schema_db.sql + миграции).
        Идемпотентно: безопасно выполнять на каждом старте приложения, ничего не удаляет
        и не трогает существующие данные.
        """
        try:
            server_conn = mariadb.connect(
                user=self.data['db_user'],
                password=self.data['db_password'],
                host=self.data['db_host'],
                port=self.data['db_port'],
                connect_timeout=5
            )
        except mariadb.Error as e:
            raise RuntimeError(f"Не удалось подключиться к серверу MariaDB: {e}")

        with closing(server_conn) as conn:
            cur = conn.cursor()
            cur.execute(
                "CREATE DATABASE IF NOT EXISTS `{}` DEFAULT CHARACTER SET utf8mb4".format(self.data['db_name'])
            )
            conn.commit()

        db_conn = self.connect()
        if isinstance(db_conn, str):
            raise RuntimeError(db_conn)

        with closing(db_conn) as conn:
            cur = conn.cursor()

            with open('schema_db.sql', 'r', encoding='utf-8') as f:
                script = f.read()
            for raw_statement in script.split(';'):
                lines = [line for line in raw_statement.splitlines() if not line.strip().startswith('--')]
                statement = "\n".join(lines).strip()
                if statement:
                    cur.execute(statement)
            conn.commit()

            # миграция для БД, созданных до появления таблицы "УК"
            self._ensure_column(
                cur, self.data['table_doma'], 'id_ук',
                "ADD COLUMN `id_ук` int(11) DEFAULT NULL, "
                "ADD CONSTRAINT `fk_doma_uk` FOREIGN KEY (`id_ук`) REFERENCES `{}` (`id`)"
                .format(self.data['table_uk'])
            )
            conn.commit()

    def _ensure_column(self, cur, table, column, alter_clause):
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s AND column_name = %s",
            (self.data['db_name'], table, column)
        )
        (count,) = cur.fetchone()
        if not count:
            cur.execute(f"ALTER TABLE `{table}` {alter_clause}")

    def settings(self):
        settings = {
            'pc_id': self.data['pc_id']
        }
