import os, hmac, hashlib, json
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, render_template, jsonify, flash
from flask_login import login_required, current_user
import razorpay
from database.models import Payment, User, db

payment_bp = Blueprint('payment', __name__)

KEY_ID     = os.environ.get('RAZORPAY_KEY_ID')
KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
client     = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

@payment_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@payment_bp.route('/upgrade')
@login_required
def upgrade():
    if current_user.is_premium:
        flash('Aap pehle se premium hain!', 'success')
        return redirect(url_for('dashboard.index'))
    return render_template('payment/upgrade.html', razorpay_key_id=KEY_ID)

@payment_bp.route('/create-order', methods=['POST'])
@login_required
def create_order():
    order = client.order.create({
        'amount':   4900,
        'currency': 'INR',
        'receipt':  f'order_{current_user.id}_{int(datetime.utcnow().timestamp())}',
        'notes':    {'user_id': str(current_user.id)}
    })
    payment = Payment(
        user_id           = current_user.id,
        razorpay_order_id = order['id'],
        amount            = 4900,
        status            = 'created'
    )
    db.session.add(payment)
    db.session.commit()
    return jsonify({
        'order_id': order['id'],
        'key_id':   KEY_ID,
        'amount':   4900,
        'name':     current_user.name,
        'email':    current_user.email
    })

@payment_bp.route('/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    payment_id  = request.form.get('razorpay_payment_id','')
    order_id    = request.form.get('razorpay_order_id','')
    signature   = request.form.get('razorpay_signature','')
    
    # Verify signature using HMAC-SHA256
    message = f'{order_id}|{payment_id}'
    expected = hmac.new(
        KEY_SECRET.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    
    if expected == signature:
        # Update payment record
        payment = Payment.query.filter_by(razorpay_order_id=order_id).first()
        if payment:
            payment.razorpay_payment_id = payment_id
            payment.status              = 'captured'
        # Upgrade user
        current_user.is_premium = True
        current_user.premium_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('payment.payment_success'))
    else:
        return redirect(url_for('payment.payment_failed'))

@payment_bp.route('/payment/success')
@login_required
def payment_success():
    return render_template('payment/success.html')

@payment_bp.route('/payment/failed')
def payment_failed():
    return render_template('payment/failed.html')

@payment_bp.route('/dashboard/billing')
@login_required
def billing_history():
    payments = Payment.query.filter_by(
        user_id=current_user.id, status='captured'
    ).order_by(Payment.created_at.desc()).all()
    return render_template('dashboard/billing.html', payments=payments)
