import chess
from reconchess import utilities as ut

fen= input().strip()         # Read FEN string input and remove any whitespaces/tabs from string from beginning to end

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
    return mv,board.fen()                #Make the Move
    #print(board.fen())
#Display the resulting position using a FEN string

def getMoves(fen):
    valid_moves = []
    board = chess.Board(fen)
    psuedoLegalMoves = board.pseudo_legal_moves
    null_move = str(chess.Move.null())
    #print(psuedoLegalMoves)
    for move in ut.without_opponent_pieces(board).generate_castling_moves():
        if not ut.is_illegal_castle(board,move):
            valid_moves.append(str(move))
    for move in psuedoLegalMoves:
        if str(move) not in valid_moves:
            valid_moves.append(str(move))
    valid_moves.sort()
    valid_moves.insert(0,null_move)
    return valid_moves

valid_moves = getMoves(fen)
fenStates = []
captureStates = []
for move in valid_moves:
    fenStates.append(str(makeMove(fen,move)))
    mv,b = makeCaptureMove(fen,move)
    if chess.Board().is_capture(mv):
        captureStates.append(str(b))

captureStates.sort()
for state in captureStates:
    print(state)