from flask import Blueprint, render_template

payment = Blueprint('payment', __name__)

@payment.route('/')
def index():
    return render_template('payment/index.html')
