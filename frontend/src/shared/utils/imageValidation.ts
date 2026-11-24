import { MAX_IMAGE_UPLOAD_BYTES } from '../api/types';

export type SupportedImageMime = 'image/jpeg' | 'image/png' | 'image/webp';

export const ALLOWED_IMAGE_MIME_TYPES: readonly SupportedImageMime[] = [
  'image/jpeg',
  'image/png',
  'image/webp',
];

const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];

export interface ValidImageInspection {
  ok: true;
  mimeType: SupportedImageMime;
  exifOrientation: number;
  swapsAxes: boolean;
}

export interface InvalidImageInspection {
  ok: false;
  status: 413 | 415 | 422;
  code: 'IMAGE_TOO_LARGE' | 'UNSUPPORTED_IMAGE_TYPE' | 'INVALID_IMAGE';
  message: string;
}

export type ImageInspectionResult =
  | ValidImageInspection
  | InvalidImageInspection;

/**
 * Kiểm tra chữ ký nhị phân (Magic Bytes) khớp chính xác với backend/app/ai/image_processor/decoder.py:
 * - JPEG: FF D8 FF
 * - PNG : 89 50 4E 47 0D 0A 1A 0A
 * - WebP: RIFF....WEBP
 */
export function detectImageMagicMime(
  bytes: Uint8Array
): SupportedImageMime | null {
  if (
    bytes.length >= 3 &&
    bytes[0] === 0xff &&
    bytes[1] === 0xd8 &&
    bytes[2] === 0xff
  ) {
    return 'image/jpeg';
  }

  if (
    bytes.length >= 8 &&
    bytes[0] === 0x89 &&
    bytes[1] === 0x50 &&
    bytes[2] === 0x4e &&
    bytes[3] === 0x47 &&
    bytes[4] === 0x0d &&
    bytes[5] === 0x0a &&
    bytes[6] === 0x1a &&
    bytes[7] === 0x0a
  ) {
    return 'image/png';
  }

  if (
    bytes.length >= 12 &&
    bytes[0] === 0x52 &&
    bytes[1] === 0x49 &&
    bytes[2] === 0x46 &&
    bytes[3] === 0x46 &&
    bytes[8] === 0x57 &&
    bytes[9] === 0x45 &&
    bytes[10] === 0x42 &&
    bytes[11] === 0x50
  ) {
    return 'image/webp';
  }

  return null;
}

/**
 * Đọc cờ EXIF Orientation (1..8) trực tiếp từ header JPEG APP1 (0xFFE1 / Tag 0x0112).
 * Trả về 1 (chiều chuẩn) nếu ảnh không có EXIF hoặc không phải JPEG.
 * Giá trị 5, 6, 7, 8 biểu thị ảnh chụp xoay 90°/270° (ví dụ ảnh dọc điện thoại có Orientation = 6).
 */
export function readJpegExifOrientation(bytes: Uint8Array): number {
  if (bytes.length < 14 || bytes[0] !== 0xff || bytes[1] !== 0xd8) {
    return 1;
  }

  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  let offset = 2;

  while (offset + 4 <= bytes.length) {
    const marker = view.getUint16(offset, false);
    offset += 2;

    if (marker === 0xffda || marker === 0xffd9) {
      break;
    }

    if ((marker & 0xff00) !== 0xff00) {
      break;
    }

    if (offset + 2 > bytes.length) {
      break;
    }

    const segmentLength = view.getUint16(offset, false);
    if (segmentLength < 2 || offset + segmentLength > bytes.length) {
      break;
    }

    // APP1 marker (0xFFE1) chứa chuỗi "Exif\0\0"
    if (marker === 0xffe1 && segmentLength >= 10) {
      const exifHeaderOffset = offset + 2;
      if (
        exifHeaderOffset + 6 <= bytes.length &&
        bytes[exifHeaderOffset] === 0x45 && // E
        bytes[exifHeaderOffset + 1] === 0x78 && // x
        bytes[exifHeaderOffset + 2] === 0x69 && // i
        bytes[exifHeaderOffset + 3] === 0x66 && // f
        bytes[exifHeaderOffset + 4] === 0x00 &&
        bytes[exifHeaderOffset + 5] === 0x00
      ) {
        const tiffStart = exifHeaderOffset + 6;
        if (tiffStart + 8 <= bytes.length) {
          const byteOrder = view.getUint16(tiffStart, false);
          const littleEndian = byteOrder === 0x4949; // "II"
          const bigEndian = byteOrder === 0x4d4d; // "MM"

          if (littleEndian || bigEndian) {
            const ifd0Offset = view.getUint32(tiffStart + 4, littleEndian);
            const dirStart = tiffStart + ifd0Offset;

            if (dirStart + 2 <= bytes.length) {
              const entryCount = view.getUint16(dirStart, littleEndian);
              for (let i = 0; i < entryCount; i += 1) {
                const entryOffset = dirStart + 2 + i * 12;
                if (entryOffset + 12 > bytes.length) {
                  break;
                }
                const tag = view.getUint16(entryOffset, littleEndian);
                if (tag === 0x0112) {
                  const orientation = view.getUint16(
                    entryOffset + 8,
                    littleEndian
                  );
                  if (orientation >= 1 && orientation <= 8) {
                    return orientation;
                  }
                  return 1;
                }
              }
            }
          }
        }
      }
    }

    offset += segmentLength;
  }

  return 1;
}

function hasAllowedNameOrMime(file: File): boolean {
  const normalizedMime = (file.type || '').toLowerCase().trim();
  if (
    normalizedMime &&
    (ALLOWED_IMAGE_MIME_TYPES as readonly string[]).includes(normalizedMime)
  ) {
    return true;
  }

  // Nếu trình duyệt báo rõ MIME khác (VD: application/pdf, image/tiff, image/heic) -> từ chối 415
  if (normalizedMime && normalizedMime !== 'application/octet-stream') {
    return false;
  }

  const lowerName = (file.name || '').toLowerCase();
  return ALLOWED_EXTENSIONS.some((ext) => lowerName.endsWith(ext));
}

async function readHeaderBytes(file: File, maxBytes = 65536): Promise<Uint8Array> {
  const slice = file.slice(0, Math.min(file.size, maxBytes));
  if (typeof slice.arrayBuffer === 'function') {
    const buf = await slice.arrayBuffer();
    return new Uint8Array(buf);
  }

  return await new Promise<Uint8Array>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (reader.result instanceof ArrayBuffer) {
        resolve(new Uint8Array(reader.result));
      } else {
        reject(new Error('Không đọc được dữ liệu tệp ảnh.'));
      }
    };
    reader.onerror = () => reject(new Error('Không đọc được dữ liệu tệp ảnh.'));
    reader.readAsArrayBuffer(slice);
  });
}

/**
 * Kiểm tra toàn diện tệp ảnh ở phía trình duyệt trước khi gửi POST /api/v1/ai/detect (FR-03, TC-05, TC-06, TC-43):
 * 1. Rỗng (0 byte) -> 422 INVALID_IMAGE
 * 2. Dung lượng > 5 MiB -> 413 IMAGE_TOO_LARGE
 * 3. Định dạng ngoài JPEG/PNG/WebP -> 415 UNSUPPORTED_IMAGE_TYPE
 * 4. Tệp giả mạo đuôi .jpg/.png nhưng chữ ký nhị phân hỏng -> 422 INVALID_IMAGE
 * 5. Trích xuất cờ EXIF Orientation (1..8) để hiển thị & căn khung bbox chuẩn xác.
 */
export async function inspectImageFile(
  file: File
): Promise<ImageInspectionResult> {
  if (!file || file.size === 0) {
    return {
      ok: false,
      status: 422,
      code: 'INVALID_IMAGE',
      message:
        'Tệp ảnh tải lên đang rỗng. Vui lòng chọn một ảnh hợp lệ hoặc nhập nguyên liệu thủ công.',
    };
  }

  if (file.size > MAX_IMAGE_UPLOAD_BYTES) {
    const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
    return {
      ok: false,
      status: 413,
      code: 'IMAGE_TOO_LARGE',
      message: `Dung lượng ảnh (${sizeMb} MiB) vượt quá giới hạn tối đa 5 MiB. Vui lòng chọn ảnh nhẹ hơn hoặc nhập nguyên liệu thủ công.`,
    };
  }

  if (!hasAllowedNameOrMime(file)) {
    return {
      ok: false,
      status: 415,
      code: 'UNSUPPORTED_IMAGE_TYPE',
      message:
        'Định dạng tệp không được hỗ trợ. Chỉ chấp nhận ảnh JPEG (.jpg), PNG (.png) hoặc WebP (.webp).',
    };
  }

  let headerBytes: Uint8Array;
  try {
    headerBytes = await readHeaderBytes(file, 65536);
  } catch {
    return {
      ok: false,
      status: 422,
      code: 'INVALID_IMAGE',
      message:
        'Không thể đọc dữ liệu ảnh. Vui lòng kiểm tra lại tệp hoặc nhập nguyên liệu thủ công.',
    };
  }

  const magicMime = detectImageMagicMime(headerBytes);
  if (!magicMime) {
    return {
      ok: false,
      status: 422,
      code: 'INVALID_IMAGE',
      message:
        'Dữ liệu ảnh bị hỏng hoặc không đúng chuẩn ảnh thực tế. Vui lòng chọn ảnh khác hoặc nhập nguyên liệu thủ công.',
    };
  }

  const exifOrientation =
    magicMime === 'image/jpeg' ? readJpegExifOrientation(headerBytes) : 1;

  return {
    ok: true,
    mimeType: magicMime,
    exifOrientation,
    swapsAxes: exifOrientation >= 5 && exifOrientation <= 8,
  };
}
