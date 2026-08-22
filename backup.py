# -*- coding: utf-8 -*-
"""
Резервное копирование и восстановление данных БД.

Бэкап -- один .zip с одним файлом db.json: дамп всех таблиц БД (список
таблиц передаётся вызывающим кодом, см. Main.tables в mitol.py). config.json
(пароль/адрес MariaDB конкретного ПК) в бэкап НЕ входит -- он привязан к
конкретной установке, восстанавливать его на другом компьютере бессмысленно
и небезопасно.

Дамп/восстановление -- чистым Python через уже используемый в проекте
mariadb-коннектор (тот же, что и db_manager.py), без внешнего mysqldump.exe.

Восстановление: TRUNCATE + INSERT всех таблиц с отключенными проверками
внешних ключей (FOREIGN_KEY_CHECKS=0) -- порядок таблиц тогда не важен.
"""

import os
import json
import zipfile
import glob
from datetime import datetime, date
from decimal import Decimal
from contextlib import closing

import mariadb

DB_DUMP_NAME = "db.json"
BACKUP_FILE_PREFIX = "mitol_backup_"


class BackupShrinkAnomaly(Exception):
    """
    Новых данных заметно меньше, чем в последнем существующем бэкапе --
    похоже на потерю/порчу данных (взлом, случайное удаление), а не на
    обычную работу. В приложении почти нет жёсткого удаления (только
    is_active-флаги), так что суммарное число строк во всех таблицах в
    норме только растёт -- падение больше drop_ratio это сильный сигнал.

    Смысл ловить это ДО записи нового бэкапа: иначе через `keep` циклов
    ротации (см. rotate_backups) даже все резервные копии окажутся такими
    же пустыми/испорченными, как и сама база, и восстанавливать будет
    нечего.
    """

    def __init__(self, previous_total, current_total):
        self.previous_total = previous_total
        self.current_total = current_total
        super().__init__(
            f"Строк в базе стало заметно меньше: было {previous_total}, стало {current_total}."
        )


def _json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Не удалось сериализовать значение типа {type(value)}")


def _dump_database(db_manager, tables) -> dict:
    """Считать все строки перечисленных таблиц."""
    with closing(db_manager.connect()) as connection:
        cursor = connection.cursor(dictionary=True)
        dump = {}
        for table_name in tables:
            cursor.execute(f"SELECT * FROM `{table_name}`")
            dump[table_name] = cursor.fetchall()
        return dump


def _restore_database(db_manager, tables, dump: dict) -> None:
    """Полностью заменить содержимое перечисленных таблиц данными из dump."""
    with closing(db_manager.connect()) as connection:
        cursor = connection.cursor()
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        try:
            for table_name in tables:
                cursor.execute(f"TRUNCATE TABLE `{table_name}`")

            for table_name, rows in dump.items():
                if table_name not in tables or not rows:
                    continue
                columns = list(rows[0].keys())
                col_list = ", ".join(f"`{c}`" for c in columns)
                placeholders = ", ".join(["?"] * len(columns))
                sql = f"INSERT INTO `{table_name}` ({col_list}) VALUES ({placeholders})"
                for row in rows:
                    cursor.execute(sql, [row[c] for c in columns])
        finally:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        connection.commit()


def _previous_backup_total(backup_dir: str):
    """Суммарное число строк во всех таблицах последнего существующего
    бэкапа, или None, если бэкапов ещё нет / прошлый файл не читается."""
    existing = list_backups(backup_dir)
    if not existing:
        return None
    try:
        with zipfile.ZipFile(existing[0], "r") as zf:
            prev_dump = json.loads(zf.read(DB_DUMP_NAME).decode("utf-8"))
    except Exception:
        return None
    return sum(len(rows) for rows in prev_dump.values())


def create_backup(db_manager, tables, backup_dir: str,
                   check_shrink: bool = True, drop_ratio: float = 0.5) -> str:
    """
    Создать .zip-бэкап в backup_dir. Возвращает путь к созданному файлу.

    check_shrink=True (по умолчанию) -- перед записью сравнивает общее
    число строк во всех таблицах с последним существующим бэкапом; если
    просело более чем на drop_ratio (по умолчанию 50%), НЕ перезаписывает
    последний хороший бэкап новым "пустым" и бросает BackupShrinkAnomaly
    вместо тихой записи файла (кроме случая, когда бэкапов ещё не было --
    тогда сравнивать не с чем).
    """
    dump = _dump_database(db_manager, tables)

    if check_shrink:
        prev_total = _previous_backup_total(backup_dir)
        if prev_total:
            current_total = sum(len(rows) for rows in dump.values())
            if current_total <= prev_total * (1 - drop_ratio):
                raise BackupShrinkAnomaly(prev_total, current_total)

    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    zip_path = os.path.join(backup_dir, f"{BACKUP_FILE_PREFIX}{timestamp}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(DB_DUMP_NAME, json.dumps(dump, ensure_ascii=False, default=_json_default))

    return zip_path


def restore_backup(db_manager, tables, zip_path: str) -> None:
    """Восстановить БД из .zip-бэкапа (полностью заменяет текущие данные)."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        dump = json.loads(zf.read(DB_DUMP_NAME).decode("utf-8"))
    _restore_database(db_manager, tables, dump)


def list_backups(backup_dir: str) -> list:
    """Список файлов бэкапа в папке, от новых к старым."""
    if not backup_dir or not os.path.isdir(backup_dir):
        return []
    paths = glob.glob(os.path.join(backup_dir, f"{BACKUP_FILE_PREFIX}*.zip"))
    return sorted(paths, key=os.path.getmtime, reverse=True)


def rotate_backups(backup_dir: str, keep: int = 14) -> None:
    """Оставить только keep самых свежих бэкапов, остальные удалить."""
    for old_path in list_backups(backup_dir)[keep:]:
        try:
            os.remove(old_path)
        except OSError:
            pass


def needs_backup(backup_dir: str, min_interval_hours: float = 24) -> bool:
    """
    True, если самого свежего бэкапа в backup_dir нет вовсе, либо он старше
    min_interval_hours. Время последнего бэкапа не хранится отдельно (не
    нужен свой settings.json) -- берётся дата изменения самого свежего файла.
    """
    backups = list_backups(backup_dir)
    if not backups:
        return True
    age_hours = (datetime.now().timestamp() - os.path.getmtime(backups[0])) / 3600
    return age_hours >= min_interval_hours
