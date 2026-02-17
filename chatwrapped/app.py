from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from os import path

db = SQLAlchemy()
DB_NAME = "chatwrapped.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'devkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from routes.auth import auth
    from routes.dashboard import dashboard
    from routes.upload import upload
    from routes.analysis import analysis
    from routes.image_gen import image_gen
    from routes.payment import payment

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(dashboard, url_prefix='/dashboard')
    app.register_blueprint(upload, url_prefix='/upload')
    app.register_blueprint(analysis, url_prefix='/analysis')
    app.register_blueprint(image_gen, url_prefix='/image_gen')
    app.register_blueprint(payment, url_prefix='/payment')

    from database import models

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
