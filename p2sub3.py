import chess
from reconchess import utilities as ut

fen= input().strip()         # Read FEN string input and remove any whitespaces/tabs from string from beginning to end
sq = input()
square = chess.parse_square(sq)
#square = chess.parse_square(square)


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
board = chess.Board()
valid_moves = getMovesToTarget(fen,square)
fenStates = []
captureStates = []
moves = []

'''for move in valid_moves:
    fenStates.append(str(makeMove(fen,move)))
    mv,b = makeCaptureMove(fen,move)
    if board.is_capture(mv):
        captureStates.append(str(b))

captureStates.sort()
for state in captureStates:
    print(state)'''
for move in valid_moves:
    '''mv = chess.Move.from_uci(move)
    if board.is_capture(mv):
        print(makeMove(fen,move))'''
    #print(makeMove(fen,move))
    fenStates.append(str(makeMove(fen,move)))

fenStates.sort()

for state in fenStates:
    print(state)

#moves = [move for move in board.legal_moves if move.from_square == square]
#print(valid_moves)