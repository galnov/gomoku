import requests
import time
import socketio

SERVER_URL = "http://127.0.0.1:5001"
ROOM_CODE = "1234"
MY_SYMBOL = 'X'
CURRENT_PLAYER = 'X'

sio = socketio.Client(reconnection=True, logger=True, engineio_logger=True)  # Enable logging for debug

def create_room_if_needed():
    global MY_SYMBOL
    try:
        response = requests.get(f"{SERVER_URL}/api/game/{ROOM_CODE}")
        if response.status_code == 200:
            print(f"Room '{ROOM_CODE}' exists. Joining the room.")
            MY_SYMBOL = 'O'
            sio.emit('join_game', {'room': ROOM_CODE, 'player': MY_SYMBOL})  # Join the game room
        else:
            print(f"Room '{ROOM_CODE}' not found. Attempting to create it.")
            MY_SYMBOL = 'X'
            sio.emit('join_game', {'room': ROOM_CODE, 'player': MY_SYMBOL})  # Join the game room
            #print(f"Failed to create the room. Server responded with: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with server: {e}")


def get_game():
    try:
        response = requests.get(f"{SERVER_URL}/api/game/{ROOM_CODE}")
        response.raise_for_status()
        return response.json()["players"], response.json()["board"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching board: {e}")
    except ValueError:
        print(f"Failed to parse JSON response: {response.text}")
    return None


def make_move(row, col):
    global MY_SYMBOL
    try:
        response = requests.post(f"{SERVER_URL}/api/make_move",
                                 json={"room": ROOM_CODE, "player": MY_SYMBOL, "position": [row, col]})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making move: {e}")
    except ValueError:
        print(f"Failed to parse JSON response: {response.text}")
    return None


def find_best_move(board):
    for i, row in enumerate(board):
        for j, cell in enumerate(row):
            if cell == "":
                return i, j
    return None


def check_game_over(board, symbol):
    """Check if there are five consecutive symbols in any row, column, or diagonal."""
    board_size = len(board)

    # Check rows and columns
    for i in range(board_size):
        # Check row
        if symbol * 5 in "".join(board[i]):
            return True
        # Check column
        if symbol * 5 in "".join(row[i] for row in board):
            return True

    # Check diagonals
    for row in range(board_size - 4):
        for col in range(board_size - 4):
            # Check diagonal from top-left to bottom-right
            if all(board[row + k][col + k] == symbol for k in range(5)):
                return True
            # Check diagonal from bottom-left to top-right
            if all(board[row + 4 - k][col + k] == symbol for k in range(5)):
                return True

    return False


def play_game():
    global CURRENT_PLAYER
    global MY_SYMBOL

    create_room_if_needed()

    while True:
        players, board = get_game()

        while 'O' not in players:
            print("Waiting for other player to join...")
            time.sleep(3)
            players, board = get_game()

        if board is None:
            print("Unable to fetch board. Exiting.")
            break

        if check_game_over(board, 'O' if MY_SYMBOL == 'X' else 'X'):
            print("Game Over!")
            break

        while CURRENT_PLAYER != MY_SYMBOL:
            print("Waiting for my turn...")
            time.sleep(1)

        move = find_best_move(board)
        if move:
            row, col = move
            print(f"Playing at ({row}, {col})")
            make_move(row, col)
        else:
            print("No moves available.")
            break

        time.sleep(1)


@sio.event
def connect():
    print("Connected to the server.")

@sio.event
def disconnect():
    print("Disconnected from the server.")

@sio.on('game_update')
def game_update(game):
    global CURRENT_PLAYER
    CURRENT_PLAYER = game['current_turn']
    print("Received game update!")

@sio.on('test_event')
def test_event(data):
    print("Received test event:", data)


if __name__ == "__main__":
    sio.connect(SERVER_URL, transports=["websocket"])
    play_game()
