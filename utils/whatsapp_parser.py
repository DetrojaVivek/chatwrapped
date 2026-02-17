import re
from datetime import datetime
import emoji as emoji_lib

def parse_whatsapp_chat(file_path):
    """
    Parse WhatsApp exported .txt file.
    Handles BOTH Android and iPhone export formats.
    Returns: list of dicts [{datetime, sender, text}, ...]
    """
    messages = []       # Android format: "12/01/2024, 10:30 PM - Name: message"
    android_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2}\s?[AP]M)\s-\s([^:]+):\s(.*)'
    
    # iPhone format: "[12/01/24, 10:30:15 PM] Name: message"
    iphone_pattern  = r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2}:\d{2}\s?[AP]M)\]\s([^:]+):\s(.*)'
    
    skip_phrases = [
        'Messages and calls are end-to-end encrypted',
        'changed their phone number',
        'added you',
        'left',
        'created group',
        '<Media omitted>',
        'null',
        'image omitted',
        'video omitted',
        'audio omitted',
        'sticker omitted',
    ]
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Skip system messages
            if any(skip in line for skip in skip_phrases):
                continue
            
            # Try Android format first
            match = re.match(android_pattern, line)
            fmt   = '%m/%d/%Y %I:%M %p'
            
            if not match:
                match = re.match(iphone_pattern, line)
                fmt   = '%m/%d/%y %I:%M:%S %p'
            
            if match:
                date_str, time_str, sender, text = match.groups()
                try:
                    dt = datetime.strptime(f'{date_str} {time_str}', fmt)
                    messages.append({
                        'datetime': dt,
                        'sender':   sender.strip(),
                        'text':     text.strip()
                    })
                except Exception:
                    continue
    
    return messages

def extract_emojis(text):
    """Extract list of all emojis from text"""
    return [c for c in text if c in emoji_lib.EMOJI_DATA]

def extract_words(text):
    """Extract clean word list from text"""
    text = re.sub(r'[^a-zA-Z\u0900-\u097F\s]', ' ', text)
    return [w.lower() for w in text.split() if len(w) > 1]

def calculate_response_time(dt1, dt2):
    """Return seconds between two datetime objects"""
    diff = (dt2 - dt1).total_seconds()
    return diff if diff > 0 else 0
