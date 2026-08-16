import os
import sys
import subprocess
from PIL import Image, ImageFilter, ImageDraw

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    # Định nghĩa các đường dẫn tuyệt đối
    base_dir = r"d:\vocab"
    jpg_path = os.path.join(base_dir, "extension", "icons", "mèo mũ nồiiiiiiiiiiii.jpg")
    ico_path = os.path.join(base_dir, "desktop-app", "icon_transparent_v2.ico")
    main_py = os.path.join(base_dir, "desktop-app", "main.py")
    working_dir = os.path.join(base_dir, "desktop-app")
    
    # 1. Chuyển đổi và tách nền thông minh sử dụng thuật toán đóng kín nét vẽ (Morphological Closing Mask)
    if os.path.exists(jpg_path):
        print(f"Đang đọc ảnh gốc {jpg_path}...")
        img_orig = Image.open(jpg_path).convert("RGBA")
        w, h = img_orig.size
        
        # 1.1. Tạo ảnh nhị phân phân tách nét vẽ vẽ và màu nền trắng tinh
        img_bin = Image.new("L", (w, h), 0)
        p_orig = img_orig.load()
        p_bin = img_bin.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = p_orig[x, y]
                # Nếu pixel lệch khỏi màu trắng tinh khiết -> coi là nét vẽ hoặc chi tiết tranh
                if r < 240 or g < 240 or b < 240:
                    p_bin[x, y] = 255
                    
        # 1.2. Giãn nở đường nét (Dilation) bằng MaxFilter để bịt kín tất cả các khoảng hở ở outline mèo
        # Bộ lọc MaxFilter(21) nối liền các nét vẽ đứt khúc, ngăn màu tràn vào cơ thể mèo
        img_dilated = img_bin.filter(ImageFilter.MaxFilter(21))
        
        # 1.3. Loang màu nền trắng ngoài (Floodfill) bắt đầu từ điểm góc (0,0)
        ImageDraw.floodfill(img_dilated, (0, 0), 128)
        
        # 1.4. Áp mặt nạ: các pixel tương ứng với màu loang 128 ở ngoài rìa sẽ chuyển thành trong suốt (alpha = 0)
        p_dil = img_dilated.load()
        for y in range(h):
            for x in range(w):
                if p_dil[x, y] == 128:
                    p_orig[x, y] = (255, 255, 255, 0)
                    
        # Lưu file dưới dạng ICO có trong suốt
        img_orig.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        print(f"Đã tạo thành công file icon trong suốt thực tế tại {ico_path}")
    else:
        print(f"Lỗi: Không tìm thấy ảnh gốc tại {jpg_path}")
        return

    # 2. Xác định đường dẫn chạy không hiện cửa sổ CMD (pythonw.exe)
    pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw_path):
        pythonw_path = sys.executable
        print(f"Không tìm thấy pythonw.exe, chuyển sang dùng: {pythonw_path}")

    # 3. Tạo/Cập nhật Shortcut bằng PowerShell Script
    ps_script = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $Shortcut = $WshShell.CreateShortcut("$DesktopPath\\Meow-morize.lnk")
    $Shortcut.TargetPath = "{pythonw_path}"
    $Shortcut.Arguments = "{main_py}"
    $Shortcut.WorkingDirectory = "{working_dir}"
    $Shortcut.IconLocation = "{ico_path}"
    $Shortcut.Description = "Meow-morize Vocabulary Review App"
    $Shortcut.Save()
    """
    
    print("Đang tạo icon shortcut trong suốt trên Desktop...")
    try:
        subprocess.run(["powershell", "-Command", ps_script], check=True)
        desktop_dir = os.path.join(os.environ["USERPROFILE"], "Desktop")
        print(f"Đã cập nhật biểu tượng mèo mũ nồi trong suốt thành công!")
        print(f"Đường dẫn shortcut: {desktop_dir}\\Meow-morize.lnk")
    except Exception as e:
        print(f"Không thể tạo shortcut: {e}")

if __name__ == "__main__":
    main()
