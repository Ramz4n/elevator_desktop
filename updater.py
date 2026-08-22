# -*- coding: utf-8 -*-
"""
Модуль авто-обновления приложения через GitHub Releases.

Источник обновлений — GitHub API "latest release" публичного репозитория:
    https://api.github.com/repos/<GITHUB_REPO>/releases/latest

Репозиторий ДОЛЖЕН быть публичным — иначе API отдаёт 404 без токена.
Исходный код mitol остаётся в отдельном репозитории (обычном, приватном
или нет — неважно); GITHUB_REPO указывает на отдельный публичный
репозиторий mitol_releases, куда заливаются только .zip с готовой сборкой
(см. package_release.bat) — так история релизов не раздувает репозиторий
с кодом.

Сборка -- onefile (см. mitol.spec + build.bat): mitol.exe -- единственный
исполняемый файл, рядом с ним лежат схема БД (schema_db.sql) и иконка
(icon.png), не входящие в сам exe. Поэтому в релиз заливается .zip папки
dist (exe + schema_db.sql + icon.png + on.png + off.png + VERSION), а
не один голый .exe.

ВАЖНО: config.json (пароль/адрес MariaDB и pc_id конкретного компьютера)
и mitol.lock (файл-блокировка запущенного процесса) -- это ЛОКАЛЬНЫЕ
данные конкретной установки, их НЕЛЬЗЯ заливать в архив на публичный
GitHub и НЕЛЬЗЯ трогать при обновлении. Поэтому архив собирается НЕ
вручную, а через package_release.bat в корне проекта -- он копирует
сборку во временную папку, исключает config.json и уже из этой чистой
копии делает release\mitol_v<версия>.zip. При установке apply_update
тоже исключает config.json и mitol.lock из перезаписи (см. bat_content).

Версия приложения (APP_VERSION) читается из файла VERSION в корне
проекта (или рядом с exe в собранной версии). package_release.bat сам
увеличивает patch-число в VERSION при каждой упаковке релиза (чтобы
никто не забыл поднять версию, из-за чего свежая сборка продолжала бы
считать себя старой и зацикливала предложение обновиться).

Как выпустить обновление:
  1. Запустить package_release.bat -- он сам:
       - увеличит patch-версию в файле VERSION (например 1.0.0 → 1.0.1),
       - соберёт актуальный dist\mitol.exe (запускает build.bat),
       - упакует dist\ в release\mitol_v<версия>.zip
         (уже без config.json/mitol.lock),
       - выведет в консоль версию и тег, который нужно создать на GitHub.
  2. На GitHub (в репозитории mitol_releases) → Releases → Draft a new
     release:
       - тег: "v1.0.1"              → обычное необязательное обновление
               "v1.0.1-force"       → обязательное (нельзя отказаться,
                                       применяется ко всем версиям ниже 1.0.1)
         (точный тег package_release.bat печатает в конце -- просто скопировать)
       - приложить release\mitol_v1.0.1.zip как asset
       - в описании релиза — текст для пользователя (changelog)
  3. Опубликовать релиз — всё, клиенты подхватят это в течение
     UPDATE_CHECK_INTERVAL_MS (см. блок автообновления в mitol.py).

При установке update.zip разворачивается поверх текущей папки; личные
config.json и mitol.lock клиента при этом не трогаются.

Логика:
  - тег без "-force"  и версия клиента < версии тега → предложение (Да / Нет)
  - тег с "-force"    и версия клиента < версии тега → обязательное обновление
  - иначе → ничего не происходит
"""

import os
import sys
import shutil
import subprocess
import threading
import traceback
import zipfile
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import requests


def _read_app_version() -> str:
    """
    Версия приложения читается из файла VERSION -- рядом с exe в собранной
    версии (кладёт package_release.bat) или в корне репозитория при запуске
    из исходников. Так версию не нужно руками менять в коде: забыть об
    этом и оставить приложение считать себя старой версией уже нельзя.
    """
    exe_dir = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
    for path in (
        os.path.join(exe_dir, "VERSION"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION"),
    ):
        try:
            with open(path, "r", encoding="utf-8") as f:
                v = f.read().strip()
                if v:
                    return v
        except Exception:
            continue
    return "0.0.0"


# ─────────────────────────────────────────
APP_VERSION = _read_app_version()

# Публичный репозиторий с релизами (только .zip-сборки, не исходники): "владелец/репозиторий"
GITHUB_REPO = "Ramz4n/mitol_releases"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
# ─────────────────────────────────────────


def _current_exe() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.abspath(__file__)


def _log_path() -> str:
    return os.path.join(os.path.dirname(_current_exe()), "updater_debug.log")


def _log(msg: str) -> None:
    """Пишет строку в updater_debug.log рядом с exe -- обновление не должно
    шуметь окнами при каждой фоновой проверке, но причина сбоя/пропуска
    должна быть видна, если что-то не работает."""
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}\n")
    except Exception:
        pass


def _log_error(context: str, exc: Exception) -> None:
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] {context}\n")
            f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    except Exception:
        pass


def _parse_version(v: str) -> tuple:
    """'1.2.3' → (1, 2, 3)"""
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except Exception:
        return (0,)


def _no_proxy_session() -> requests.Session:
    """
    Сессия requests, полностью игнорирующая системный прокси (в т.ч. на
    редиректах, например с api.github.com на objects.githubusercontent.com).
    trust_env=False -- иначе requests подхватывает системный/переменные
    окружения прокси (в т.ч. SOCKS, для которого может не быть установлен
    PySocks) и падает с "Missing dependencies for SOCKS support"; простой
    proxies={"https": None} на верхнем запросе на это не влияет, потому что
    редирект пересобирает прокси заново.
    """
    session = requests.Session()
    session.trust_env = False
    return session


def check_for_update(silent: bool = True) -> dict | None:
    """
    Проверяет наличие обновления через GitHub Releases API (последний релиз
    публичного репозитория GITHUB_REPO).
    Возвращает dict с ключами:
        latest_version, min_version, download_url, changelog, forced
    или None если обновлений нет (текущая версия уже последняя).

    silent=True  (фоновая периодическая проверка) — любая ошибка (нет сети,
        GitHub недоступен, битый релиз) молча логируется в
        updater_debug.log и трактуется как «обновлений нет».
    silent=False (ручная проверка по кнопке) — в этих же случаях бросает
        исключение с понятной причиной, чтобы её можно было показать
        пользователю и понять, почему автообновление не сработало.
    """
    try:
        r = _no_proxy_session().get(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github+json"},
            timeout=5,
        )
        if r.status_code != 200:
            msg = f"GitHub API вернул {r.status_code}, тело: {r.text[:300]}"
            _log(f"check_for_update: {msg}")
            if not silent:
                raise RuntimeError(msg)
            return None
        data = r.json()

        tag = (data.get("tag_name") or "").strip()
        if not tag:
            _log("check_for_update: в latest-релизе нет tag_name")
            if not silent:
                raise RuntimeError("В последнем релизе на GitHub не указан тег версии")
            return None

        # "v1.0.1-force" → обязательное обновление, "v1.0.1" → обычное
        forced = tag.endswith("-force")
        version_str = tag[:-len("-force")] if forced else tag
        version_str = version_str.lstrip("vV")
        if not version_str:
            _log(f"check_for_update: не удалось распарсить версию из тега {tag!r}")
            if not silent:
                raise RuntimeError(f"Не удалось распознать версию из тега {tag!r}")
            return None

        # Сборка onefile -- в релизе должен лежать .zip (exe + schema_db.sql
        # + icon.png + on.png + off.png + VERSION), а не голый .exe.
        download_url = None
        for asset in data.get("assets", []):
            name = (asset.get("name") or "").lower()
            if name.endswith(".zip"):
                download_url = asset.get("browser_download_url")
                break
        if not download_url:
            asset_names = [a.get("name") for a in data.get("assets", [])]
            _log(f"check_for_update: в релизе {tag!r} нет .zip среди asset'ов: {asset_names}")
            if not silent:
                raise RuntimeError(f"В релизе {tag!r} на GitHub не приложен .zip с обновлением")
            return None

        current = _parse_version(APP_VERSION)
        latest = _parse_version(version_str)

        if current >= latest:
            _log(f"check_for_update: тег {version_str} <= текущей версии {APP_VERSION}, обновление не нужно")
            return None

        _log(f"check_for_update: найдено обновление {APP_VERSION} → {version_str} (forced={forced})")
        return {
            "latest_version": version_str,
            "min_version": version_str if forced else "0.0.0",
            "download_url": download_url,
            "changelog": data.get("body") or "",
            "forced": forced,
        }

    except Exception as e:
        _log_error("check_for_update: исключение", e)
        if not silent:
            raise
    return None


def show_update_dialog(update_info: dict, parent=None) -> bool:
    """
    Показывает диалог обновления.
    Принудительное: только кнопка «Обновить».
    Обычное: кнопки «Обновить» / «Не сейчас».
    Возвращает True если нужно качать.
    """
    forced = update_info.get("forced", False)
    latest = update_info["latest_version"]
    changes = update_info.get("changelog", "")

    win = tk.Toplevel(parent)
    win.resizable(False, False)
    win.wm_attributes('-topmost', 1)

    if forced:
        win.title("Требуется обновление")
        win.protocol("WM_DELETE_WINDOW", lambda: None)  # нельзя закрыть
    else:
        win.title("Доступно обновление")

    f = tk.Frame(win, padx=24, pady=18)
    f.pack(fill=tk.BOTH, expand=True)

    if forced:
        tk.Label(f, text="Требуется обязательное обновление",
                 font=('Calibri', 14, 'bold'), fg='#c62828').pack(anchor='w', pady=(0, 6))
    else:
        tk.Label(f, text="Доступна новая версия",
                 font=('Calibri', 14, 'bold')).pack(anchor='w', pady=(0, 6))

    tk.Label(f, text=f"Версия {latest}  (у вас {APP_VERSION})",
             font=('Calibri', 12), fg='gray30').pack(anchor='w', pady=(0, 10))

    if changes:
        tk.Label(f, text="Что нового:", font=('Calibri', 12, 'bold'),
                 anchor='w').pack(fill=tk.X)
        tk.Label(f, text=changes, font=('Calibri', 12),
                 anchor='w', justify='left', wraplength=360).pack(fill=tk.X, pady=(2, 14))

    result = [False]

    btn_frame = tk.Frame(f)
    btn_frame.pack(fill=tk.X, pady=(6, 0))

    def on_yes():
        result[0] = True
        win.destroy()

    def on_no():
        win.destroy()

    tk.Button(btn_frame, text="Обновить", font=('Calibri', 12, 'bold'), bg='#d7efd7',
              width=14, height=2, command=on_yes).pack(side=tk.LEFT)

    if not forced:
        tk.Button(btn_frame, text="Не сейчас", font=('Calibri', 12),
                  width=12, height=2, command=on_no).pack(side=tk.LEFT, padx=(10, 0))

    win.update_idletasks()
    if parent is not None:
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (win.winfo_width() // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")
    win.grab_set()
    win.wait_window()
    return result[0]


def apply_update(download_url: str, parent_widget=None) -> None:
    """
    Скачивает архив новой версии (.zip: exe + schema_db.sql + icon.png +
    on.png + off.png + VERSION), распаковывает во временную папку и запускает bat-установщик,
    который после закрытия приложения разворачивает архив поверх текущей
    установки (не трогая config.json и mitol.lock клиента) и перезапускает
    программу. После запуска bat -- завершает текущий процесс.
    """
    win = tk.Toplevel(parent_widget)
    win.title("Загрузка обновления")
    win.resizable(False, False)
    win.protocol("WM_DELETE_WINDOW", lambda: None)  # нельзя закрыть
    win.wm_attributes('-topmost', 1)

    f = tk.Frame(win, padx=20, pady=16)
    f.pack(fill=tk.BOTH, expand=True)

    tk.Label(f, text="Загрузка обновления...", font=('Calibri', 12)).pack(pady=(0, 8))

    progress = ttk.Progressbar(f, length=320, mode='determinate', maximum=1.0)
    progress.pack(pady=(0, 8))

    size_label = tk.Label(f, text="", font=('Calibri', 10), fg='gray30')
    size_label.pack()

    win.update_idletasks()
    if parent_widget is not None:
        x = parent_widget.winfo_rootx() + (parent_widget.winfo_width() // 2) - (win.winfo_width() // 2)
        y = parent_widget.winfo_rooty() + (parent_widget.winfo_height() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")
    win.grab_set()

    error_holder = [None]

    def do_download():
        try:
            exe_path = _current_exe()
            exe_name = os.path.basename(exe_path)
            install_dir = os.path.dirname(exe_path)

            tmp_dir = os.path.join(os.environ.get("TEMP", install_dir), "mitol_update")
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
            os.makedirs(tmp_dir, exist_ok=True)

            zip_path = os.path.join(tmp_dir, "update.zip")
            extract_dir = os.path.join(tmp_dir, "extracted")
            bat_path = os.path.join(install_dir, "_updater.bat")

            r = _no_proxy_session().get(download_url, stream=True, timeout=60)
            r.raise_for_status()

            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0

            with open(zip_path, "wb") as f_zip:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f_zip.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            win.after(0, lambda p=downloaded / total: progress.configure(value=p))
                        mb_downloaded = downloaded / 1024 / 1024
                        win.after(0, lambda m=mb_downloaded: size_label.configure(
                            text=f"{m:.1f} МБ" + (f" / {total / 1024 / 1024:.1f} МБ" if total else "")
                        ))

            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)

            # В архиве может быть либо содержимое папки сразу, либо оно
            # обёрнуто в одну вложенную папку (если архивировали руками
            # через "Отправить -> сжатая папка") -- ищем, где реально exe.
            new_root = extract_dir
            if not os.path.exists(os.path.join(new_root, exe_name)):
                for entry in os.listdir(extract_dir):
                    candidate = os.path.join(extract_dir, entry)
                    if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, exe_name)):
                        new_root = candidate
                        break

            # /MIR -- зеркалирует папку, /XF -- не трогает то, что
            # принадлежит этой установке клиента, а не релизу: настройки
            # подключения к БД (config.json), файл-блокировку запущенного
            # процесса (mitol.lock) и сам bat-скрипт (иначе он удалит себя
            # раньше времени).
            bat_content = (
                "@echo off\n"
                "timeout /t 2 /nobreak >nul\n"
                f'robocopy "{new_root}" "{install_dir}" /MIR '
                f'/XF config.json mitol.lock _updater.bat >nul\n'
                f'rmdir /S /Q "{tmp_dir}"\n'
                f'start "" "{exe_path}"\n'
                '(goto) 2>nul & del "%~f0"\n'
            )
            with open(bat_path, "w", encoding="cp866") as f_bat:
                f_bat.write(bat_content)

            win.after(0, _launch_and_exit, bat_path)

        except Exception as e:
            _log_error("apply_update: исключение", e)
            error_holder[0] = str(e)
            win.after(0, win.destroy)

    def _launch_and_exit(bat_path):
        win.destroy()
        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        sys.exit(0)

    threading.Thread(target=do_download, daemon=True).start()
    win.wait_window()

    if error_holder[0]:
        messagebox.showerror(
            "Ошибка обновления",
            f"Не удалось скачать обновление:\n{error_holder[0]}\n\nПопробуйте позже.",
            parent=parent_widget,
        )
