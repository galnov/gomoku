const socket = io();
let player = '';
let room = '';

function joinGame() {
    room = document.getElementById('room').value;
    player = room ? 'X' : 'O';  // Assign player X to the first player
    socket.emit('join_game', { room: room, player: player });
}

socket.on('game_update', (game) => {
    renderBoard(game.board);
    document.getElementById('status').innerText = 
        game.winner ? `Player ${game.winner} wins!` : `Player ${game.current_turn}'s turn`;
});

function makeMove(x, y) {
    socket.emit('make_move', { room: room, position: [x, y], player: player });
}

function renderBoard(board) {
    const boardDiv = document.getElementById('game-board');
    boardDiv.innerHTML = '';
    for (let i = 0; i < board.length; i++) {
        for (let j = 0; j < board[i].length; j++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.innerText = board[i][j];
            cell.onclick = () => makeMove(i, j);
            boardDiv.appendChild(cell);
        }
    }
}
