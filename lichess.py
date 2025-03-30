import time
import berserk
from dotenv import load_dotenv
import os
import threading



def delete_stale_games(client, game_id=None) -> list:

    if not game_id:
        return []
    my_games = client.games.get_ongoing()
    print(my_games) 
    stale_games = [c['gameId'] for c in my_games if c['gameId'] != game_id]

    for s_c in stale_games:
        client.board.abort_game(s_c)

    return stale_games

def start_game(client) -> str:
    challenge = client.challenges.create_ai(color='white')
    game_id = challenge['id']
    return game_id

def check_if_challenge_exists(client, game_id=None) -> bool:
    if not game_id:
        return False
    mine_challenges = client.challenges.get_mine()
    return any(c['id'] == game_id for c in mine_challenges)

# Function to handle streaming the board state in a separate thread
def stream_game_state(client, game_id: str, moves: list[str]):
    for move in client.games.stream_game_moves(game_id):
        print(move)
    print("Starting board stream...")
    for board_state in client.board.stream_game_state(game_id):
        if board_state.get('moves'):
            move = board_state.get('moves').lower().split()[-1]  # Get the latest move
            moves.append(move)  # Add only the latest move to the moves list
        else:
            moves.append(-1)  # Add -1 if there are no moves yet

        annotated_moves = annotate_moves_wrt_pieces(client, moves)
        print(annotated_moves)  # Print the annotated moves
        time.sleep(3)  # Sleep to simulate real-time updates

# Annotate the moves with respect to the pieces
def annotate_moves_wrt_pieces(client, moves: list[str]):
    annotated_moves = []
    for move in moves:
        ''' each move can have '''
        #check for pawn move
        annotated_moves.append(move)  # You can modify this to add actual piece annotations
    return annotated_moves


# Function to handle user input
def handle_user_input(client, game_id):
    while True:
        move = input("Enter your move (or type 'end' to quit): ----------------------").strip().lower()
        
        print("\n")
        if move == 'end':
            print("Exiting game.")
            client.board.resign_game(game_id)
            break

        # Make player move
        try:
            client.board.make_move(game_id=game_id, move=str(move))
        except berserk.exceptions.ResponseError as e:
            print("Invalid move, try again.")
            continue

        # Wait for AI move
        print("Waiting for AI...")

def main():
    load_dotenv()
    API_KEY = os.environ['lichess']

    session = berserk.TokenSession(API_KEY)
    client = berserk.Client(session)

    game_id = start_game(client)
    print("Game ID:", game_id)

    moves=[]
    # # Delete stale games
    # stale_games = delete_stale_games(client, game_id)
    # print(f'Deleted {len(stale_games)} stale games')

    # Start the game state streaming in a separate thread
    stream_thread = threading.Thread(target=stream_game_state, args=(client, game_id, moves))
    stream_thread.start()

    # Handle user input in the main thread
    handle_user_input(client, game_id)

if __name__ == "__main__":
    main()

