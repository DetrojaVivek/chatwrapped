import json
from flask import Blueprint, render_template, abort
from database.models import Analysis

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/results/<int:analysis_id>')
def show_results(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
    stats    = json.loads(analysis.results_json)
    return render_template('results.html', stats=stats, analysis=analysis)
