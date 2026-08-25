import datetime

def calculate_anki_previews(item_srs):
    """
    Trả về dict chứa nhãn hiển thị thời gian cho 4 lựa chọn (Again, Hard, Good, Easy):
    Ví dụ: {1: '1m', 3: '10m', 4: '1d', 5: '4d'} hoặc {1: '1m', 3: '6d', 4: '15d', 5: '28d'}
    """
    reps = item_srs.get("repetitions", 0)
    state = item_srs.get("state", "new" if reps == 0 else "review")
    step = item_srs.get("step", 0)

    if state in ["new", "learning"]:
        # Mốc học từ mới / đang học (Learning Steps: 1m, 10m -> 1d)
        again_str = "1m"
        hard_str = "10m"
        good_str = "1d" if step >= 1 else "10m"
        easy_str = "4d"
        return {1: again_str, 3: hard_str, 4: good_str, 5: easy_str}
    else:
        # Mốc thẻ đã tốt nghiệp (Review state)
        s = float(item_srs.get("stability", max(1.0, float(item_srs.get("interval", 1.0)))))
        d = float(item_srs.get("difficulty", max(1.0, min(10.0, 11.0 - float(item_srs.get("ease_factor", 2.5)) * 3.0))))
        interval = int(item_srs.get("interval", max(1, int(round(s)))))

        again_str = "1m"
        hard_days = max(1, int(round(interval * 1.2)))
        
        # FSRS Growth calculation for Good & Easy
        good_growth = 1.0 + 0.8 * (11.0 - d) * (s ** -0.2)
        good_s = max(interval + 1, round(s * good_growth))
        good_days = int(good_s)

        easy_growth = 1.0 + 1.4 * (11.0 - d) * (s ** -0.2)
        easy_s = max(good_days + 1, round(s * easy_growth))
        easy_days = int(easy_s)

        return {1: again_str, 3: f"{hard_days}d", 4: f"{good_days}d", 5: f"{easy_days}d"}

def calculate_fsrs_preview(item_srs):
    """Alias tương thích ngược."""
    return calculate_anki_previews(item_srs)

def update_srs_item(srs_data, word, quality):
    """
    Cập nhật dữ liệu SRS theo chuẩn Anki + FSRS:
    quality: 1 (Again), 3 (Hard), 4 (Good), 5 (Easy)
    Trả về: (srs_data, graduated) với graduated = True khi từ tốt nghiệp khỏi bước học.
    """
    now = datetime.datetime.now()
    today_str = now.date().isoformat()
    
    item = srs_data.get(word, {})
    reps = item.get("repetitions", 0)
    lapses = item.get("lapses", 0)
    state = item.get("state", "new" if reps == 0 else "review")
    step = item.get("step", 0)

    # Phục hồi / khởi tạo S & D
    s = float(item.get("stability", max(1.0, float(item.get("interval", 1.0)))))
    d = float(item.get("difficulty", max(1.0, min(10.0, 11.0 - float(item.get("ease_factor", 2.5)) * 3.0))))

    graduated = False
    next_interval_days = 0

    if state in ["new", "learning"]:
        if quality == 1: # Again (1m)
            state = "learning"
            step = 0
        elif quality == 3: # Hard (10m)
            state = "learning"
            step = 0
        elif quality == 4: # Good (10m / 1d)
            if step == 0:
                state = "learning"
                step = 1
            else:
                # Tốt nghiệp sang Review (1d)
                graduated = True
                state = "review"
                s = 1.0
                d = 4.5
                next_interval_days = 1
        elif quality == 5: # Easy (4d)
            # Tốt nghiệp xuất sắc sang Review (4d)
            graduated = True
            state = "review"
            s = 4.0
            d = 3.5
            next_interval_days = 4
    else:
        # Review State (Thẻ đã tốt nghiệp)
        if quality == 1: # Again -> Quên! Chuyển thành Re-learning 1m
            lapses += 1
            state = "learning"
            step = 0
            d = min(10.0, d + 1.2)
            s = max(0.4, round(s * 0.25, 2))
        elif quality == 3: # Hard (x1.2)
            graduated = True
            d = min(10.0, d + 0.3)
            s = max(s + 1.0, round(s * (1.0 + 0.4 * (11.0 - d) * (s ** -0.2)), 2))
            next_interval_days = max(1, int(round(item.get("interval", 1) * 1.2)))
        elif quality == 4: # Good (FSRS)
            graduated = True
            d = max(1.0, d - 0.1)
            s = max(s + 2.0, round(s * (1.0 + 0.8 * (11.0 - d) * (s ** -0.2)), 2))
            next_interval_days = max(item.get("interval", 1) + 1, int(round(s)))
        elif quality == 5: # Easy (FSRS Bonus)
            graduated = True
            d = max(1.0, d - 0.4)
            s = max(s + 4.0, round(s * (1.0 + 1.4 * (11.0 - d) * (s ** -0.2)), 2))
            next_interval_days = max(item.get("interval", 1) + 2, int(round(s)))

    reps += 1
    item["state"] = state
    item["step"] = step
    item["stability"] = s
    item["difficulty"] = d
    item["repetitions"] = reps
    item["lapses"] = lapses
    item["last_review"] = today_str

    if graduated:
        item["interval"] = next_interval_days
        next_date = now + datetime.timedelta(days=next_interval_days)
        item["next_review"] = next_date.date().isoformat()
    else:
        # Vẫn đang ở bước intraday 1m/10m, hẹn tạm trong hôm nay
        item["interval"] = 0
        item["next_review"] = today_str

    srs_data[word] = item
    return srs_data, graduated
