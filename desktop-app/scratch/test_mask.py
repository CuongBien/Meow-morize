import os
import shutil
from PIL import Image, ImageFilter, ImageDraw

def main():
    jpg_path = r"d:\vocab\extension\icons\mèo mũ nồiiiiiiiiiiii.jpg"
    out_png = r"d:\vocab\desktop-app\scratch\test_mask.png"
    
    img_orig = Image.open(jpg_path).convert("RGBA")
    w, h = img_orig.size
    
    # 1. Tạo ảnh nhị phân: đường nét/foreground = 255 (trắng), nền trắng gốc = 0 (đen)
    img_bin = Image.new("L", (w, h), 0)
    p_orig = img_orig.load()
    p_bin = img_bin.load()
    
    for y in range(h):
        for x in range(w):
            r, g, b, a = p_orig[x, y]
            # Nếu pixel lệch nhiều khỏi màu trắng tinh khiết -> được coi là nét vẽ
            if r < 240 or g < 240 or b < 240:
                p_bin[x, y] = 255
                
    # 2. Giãn nở đường nét (Dilation) bằng MaxFilter để đóng kín các khoảng hở
    # Phễu lọc size=21 sẽ nối liền mọi khoảng hở nhỏ dưới 10px của nét vẽ
    img_dilated = img_bin.filter(ImageFilter.MaxFilter(21))
    
    # 3. Loang màu (Floodfill) vùng nền đen phía ngoài từ điểm gốc (0,0)
    ImageDraw.floodfill(img_dilated, (0, 0), 128)
    
    # 4. Áp mặt nạ: Điểm nào ở ảnh loang màu có giá trị 128 -> thuộc nền ngoài -> chuyển thành trong suốt
    p_dil = img_dilated.load()
    for y in range(h):
        for x in range(w):
            if p_dil[x, y] == 128:
                p_orig[x, y] = (255, 255, 255, 0)
                
    img_orig.save(out_png)
    # Sao chép vào thư mục artifact để xem thử
    shutil.copy(out_png, r"C:\Users\Victus\.gemini\antigravity\brain\9f26d78a-a4ad-4564-ba48-269030e3f96b\test_mask.png")
    print("Xử lý mặt nạ thành công!")

if __name__ == "__main__":
    main()
