import os
import sys
import cv2
import numpy as np
from ultralytics import YOLO

# ==============================================================================
# KONFIGURASI
# ==============================================================================

def resource_path(relative_path):
    """ Mendapatkan path absolut ke resource, berfungsi untuk mode dev dan PyInstaller """
    try:
        # PyInstaller membuat folder sementara dan menyimpan path-nya di _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Path ke file model. Sekarang menggunakan fungsi resource_path.
MODEL_PATH = resource_path('best.pt')

# Parameter untuk proses masking
MIN_CONFIDENCE = 0.65 # Ambang batas kepercayaan deteksi
MASK_OFFSET = 15      # Jumlah piksel untuk menyusutkan mask (offset ke dalam)
DILATE_INITIAL_MASK_KERNEL_SIZE = 9 # Ukuran kernel untuk melebarkan mask awal

# ==============================================================================

def shrink_polygon_by_scaling(polygon_np, scale_factor):
    """
    Menyusutkan poligon ke arah titik pusatnya (centroid).
    """
    # Membutuhkan setidaknya 3 titik untuk membentuk poligon
    if polygon_np.shape[0] < 3:
        return polygon_np

    # Hitung centroid dari poligon
    M = cv2.moments(polygon_np)
    if M['m00'] == 0:
        return polygon_np
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])
    centroid = np.array([cx, cy])

    # Ubah tipe data untuk kalkulasi floating point
    polygon_float = polygon_np.astype(np.float32).reshape(-1, 2)

    # Susutkan koordinat dengan mengalikannya dengan faktor skala
    shrunk_coords = (polygon_float - centroid) * scale_factor + centroid

    # Kembalikan ke format integer dan bentuk asli
    return shrunk_coords.reshape(-1, 1, 2).astype(np.int32)

def main():
    """
    Fungsi utama untuk menjalankan proses inference dari terminal.
    """
    print("==============================================")
    print(" Manga Bubble Cleaner - Terminal Version")
    print("==============================================\n")

    # 1. Minta path dari pengguna
    input_dir = input("➡️ Masukkan path ke direktori gambar input: ")
    output_dir = input("⬅️ Masukkan path ke direktori untuk menyimpan hasil: ")

    # 2. Validasi path input
    if not os.path.isdir(input_dir):
        print(f"\n❌ ERROR: Direktori input tidak ditemukan di '{input_dir}'")
        sys.exit(1) # Keluar dari skrip jika direktori tidak ada

    # 3. Buat direktori output jika belum ada
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n✅ Hasil akan disimpan di: '{output_dir}'")

    # 4. Muat model YOLO
    try:
        print("\n⏳ Memuat model, mohon tunggu...")
        model = YOLO(MODEL_PATH)
        print("✅ Model berhasil dimuat.")
    except Exception as e:
        print(f"\n❌ ERROR: Gagal memuat model dari '{MODEL_PATH}'. Pastikan file ada dan tidak rusak.")
        print(f"Detail error: {e}")
        sys.exit(1)

    print("\n🚀 Memulai proses batch...\n")

    # 5. Loop utama untuk memproses setiap gambar
    image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    total_files = len(image_files)

    for i, filename in enumerate(image_files):
        input_image_path = os.path.join(input_dir, filename)
        output_image_path = os.path.join(output_dir, filename)

        print(f"[{i+1}/{total_files}] Memproses: {filename}")

        # Baca gambar
        img = cv2.imread(input_image_path)
        if img is None:
            print(f"  ⚠️ Gagal memuat gambar, dilewati.")
            continue

        # Konversi gambar grayscale ke BGR jika perlu
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # Lakukan inference
        results = model(input_image_path, retina_masks=True, verbose=False)
        orig_h, orig_w = results[0].orig_shape
        
        # Buat kanvas putih sebagai target output
        white_mask_output_img = img.copy()

        if results[0].masks is not None:
            masks = results[0].masks.data
            confidences = results[0].boxes.conf

            for idx, mask_tensor in enumerate(masks):
                confidence = confidences[idx].item()

                if confidence >= MIN_CONFIDENCE:
                    # Konversi tensor mask ke numpy array
                    mask_np = (mask_tensor.cpu().numpy() * 255).astype(np.uint8)
                    mask_np = cv2.resize(mask_np, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

                    # Perlebar (dilate) mask untuk menutupi area tepi dengan lebih baik
                    if DILATE_INITIAL_MASK_KERNEL_SIZE > 0:
                        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (DILATE_INITIAL_MASK_KERNEL_SIZE, DILATE_INITIAL_MASK_KERNEL_SIZE))
                        mask_np = cv2.dilate(mask_np, dilate_kernel, iterations=1)

                    # Temukan kontur dari mask
                    contours, _ = cv2.findContours(mask_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if not contours:
                        continue
                    
                    # Ambil kontur terbesar sebagai poligon utama
                    main_polygon = max(contours, key=cv2.contourArea)

                    # Susutkan poligon berdasarkan MASK_OFFSET
                    shrunk_polygon = main_polygon
                    if MASK_OFFSET > 0:
                        x, y, w, h = cv2.boundingRect(main_polygon)
                        if min(w, h) > 0:
                            # Hitung persentase penyusutan berdasarkan ukuran bounding box
                            shrink_percentage = MASK_OFFSET / ((w + h) / 4.0)
                            scale_factor = max(1.0 - shrink_percentage, 0.1) # Batasi agar tidak terlalu kecil
                            shrunk_polygon = shrink_polygon_by_scaling(main_polygon, scale_factor)
                        else:
                            shrunk_polygon = None

                    # Gambar poligon yang sudah disusutkan ke gambar output dengan warna putih
                    if shrunk_polygon is not None and len(shrunk_polygon) >= 3:
                        cv2.fillPoly(white_mask_output_img, [shrunk_polygon], (255, 255, 255))

        # Simpan gambar hasil
        cv2.imwrite(output_image_path, white_mask_output_img)

    print("\n==============================================")
    print("✅ Semua gambar telah selesai diproses.")
    print("==============================================")


if __name__ == "__main__":
    main()