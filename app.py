from flask import Flask, render_template, request, redirect, url_for, session
import uuid

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Klucz do obsługi sesji

# Rozmiar planszy
SIZE = 8

# Lista pokoi gier (dla wielu par graczy)
game_rooms = {}

# Stan gry
game_state = {
    "fox": [7, 2],  # Początkowa pozycja lisa
    "dogs": [[0, 1], [0, 3], [0, 5], [0, 7]],  # Początkowe pozycje psów
    "selected": None,  # Wybrana figura (lis lub pies)
    "turn": "fox",  # Lis zaczyna
    "game_over": False,  # Stan gry
    "winner": None  # Zwycięzca
}


# Funkcja sprawdzająca, czy pole jest brązowe
def is_brown_field(x, y):
    return (x + y) % 2 == 1


# Funkcja sprawdzająca, czy pole jest zajęte
def is_occupied(new_pos):
    return new_pos == game_state["fox"] or new_pos in game_state["dogs"]


# Funkcja sprawdzająca, czy ruch jest poprawny
def is_valid_move(piece, current_pos, new_pos):
    x, y = current_pos
    new_x, new_y = new_pos

    # Sprawdzenie, czy ruch mieści się na planszy i prowadzi na brązowe pole
    if not (0 <= new_x < SIZE and 0 <= new_y < SIZE) or not is_brown_field(new_x, new_y):
        return False

    # Sprawdzenie, czy pole docelowe jest zajęte
    if is_occupied(new_pos):
        return False

    # Oblicz różnicę w pozycjach
    dx = new_x - x
    dy = new_y - y

    # Zasady ruchu lisa
    if piece == "fox":
        return abs(dx) == 1 and abs(dy) == 1

    # Zasady ruchu psa
    if piece == "dog":
        return dx == 1 and abs(dy) == 1

    return False


# Funkcja sprawdzająca, czy lis ma dostępne ruchy
def has_fox_moves():
    x, y = game_state["fox"]
    for dx in [-1, 1]:
        for dy in [-1, 1]:
            new_x, new_y = x + dx, y + dy
            if is_valid_move("fox", [x, y], [new_x, new_y]):
                return True
    return False


# Funkcja sprawdzająca, czy dany pies jest otoczony
def is_dog_surrounded(dog_pos):
    x, y = dog_pos
    for dx in [-1, 1]:
        for dy in [-1, 1]:
            new_x, new_y = x + dx, y + dy
            if is_valid_move("dog", [x, y], [new_x, new_y]):
                return False  # Jeśli pies ma choć jeden ruch, nie jest otoczony
    return True


# Funkcja sprawdzająca, czy wszystkie psy są otoczone
def are_all_dogs_surrounded():
    return all(is_dog_surrounded(dog) for dog in game_state["dogs"])


# Funkcja sprawdzająca, czy gra jest zakończona
def check_game_over():
    # Zwycięstwo lisa: Lis osiągnął jedno z górnych brązowych pól
    if game_state["fox"][0] == 0 and is_brown_field(game_state["fox"][0], game_state["fox"][1]):
        game_state["game_over"] = True
        game_state["winner"] = "fox"
        session.clear()  # Wyczyszczenie sesji po zakończeniu gry
        return True

    # Przegrana lisa: Lis nie ma dostępnych ruchów (jest okrążony przez psy)
    if game_state["turn"] == "fox" and not has_fox_moves():
        game_state["game_over"] = True
        game_state["winner"] = "dogs"
        session.clear()  # Wyczyszczenie sesji po zakończeniu gry
        return True

    # Przegrana psów: Wszystkie psy są otoczone
    if are_all_dogs_surrounded():
        game_state["game_over"] = True
        game_state["winner"] = "fox"  # Jeśli psy są otoczone, lis wygrywa
        session.clear()  # Wyczyszczenie sesji po zakończeniu gry
        return True

    return False


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/instructions")
def instructions():
    return render_template("instructions.html")


@app.route("/game_modes", methods=["GET", "POST"])
def game_modes():
    if request.method == "POST":
        game_mode = request.form.get("game_mode")

        if game_mode == "2players":
            return redirect(url_for("game"))  # Tryb 2 graczy na jednym komputerze
        elif game_mode == "vs_computer":
            return redirect(url_for("game_computer"))  # Tryb z komputerem
        elif game_mode == "online":
            return redirect(url_for("game_online"))  # Tryb online

    return render_template("game_modes.html")


def reset_game():
    global game_state

    game_state = {
        "fox": [7, 2],  # Początkowa pozycja lisa
        "dogs": [[0, 1], [0, 3], [0, 5], [0, 7]],  # Początkowe pozycje psów
        "selected": None,  # Wybrana figura (lis lub pies)
        "turn": "fox",  # Lis zaczyna
        "game_over": False,  # Stan gry
        "winner": None  # Zwycięzca
    }


"""TRYB 2 GRACZY NA JEDNYM KOMPUTERZE"""
@app.route("/game", methods=["GET", "POST"])
def game():
    global game_state

    # Obsługa resetu gry
    if request.method == "POST" and "reset" in request.form:
        reset_game()  # Resetowanie stanu gry
        return redirect(url_for("game"))  # Przeładuj stronę po restarcie

    # Jeśli gra jest zakończona, wyświetl zwycięzcę na tej samej stronie
    if game_state["game_over"]:
        return render_template("game.html", state=game_state, size=SIZE, winner=game_state["winner"])

    if request.method == "POST":
        x = request.form.get("x")
        y = request.form.get("y")

        # Sprawdzamy, czy wartości x i y zostały przekazane i nie są None
        if x is not None and y is not None:
            try:
                x = int(x)
                y = int(y)
            except ValueError:
                print(f"Niepoprawne dane: x={x}, y={y}")
                return redirect(url_for("game"))  # Przykład: wróć do gry

            if game_state["selected"] is None:
                if game_state["fox"] == [x, y] and game_state["turn"] == "fox":
                    game_state["selected"] = ("fox", game_state["fox"])
                elif [x, y] in game_state["dogs"] and game_state["turn"] == "dogs":
                    index = game_state["dogs"].index([x, y])
                    game_state["selected"] = (f"dog_{index}", game_state["dogs"][index])

            elif game_state["selected"]:
                piece, current_pos = game_state["selected"]
                if is_valid_move("fox" if piece == "fox" else "dog", current_pos, [x, y]):
                    if piece == "fox":
                        game_state["fox"] = [x, y]
                    else:
                        index = int(piece.split("_")[1])
                        game_state["dogs"][index] = [x, y]

                    # Zmień kolej
                    game_state["turn"] = "dogs" if game_state["turn"] == "fox" else "fox"

                game_state["selected"] = None  # Reset wyboru

            check_game_over()

            return redirect(url_for("game"))

    return render_template("game.html", state=game_state, size=SIZE)


@app.route("/game_online", methods=["GET", "POST"])
def game_online():
    room_id = session.get("room_id")

    if room_id not in game_rooms:
        return redirect(url_for("choose_room"))  # Jeśli nie ma pokoju, wróć do wyboru pokoju

    # Sprawdzanie zakończenia gry
    if game_rooms[room_id]["game_over"]:
        winner = game_rooms[room_id]["winner"]
        session.clear()  # Wyczyszczenie sesji po zakończeniu gry
        return render_template("game_online.html", state=game_rooms[room_id], winner=winner)

    # Inicjalizuj stan gry w przypadku braku pokoju
    if room_id not in game_rooms:
        game_rooms[room_id] = {
            "fox": [7, 2],  # Początkowa pozycja lisa
            "dogs": [[0, 1], [0, 3], [0, 5], [0, 7]],  # Początkowe pozycje psów
            "selected": None,  # Wybrana figura
            "turn": "fox",  # Lis zaczyna
            "game_over": False,  # Gra nie zakończona
            "winner": None,  # Brak zwycięzcy
            "players": {}  # Lista graczy
        }

    # Sprawdź, czy to nowy gracz, czy już ktoś jest w pokoju
    if session.get("player_role") is None:
        current_players = len(game_rooms[room_id]["players"])

        if current_players == 0:
            session["player_role"] = "fox"  # Pierwszy gracz = lis
        else:
            session["player_role"] = "dogs"  # Drugi gracz = psy

        # Dodajemy gracza do pokoju z unikalnym ID
        player_id = str(uuid.uuid4())  # Generujemy unikalny ID dla gracza
        game_rooms[room_id]["players"][session.get("player_role")] = player_id

    # Obsługa przesyłania ruchów gracza
    if request.method == "POST":
        x = request.form.get("x")
        y = request.form.get("y")

        # Jeśli gracz ma prawidłowy ruch
        if x is not None and y is not None:
            try:
                x = int(x)
                y = int(y)
            except ValueError:
                print(f"Niepoprawne dane: x={x}, y={y}")
                return redirect(url_for("game_online"))

            player_role = session.get("player_role")
            if player_role == game_rooms[room_id]["turn"]:
                if game_rooms[room_id]["selected"] is None:
                    if game_rooms[room_id]["fox"] == [x, y] and player_role == "fox":
                        game_rooms[room_id]["selected"] = ("fox", game_rooms[room_id]["fox"])
                    elif [x, y] in game_rooms[room_id]["dogs"] and player_role == "dogs":
                        index = game_rooms[room_id]["dogs"].index([x, y])
                        game_rooms[room_id]["selected"] = (f"dog_{index}", game_rooms[room_id]["dogs"][index])

                elif game_rooms[room_id]["selected"]:
                    piece, current_pos = game_rooms[room_id]["selected"]
                    if is_valid_move("fox" if piece == "fox" else "dog", current_pos, [x, y]):
                        if piece == "fox":
                            game_rooms[room_id]["fox"] = [x, y]
                        else:
                            index = int(piece.split("_")[1])
                            game_rooms[room_id]["dogs"][index] = [x, y]

                        # Zmiana tury
                        game_rooms[room_id]["turn"] = "dogs" if game_rooms[room_id]["turn"] == "fox" else "fox"

                    game_rooms[room_id]["selected"] = None

                # Sprawdź zakończenie gry
                check_game_over()

                return redirect(url_for("game_online"))

    return render_template("game_online.html", state=game_rooms[room_id], size=SIZE)


@app.route("/choose_room", methods=["GET", "POST"])
def choose_room():
    if request.method == "POST":
        room_id = request.form.get("room_id")

        # Jeśli użytkownik próbuje dołączyć do pokoju
        if room_id:
            if room_id in game_rooms:
                session["room_id"] = room_id  # Zapisujemy ID pokoju w sesji

                # Sprawdzamy, czy w pokoju jest już jeden gracz (lis)
                if len(game_rooms[room_id]["players"]) == 1:
                    session["player_role"] = "dogs"  # Drugi gracz (psy) dostaje ID
                    game_rooms[room_id]["players"]["dogs"] = str(uuid.uuid4())  # Drugi gracz dostaje ID
                    return redirect(url_for("game_online"))  # Drugi gracz wchodzi do gry
                elif len(game_rooms[room_id]["players"]) == 2:
                    return "Pokój jest pełny. Proszę wybrać inny pokój lub poczekać."
            else:
                return "Pokój o podanym ID nie istnieje. Sprawdź ID i spróbuj ponownie."

        # Jeśli gracz chce stworzyć nowy pokój
        else:
            room_id = str(uuid.uuid4())  # Generujemy nowe ID pokoju
            session["room_id"] = room_id  # Zapisujemy ID pokoju w sesji
            session["player_role"] = "fox"  # Pierwszy gracz to lis
            game_rooms[room_id] = {
                "fox": [7, 2],  # Początkowa pozycja lisa
                "dogs": [[0, 1], [0, 3], [0, 5], [0, 7]],  # Początkowe pozycje psów
                "selected": None,
                "turn": "fox",  # Lis zaczyna
                "game_over": False,  # Gra nie zakończona
                "winner": None,
                "players": {"fox": str(uuid.uuid4())}  # Gracz (lis) dostaje unikalny ID
            }
            return render_template("choose_room.html", room_id=room_id)  # Przekazujemy ID nowego pokoju

    return render_template("choose_room.html")



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000 ,debug=True)
