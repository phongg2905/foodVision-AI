/**
 * Bộ nạp ảnh mẫu ẩm thực thật cục bộ (/samples/*.jpg >= 640x480 px)
 * kèm dữ liệu nhị phân dự phòng 64x64 px hợp lệ cho môi trường JSDOM / ngoại tuyến.
 * Không vẽ hình học giả tạo trên canvas và không bao giờ gửi ảnh < 64x64 gây 422 INVALID_IMAGE.
 */

export type DemoFixtureKind = 'basket-hitl' | 'portrait-exif' | 'blur-empty';

const LOCAL_SAMPLE_PATHS: Record<DemoFixtureKind, string> = {
  'basket-hitl': '/samples/basket-hitl.jpg',
  'portrait-exif': '/samples/portrait-exif-6.jpg',
  'blur-empty': '/samples/blur-empty.jpg',
};

/**
 * Ảnh PNG 64x64 px hợp lệ (139 bytes, nền kem ấm #EFE2D2) dùng làm fallback trong JSDOM / offline,
 * đạt ngưỡng kích thước tối thiểu >= 64x64 của Backend preprocess_uploaded_image.
 */
export const FALLBACK_64X64_PNG_BYTES = new Uint8Array([
  137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82, 0, 0, 0, 64, 0,
  0, 0, 64, 8, 2, 0, 0, 0, 37, 11, 230, 137, 0, 0, 0, 82, 73, 68, 65, 84, 120,
  218, 237, 207, 49, 13, 0, 48, 8, 0, 48, 152, 127, 93, 104, 64, 2, 50, 166,
  130, 131, 164, 117, 208, 156, 174, 184, 236, 197, 113, 2, 2, 2, 2, 2, 2, 2,
  2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
  2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 251, 62, 4, 176, 3, 6, 92, 31, 166, 61,
  0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130,
]);

/**
 * Ảnh JPEG 64x64 px hợp lệ (310 bytes, SOF0 64x64) dùng làm fallback EXIF trong JSDOM / offline.
 */
export const FALLBACK_64X64_JPEG_BYTES = new Uint8Array([
  255, 216, 255, 224, 0, 16, 74, 70, 73, 70, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 255,
  219, 0, 67, 0, 8, 6, 6, 7, 6, 5, 8, 7, 7, 7, 9, 9, 8, 10, 12, 20, 13, 12, 11,
  11, 12, 25, 18, 19, 15, 20, 29, 26, 31, 30, 29, 26, 28, 28, 32, 36, 46, 39,
  32, 34, 44, 35, 28, 28, 40, 55, 41, 44, 48, 49, 52, 52, 52, 31, 39, 57, 61,
  56, 50, 60, 46, 51, 52, 50, 255, 219, 0, 67, 1, 9, 9, 9, 12, 11, 12, 24, 13,
  13, 24, 50, 33, 28, 33, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50,
  50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50,
  50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 255,
  192, 0, 17, 8, 0, 64, 0, 64, 3, 1, 34, 0, 2, 17, 1, 3, 17, 1, 255, 196, 0,
  21, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 255, 196, 0, 20,
  16, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 196, 0, 21, 1, 1,
  1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 255, 196, 0, 20, 17, 1, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 218, 0, 12, 3, 1, 0, 2, 17,
  3, 17, 0, 63, 0, 173, 128, 145, 64, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 63, 255, 217,
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

function isExifApp1Payload(bytes: Uint8Array, payloadOffset: number, segLen: number): boolean {
  // segLen bao gồm 2 byte độ dài + ít nhất 6 byte "Exif\0\0"
  if (segLen < 8 || payloadOffset + 6 > bytes.length) {
    return false;
  }
  return (
    bytes[payloadOffset] === 0x45 &&
    bytes[payloadOffset + 1] === 0x78 &&
    bytes[payloadOffset + 2] === 0x69 &&
    bytes[payloadOffset + 3] === 0x66 &&
    bytes[payloadOffset + 4] === 0x00 &&
    bytes[payloadOffset + 5] === 0x00
  );
}

/**
 * Chèn segment APP1 EXIF Orientation ngay sau SOI (0xFFD8) của luồng byte JPEG,
 * đồng thời quét và xóa toàn bộ các segment APP1 (0xFFE1 Exif\0\0) cũ trước đó (F2)
 * để trình duyệt và Backend Pillow không bao giờ gặp xung đột nhiều thẻ EXIF.
 */
export function injectJpegExifOrientation(
  jpegBytes: Uint8Array,
  orientation: number
): Uint8Array<ArrayBuffer> {
  if (jpegBytes.length < 4 || jpegBytes[0] !== 0xff || jpegBytes[1] !== 0xd8) {
    return new Uint8Array(jpegBytes);
  }

  const keptChunks: Uint8Array[] = [];
  let offset = 2;

  while (offset < jpegBytes.length) {
    if (jpegBytes[offset] !== 0xff) {
      keptChunks.push(jpegBytes.subarray(offset));
      break;
    }

    const segStart = offset;
    let pos = offset + 1;
    while (pos < jpegBytes.length && jpegBytes[pos] === 0xff) {
      pos += 1;
    }

    if (pos >= jpegBytes.length) {
      keptChunks.push(jpegBytes.subarray(segStart));
      break;
    }

    const marker = jpegBytes[pos];

    // SOS (0xFFDA) hoặc EOI (0xFFD9): toàn bộ luồng dữ liệu nén phía sau giữ nguyên
    if (marker === 0xda || marker === 0xd9 || marker === 0x00) {
      keptChunks.push(jpegBytes.subarray(segStart));
      break;
    }

    // Các marker độc lập không có trường length (RST0..RST7, SOI, TEM)
    if ((marker >= 0xd0 && marker <= 0xd8) || marker === 0x01) {
      keptChunks.push(jpegBytes.subarray(segStart, pos + 1));
      offset = pos + 1;
      continue;
    }

    if (pos + 2 >= jpegBytes.length) {
      keptChunks.push(jpegBytes.subarray(segStart));
      break;
    }

    const segLen = (jpegBytes[pos + 1] << 8) | jpegBytes[pos + 2];
    const segEnd = pos + 1 + segLen;
    if (segLen < 2 || segEnd > jpegBytes.length) {
      keptChunks.push(jpegBytes.subarray(segStart));
      break;
    }

    // Xóa mọi segment APP1 (0xFFE1) mang header "Exif\0\0" cũ
    if (marker === 0xe1 && isExifApp1Payload(jpegBytes, pos + 3, segLen)) {
      offset = segEnd;
      continue;
    }

    keptChunks.push(jpegBytes.subarray(segStart, segEnd));
    offset = segEnd;
  }

  const app1 = buildExifApp1Segment(orientation);
  const keptLength = keptChunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const combined = new Uint8Array(2 + app1.length + keptLength);

  combined[0] = 0xff;
  combined[1] = 0xd8;
  combined.set(app1, 2);

  let writePos = 2 + app1.length;
  for (const chunk of keptChunks) {
    combined.set(chunk, writePos);
    writePos += chunk.length;
  }

  return combined;
}

export async function createDemoScanFile(kind: DemoFixtureKind): Promise<File> {
  const isJsdom =
    typeof navigator !== 'undefined' && /jsdom/i.test(navigator.userAgent);

  if (!isJsdom && typeof fetch === 'function') {
    try {
      const response = await fetch(LOCAL_SAMPLE_PATHS[kind]);
      if (response.ok) {
        const rawBuf = new Uint8Array(await response.arrayBuffer());
        if (kind === 'portrait-exif') {
          const oriented = injectJpegExifOrientation(rawBuf, 6);
          return new File([oriented], 'anh-doc-exif-6.jpg', {
            type: 'image/jpeg',
          });
        }

        const fileName =
          kind === 'basket-hitl'
            ? 'ro-nguyen-lieu-hitl.jpg'
            : 'anh-mo-khong-ro.jpg';
        return new File([rawBuf], fileName, {
          type: 'image/jpeg',
        });
      }
    } catch {
      // Ngoại tuyến hoặc môi trường test không có static server -> dùng ảnh 64x64 nhị phân hợp lệ
    }
  }

  if (kind === 'portrait-exif') {
    const oriented = injectJpegExifOrientation(FALLBACK_64X64_JPEG_BYTES, 6);
    return new File([oriented], 'anh-doc-exif-6.jpg', { type: 'image/jpeg' });
  }

  if (kind === 'blur-empty') {
    return new File([FALLBACK_64X64_PNG_BYTES], 'anh-mo-khong-ro.png', {
      type: 'image/png',
    });
  }

  return new File([FALLBACK_64X64_PNG_BYTES], 'ro-nguyen-lieu-hitl.png', {
    type: 'image/png',
  });
}
