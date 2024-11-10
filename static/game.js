const socket = io();
let player = '';
let room = '';

function joinGame() {
    room = document.getElementById('room').value;
    socket.emit('join_game', { room: room, player: player });
}

socket.on('assign_symbol', (data) => {
    player = data.player;  // Set the player symbol ('X' or 'O')
    document.getElementById('status').innerText = `You are player ${player}`;
});

socket.on('game_update', (game) => {
    renderBoard(game.board);
    document.getElementById('status').innerText =
        game.winner ? `Player ${game.winner} wins!` : `Player ${game.current_turn}'s turn`;
    if (game.winner) {
        alert(`Player ${game.winner} wins!`);
    }
});

socket.on('error', (data) => {
    alert(data.message);
});

function makeMove(x, y) {
    socket.emit('make_move', { room: room, position: [x, y], player: player });
}

function renderBoard(board) {
    const boardDiv = document.getElementById('game-board');
    boardDiv.innerHTML = '';  // Clear previous board state
    boardDiv.className = 'board'; // Ensures correct styling is applied

    // Populate cells
    for (let i = 0; i < board.length; i++) {
        for (let j = 0; j < board[i].length; j++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.innerText = board[i][j] || ''; // Show 'X', 'O', or empty string
            cell.onclick = () => makeMove(i, j);  // Click handler for making moves
            boardDiv.appendChild(cell);
        }
    }
}

