import chess

fen= input().strip()         # Read FEN string input and remove any whitespaces/tabs from string from beginning to end
board = chess.Board(fen)     # Convert FEN string into a Chess board
print(board)                 #Display the ASCII representation of the chess board

