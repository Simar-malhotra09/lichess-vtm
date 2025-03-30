import time
import berserk
from dotenv import load_dotenv
import os
import threading
import speech_recognition as sr

class LichessClient:
    def __init__(self):
        load_dotenv()
        API_KEY = os.environ['lichess']
        self.session = berserk.TokenSession(API_KEY)
        self.client = berserk.Client(self.session)
        self.game_id = None
        self.moves = []

    def delete_stale_games(self):
        if not self.game_id:
            return []
        
        my_games = self.client.games.get_ongoing()
        stale_games = [c['gameId'] for c in my_games if c['gameId'] != self.game_id]
        
        for game in stale_games:
            self.client.board.abort_game(game)
        
        return stale_games

    def start_game(self):
        challenge = self.client.challenges.create_ai(color='white')
        self.game_id = challenge['id']
        print("Game ID:", self.game_id)
        return self.game_id

    def check_if_challenge_exists(self):
        if not self.game_id:
            return False
        
        mine_challenges = self.client.challenges.get_mine()
        return any(c['id'] == self.game_id for c in mine_challenges)

    def stream_game_state(self):
        print("Starting board stream...")
        for board_state in self.client.board.stream_game_state(self.game_id):
            if board_state.get('moves'):
                move = board_state.get('moves').lower().split()[-1]
                self.moves.append(move)
            else:
                self.moves.append(-1)

            annotated_moves = self.annotate_moves_wrt_pieces()
            print(annotated_moves)
            time.sleep(3)

    def annotate_moves_wrt_pieces(self):
        return [move for move in self.moves]  

    def recognize_speech(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Say your move or 'end' to quit:")
            try:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=100)
                move = recognizer.recognize_google(audio).lower()
                move=str(move)
                move="".join(move.split())
                return move
            except sr.UnknownValueError:
                print("Could not understand, try again.")
                return None
            except sr.RequestError:
                print("Speech recognition service error.")
                return None

    def handle_user_input(self):
        while True:
            move = self.recognize_speech()
            if not move:
                continue
            
            print("Recognized move:", move)
            
            if move == 'end':
                print("Exiting game.")
                self.client.board.resign_game(self.game_id)
                break

            try:
                self.client.board.make_move(game_id=self.game_id, move=move)

            except berserk.exceptions.ResponseError:
                print("Invalid move, try again.")
                continue

            print("Waiting for AI...")

    def play(self):
        self.start_game()
        stream_thread = threading.Thread(target=self.stream_game_state)
        stream_thread.start()
        self.handle_user_input()

if __name__ == "__main__":
    lichess_client = LichessClient()
    lichess_client.play()

