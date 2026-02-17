import json
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from database.models import Analysis, GeneratedImage, Payment, User, db
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    analyses_count = Analysis.query.filter_by(user_id=current_user.id).count()
    last_analysis  = Analysis.query.filter_by(
        user_id=current_user.id).order_by(Analysis.created_at.desc()).first()
    recent = Analysis.query.filter_by(
        user_id=current_user.id).order_by(Analysis.created_at.desc()).limit(3).all()
    return render_template('dashboard/index.html',
        analyses_count=analyses_count, last_analysis=last_analysis, recent=recent)

@dashboard_bp.route('/dashboard/analyses')
@login_required
def analyses():
    page = request.args.get('page', 1, type=int)
    all_analyses = Analysis.query.filter_by(
        user_id=current_user.id).order_by(
        Analysis.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('dashboard/analyses.html', analyses=all_analyses)

@dashboard_bp.route('/dashboard/settings', methods=['GET','POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            current_user.name = request.form.get('name', current_user.name).strip()[:100]
            db.session.commit()
            flash('Profile update ho gaya!', 'success')
    return render_template('dashboard/settings.html')

@dashboard_bp.route('/dashboard/delete-account', methods=['POST'])
@login_required
def delete_account():
    confirm = request.form.get('confirm_text','')
    if confirm == 'DELETE':
        # Delete all user data
        Analysis.query.filter_by(user_id=current_user.id).delete()
        Payment.query.filter_by(user_id=current_user.id).delete()
        User.query.filter_by(id=current_user.id).delete()
        db.session.commit()
        flash('Account delete ho gaya.', 'success')
        return redirect(url_for('upload.handle_upload'))
    flash('Type DELETE to confirm!', 'error')
    return redirect(url_for('dashboard.settings'))
