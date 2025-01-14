from flask import Flask
from flask_socketio import SocketIO
from models import db
from auth import auth
from upload import upload
from elearning import elearning
from tracking import tracking
from content import content
from analytics import analytics
from realtime import realtime
from error_handlers import register_error_handlers

app = Flask(__name__)
socketio = SocketIO(app)

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(upload)
app.register_blueprint(elearning)
app.register_blueprint(tracking)
app.register_blueprint(content)
app.register_blueprint(analytics)
app.register_blueprint(realtime)

# Setup error handlers
register_error_handlers(app)

if __name__ == '__main__':
    socketio.run(app, debug=True)
