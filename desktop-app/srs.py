import datetime

def update_srs_item(srs_data, word, quality):
    # quality: 1 (Again/Quên), 3 (Hard), 4 (Good), 5 (Easy)
    now = datetime.datetime.now()
    item = srs_data.get(word, {
        "interval": 1,
        "ease_factor": 2.5,
        "repetitions": 0,
        "next_review": now.isoformat()
    })
    
    q = quality
    if q >= 3:
        if item["repetitions"] == 0:
            item["interval"] = 1
        elif item["repetitions"] == 1:
            item["interval"] = 4  # Ôn tập lại sau 4 ngày
        else:
            item["interval"] = int(round(item["interval"] * item["ease_factor"]))
            
        item["repetitions"] += 1
    else:
        item["repetitions"] = 0
        item["interval"] = 1
        
    # Tính toán Ease Factor mới
    item["ease_factor"] = item["ease_factor"] + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    if item["ease_factor"] < 1.3:
        item["ease_factor"] = 1.3
        
    # Đặt ngày ôn tiếp theo
    next_date = now + datetime.timedelta(days=item["interval"])
    item["next_review"] = next_date.date().isoformat()
    
    srs_data[word] = item
    return srs_data
