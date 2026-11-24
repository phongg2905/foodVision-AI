/**
 * Bộ tạo tệp ảnh mẫu dùng ảnh chụp ẩm thực thật (khi chạy trên trình duyệt có mạng)
 * kèm dự phòng nhị phân tối giản cho môi trường kiểm thử tự động JSDOM / ngoại tuyến.
 * Không vẽ hình học giả tạo trên canvas.
 */

export type DemoFixtureKind = 'basket-hitl' | 'portrait-exif' | 'blur-empty';

const REAL_SAMPLE_URLS: Record<DemoFixtureKind, string> = {
  'basket-hitl':
    'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=760&q=80',
  'portrait-exif':
    'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=520&h=720&q=80',
  'blur-empty':
    'https://images.unsplash.com/photo-1495195134817-aeb325a55b65?auto=format&fit=crop&w=720&q=60',
};

const MINIMAL_PNG_BYTES = new Uint8Array([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00, 0x00, 0x0d,
  0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
  0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xde, 0x00, 0x00, 0x00,
  0x0c, 0x49, 0x44, 0x41, 0x54, 0x08, 0xd7, 0x63, 0xf8, 0xcf, 0xc0, 0x00,
  0x00, 0x03, 0x01, 0x01, 0x00, 0x18, 0xdd, 0x8d, 0xb0, 0x00, 0x00, 0x00,
  0x00, 0x49, 0x45, 0x4e, 0x44, 0xae, 0x42, 0x60, 0x82,
]);

const MINIMAL_JPEG_BYTES = new Uint8Array([
  0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46, 0x00, 0x01,
  0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xff, 0xd9,
]);

/**
 * Tạo segment JPEG APP1 (0xFFE1) chuẩn TIFF Big-Endian chứa Tag 0x0112 (Orientation = orientation).
 */
export function buildExifApp1Segment(
  orientation: number
): Uint8Array<ArrayBuffer> {
  const safeOrientation =
    orientation >= 1 && orientation <= 8 ? orientation : 1;
  return new Uint8Array([
    0xff,
    0xe1,
    0x00,
    0x22,
    0x45,
    0x78,
    0x69,
    0x66,
    0x00,
    0x00,
    0x4d,
    0x4d,
    0x00,
    0x2a,
    0x00,
    0x00,
    0x00,
    0x08,
    0x00,
    0x01,
    0x01,
    0x12,
    0x00,
    0x03,
    0x00,
    0x00,
    0x00,
    0x01,
    0x00,
    safeOrientation,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
  ]);
}

/**
 * Chèn segment APP1 EXIF Orientation ngay sau SOI (0xFFD8) của luồng byte JPEG,
 * đồng thời loại bỏ các segment APP1 EXIF cũ (nếu có) để không xung đột cờ hướng ảnh.
 */
export function injectJpegExifOrientation(
  jpegBytes: Uint8Array,
  orientation: number
): Uint8Array<ArrayBuffer> {
  if (jpegBytes.length < 4 || jpegBytes[0] !== 0xff || jpegBytes[1] !== 0xd8) {
    return new Uint8Array(jpegBytes);
  }

  const app1 = buildExifApp1Segment(orientation);
  const combined = new Uint8Array(jpegBytes.length + app1.length);
  combined[0] = 0xff;
  combined[1] = 0xd8;
  combined.set(app1, 2);
  combined.set(jpegBytes.subarray(2), 2 + app1.length);
  return combined;
}

function dataUrlToBytes(dataUrl: string): Uint8Array<ArrayBuffer> | null {
  const commaIdx = dataUrl.indexOf(',');
  if (commaIdx < 0) return null;
  const base64 = dataUrl.slice(commaIdx + 1);
  if (!base64 || typeof atob !== 'function') return null;
  const binary = atob(base64);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    out[i] = binary.charCodeAt(i);
  }
  return out;
}

/**
 * Với mẫu ảnh dọc EXIF: xoay ảnh thực 90° CCW trên bộ nhớ rồi gắn cờ EXIF Orientation = 6 (90° CW)
 * để trình duyệt & Backend tự xoay thẳng đứng về đúng chiều ảnh chụp thật.
 */
async function buildRealPortraitExifFromBlob(
  blob: Blob
): Promise<Uint8Array<ArrayBuffer> | null> {
  if (typeof createImageBitmap !== 'function' || typeof document === 'undefined') {
    return null;
  }
  try {
    const bitmap = await createImageBitmap(blob);
    const uprightW = bitmap.width;
    const uprightH = bitmap.height;
    const canvas = document.createElement('canvas');
    canvas.width = uprightH;
    canvas.height = uprightW;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      bitmap.close();
      return null;
    }
    ctx.translate(0, uprightW);
    ctx.rotate(-Math.PI / 2);
    ctx.drawImage(bitmap, 0, 0, uprightW, uprightH);
    bitmap.close();

    const jpegBytes = dataUrlToBytes(canvas.toDataURL('image/jpeg', 0.88));
    if (!jpegBytes) return null;
    return injectJpegExifOrientation(jpegBytes, 6);
  } catch {
    return null;
  }
}

export async function createDemoScanFile(kind: DemoFixtureKind): Promise<File> {
  const isJsdom =
    typeof navigator !== 'undefined' && /jsdom/i.test(navigator.userAgent);

  if (!isJsdom && typeof fetch === 'function') {
    try {
      const response = await fetch(REAL_SAMPLE_URLS[kind], { mode: 'cors' });
      if (response.ok) {
        const blob = await response.blob();
        if (kind === 'portrait-exif') {
          const exifBytes = await buildRealPortraitExifFromBlob(blob);
          if (exifBytes) {
            return new File([exifBytes], 'anh-doc-exif-6.jpg', {
              type: 'image/jpeg',
            });
          }
          const rawBuf = new Uint8Array(await blob.arrayBuffer());
          const oriented = injectJpegExifOrientation(rawBuf, 6);
          return new File([oriented], 'anh-doc-exif-6.jpg', {
            type: 'image/jpeg',
          });
        }

        const fileName =
          kind === 'basket-hitl'
            ? 'ro-nguyen-lieu-hitl.jpg'
            : 'anh-mo-khong-ro.jpg';
        return new File([blob], fileName, {
          type: blob.type || 'image/jpeg',
        });
      }
    } catch {
      // Ngoại tuyến hoặc bị chặn mạng -> dùng tệp nhị phân tối giản bên dưới
    }
  }

  if (kind === 'portrait-exif') {
    const oriented = injectJpegExifOrientation(MINIMAL_JPEG_BYTES, 6);
    return new File([oriented], 'anh-doc-exif-6.jpg', { type: 'image/jpeg' });
  }

  if (kind === 'blur-empty') {
    return new File([MINIMAL_PNG_BYTES], 'anh-mo-khong-ro.png', {
      type: 'image/png',
    });
  }

  return new File([MINIMAL_PNG_BYTES], 'ro-nguyen-lieu-hitl.png', {
    type: 'image/png',
  });
}
