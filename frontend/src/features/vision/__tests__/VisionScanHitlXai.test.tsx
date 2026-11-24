import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../../../App';
import {
  buildExifApp1Segment,
  injectJpegExifOrientation,
} from '../utils/demoScanFixtures';
import {
  inspectImageFile,
  readJpegExifOrientation,
} from '../../../shared/utils/imageValidation';

const VALID_PNG_BYTES = new Uint8Array([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00, 0x00, 0x0d,
  0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
  0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xde, 0x00, 0x00, 0x00,
  0x00, 0x49, 0x45, 0x4e, 0x44, 0xae, 0x42, 0x60, 0x82,
]);

const VALID_JPEG_SOI_EOI = new Uint8Array([
  0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46, 0x00, 0x01,
  0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xff, 0xd9,
]);

describe('Thẻ #22 (GĐ3 - TP14): Upload/Camera, BBox EXIF, Cảnh báo HITL (< 0.80), Fallback FR-18 & Giải thích XAI', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
    window.sessionStorage.clear();
    window.history.replaceState(null, '', '/?tab=kitchen');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('TC-05, TC-06 & TC-43: Kiểm tra dung lượng <= 5 MiB, định dạng MIME, chữ ký nhị phân giả mạo và đọc cờ EXIF Orientation', async () => {
    // 1. TC-05: File > 5 MiB -> 413 IMAGE_TOO_LARGE
    const oversizedBytes = new Uint8Array(5 * 1024 * 1024 + 128);
    oversizedBytes.set(VALID_PNG_BYTES, 0);
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

    // 4. TC-43: Đọc đúng cờ EXIF Orientation = 6 trên ảnh dọc điện thoại
    expect(buildExifApp1Segment(6).length).toBe(36);
    const portraitBytes = injectJpegExifOrientation(VALID_JPEG_SOI_EOI, 6);
    expect(readJpegExifOrientation(portraitBytes)).toBe(6);

    const portraitFile = new File(
      [new Uint8Array(portraitBytes)],
      'phone-portrait.jpg',
      {
        type: 'image/jpeg',
      }
    );
    const resPortrait = await inspectImageFile(portraitFile);
    expect(resPortrait.ok).toBe(true);
    if (resPortrait.ok) {
      expect(resPortrait.exifOrientation).toBe(6);
      expect(resPortrait.swapsAxes).toBe(true);
    }
  });

  it('DEF-01, DEF-02, TC-07, TC-08 & DEF-10: Quét ảnh rổ nguyên liệu, vẽ 4 BBox, cảnh báo HITL < 80%, sửa nhãn khử trùng UUID & hiển thị XAI trực quan', async () => {
    const user = userEvent.setup();
    render(<App />);

    // Mở khay Quét ảnh AI
    await user.click(screen.getByTestId('kitchen-camera-mode-tab'));
    expect(screen.getByTestId('vision-scan-panel')).toBeInTheDocument();

    // Chạy ảnh mẫu Rổ cà chua & đậu hũ (có Dưa leo 64% < 80%)
    await user.click(screen.getByTestId('demo-fixture-basket-hitl'));

    await waitFor(() => {
      expect(screen.getByTestId('bbox-upright-stage')).toBeInTheDocument();
      expect(screen.getByTestId('hitl-uncertain-alert')).toBeInTheDocument();
    });

    // Kiểm tra có đủ 4 hộp bbox (2 hộp Cà chua + 1 Đậu hũ + 1 Dưa leo < 80%)
    expect(screen.getByTestId('bbox-item-0')).toHaveAttribute(
      'data-needs-confirmation',
      'false'
    );
    expect(screen.getByTestId('bbox-item-3')).toHaveAttribute(
      'data-needs-confirmation',
      'true'
    );

    // Huy hiệu cảnh báo HITL Review hiển thị rõ
    expect(screen.getByTestId('hitl-review-badge')).toHaveTextContent(
      'Cần kiểm tra lại'
    );

    // Ban đầu chỉ có 2 nguyên liệu clear (Cà chua & Đậu hũ) được tích sẵn; Dưa leo (64%) chưa tự chốt
    expect(screen.getByTestId('hitl-apply-btn')).toHaveTextContent(
      'Thêm vào tủ bếp (2)'
    );

    // TC-08: Người dùng đổi nhãn Dưa leo (11111111-1111-4111-8111-000000000006) trùng sang Cà chua -> phải tự khử trùng lặp UUID (vẫn là 2)
    const relabelSelect = screen.getByTestId(
      'hitl-relabel-select-11111111-1111-4111-8111-000000000006'
    );
    await user.selectOptions(
      relabelSelect,
      '11111111-1111-4111-8111-000000000002' // Cà chua
    );
    expect(screen.getByTestId('hitl-apply-btn')).toHaveTextContent(
      'Thêm vào tủ bếp (2)'
    );

    // Đổi sang Trứng gà (11111111-1111-4111-8111-000000000003) -> tổng nguyên liệu xác nhận tăng lên 3
    await user.selectOptions(
      relabelSelect,
      '11111111-1111-4111-8111-000000000003'
    );
    expect(screen.getByTestId('hitl-apply-btn')).toHaveTextContent(
      'Thêm vào tủ bếp (3)'
    );

    // Áp dụng vào tủ bếp -> cập nhật lưới gợi ý nguyên bản Phương án A
    await user.click(screen.getByTestId('hitl-apply-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('selected-chip-ca-chua')).toBeInTheDocument();
      expect(screen.getByTestId('selected-chip-dau-hu')).toBeInTheDocument();
      expect(screen.getByTestId('selected-chip-trung-ga')).toBeInTheDocument();
      expect(
        screen.getByTestId('recommendation-score-dau-hu-sot-ca-chua')
      ).toHaveTextContent('82.5 điểm');
    });

    // Mặc định thẻ giữ mặt sạch thoáng; bấm vào huy hiệu điểm mở bảng chi tiết XAI 4 tiêu chí
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

    // Mở trang chi tiết kiểm tra dải chữ tạp chí phân rã XAI 4 tiêu chí
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

    // 1. TC-27: detections = [] trên ảnh mờ
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

    // 2. TC-29 & TC-30: Giả lập Backend thật trả 504 INFERENCE_TIMEOUT -> hiển thị nút Thử quét lại & Chuyển sang nhập thủ công
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
    const validFile = new File([VALID_PNG_BYTES], 'kitchen.png', {
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

    // Bấm Chuyển sang nhập thủ công -> đóng khay lỗi và đặt con trỏ vào ô tìm tiếng Việt
    await user.click(screen.getByTestId('fallback-manual-input-btn'));
    await waitFor(() => {
      expect(
        screen.queryByTestId('vision-scan-panel')
      ).not.toBeInTheDocument();
      expect(screen.getByLabelText('Nhập tên nguyên liệu chính')).toHaveFocus();
    });
  });
});
