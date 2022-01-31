import cx_Oracle
import numpy as np

from user_secrets import PYTHON_USERNAME, PYTHON_PASSWORD

connection = cx_Oracle.connect(user=PYTHON_USERNAME, password=PYTHON_PASSWORD,
                               dsn="//labora.mimuw.edu.pl/LABS")


get_games_request = "SELECT nazwa, id FROM GRA"
get_game_info_request = "SELECT nazwa, ilu_graczy FROM GRA WHERE id = :g_id"
get_players_request = "SELECT nazwa, id FROM GRACZ"

insert_play = "INSERT INTO ROZGRYWKA (id_gry) VALUES (:g_id) " \
              "RETURNING id INTO :new_id"
insert_playing = "INSERT INTO UDZIAL (id_rozgrywki, id_gracza, czy_wygral) " \
                 "VALUES (:r_id, :p_id, :w)"
insert_move = "INSERT INTO RUCH (id_rozgrywki, id_gracza, nr_ruchu, opis_ruchu) " \
              "VALUES (:r_id, :p_id, :numer, :opis)"

def print_array(arr):
    for r in arr:
        w = ''
        for e in r:
            w += str(e) + ", "
        print(w)


def generate_results_and_moves(players, how_many, game_id):
    def random_on_chessboard():
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        r = np.random.randint(0, 8, 2)
        return letters[r[0]] + str(r[1])

    def random_placeholder_move_description():
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'x', 'w', 'l', 'o', 'u', 'j', 'v', 'z']
        r = np.random.randint(0, 16, 4)
        w = "Placeholder description: "
        for x in r:
            w += letters[x]
        return w

    def random_card():
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        colours = ["Kier", "Karo", "Pik", "Trefl"]
        v = np.random.randint(13)
        c = np.random.randint(4)
        return values[v] + " " + colours[c]


    moves = []
    winners = []
    if game_id == 1 or game_id == 2:
        for i in range(how_many):
            moves.append(
                [players[i % len(players)],
                 random_on_chessboard() + " " + random_on_chessboard()])
        winners.append(players[np.random.randint(0, len(players))])
    elif game_id == 4:
        for i in range(how_many):
            moves.append([players[i % len(players)], random_card()])
        w_index = np.random.randint(0, len(players))
        winners.append(players[w_index])
        winners.append(players[(w_index + 2) % len(players)])
    else:
        for i in range(how_many):
            moves.append([players[i % len(players)],
                          random_placeholder_move_description()])
        winners.append(players[np.random.randint(0, len(players))])
    return winners, moves


def simulate_game():

    cursor = connection.cursor()
    cursor.execute(get_games_request)
    games = np.array(cursor.fetchall())
    if len(games) == 0:
        print('No games')
        return

    print("Games: ")
    print_array(games)
    print()
    while True:
        game_id = input("Choose game ID: ")
        if game_id in games[:, 1]:
            break
        print("Wrong ID")

    cursor.execute(get_game_info_request, g_id=game_id)
    game_info = np.array(cursor.fetchall())[0]

    cursor.execute(get_players_request)
    players = np.array(cursor.fetchall())
    if len(players) == 0:
        print('No players')
        return

    print("Players: ")
    print_array(players)
    chosen_players = set()
    while True:
        print()
        print("Choose " + game_info[1] + " players")
        chosen_players.clear()
        for i in range(int(game_info[1])):
            p = input("Player " + str(i + 1) + ": ")
            if p in chosen_players:
                print("Player already selected")
                break
            elif p not in players[:, 1]:
                print("Incorrect player")
                break
            else:
                chosen_players.add(p)
        if len(chosen_players) == int(game_info[1]):
            break
    chosen_players = list(chosen_players)
    print()
    how_many_moves = -1
    while how_many_moves < 0:
        how_many_moves = int(input("How many moves: "))
        if how_many_moves < 0:
            print("Moves number must be greater then 0")

    winners, moves = generate_results_and_moves(chosen_players,
                                                how_many_moves, int(game_id))

    new_play_id = cursor.var(cx_Oracle.NUMBER)
    cursor.execute(insert_play, g_id=game_id, new_id=new_play_id)
    new_play_id = int(new_play_id.getvalue()[0])
    for p in chosen_players:
        cursor.execute(insert_playing, r_id=new_play_id, p_id=p,
                       w=(int(p in winners)))

    no = 0
    for p, m in moves:
        no += 1
        cursor.execute(insert_move, r_id=new_play_id, p_id=p, numer=no, opis=m)

    connection.commit()


while True:
    simulate_game()

