from flask import Blueprint, render_template

image_gen = Blueprint('image_gen', __name__)

@image_gen.route('/')
def index():
    return "Image Generation Page"
