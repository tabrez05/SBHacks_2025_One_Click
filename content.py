from flask import Blueprint
import os

content = Blueprint('content', __name__)

@content.route('/content')
def list_content():
    return {'content': []}

@content.route('/content/create', methods=['POST'])
def create_content():
    return {'message': 'Content created'}
