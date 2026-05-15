"""
批量给测试集图片注入GPS EXIF信息
模拟一条道路巡检路线（北京某道路段）
使用 piexif 库可靠地写入 GPS IFD
"""
import os
import sys
import random
from fractions import Fraction
import piexif
from PIL import Image


def _dd_to_rational(dd):
    """十进制度 → EXIF GPS DMS 格式 [(度,1), (分,1), (秒分子,秒分母)]"""
    is_neg = dd < 0
    dd = abs(dd)
    d = int(dd)
    m = int((dd - d) * 60)
    s = (dd - d - m / 60.0) * 3600.0
    s_frac = Fraction(s).limit_denominator(1000000)
    return [(d, 1), (m, 1), (s_frac.numerator, s_frac.denominator)]


def inject_gps(image_path, lat, lon):
    """给单张图片注入GPS EXIF，返回实际保存路径"""
    ext = os.path.splitext(image_path)[1].lower()

    # PNG 不支持 EXIF，转 JPEG
    if ext == '.png':
        img = Image.open(image_path)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        out_path = image_path.replace('.png', '.jpg')
        img.save(out_path, 'jpeg', quality=95)
        img.close()
        os.remove(image_path)
        image_path = out_path

    # 用 piexif 写入 GPS
    try:
        exif_dict = piexif.load(image_path)
    except Exception:
        exif_dict = {'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}, 'Interop': {}}

    lat_r = _dd_to_rational(lat)
    lon_r = _dd_to_rational(lon)

    exif_dict['GPS'] = {
        piexif.GPSIFD.GPSLatitudeRef: b'N' if lat >= 0 else b'S',
        piexif.GPSIFD.GPSLatitude: lat_r,
        piexif.GPSIFD.GPSLongitudeRef: b'E' if lon >= 0 else b'W',
        piexif.GPSIFD.GPSLongitude: lon_r,
    }

    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, image_path)
    return image_path


def main():
    # 模拟巡检路线：北京某道路段（天安门→鼓楼，约3公里）
    LAT_START = 39.9042
    LAT_END = 39.9310
    LON_START = 116.3974
    LON_END = 116.3910

    img_dir = sys.argv[1] if len(sys.argv) > 1 else input("请输入图片目录路径: ").strip().strip('"')
    if not os.path.isdir(img_dir):
        print(f"目录不存在: {img_dir}")
        return

    images = sorted([
        os.path.join(img_dir, f) for f in os.listdir(img_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])

    if not images:
        print("未找到图片文件")
        return

    n = len(images)
    print(f"找到 {n} 张图片，开始注入GPS...")

    converted = 0
    for i, img_path in enumerate(images):
        t = i / max(n - 1, 1)
        lat = LAT_START + (LAT_END - LAT_START) * t + random.uniform(-0.0003, 0.0003)
        lon = LON_START + (LON_END - LON_START) * t + random.uniform(-0.0003, 0.0003)

        try:
            inject_gps(img_path, lat, lon)
            converted += 1
            if (i + 1) % 50 == 0:
                print(f"  已处理 {i + 1}/{n}")
        except Exception as e:
            print(f"  失败: {os.path.basename(img_path)} - {e}")

    print(f"\n完成！成功注入 {converted}/{n} 张。")


if __name__ == '__main__':
    main()
