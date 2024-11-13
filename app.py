from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room


# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None)

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
        #print("Assigning X to first player")
        rooms[room] = {
            'board': create_board(),
            'current_turn': 'X',
            'players': {'X': data['player']},  # Store player symbols in dictionary
            'winner': None
        }
        player = 'X'
    else:
        # Assign 'O' to the second player if the room already exists and has only one player
        #print("Assigning O to second player")
        if 'O' not in rooms[room]['players']:
            rooms[room]['players']['O'] = data['player']
            player = 'O'
        else:
            socketio.emit('error', {'message': 'Room is full!'}, to=request.sid)
            return

    # Confirm player joined and update the room
    join_room(room)
    socketio.emit('assign_symbol', {'player': player}, to=request.sid)  # Inform player of their symbol
    socketio.emit('game_update', rooms[room], room=room)  # Broadcast updated game state to the room
    #print("game_update 0")


@socketio.on('make_move')
def on_move(data):
    room = data['room']
    x, y = data['position']
    player = data['player']

    game = rooms[room]
    if game['current_turn'] == player and not game['winner'] and game['board'][x][y] == '':
        game['board'][x][y] = player
        game['current_turn'] = 'O' if player == 'X' else 'X'

        socketio.emit('game_update', game, room=room)
        #print("game_update 1")
        # Check for win condition
        if check_winner(game['board'], player, x, y):
            game['winner'] = player
            socketio.emit('game_update', game, room=room)
            #print("game_update 2")


    else:
        socketio.emit('error', {'message': 'Invalid move or not your turn'}, to=request.sid)


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


'''
@app.route('/api/join_room', methods=['POST'])
def api_create_room():
    data = request.get_json()
    room = data['room']

    if room not in rooms:
        rooms[room] = {
            'board': create_board(),
            'current_turn': 'X',
            'players': {'X': None},
            'winner': None
        }
        return jsonify({"message": "Room created successfully", "board": rooms[room]['board']}), 201
    return jsonify({"message": "Room already exists", "board": rooms[room]['board']}), 200
'''

@app.route('/api/game/<room>', methods=['GET'])
def api_get_game(room):
    if room in rooms:
        return jsonify({"players": rooms[room]['players'],
                        "board": rooms[room]['board'],
                        "current_turn": rooms[room]['current_turn'],
                        "winner": rooms[room]['winner']}), 200
    return jsonify({"error": "Room not found"}), 404


@app.route('/api/make_move', methods=['POST'])
def api_make_move():
    data = request.get_json()
    room = data['room']
    player = data['player']
    x, y = data['position']

    if room in rooms:
        game = rooms[room]
        if game['current_turn'] != player:
            return jsonify({"error": "Not your turn"}), 400
        if game['board'][x][y] != '' or game['winner']:
            return jsonify({"error": "Invalid move"}), 400

        game['board'][x][y] = player
        game['current_turn'] = 'O' if player == 'X' else 'X'

        # Check for win condition
        if check_winner(game['board'], player, x, y):
            game['winner'] = player
        socketio.emit('game_update', game, room=room)
        #print("game update 2")
        return jsonify({"message": "Move successful", "board": game['board'], "winner": game['winner']}), 200

    return jsonify({"error": "Room not found"}), 404


if __name__ == '__main__':
    #socketio.run(app, host='0.0.0.0', port=5001, debug=True)
    socketio.run(app, host='0.0.0.0', port=5000)  # remove debug=True for production
