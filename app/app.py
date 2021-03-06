from flask import Flask
from flask import render_template
from flask import url_for
from flask import request
from flask import redirect
import numpy as np
from py_expression_eval import Parser
from collections import defaultdict

import os
import sys
import cx_Oracle

from user_secrets import PYTHON_USERNAME, PYTHON_PASSWORD

os.environ['PYTHON_USERNAME'] = PYTHON_USERNAME
os.environ['PYTHON_PASSWORD'] = PYTHON_PASSWORD
os.environ['PYTHON_CONNECTSTRING'] = "//labora.mimuw.edu.pl/LABS"

app = Flask(__name__)

if sys.platform.startswith("darwin"):
    cx_Oracle.init_oracle_client(
        lib_dir=os.environ.get("HOME")+"/instantclient_19_3")
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
    # players_request = "SELECT grc.id, grc.nazwa , COUNT(DISTINCT win.id_rozgrywki), COUNT(DISTINCT loos.id_rozgrywki) FROM " \
    #                   "GRACZ grc JOIN UDZIAL ud ON grc.id = ud.id_gracza " \
    #                   "JOIN ROZGRYWKA ro ON ud.id_rozgrywki = ro.id " \
    #                   "JOIN GRA gra ON ro.id_gry = gra.id " \
    #                   "LEFT JOIN (SELECT id_rozgrywki, id_gracza FROM UDZIAL WHERE czy_wygral = 1) win ON win.id_gracza = grc.id " \
    #                   "LEFT JOIN (SELECT id_rozgrywki, id_gracza FROM UDZIAL WHERE czy_wygral = 0) loos ON loos.id_gracza = grc.id " \
    #                   "WHERE gra.id = :g_id GROUP BY grc.id, grc.nazwa"

    players_request = " SELECT G.id, G.nazwa, SUM(U.czy_wygral), COUNT(*) - SUM(U.czy_wygral) " \
                      " FROM GRACZ G " \
                      " JOIN UDZIAL U  " \
                      "     ON G.id = U.id_gracza " \
                      " JOIN ROZGRYWKA R " \
                      "     ON R.id = U.id_rozgrywki " \
                      " WHERE R.id_gry = :g_id " \
                      " GROUP BY(G.id, G.nazwa) "
                      
    cursor = connection.cursor()
    eval_ranking = Parser().parse(ranking_formula)
    cursor.execute(players_request, g_id=game_id)
    data = np.array(cursor.fetchall())

    if data.shape[0] == 0:
        return []
    ranking_points = [[eval_ranking.evaluate(
        {'w': int(row[2]), 'l': int(row[3])})] for row in data]
    ranking = np.append(data, ranking_points, axis=1)
    return np.flipud(ranking[np.argsort(ranking[:, -1])])


@app.route("/play/<play_id>")
def play_stats(play_id):

    connection = pool.acquire()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id_gry, kiedy FROM ROZGRYWKA WHERE id = :play_id", play_id=play_id)
    game_id, play_date = cursor.fetchall()[0]

    cursor.execute("SELECT nazwa FROM GRA WHERE id = :game_id",
                   game_id=game_id)
    game_name = np.array(cursor.fetchall())[0][0]

    cursor.execute(
        "SELECT id_gracza, czy_wygral FROM UDZIAL WHERE id_rozgrywki = :play_id", play_id=play_id)
    players_list = np.array(cursor.fetchall())

    game_link = url_for("ranking_gry", game_id=game_id)
    players_links = [url_for('gracze_info', player_id=i)
                     for i in players_list[:, 0]]

    winner_id = players_list[players_list[:, 1] == 1][:, 0]
    winner_link = [url_for("gracze_info", player_id=w_id) for w_id in winner_id]
    players_list = players_list[:, 0]

    moves_query = "SELECT id_gracza, opis_ruchu FROM RUCH " \
                  "WHERE id_rozgrywki = :play_id " \
                  "ORDER BY nr_ruchu ASC " 

    cursor.execute(moves_query, play_id=play_id)
    moves = np.array(cursor.fetchall())

    return render_template("play_page.html",
                            game_name=game_name,
                            game_link=game_link,
                            play_date=play_date,
                            winner_id=winner_id,
                            winner_link=winner_link,
                            players_list=players_list,
                            players_links=players_links,
                            moves=moves)


def get_player_games_history(connection, player_id):
    games_history_request = "WITH ROZGRYWKI AS ( " \
                            "   SELECT id, id_gry, kiedy FROM ROZGRYWKA " \
                            "   JOIN UDZIAL ON id = id_rozgrywki " \
                            "   WHERE id_gracza = :p_id " \
                            ") " \
                            ", GRACZE AS ( " \
                            "    SELECT ROZGRYWKI.id, ROZGRYWKI.id_gry, UDZIAL.id_gracza, UDZIAL.czy_wygral FROM  ROZGRYWKI "\
                            "    JOIN UDZIAL ON id = id_rozgrywki " \
                            "    ORDER BY ROZGRYWKI.kiedy DESC " \
                            " ) " \
                            "SELECT GRACZE.id, GRA.nazwa, GRACZE.id_gracza, GRACZE.czy_wygral FROM " \
                            "GRACZE LEFT JOIN GRA ON GRACZE.id_gry = GRA.id "
    cursor = connection.cursor()
    cursor.execute(games_history_request, p_id=player_id)
    data = np.array(cursor.fetchall())

    games_hist = defaultdict(list)
    games_wins = dict()

    for row in data:
        play_id, game_name, curr_player_id, has_won = row
        games_hist[(play_id, game_name)].append(curr_player_id)
        if play_id not in games_wins.keys():
            games_wins[play_id] = []
        if has_won == '1':
            games_wins[play_id].append(curr_player_id)

    data = []
    for (play_id, game_name), players_ids in games_hist.items():
        data.append((url_for("play_stats", play_id=play_id),
                     game_name,
                     "gracze : " + ", ".join([str(i) for i in players_ids]),
                     'link-success' if player_id in games_wins[play_id] else 'link-danger'))

    return data


def get_game_plays_history(connection, game_id):
    game_games_request = "SELECT id, kiedy FROM ROZGRYWKA WHERE id_gry = :g_id " \
                         "ORDER BY kiedy DESC"

    cursor = connection.cursor()
    cursor.execute(game_games_request, g_id=game_id)
    return np.array(cursor.fetchall())


@app.route("/gry/<game_id>")
def ranking_gry(game_id):
    connection = pool.acquire()
    game_name, how_many_players, ranking_formula = \
        get_game_info(connection, game_id)
    ranking = get_game_ranking(connection, game_id, ranking_formula)
    if len(ranking) > 0:
        links = [url_for('gracze_info', player_id=p_id)
                 for p_id in ranking[:, 0]]
        content = ranking[:, [1, 4]]
    else:
        links = []
        content = []

    plays_history = get_game_plays_history(connection, game_id)
    if len(plays_history) > 0:
        plays_table_content = plays_history[:, 0:2]
        plays_table_links = [url_for('play_stats', play_id=play_id)
                             for play_id in plays_history[:, 0]]
    else:
        plays_table_content = []
        plays_table_links = []

    ranking_formula = ranking_formula.replace("w", " wygrane ")
    ranking_formula = ranking_formula.replace("l", " przegrane ")

    return render_template('game_page.html',
                           g_name=game_name,
                           g_desc="",
                           p_no=how_many_players,
                           rank_formula=ranking_formula,
                           players_table_label=['Player', 'Points'],
                           players_table_content=content,
                           players_table_links=links,
                           plays_table_label=['Play ID', 'Timestamp'],
                           plays_table_content=plays_table_content,
                           plays_table_links=plays_table_links)


@app.route("/gracze_info/<player_id>")
def gracze_info(player_id):
    player_info_request = "SELECT id, nazwa, typ FROM GRACZ WHERE id = :p_id ORDER BY id"

    player_games_request = "SELECT DISTINCT(gra.id), gra.nazwa FROM GRA gra " \
                           "JOIN ROZGRYWKA roz ON gra.id = roz.id_gry " \
                           "JOIN UDZIAL ud ON ud.id_rozgrywki = roz.id " \
                           "WHERE ud.id_gracza = :p_id"

    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute(player_info_request, p_id=player_id)
    data = np.array(cursor.fetchall())

    p_name, p_type = data[0, 1], data[0, 2]
    p_type = cursor.execute(
        "SELECT nazwa FROM TYPY_GRACZY WHERE id = :p_type", p_type=p_type).fetchall()[0][0]

    cursor.execute(player_games_request, p_id=player_id)
    data = np.array(cursor.fetchall())

    if len(data) > 0:
        game_links = [url_for('ranking_gry', game_id=g_id)
                      for g_id in data[:, 0]]
        game_list = data[:, 1]
    else:
        game_links = []
        game_list = []

    games_history = get_player_games_history(connection, player_id)

    return render_template('player_page.html',
                           p_name=p_name, p_type=p_type,
                           game_list=game_list, game_links=game_links, games_history=games_history)


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


@app.route("/gry/change_formula")
def zmiana_formuly():
    games_names_request = "SELECT nazwa, id FROM GRA"

    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute(games_names_request)
    data = np.array(cursor.fetchall())

    return render_template("change_game_formula.html", g_names=data)


def is_formula_valid(formula):
    try:
        eval_ranking = Parser().parse(formula)
        eval_ranking.evaluate({'w': 123, "l": 321})
        eval_ranking.evaluate({'w': 123, "l": 123})
        eval_ranking.evaluate({'w': 0, "l": 123})
        eval_ranking.evaluate({'w': 123, "l": 0})
        eval_ranking.evaluate({'w': 0, "l": 0})
    except:
        return False

    return True


@app.route("/gry/change_formula/change", methods=['POST'])
def zmien_formule():
    change_fomula_update = "UPDATE GRA " \
                           "SET formula_rankingu = :f_text " \
                           "WHERE id = :g_id "

    g_id = request.form['g_id']
    f_text = request.form['f_text']

    if not g_id:
        return "Nie wybrano gry"
    if not f_text:
        "Nie wprowadzono formu??y"
    if not is_formula_valid(f_text):
        return "Wprowadzono z???? formu????"

    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        cursor.execute(change_fomula_update, (f_text, g_id))
        connection.commit()
    except cx_Oracle.DatabaseError:
        return "Database Error"

    return redirect(url_for('ranking_gry', game_id=g_id))


@app.route("/gracze/add")
def gracze_dodaj():
    player_types_request = "SELECT nazwa, id FROM TYPY_GRACZY"

    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute(player_types_request)
    data = np.array(cursor.fetchall())

    return render_template("add_player.html", p_types=data)


@app.route("/gracze/add/dodawanie", methods=['POST'])
def dodawanie_gracza():
    new_player_insert = "INSERT INTO GRACZ (nazwa, typ) VALUES (:name, :type)"

    p_type = request.form['p_type']
    p_name = request.form['p_name']

    if not p_type:
        return "nie wybrano typu"
    if not p_name:
        return "podano pust?? nazw??"
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        cursor.execute(new_player_insert, (p_name, p_type))
        connection.commit()
    except cx_Oracle.DatabaseError:
        return "Database Error"

    return redirect(url_for('gracze'))


if __name__ == '__main__':

    pool = start_pool()
    app.run(port=int(os.environ.get('PORT', '8081')), debug=True)
