from flask import Flask
from flask import render_template
from flask import url_for
import cx_Oracle
import numpy as np
from py_expression_eval import Parser

import os
import sys
import cx_Oracle

from user_secrets import PYTHON_USERNAME, PYTHON_PASSWORD

os.environ['PYTHON_USERNAME'] = PYTHON_USERNAME
os.environ['PYTHON_PASSWORD'] = PYTHON_PASSWORD
os.environ['PYTHON_CONNECTSTRING'] = "//labora.mimuw.edu.pl/LABS"

app = Flask(__name__)

if sys.platform.startswith("darwin"):
    cx_Oracle.init_oracle_client(lib_dir=os.environ.get("HOME")+"/instantclient_19_3")
elif sys.platform.startswith("win32"):
    cx_Oracle.init_oracle_client(lib_dir=r"c:\oracle\instantclient_19_8")

def start_pool():

    pool_min = 4
    pool_max = 4
    pool_inc = 0
    pool_gmd = cx_Oracle.SPOOL_ATTRVAL_WAIT

    print("Connecting to", os.environ.get("PYTHON_CONNECTSTRING"))

    pool = cx_Oracle.SessionPool(user=os.environ.get("PYTHON_USERNAME"),
                                 password=os.environ.get("PYTHON_PASSWORD"),
                                 dsn=os.environ.get("PYTHON_CONNECTSTRING"),
                                 min=pool_min,
                                 max=pool_max,
                                 increment=pool_inc,
                                 threaded=True,
                                 getmode=pool_gmd)

    return pool

#Server na stałe zalogowany czy użytkownik loguje się do bazy danych jak w 'naukowcach'
#connection = ???


@app.route("/")
def hello_world():
    return render_template("base.html")


@app.route("/gry")
def gry():
    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute("SELECT id, nazwa FROM GRA ORDER BY id")
    data = np.array(cursor.fetchall())
    names = data[:, 1]
    ids = data[:, 0]
    links = [url_for('ranking_gry', game_id=id) for id in ids]
    return render_template('list_of_links.html', names=names, links=links)


@app.route("/ranking/gry/<game_id>")
def ranking_gry(game_id):
    connection = pool.acquire()
    cursor = connection.cursor()
    request = ("SELECT grc.id, grc.nazwa FROM "
               "GRACZ grc JOIN UDZIAL ud ON grc.id = ud.id_gracza "
               "JOIN ROZGRYWKA ro ON ud.id_rozgrywki = ro.id "
               "JOIN GRA gra ON ro.id_gry = gra.id "
               "WHERE gra.id = :g_id")
    cursor.execute(request, g_id=game_id)
    data = np.array(cursor.fetchall())
    if data.shape[0] > 0:
        names = [name + " ranking???" for name in data[:, 1]]
        links = ["" for name in names]
    else:
        names = []
        links = []
    return render_template('list_of_links.html', names=names, links=links)


@app.route("/gracze")
def gracze():
    return "gracze"


@app.route("/rank")
def ranking():
    return "ranking"


if __name__ == '__main__':

    pool = start_pool()
    app.run(port=int(os.environ.get('PORT', '8081')))
