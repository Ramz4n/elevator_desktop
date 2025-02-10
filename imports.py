from tkinter import ttk, messagebox
import tkinter as tk
from tkinter import *
import tkinter.font as tkFont
from tkinter import messagebox as mb
from tkinter.messagebox import showinfo, askyesno, showerror
import mariadb
import datetime
import time
import pandas as pd
import subprocess
from contextlib import closing
from tkcalendar import DateEntry
import babel.numbers
from sqlalchemy import create_engine, text
import json
import pymysql
import sys
from speech import Speech_recorder
import threading
from menu import Menu_errors
from afternoon_statistic import Afternoon_statistic
#from sendler import Telegram_sendler
from telegram import Bot
from session import Session
from change_months import Change_months
from db_manager import DataBaseManager