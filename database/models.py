from extensions import db
from flask_login import UserMixin
from datetime import datetime

# TABLE 1: users
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    name         = db.Column(db.String(100), nullable=False)
    password_hash= db.Column(db.String(255), nullable=False)
    is_premium   = db.Column(db.Boolean, default=False)
    is_verified  = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    premium_at   = db.Column(db.DateTime, nullable=True)
    # Relationships
    analyses       = db.relationship('Analysis', backref='user', lazy=True)
    payments       = db.relationship('Payment', backref='user', lazy=True)
    password_resets= db.relationship('PasswordReset', backref='user', lazy=True)
    def __repr__(self): return f'<User {self.email}>'

# TABLE 2: analyses
class Analysis(db.Model):
    __tablename__ = 'analyses'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    chat_name    = db.Column(db.String(200), default='My Chat')
    results_json = db.Column(db.Text, nullable=False)
    file_deleted = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    images       = db.relationship('GeneratedImage', backref='analysis', lazy=True)
    def __repr__(self): return f'<Analysis {self.id} - {self.chat_name}>'

# TABLE 3: generated_images
class GeneratedImage(db.Model):
    __tablename__ = 'generated_images'
    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    analysis_id     = db.Column(db.Integer, db.ForeignKey('analyses.id'), nullable=False)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    template_name   = db.Column(db.String(50), default='dark')
    image_paths_json= db.Column(db.Text)
    is_watermarked  = db.Column(db.Boolean, default=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

# TABLE 4: payments
class Payment(db.Model):
    __tablename__ = 'payments'
    id                  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    razorpay_order_id   = db.Column(db.String(100), nullable=False)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    amount              = db.Column(db.Integer, default=4900)
    status              = db.Column(db.String(20), default='created')
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

# TABLE 5: password_resets
class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token      = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used       = db.Column(db.Boolean, default=False)
