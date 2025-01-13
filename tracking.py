from flask import Blueprint
from models import db

tracking = Blueprint('tracking', __name__)

@tracking.route('/progress/<user_id>')
def get_progress(user_id):
    return {'progress': 0}

@tracking.route('/progress/<user_id>', methods=['POST'])
def update_progress(user_id):
    return {'message': 'Progress updated'}
