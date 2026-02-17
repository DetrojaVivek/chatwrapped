from flask import Blueprint, render_template

upload = Blueprint('upload', __name__)

@upload.route('/')
def index():
    return "Upload Page"
