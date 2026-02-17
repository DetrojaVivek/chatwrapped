from flask import Blueprint, render_template

analysis = Blueprint('analysis', __name__)

@analysis.route('/')
def index():
    return "Analysis Page"
