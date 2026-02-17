from collections import Counter
from utils.whatsapp_parser import extract_emojis, extract_words, calculate_response_time
from datetime import timedelta

STOPWORDS = {
    'hai','ka','ki','ke','main','tum','aur','the','a','is','in',
    'to','you','me','my','i','we','it','of','and','that','this',
    'yaar','bhai','ji','kya','nahi','ho','kar','karo','tha','thi',
    'wo','vo','se','par','pe','ek','do','koi','aaj','kal','ok','okay'
}

def calculate_all_stats(messages):
    if not messages or len(messages) < 2:
        return {}
    
    # Get unique senders (only first 2 for couple chat)
    senders = list(dict.fromkeys([m['sender'] for m in messages]))
    p1 = senders[0]
    p2 = senders[1] if len(senders) > 1 else 'Others'
    
    p1_msgs = [m for m in messages if m['sender'] == p1]
    p2_msgs = [m for m in messages if m['sender'] == p2]
    total   = len(messages)
    
    # Time analysis
    hours      = [m['datetime'].hour for m in messages]
    days       = [m['datetime'].strftime('%a') for m in messages]
    hourly     = dict(Counter(hours))
    daily      = dict(Counter(days))          
    most_active_hour = max(hourly, key=hourly.get)
    most_active_day  = max(daily,  key=daily.get)
    
    # Date range
    start_dt = messages[0]['datetime']
    end_dt   = messages[-1]['datetime']
    total_days = (end_dt - start_dt).days + 1
    
    # Streak
    dates  = sorted(set(m['datetime'].date() for m in messages))
    streak = max_streak = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i-1]).days == 1:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 1
    
    # Emojis
    all_emojis = []
    p1_emoji_count = 0; p2_emoji_count = 0
    for m in messages:
        emojis = extract_emojis(m['text'])
        all_emojis.extend(emojis)
        if m['sender'] == p1: p1_emoji_count += len(emojis)
        else:                  p2_emoji_count += len(emojis)
    top5_emojis = [{'emoji':e,'count':c} for e,c in Counter(all_emojis).most_common(5)]
    
    # Words
    all_words = []
    for m in messages:
        words = [w for w in extract_words(m['text']) if w not in STOPWORDS and len(w)>2]
        all_words.extend(words)
    top10_words = [{'word':w,'count':c} for w,c in Counter(all_words).most_common(10)]
    
    # Response times
    response_times = []
    for i in range(1, len(messages)):
        if messages[i]['sender'] != messages[i-1]['sender']:
            rt = calculate_response_time(messages[i-1]['datetime'], messages[i]['datetime'])
            if 0 < rt < 86400:
                response_times.append({'sender': messages[i]['sender'], 'time': rt})
    
    avg_rt       = sum(r['time'] for r in response_times)/len(response_times)/60 if response_times else 0
    p1_responses = [r['time'] for r in response_times if r['sender']==p1]
    p2_responses = [r['time'] for r in response_times if r['sender']==p2]
    p1_avg_rt    = sum(p1_responses)/len(p1_responses)/60 if p1_responses else 0
    p2_avg_rt    = sum(p2_responses)/len(p2_responses)/60 if p2_responses else 0
    if response_times:
        fastest_rt = min(r['time'] for r in response_times)
    else:
        fastest_rt = 0
    
    # Fun stats
    def count_words_in_msgs(msgs, words):
        return sum(1 for m in msgs if any(w.lower() in m['text'].lower() for w in words))
    
    sorry_words = ['sorry','maafi','galti','mafi']
    haha_words  = ['haha','hehe','lol','lmao']
    gm_words    = ['good morning','gm','subah']
    
    longest_msg = max(messages, key=lambda m: len(m['text']), default=messages[0])
    
    return {
        'total_messages':     total,
        'person1_name':       p1,
        'person2_name':       p2,
        'person1_count':      len(p1_msgs),
        'person2_count':      len(p2_msgs),
        'person1_percent':    round(len(p1_msgs)/total*100, 1),
        'person2_percent':    round(len(p2_msgs)/total*100, 1),
        'date_start':         start_dt.strftime('%b %Y'),
        'date_end':           end_dt.strftime('%b %Y'),

        'total_days':         total_days,
        'most_active_hour':   most_active_hour,
        'most_active_day':    most_active_day,
        'hourly_data':        hourly,
        'daily_data':         daily,
        'longest_streak':     max_streak,
        'top5_emojis':        top5_emojis,
        'total_emojis':       len(all_emojis),
        'p1_emoji_count':     p1_emoji_count,
        'p2_emoji_count':     p2_emoji_count,
        'top10_words':        top10_words,
        'avg_response_min':   round(avg_rt, 1),
        'p1_avg_response':    round(p1_avg_rt, 1),
        'p2_avg_response':    round(p2_avg_rt, 1),
        'fastest_reply_sec':  int(fastest_rt),
        'sorry_p1':           count_words_in_msgs(p1_msgs, sorry_words),
        'sorry_p2':           count_words_in_msgs(p2_msgs, sorry_words),
        'haha_p1':            count_words_in_msgs(p1_msgs, haha_words),
        'haha_p2':            count_words_in_msgs(p2_msgs, haha_words),
        'good_morning_count': count_words_in_msgs(messages, gm_words),
        'late_night_msgs':    len([m for m in messages if 0 <= m['datetime'].hour <= 4]),
        'double_texts':       sum(1 for i in range(1,len(messages)) if messages[i]['sender']==messages[i-1]['sender']),
        'longest_msg_sender': longest_msg['sender'],
        'longest_msg_preview':longest_msg['text'][:50],
        'longest_msg_length': len(longest_msg['text']),
        'first_msg_sender':   messages[0]['sender'],
        'first_msg_date':     messages[0]['datetime'].strftime('%d %b %Y'),
    }
