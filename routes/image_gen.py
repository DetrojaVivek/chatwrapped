import json, os
from flask import Blueprint, request, redirect, url_for, render_template, send_file, abort
from flask_login import current_user
from PIL import Image
from database.models import Analysis, GeneratedImage
from extensions import db
from utils.image_builder import generate_all_slides

image_gen_bp = Blueprint('image_gen', __name__)

@image_gen_bp.route('/generate', methods=['POST'])
def generate_images():
    analysis_id   = request.form.get('analysis_id', type=int)
    template_name = request.form.get('template', 'dark') # Note: Form in templates.html sends 'template', but user requested 'template_name' logic. 
    # Let's support both just in case, or stick to what user provided if they updated frontend too.
    if not template_name:
        template_name = request.form.get('template_name', 'dark')
    
    analysis = Analysis.query.get_or_404(analysis_id)
    try:
        stats = json.loads(analysis.results_json)
    except:
        return "Error parsing stats", 500
    
    is_premium  = current_user.is_authenticated and current_user.is_premium
    user_id_val = current_user.id if current_user.is_authenticated else 0
    
    # Generate 6 slides using Pillow (no API!)
    # Ensure utils.image_builder.generate_all_slides exists and accepts these args
    try:
        image_paths = generate_all_slides(
            stats, template_name, user_id_val, analysis.id, is_premium
        )
    except Exception as e:
        print(f"Error generating slides: {e}")
        return f"Error generating slides: {e}", 500
    
    gen_img = GeneratedImage(
        analysis_id      = analysis.id,
        user_id          = user_id_val if current_user.is_authenticated else None,
        template_name    = template_name,
        image_paths_json = json.dumps(image_paths),
        is_watermarked   = not is_premium
    )
    db.session.add(gen_img)
    db.session.commit()
    
    return redirect(url_for('image_gen.preview_images', image_set_id=gen_img.id))

@image_gen_bp.route('/preview/<int:image_set_id>')
def preview_images(image_set_id):
    gen_img = GeneratedImage.query.get_or_404(image_set_id)
    paths   = json.loads(gen_img.image_paths_json)
    # Convert file paths to URL paths relative to static
    # Assuming paths stored are like 'static/generated/...' or just filenames?
    # image_builder usually returns relative paths.
    urls = []
    for p in paths:
        # standardizing path separators
        p = p.replace('\\', '/')
        if p.startswith('static/'):
            urls.append('/' + p)
        else:
            urls.append('/static/generated/' + os.path.basename(p))
            
    is_prem = current_user.is_authenticated and current_user.is_premium
    return render_template('preview.html', image_urls=urls, image_set_id=image_set_id, is_premium=is_prem)

@image_gen_bp.route('/download/<int:image_set_id>/<platform>')
def download_image(image_set_id, platform):
    SIZES = {
        'instagram_post':   (1080, 1080),
        'instagram_story':  (1080, 1920),
        'facebook':         (1200, 630),
        'whatsapp_status':  (1080, 1920),
        'twitter':          (1200, 675),
    }
    if platform not in SIZES: abort(404)
    
    gen_img = GeneratedImage.query.get_or_404(image_set_id)
    paths   = json.loads(gen_img.image_paths_json)
    
    # Use slide 1 (overview) for download, resize to platform size
    # Assuming paths[0] is correct
    original_path = paths[0]
    
    # Check if path is absolute or relative
    if not os.path.exists(original_path):
        # Try adjusting if it's relative to project root
        if os.path.exists(os.path.join(original_path)):
             pass # it exists
        elif os.path.exists(os.path.join('static', 'generated', os.path.basename(original_path))):
            original_path = os.path.join('static', 'generated', os.path.basename(original_path))
            
    try:
        w, h = SIZES[platform]
        img  = Image.open(original_path)
        # Resize maintaining aspect ratio or crop? logic:
        # The user code says: img.open(...).resize((w, h), Image.LANCZOS)
        # This stretches the image.
        img = img.resize((w, h), Image.LANCZOS)
        
        # Ensure static/generated exists
        output_dir = 'static/generated'
        os.makedirs(output_dir, exist_ok=True)
        
        output_filename = f'download_{image_set_id}_{platform}.png'
        output_path = os.path.join(output_dir, output_filename)
        img.save(output_path)
        
        return send_file(output_path, as_attachment=True,
                        download_name=f'chatwrapped_{platform}.png')
    except Exception as e:
        print(f"Error processing image: {e}")
        return str(e), 500
