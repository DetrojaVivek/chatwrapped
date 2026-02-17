from flask import Flask, render_template
from dotenv import load_dotenv
import os

from extensions import db, bcrypt, mail, login_manager

# Ensure this is after extensions init
from database.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatwrapped.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max upload

# Mail config (for password reset emails)
app.config['MAIL_SERVER']   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

from extensions import db, bcrypt, mail, login_manager

db.init_app(app)
bcrypt.init_app(app)
mail.init_app(app)
login_manager.init_app(app)

# Import and register all blueprints
from routes.auth      import auth_bp
from routes.upload    import upload_bp
from routes.analysis  import analysis_bp
from routes.image_gen import image_gen_bp
from routes.payment   import payment_bp
from routes.dashboard import dashboard_bp

app.register_blueprint(auth_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(image_gen_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(dashboard_bp)

# Error handlers
@app.errorhandler(404)
def not_found(e): return render_template('errors/404.html'), 404
@app.errorhandler(500)
@app.errorhandler(500)
def server_error(e): return render_template('errors/500.html'), 500

# Legal Pages Routes
@app.route('/privacy')
def privacy(): return render_template('legal/privacy.html')

@app.route('/terms')
def terms(): return render_template('legal/terms.html')

@app.route('/refund')
def refund(): return render_template('legal/refund.html')

@app.route('/faq')
def faq(): return render_template('faq.html')

# Create DB tables on first run
with app.app_context():
    from database.models import User, Analysis, GeneratedImage, Payment, PasswordReset
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
