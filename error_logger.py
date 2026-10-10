# -*- coding: utf-8 -*-
"""
Логирование ошибок в файл errors.log рядом с exe (или рядом с mitol.py
при запуске из исходников).

Файл с ротацией (RotatingFileHandler): как только errors.log дорастает
до MAX_BYTES, он переименовывается в errors.log.1 (а прошлый .1 -> .2 и
т.д.), и пишется новый пустой errors.log. Хранится не больше BACKUP_COUNT
таких файлов -- старые самые старые просто удаляются. Поэтому суммарный
размер логов ограничен сверху (MAX_BYTES * (BACKUP_COUNT + 1)) и никогда
не разрастётся до гигабайтов, даже если приложение будет годами сыпать
ошибками.

install(root) навешивает три перехватчика, чтобы ошибка не потерялась
независимо от того, где она произошла:
  - root.report_callback_exception -- исключения внутри обработчиков Tk
    (command=..., bind(...) и т.п.) -- почти все ошибки в этом приложении
    происходят именно тут, а Tk по умолчанию их просто печатает в stderr,
    которого в windowed-сборке (console=False в mitol.spec) может не быть.
  - sys.excepthook -- то, что происходит вне обработчиков Tk (например,
    до старта mainloop).
  - threading.excepthook -- ошибки в фоновых потоках (запись/скачивание
    бэкапа, обновление, распознавание речи).
"""

import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler

MAX_BYTES = 2 * 1024 * 1024   # 2 МБ на файл
BACKUP_COUNT = 3               # + 3 старых копии -> максимум ~8 МБ суммарно


def _log_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


LOG_PATH = os.path.join(_log_dir(), "errors.log")

logger = logging.getLogger("mitol")
logger.setLevel(logging.ERROR)

if not logger.handlers:
    _handler = RotatingFileHandler(
        LOG_PATH, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    _handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(_handler)


def install(root=None) -> None:
    """Вызывать один раз при старте приложения (после создания root)."""

    if root is not None:
        def _tk_callback_exception(exc, val, tb):
            logger.error("Необработанное исключение в обработчике Tk", exc_info=(exc, val, tb))
        root.report_callback_exception = _tk_callback_exception

    def _excepthook(exc_type, exc_value, exc_tb):
        logger.error("Необработанное исключение", exc_info=(exc_type, exc_value, exc_tb))
        try:
            # В windowed-сборке (console=False) sys.stderr обычно None --
            # запись в него упадёт с собственным исключением; лог мы уже
            # записали строкой выше, так что эта попытка -- best-effort
            # только для запуска из консоли при разработке.
            sys.__excepthook__(exc_type, exc_value, exc_tb)
        except Exception:
            pass
    sys.excepthook = _excepthook

    def _thread_excepthook(args):
        logger.error(
            "Необработанное исключение в потоке %s" % args.thread.name,
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )
    threading.excepthook = _thread_excepthook
