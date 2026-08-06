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
    if q == 1:
        item["interval"] = 1
        item["repetitions"] = 0
    else:
        # Tính toán khoảng cách ngày dựa trên số lần lặp (đồng bộ với UI)
        if item["repetitions"] == 0:
            day_easy = 4
        elif item["repetitions"] == 1:
            day_easy = 6
        else:
            day_easy = int(round(item["interval"] * item["ease_factor"]))
            
        # Áp dụng khoảng cách ngày thực tế tương ứng với lựa chọn
        if q == 3:     # Hard
            item["interval"] = max(1, int(day_easy * 0.5))
        elif q == 4:   # Good
            item["interval"] = max(2, int(day_easy * 0.8))
        elif q == 5:   # Easy
            item["interval"] = day_easy
            
        item["repetitions"] += 1
        
    # Tính toán Ease Factor mới theo thuật toán SM-2
    item["ease_factor"] = item["ease_factor"] + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    if item["ease_factor"] < 1.3:
        item["ease_factor"] = 1.3
        
    # Đặt ngày ôn tiếp theo
    next_date = now + datetime.timedelta(days=item["interval"])
    item["next_review"] = next_date.date().isoformat()
    
    srs_data[word] = item
    return srs_data
