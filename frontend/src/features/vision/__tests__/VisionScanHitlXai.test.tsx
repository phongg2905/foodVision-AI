import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../../../App';
import {
  FALLBACK_64X64_JPEG_BYTES,
  FALLBACK_64X64_PNG_BYTES,
  buildExifApp1Segment,
  createDemoScanFile,
  injectJpegExifOrientation,
} from '../utils/demoScanFixtures';
import { normalizeDetectResponse } from '../../../shared/api/aiDetectApi';
import {
  inspectImageFile,
  readJpegExifOrientation,
} from '../../../shared/utils/imageValidation';

function countExifApp1Headers(bytes: Uint8Array): number {
  let count = 0;
  for (let i = 0; i + 9 < bytes.length; i += 1) {
    if (
      bytes[i] === 0xff &&
      bytes[i + 1] === 0xe1 &&
      bytes[i + 4] === 0x45 &&
      bytes[i + 5] === 0x78 &&
      bytes[i + 6] === 0x69 &&
      bytes[i + 7] === 0x66 &&
      bytes[i + 8] === 0x00 &&
      bytes[i + 9] === 0x00
    ) {
      count += 1;
    }
  }
  return count;
}

function readJpegSofDimensions(bytes: Uint8Array): {
  width: number;
  height: number;
} | null {
  let offset = 2;
  while (offset + 8 < bytes.length) {
    if (bytes[offset] !== 0xff) {
      offset += 1;
      continue;
    }
    const marker = bytes[offset + 1];
    if (marker === 0xd9 || marker === 0xda) break;
    const segLen = (bytes[offset + 2] << 8) | bytes[offset + 3];
    if (marker === 0xc0 || marker === 0xc1 || marker === 0xc2) {
      const height = (bytes[offset + 5] << 8) | bytes[offset + 6];
      const width = (bytes[offset + 7] << 8) | bytes[offset + 8];
      return { width, height };
    }
    offset += 2 + segLen;
  }
  return null;
}

describe('Thẻ #22 & #30 (GĐ3..GĐ4): Upload/Camera, BBox EXIF (F2), Cảnh báo HITL (< 0.80, F3), Fallback FR-18 & Giải thích XAI', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
    window.sessionStorage.clear();
    window.history.replaceState(null, '', '/?tab=kitchen');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('TC-05, TC-06, TC-43 & F2: Kiểm tra <= 5 MiB, MIME, chữ ký nhị phân, xóa segment EXIF APP1 cũ và ảnh mẫu thật >= 640x480', async () => {
    // 1. TC-05: File > 5 MiB -> 413 IMAGE_TOO_LARGE
    const oversizedBytes = new Uint8Array(5 * 1024 * 1024 + 128);
    oversizedBytes.set(FALLBACK_64X64_PNG_BYTES, 0);
    const oversizedFile = new File([oversizedBytes], 'oversized.png', {
      type: 'image/png',
    });
    const resOversize = await inspectImageFile(oversizedFile);
    expect(resOversize.ok).toBe(false);
    if (!resOversize.ok) {
      expect(resOversize.status).toBe(413);
      expect(resOversize.code).toBe('IMAGE_TOO_LARGE');
    }

    // 2. TC-06(1): File sai định dạng (.pdf) -> 415 UNSUPPORTED_IMAGE_TYPE
    const pdfFile = new File(['%PDF-1.7 test'], 'document.pdf', {
      type: 'application/pdf',
    });
    const resPdf = await inspectImageFile(pdfFile);
    expect(resPdf.ok).toBe(false);
    if (!resPdf.ok) {
      expect(resPdf.status).toBe(415);
      expect(resPdf.code).toBe('UNSUPPORTED_IMAGE_TYPE');
    }

    // 3. TC-06(2): File giả mạo đuôi .jpg chứa text hỏng -> 422 INVALID_IMAGE
    const fakeJpg = new File(['not-a-real-jpeg-stream'], 'corrupt.jpg', {
      type: 'image/jpeg',
    });
    const resCorrupt = await inspectImageFile(fakeJpg);
    expect(resCorrupt.ok).toBe(false);
    if (!resCorrupt.ok) {
      expect(resCorrupt.status).toBe(422);
      expect(resCorrupt.code).toBe('INVALID_IMAGE');
    }

    // 4. F2: Fallback nhị phân đạt chuẩn >= 64x64 px (không bao giờ 1x1)
    const pngWidth =
      (FALLBACK_64X64_PNG_BYTES[16] << 24) |
      (FALLBACK_64X64_PNG_BYTES[17] << 16) |
      (FALLBACK_64X64_PNG_BYTES[18] << 8) |
      FALLBACK_64X64_PNG_BYTES[19];
    const pngHeight =
      (FALLBACK_64X64_PNG_BYTES[20] << 24) |
      (FALLBACK_64X64_PNG_BYTES[21] << 16) |
      (FALLBACK_64X64_PNG_BYTES[22] << 8) |
      FALLBACK_64X64_PNG_BYTES[23];
    expect(pngWidth).toBeGreaterThanOrEqual(64);
    expect(pngHeight).toBeGreaterThanOrEqual(64);

    const jpegDims = readJpegSofDimensions(FALLBACK_64X64_JPEG_BYTES);
    expect(jpegDims).toEqual({ width: 64, height: 64 });

    // 5. TC-43 & F2: injectJpegExifOrientation xóa sạch segment 0xFFE1 cũ trước khi gắn cờ mới
    expect(buildExifApp1Segment(6).length).toBe(36);
    const onceBytes = injectJpegExifOrientation(FALLBACK_64X64_JPEG_BYTES, 3);
    expect(readJpegExifOrientation(onceBytes)).toBe(3);
    expect(countExifApp1Headers(onceBytes)).toBe(1);

    const twiceBytes = injectJpegExifOrientation(onceBytes, 6);
    expect(readJpegExifOrientation(twiceBytes)).toBe(6);
    expect(countExifApp1Headers(twiceBytes)).toBe(1);
    expect(twiceBytes.length).toBe(onceBytes.length);

    const portraitFile = await createDemoScanFile('portrait-exif');
    const resPortrait = await inspectImageFile(portraitFile);
    expect(resPortrait.ok).toBe(true);
    if (resPortrait.ok) {
      expect(resPortrait.exifOrientation).toBe(6);
      expect(resPortrait.swapsAxes).toBe(true);
    }

    // 6. F2: 3 ảnh mẫu tĩnh trong public/samples/*.jpg tồn tại thật và có kích thước >= 640x480 px
    const fsSpecifier = 'node:fs';
    const nodeFs = (await import(/* @vite-ignore */ fsSpecifier)) as {
      readFileSync: (filePath: string) => Uint8Array;
    };
    for (const fileName of [
      'basket-hitl.jpg',
      'portrait-exif-6.jpg',
      'blur-empty.jpg',
    ]) {
      const sampleBytes = new Uint8Array(
        nodeFs.readFileSync(`public/samples/${fileName}`)
      );
      expect(sampleBytes[0]).toBe(0xff);
      expect(sampleBytes[1]).toBe(0xd8);
      const dims = readJpegSofDimensions(sampleBytes);
      expect(dims).not.toBeNull();
      expect(Math.max(dims!.width, dims!.height)).toBeGreaterThanOrEqual(640);
      expect(Math.min(dims!.width, dims!.height)).toBeGreaterThanOrEqual(480);
    }
  });

  it('F3: normalizeDetectResponse chỉ tự tách clear/uncertain khi CẢ HAI mảng từ server cùng rỗng', () => {
    const idTomato = '11111111-1111-4111-8111-111111111101';
    const idCucumber = '11111111-1111-4111-8111-111111111207';

    // Server chỉ trả clear_ingredients có phần tử, uncertain_ingredients cố ý rỗng -> bảo toàn rỗng
    const preservedClearOnly = normalizeDetectResponse({
      scan_id: 'scan-f3-1',
      model_version: 'yolo11n-foodvision-v1',
      detections: [],
      suggested_ingredients: [
        { ingredient_id: idTomato, name_vi: 'Cà chua', max_confidence: 0.91 },
        {
          ingredient_id: idCucumber,
          name_vi: 'Dưa leo',
          max_confidence: 0.65,
        },
      ],
      clear_ingredients: [
        { ingredient_id: idTomato, name_vi: 'Cà chua', max_confidence: 0.91 },
      ],
      uncertain_ingredients: [],
    });
    expect(preservedClearOnly.clear_ingredients).toHaveLength(1);
    expect(preservedClearOnly.uncertain_ingredients).toHaveLength(0);

    // Server chỉ trả uncertain_ingredients có phần tử, clear_ingredients rỗng -> bảo toàn rỗng
    const preservedUncertainOnly = normalizeDetectResponse({
      scan_id: 'scan-f3-2',
      model_version: 'yolo11n-foodvision-v1',
      detections: [],
      suggested_ingredients: [
        { ingredient_id: idTomato, name_vi: 'Cà chua', max_confidence: 0.91 },
        {
          ingredient_id: idCucumber,
          name_vi: 'Dưa leo',
          max_confidence: 0.65,
        },
      ],
      clear_ingredients: [],
      uncertain_ingredients: [
        {
          ingredient_id: idCucumber,
          name_vi: 'Dưa leo',
          max_confidence: 0.65,
        },
      ],
    });
    expect(preservedUncertainOnly.clear_ingredients).toHaveLength(0);
    expect(preservedUncertainOnly.uncertain_ingredients).toHaveLength(1);
  });

  it('DEF-01, DEF-02, TC-07, TC-08 & DEF-10: Quét ảnh rổ nguyên liệu, vẽ 4 BBox, cảnh báo HITL < 80%, sửa nhãn khử trùng UUID chuẩn & hiển thị XAI trực quan', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByTestId('kitchen-camera-mode-tab'));
    expect(screen.getByTestId('vision-scan-panel')).toBeInTheDocument();

    await user.click(screen.getByTestId('demo-fixture-basket-hitl'));

    await waitFor(() => {
      expect(screen.getByTestId('bbox-upright-stage')).toBeInTheDocument();
      expect(screen.getByTestId('hitl-uncertain-alert')).toBeInTheDocument();
    });

    expect(screen.getByTestId('bbox-item-0')).toHaveAttribute(
      'data-needs-confirmation',
      'false'
    );
    expect(screen.getByTestId('bbox-item-3')).toHaveAttribute(
      'data-needs-confirmation',
      'true'
    );

    expect(screen.getByTestId('hitl-review-badge')).toHaveTextContent(
      'Cần kiểm tra lại'
    );

    expect(screen.getByTestId('hitl-apply-btn')).toHaveTextContent(
      'Thêm vào tủ bếp (2)'
    );

    // TC-08: Đổi nhãn Dưa leo (...1207) trùng sang Cà chua (...1101) -> tự khử trùng lặp UUID (vẫn là 2)
    const relabelSelect = screen.getByTestId(
      'hitl-relabel-select-11111111-1111-4111-8111-111111111207'
    );
    await user.selectOptions(
      relabelSelect,
      '11111111-1111-4111-8111-111111111101'
    );
    expect(screen.getByTestId('hitl-apply-btn')).toHaveTextContent(
      'Thêm vào tủ bếp (2)'
    );

    // Đổi sang Trứng gà (...1102) -> tổng nguyên liệu xác nhận tăng lên 3
    await user.selectOptions(
      relabelSelect,
      '11111111-1111-4111-8111-111111111102'
    );
    expect(screen.getByTestId('hitl-apply-btn')).toHaveTextContent(
      'Thêm vào tủ bếp (3)'
    );

    await user.click(screen.getByTestId('hitl-apply-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('selected-chip-ca-chua')).toBeInTheDocument();
      expect(screen.getByTestId('selected-chip-dau-hu')).toBeInTheDocument();
      expect(screen.getByTestId('selected-chip-trung-ga')).toBeInTheDocument();
      expect(
        screen.getByTestId('recommendation-score-dau-hu-sot-ca-chua')
      ).toHaveTextContent('82.5 điểm');
    });

    const xaiBlock = screen.getByTestId('score-xai-dau-hu-sot-ca-chua');
    expect(xaiBlock).toHaveClass('sr-only');
    await user.click(
      screen.getByTestId('recommendation-score-dau-hu-sot-ca-chua')
    );
    expect(xaiBlock).not.toHaveClass('sr-only');
    expect(xaiBlock).toHaveTextContent('50.0/50');
    expect(xaiBlock).toHaveTextContent('12.5/25');
    expect(xaiBlock).toHaveTextContent('15.0/15');
    expect(xaiBlock).toHaveTextContent('5.0/10');

    await user.click(
      screen.getByTestId('view-recipe-detail-dau-hu-sot-ca-chua')
    );
    await waitFor(() => {
      expect(
        screen.getByTestId('detail-xai-breakdown-grid')
      ).toBeInTheDocument();
    });
    expect(screen.getByTestId('detail-xai-breakdown-grid')).toHaveTextContent(
      '50.0/50'
    );
  });

  it('TC-43: Hiển thị ảnh dọc có cờ EXIF Orientation = 6 với image-orientation: from-image và thông báo căn chiều', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByTestId('kitchen-camera-mode-tab'));
    await user.click(screen.getByTestId('demo-fixture-portrait-exif'));

    await waitFor(() => {
      expect(screen.getByTestId('exif-orientation-badge')).toBeInTheDocument();
    });

    const previewImg = screen.getByTestId('bbox-preview-image');
    expect(previewImg).toHaveStyle({ imageOrientation: 'from-image' });
    expect(screen.getByTestId('bbox-upright-stage')).toHaveAttribute(
      'data-exif-orientation',
      '6'
    );
  });

  it('TC-27, TC-29, TC-30 & UI-02: Chuyển tiếp mượt sang chế độ nhập thủ công (FR-18) khi detections=[] hoặc gặp lỗi 503/504', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByTestId('kitchen-camera-mode-tab'));
    await user.click(screen.getByTestId('demo-fixture-blur-empty'));

    await waitFor(() => {
      expect(screen.getByTestId('hitl-empty-detections')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('fallback-manual-input-btn'));
    await waitFor(() => {
      expect(
        screen.queryByTestId('vision-scan-panel')
      ).not.toBeInTheDocument();
      expect(screen.getByLabelText('Nhập tên nguyên liệu chính')).toHaveFocus();
    });

    import.meta.env.VITE_API_MOCK_MODE = 'false';
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          code: 'INFERENCE_TIMEOUT',
          message: 'Quá thời gian chờ suy luận ảnh từ dịch vụ AI.',
          details: { timeout_seconds: 10 },
          request_id: 'req-test-504',
        }),
        {
          status: 504,
          headers: { 'Content-Type': 'application/json' },
        }
      )
    );

    await user.click(screen.getByTestId('kitchen-camera-mode-tab'));
    const fileInput = screen.getByTestId('vision-file-input');
    const validFile = new File([FALLBACK_64X64_PNG_BYTES], 'kitchen.png', {
      type: 'image/png',
    });
    await user.upload(fileInput, validFile);

    await waitFor(() => {
      expect(screen.getByTestId('vision-error-banner')).toHaveAttribute(
        'data-error-code',
        'INFERENCE_TIMEOUT'
      );
    });
    expect(fetchSpy).toHaveBeenCalled();
    expect(screen.getByTestId('vision-retry-btn')).toBeInTheDocument();

    await user.click(screen.getByTestId('fallback-manual-input-btn'));
    await waitFor(() => {
      expect(
        screen.queryByTestId('vision-scan-panel')
      ).not.toBeInTheDocument();
      expect(screen.getByLabelText('Nhập tên nguyên liệu chính')).toHaveFocus();
    });
  });
});
