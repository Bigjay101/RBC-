import chess

fen= input().strip()              # Read FEN string input and remove any whitespaces/tabs from string from beginning to end
move=input().strip()              # Read move and remove any whitespaces/tabs from 
board = chess.Board(fen)          # Convert FEN string into a Chess board
mv= chess.Move.from_uci(move) 
board.push(mv)                    #Make the Move

#Display the resulting position using a FEN string
print(board.fen())