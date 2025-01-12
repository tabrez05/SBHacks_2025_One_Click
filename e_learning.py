from flask import Blueprint
import os

elearning = Blueprint('elearning', __name__)

@elearning.route('/courses')
def list_courses():
    return {'courses': []}

@elearning.route('/lessons')
def list_lessons():
    return {'lessons': []}
