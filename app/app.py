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


def get_game_info(connection, game_id):
    game_info_request = "SELECT nazwa, ilu_graczy, formula_rankingu FROM GRA " \
                        "WHERE id = :g_id"

    cursor = connection.cursor()
    cursor.execute(game_info_request, g_id=game_id)
    data = cursor.fetchall()
    if len(data) == 0:
        raise ValueError("GAME NOT FOUND")
    return data[0]


def get_game_ranking(connection, game_id, ranking_formula):
    players_request = "SELECT DISTINCT(grc.id), grc.nazwa FROM " \
                       "GRACZ grc JOIN UDZIAL ud ON grc.id = ud.id_gracza " \
                       "JOIN ROZGRYWKA ro ON ud.id_rozgrywki = ro.id " \
                       "JOIN GRA gra ON ro.id_gry = gra.id " \
                       "WHERE gra.id = :g_id"

    count_games_request = "SELECT COUNT(u.czy_wygral) FROM " \
                          "GRACZ g JOIN UDZIAL u ON g.id = u.id_gracza " \
                          "JOIN ROZGRYWKA r ON u.id_rozgrywki = r.id " \
                          "WHERE r.id_gry = :g_id " \
                          "AND g.id = :p_id " \
                          "AND u.czy_wygral = :win"

    cursor = connection.cursor()
    eval_ranking = Parser().parse(ranking_formula)

    def get_player_ranking(player_id):
        cursor.execute(count_games_request, g_id=game_id, p_id=player_id, win=1)
        wins = cursor.fetchall()[0][0]
        cursor.execute(count_games_request, g_id=game_id, p_id=player_id, win=0)
        looses = cursor.fetchall()[0][0]
        return eval_ranking.evaluate({'w': wins, 'l': looses})

    cursor.execute(players_request, g_id=game_id)
    data = np.array(cursor.fetchall())
    if data.shape[0] == 0:
        return []
    ranking_points = [[get_player_ranking(p_id)] for p_id in data[:, 0]]
    ranking = np.append(data, ranking_points, axis=1)
    return np.flipud(ranking[np.argsort(ranking[:, -1])])


@app.route("/gry/<game_id>")
def ranking_gry(game_id):
    connection = pool.acquire()
    game_name, how_many_players, ranking_formula = \
        get_game_info(connection, game_id)
    ranking = get_game_ranking(connection, game_id, ranking_formula)
    if len(ranking) > 0:
        links = [url_for('ranking_gracza', player_id=p_id) for p_id in ranking[:, 0]]
        content = ranking[:, 1:]
    else:
        links = []
        content = []
    return render_template('game_page.html',
                           table_label=['Player', 'Points'],
                           table_content=content, table_links=links)

@app.route("/gracze_info/<player_id>")
def gracze_info(player_id):
    player_info_request  = "SELECT id, nazwa, typ FROM GRACZ WHERE id = :p_id ORDER BY id"

    player_games_request = "SELECT DISTINCT(gra.id), gra.nazwa FROM GRA gra " \
                           "JOIN ROZGRYWKA roz ON gra.id = roz.id_gry " \
                           "JOIN UDZIAL ud ON ud.id_rozgrywki = roz.id " \
                           "WHERE ud.id_gracza = :p_id"

    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute(player_info_request, p_id=player_id)
    data = np.array(cursor.fetchall())

    p_name, p_type = data[0, 1], data[0 ,2]
    p_type = cursor.execute("SELECT nazwa FROM TYPY_GRACZY WHERE id = :p_type", p_type=p_type).fetchall()[0][0]

    cursor.execute(player_games_request, p_id=player_id)
    data = np.array(cursor.fetchall())

    if len(data) > 0:
        game_links = [url_for('ranking_gry', game_id=g_id) for g_id in data[:, 0]]
    else:
        game_links = []

    return render_template('player_page.html',
                            p_name=p_name, p_type=p_type,
                            game_list=data[:, 1], game_links=game_links)

@app.route("/gracze")
def gracze():
    players_info_request = "SELECT id, nazwa FROM GRACZ ORDER BY id"

    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute(players_info_request)
    data = np.array(cursor.fetchall())

    names = data[:, 1]
    ids = data[:, 0]
    links = [url_for('gracze_info', player_id=id) for id in ids]

    return render_template('list_of_links.html', names=names, links=links)


@app.route("/gracze/<player_id>")
def ranking_gracza(player_id):
    return "gracz " + str(player_id)


if __name__ == '__main__':

    pool = start_pool()
    app.run(port=int(os.environ.get('PORT', '8081')), debug=True)
