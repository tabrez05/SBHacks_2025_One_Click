from flask import Blueprint
from flask_socketio import SocketIO

realtime = Blueprint('realtime', __name__)
socketio = SocketIO()

@socketio.on('process')
def handle_process(data):
    socketio.emit('result', {'status': 'processed'})
