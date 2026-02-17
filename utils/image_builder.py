from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, json

TEMPLATES = {
    'dark':     {'bg':'#1a1a2e', 'text':'#FFFFFF', 'accent':'#25D366', 'sub':'#AAAAAA'},
    'light':    {'bg':'#FFFFFF', 'text':'#1a1a2e', 'accent':'#25D366', 'sub':'#666666'},
    'colorful': {'bg':'#6C3483', 'text':'#FFFFFF', 'accent':'#F39C12', 'sub':'#E0AAFF'},
    'minimal':  {'bg':'#F8F9FA', 'text':'#2C3E50', 'accent':'#3498DB', 'sub':'#888888'},
}

SLIDE_SIZE = (1080, 1080)
OUTPUT_DIR = 'static/generated'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def get_font(size, bold=False):
    font_paths = [
        # Linux / standard paths
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',         
        '/System/Library/Fonts/Helvetica.ttc',
        # Windows paths (common)
        'C:\\Windows\\Fonts\\arialbd.ttf' if bold else 'C:\\Windows\\Fonts\\arial.ttf',
        'C:\\Windows\\Fonts\\seguiSB.ttf' if bold else 'C:\\Windows\\Fonts\\segoeui.ttf',
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try: return ImageFont.truetype(fp, size)
            except: pass
    return ImageFont.load_default()

def draw_text_center(draw, y, text, font, color, width=1080):
    bbox = draw.textbbox((0,0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (width - w) // 2
    draw.text((x, y), text, font=font, fill=color)
    return bbox[3] - bbox[1]

def draw_bar(draw, x, y, val, max_val, bar_w, bar_h, color):
    filled = int(bar_w * (val / max_val)) if max_val > 0 else 0
    draw.rectangle([x, y, x+bar_w, y+bar_h], fill=hex_to_rgb('#333333'))
    # Ensure filled width is valid
    if filled > 0:
        draw.rectangle([x, y, x+filled, y+bar_h], fill=hex_to_rgb(color))

def generate_all_slides(stats, template_name, user_id, analysis_id, is_premium=False):
    colors = TEMPLATES.get(template_name, TEMPLATES['dark'])
    paths  = []
    
    funcs = [
        _slide_overview, _slide_texting_champ,
        _slide_peak_hours, _slide_emojis,
        _slide_fun_facts,  _slide_word_stats
    ]
    
    for i, func in enumerate(funcs, 1):
        img  = Image.new('RGB', SLIDE_SIZE, hex_to_rgb(colors['bg']))
        draw = ImageDraw.Draw(img)
        func(draw, img, stats, colors)
        
        # Watermark (free users)
        if not is_premium:
            wm_font  = get_font(22)
            wm_color = hex_to_rgb('#555555')
            draw.text((20, SLIDE_SIZE[1]-35), 'ChatWrapped.in', font=wm_font, fill=wm_color)
        
        # Logo top right
        logo_font = get_font(20)
        draw.text((SLIDE_SIZE[0]-200, 20), 'ChatWrapped.in', font=logo_font, fill=hex_to_rgb(colors['accent']))
        
        filename = f'{user_id}_{analysis_id}_slide{i}.png'
        path = os.path.join(OUTPUT_DIR, filename)
        # Using absolute path for safety/consistency if needed, but relative usually fine for web serving
        # However, Flask usually serves from static folder.
        img.save(path, 'PNG')
        paths.append(filename) # Return filename relative to static/generated usually, or just filename
    
    return paths

def _slide_overview(draw, img, s, c):
    draw_text_center(draw, 80,  'Your Chat Wrapped',  get_font(52, True), hex_to_rgb(c['accent']))
    draw_text_center(draw, 160, '2024',               get_font(36),       hex_to_rgb(c['sub']))
    draw_text_center(draw, 300, str(s.get('total_messages','0')), get_font(120, True), hex_to_rgb(c['text']))
    draw_text_center(draw, 440, 'Total Messages',     get_font(32),       hex_to_rgb(c['sub']))
    names = f"{s.get('person1_name','?')}  &  {s.get('person2_name','?')}"
    draw_text_center(draw, 560, names[:30],           get_font(40, True), hex_to_rgb(c['text']))
    date_range = f"{s.get('date_start','')} - {s.get('date_end','')} ({s.get('total_days',0)} days)"
    draw_text_center(draw, 650, date_range,           get_font(26),       hex_to_rgb(c['sub']))

def _slide_texting_champ(draw, img, s, c):
    draw_text_center(draw, 60, 'Who Texts More?', get_font(48, True), hex_to_rgb(c['accent']))
    p1, p2 = s.get('person1_name','P1'), s.get('person2_name','P2')
    pc1, pc2 = s.get('person1_percent',50), s.get('person2_percent',50)
    
    bar_y = 300; bar_h = 80; bar_x = 80; bar_w = 920
    draw_bar(draw, bar_x, bar_y, pc1, 100, bar_w, bar_h, c['accent'])
    
    draw_text_center(draw, 220, f'{p1[:15]}: {pc1}%', get_font(36, True), hex_to_rgb(c['text']))
    draw_text_center(draw, 420, f'{p2[:15]}: {pc2}%', get_font(36),       hex_to_rgb(c['sub']))
    
    bar2_y = 500
    draw_bar(draw, bar_x, bar2_y, pc2, 100, bar_w, bar_h, '#E74C3C')
    
    winner = p1 if pc1 > pc2 else p2
    draw_text_center(draw, 700, f'Winner: {winner[:15]}!', get_font(44, True), hex_to_rgb(c['text']))

def _slide_peak_hours(draw, img, s, c):
    draw_text_center(draw, 40, 'Peak Hours', get_font(52, True), hex_to_rgb(c['accent']))
    hourly = s.get('hourly_data', {})
    if hourly:
        max_val = max(hourly.values()) if hourly else 1
        chart_x, chart_y = 40, 200
        chart_w, chart_h = 1000, 500
        bar_w = chart_w // 24 - 2
        for hour in range(24):
            count = hourly.get(str(hour), hourly.get(hour, 0))
            bh    = int((count / max_val) * chart_h) if max_val > 0 else 0
            bx    = chart_x + hour * (bar_w + 2)
            by    = chart_y + chart_h - bh
            color = c['accent'] if hour == s.get('most_active_hour', 0) else '#334455'
            draw.rectangle([bx, by, bx+bar_w, chart_y+chart_h], fill=hex_to_rgb(color))
        
        label_font = get_font(18)
        for h in [0, 6, 12, 18, 23]:
            lx = chart_x + h * (bar_w + 2)
            draw.text((lx, chart_y+chart_h+5), f'{h:02d}h', font=label_font, fill=hex_to_rgb(c['sub']))
    
    peak = s.get('most_active_hour', 0)
    peak_str = 'Night Owl (After Midnight)' if peak >= 0 and peak <= 5 else ('Early Bird' if peak < 9 else f'{peak}:00 Most Active')
    draw_text_center(draw, 780, peak_str, get_font(32), hex_to_rgb(c['text']))

def _slide_emojis(draw, img, s, c):
    draw_text_center(draw, 40, 'Emoji Report', get_font(52, True), hex_to_rgb(c['accent']))
    draw_text_center(draw, 120, f'Total: {s.get("total_emojis", 0)} emojis used!', get_font(28), hex_to_rgb(c['sub']))
    top5 = s.get('top5_emojis', [])
    y = 220
    for item in top5[:5]:
        emoji_text = f'{item["emoji"]}  x{item["count"]}'
        # Ensure emoji rendering (might fail on some fonts but we hope fallback works)
        draw_text_center(draw, y, emoji_text, get_font(56), hex_to_rgb(c['text']))
        y += 120

def _slide_fun_facts(draw, img, s, c):
    draw_text_center(draw, 40, 'Fun Facts', get_font(52, True), hex_to_rgb(c['accent']))
    facts = [
        f'Sorry Count: {s.get("person1_name","P1")} said it {s.get("sorry_p1",0)}x',
        f'Late Night Messages: {s.get("late_night_msgs",0)}',
        f'Avg Reply Time: {s.get("avg_response_min",0):.0f} minutes',
        f'Longest Streak: {s.get("longest_streak",0)} days in a row',
        f'Double Texts: {s.get("double_texts",0)} times',
        f'First Message: {s.get("first_msg_sender","")} on {s.get("first_msg_date","")}',
    ]
    y = 180
    for fact in facts:
        draw_text_center(draw, y, fact[:45], get_font(30), hex_to_rgb(c['text']))
        y += 120

def _slide_word_stats(draw, img, s, c):
    draw_text_center(draw, 40, 'Most Used Words', get_font(52, True), hex_to_rgb(c['accent']))
    top10 = s.get('top10_words', [])
    y = 160
    col = 0
    for item in top10[:8]:
        x = 200 if col == 0 else 620
        draw.text((x, y), f'{item["word"]}: {item["count"]}', font=get_font(34), fill=hex_to_rgb(c['text']))
        col = 1 - col
        if col == 0: y += 90
