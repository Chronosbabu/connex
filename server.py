from flask import Flask
from flask_socketio import SocketIO, emit
from googletrans import Translator

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
translator = Translator()

users = {}

@socketio.on("connect")
def connect():
    print("User connected")

@socketio.on("register")
def register(data):
    username = data["username"]
    users[username] = request.sid
    print(f"{username} registered")

@socketio.on("send_message")
def handle_message(data):
    sender = data["sender"]
    receiver = data["receiver"]
    message = data["message"]
    target_lang = data["lang"]

    translated = translator.translate(message, dest=target_lang).text

    if receiver in users:
        socketio.emit(
            "receive_message",
            {
                "sender": sender,
                "message": translated
            },
            room=users[receiver]
        )

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
