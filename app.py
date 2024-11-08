from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# In-memory game storage for rooms
rooms = {}


def create_board():
    """Create an empty 15x15 Gomoku board."""
    return [['' for _ in range(15)] for _ in range(15)]


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('join_game')
def on_join(data):
    room = data['room']
    player = None

    # Check if room already exists
    if room not in rooms:
        # Initialize new room with the first player as 'X'
        rooms[room] = {
            'board': create_board(),
            'current_turn': 'X',
            'players': {'X': data['player']},  # Store player symbols in dictionary
            'winner': None
        }
        player = 'X'
    else:
        # Assign 'O' to the second player if the room already exists and has only one player
        if 'O' not in rooms[room]['players']:
            rooms[room]['players']['O'] = data['player']
            player = 'O'
        else:
            emit('error', {'message': 'Room is full!'}, to=request.sid)
            return

    # Confirm player joined and update the room
    join_room(room)
    emit('assign_symbol', {'player': player}, to=request.sid)  # Inform player of their symbol
    emit('game_update', rooms[room], room=room)  # Broadcast updated game state to the room


@socketio.on('make_move')
def on_move(data):
    room = data['room']
    x, y = data['position']
    player = data['player']

    game = rooms[room]
    if game['current_turn'] == player and not game['winner'] and game['board'][x][y] == '':
        game['board'][x][y] = player
        game['current_turn'] = 'O' if player == 'X' else 'X'

        # Check for win condition
        if check_winner(game['board'], player, x, y):
            game['winner'] = player

        emit('game_update', game, room=room)
    else:
        emit('error', {'message': 'Invalid move or not your turn'}, to=request.sid)


def check_winner(board, player, x, y):
    """Check for 5 in a row from position (x, y) for the given player."""
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dx, dy in directions:
        count = 1
        for i in range(1, 5):
            if 0 <= x + i * dx < 15 and 0 <= y + i * dy < 15 and board[x + i * dx][y + i * dy] == player:
                count += 1
            else:
                break
        for i in range(1, 5):
            if 0 <= x - i * dx < 15 and 0 <= y - i * dy < 15 and board[x - i * dx][y - i * dy] == player:
                count += 1
            else:
                break
        if count >= 5:
            return True
    return False


if __name__ == '__main__':
    #socketio.run(app, debug=True)
    if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)  # remove debug=True for production
