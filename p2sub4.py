import chess
from reconchess import utilities as ut

#N = int(input())
#window = input()
#fen= input().strip()         # Read FEN string input and remove any whitespaces/tabs from string from beginning to end
#sq = input()
#square = chess.parse_square(sq)
#square = chess.parse_square(square)

def isConsistent(fen,window):
    positions = window.split(";")
    pos_map = {}
    for pos in positions:
        pos = pos.split(":")
        pos_map[pos[0]] = pos[1]
    l = len(pos_map)
    matches = 0
    board =  chess.Board(fen)
    isConsistent = True
    for square,piece in pos_map.items():
        p = board.piece_at(chess.parse_square(square))
        symbol = p.symbol() if p else "?"
        if pos_map[square] == symbol:
            continue
        else:
            isConsistent = False
            break
    return isConsistent
        
        

    #print(pos_map)

    

def printBoard(fen):
    #fen= input().strip()         # Read FEN string input and remove any whitespaces/tabs from string from beginning to end
    board = chess.Board(fen)     # Convert FEN string into a Chess board
    print(board)                 #Display the ASCII representation of the chess board

def makeMove(fen,move):              # Read move and remove any whitespaces/tabs from 
    board = chess.Board(fen)          # Convert FEN string into a Chess board
    mv= chess.Move.from_uci(move) 
    board.push(mv)  
    return board.fen()                #Make the Move
    #print(board.fen())
#Display the resulting position using a FEN string
    
def makeCaptureMove(fen,move):              # Read move and remove any whitespaces/tabs from 
    board = chess.Board(fen)          # Convert FEN string into a Chess board
    mv= chess.Move.from_uci(move) 
    board.push(mv)  
    return board.fen()                #Make the Move
    #print(board.fen())
#Display the resulting position using a FEN string

def getMovesToTarget(fen,square):
    valid_moves = []
    moves = []
    board = chess.Board(fen)
    psuedoLegalMoves = [move for move in board.pseudo_legal_moves if move.to_square == square]
    null_move = str(chess.Move.null())
    #print(psuedoLegalMoves)
    for move in ut.without_opponent_pieces(board).generate_castling_moves():
        if not ut.is_illegal_castle(board,move) and move.to_square == square:
            valid_moves.append(str(move))
            #moves.append(move)
    for move in psuedoLegalMoves:
        if str(move) not in valid_moves:
            valid_moves.append(str(move))
            #moves.append(move)
    valid_moves.sort()
    #valid_moves.insert(0,null_move)
    return valid_moves

N = int(input())
states = []
consistent_states = []
for i in range(N):
    states.append(input())
    
window = input()
for i in range(N):
    if isConsistent(states[i],window):
        consistent_states.append(states[i])

consistent_states.sort()

for cons_state in consistent_states:
    print(cons_state)


