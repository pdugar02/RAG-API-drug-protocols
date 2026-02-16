from collections import defaultdict

class SessionStore:
    def __init__(self):
        self.history = defaultdict(list)

    def add_message(self, session_id, message):
        self.history[session_id].append(message)

    def get_history(self, session_id):
        return self.history[session_id]

session_store = SessionStore()