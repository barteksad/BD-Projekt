from flask import Flask
from flask import render_template
from flask import url_for
import cx_Oracle
import numpy as np

app = Flask(__name__)

#Server na stałe zalogowany czy użytkownik loguje się do bazy danych jak w 'naukowcach'
#connection = ???


@app.route("/")
def hello_world():
    return render_template("base.html")


@app.route("/gry")
def gry():
    cursor = connection.cursor()
    cursor.execute("SELECT id, nazwa FROM GRA ORDER BY id")
    data = np.array(cursor.fetchall())
    names = data[:, 1]
    ids = data[:, 0]
    links = [url_for('ranking_gry', game_id=id) for id in ids]
    return render_template('list_of_links.html', names=names, links=links)


@app.route("/ranking/gry/<game_id>")
def ranking_gry(game_id):
    cursor = connection.cursor()
    request = ("SELECT grc.id, grc.nazwa FROM "
               "GRACZ grc JOIN UDZIAL ud ON grc.id = ud.id_gracza "
               "JOIN ROZGRYWKA ro ON ud.id_rozgrywki = ro.id "
               "JOIN GRA gra ON ro.id_gry = gra.id "
               "WHERE gra.id = " + game_id)
    cursor.execute(request)
    data = np.array(cursor.fetchall())
    names = [name + " ranking???" for name in data[:, 1]]
    links = ["" for name in names]
    return render_template('list_of_links.html', names=names, links=links)


@app.route("/gracze")
def gracze():
    return "gracze"


@app.route("/rank")
def ranking():
    return "ranking"
