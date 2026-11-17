import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import { App } from '../App';

describe('Luồng End-to-End GĐ2: Chọn nguyên liệu -> Tùy chọn -> Gợi ý Ready/Missing -> Chi tiết Công thức', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
    window.sessionStorage.clear();
    window.history.replaceState(null, '', '/');
  });

  it('Cho phép mở chi tiết từ Danh mục công thức và quay lại bình thường', async () => {
    const user = userEvent.setup();
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('open-recipe-dau-hu-sot-ca-chua')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('open-recipe-dau-hu-sot-ca-chua'));

    await waitFor(() => {
      expect(
        screen.getByTestId('recipe-detail-view-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });
    expect(screen.getByTestId('nutrition-disclaimer')).toBeInTheDocument();

    await user.click(screen.getByTestId('recipe-detail-back-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('recipe-catalog-grid')).toBeInTheDocument();
    });
  });

  it('Cho phép chọn Đậu hũ + Cà chua, đánh dấu món chính & thời gian 30p, xem Gợi ý Ready/Missing rồi mở chi tiết và quay lại', async () => {
    const user = userEvent.setup();
    render(<App />);

    // 1. Vào tab Chọn nguyên liệu & Bếp
    await user.click(screen.getByTestId('nav-tab-kitchen'));

    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-dau-hu')).toBeInTheDocument();
    });

    // 2. Chọn Đậu hũ & Cà chua
    await user.click(screen.getByTestId('suggestion-item-dau-hu'));
    await user.click(screen.getByTestId('suggestion-item-ca-chua'));

    // 3. Tùy chọn Đậu hũ làm món chính & thời gian 30 phút
    await user.click(screen.getByTestId('toggle-main-dau-hu'));
    await user.click(screen.getByTestId('desired-time-preset-30'));

    // 4. Bấm Gợi ý món ăn -> tự chuyển sang màn Danh sách Gợi ý
    await user.click(screen.getByTestId('recommend-submit-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('recommend-ready-section')).toBeInTheDocument();
    });
    expect(
      screen.getByTestId('recommendation-card-dau-hu-sot-ca-chua')
    ).toBeInTheDocument();
    expect(
      screen.getByTestId('recommend-missing-section')
    ).toBeInTheDocument();

    // 5. Mở Chi tiết công thức Đậu hũ sốt cà chua từ thẻ Gợi ý
    await user.click(screen.getByTestId('view-recipe-detail-dau-hu-sot-ca-chua'));

    await waitFor(() => {
      expect(
        screen.getByTestId('recipe-detail-view-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });
    expect(
      screen.getByTestId('detail-recommendation-summary')
    ).toBeInTheDocument();

    // 6. Quay lại Danh sách gợi ý -> kết quả vẫn được giữ nguyên
    await user.click(screen.getByTestId('recipe-detail-back-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('recommend-ready-section')).toBeInTheDocument();
    });
    expect(
      screen.getByTestId('recommendation-card-dau-hu-sot-ca-chua')
    ).toBeInTheDocument();
  });

  it('Đồng bộ URL trình duyệt và xử lý nút Back vật lý (popstate) không bị thoát khỏi ứng dụng', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByTestId('nav-tab-kitchen'));
    expect(window.location.search).toBe('?tab=kitchen');

    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-dau-hu')).toBeInTheDocument();
    });
    await user.click(screen.getByTestId('suggestion-item-dau-hu'));
    await user.click(screen.getByTestId('suggestion-item-ca-chua'));
    await user.click(screen.getByTestId('recommend-submit-btn'));

    await waitFor(() => {
      expect(window.location.search).toBe('?tab=recommendations');
      expect(
        screen.getByTestId('view-recipe-detail-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('view-recipe-detail-dau-hu-sot-ca-chua'));
    await waitFor(() => {
      expect(window.location.search).toContain('tab=recommendations');
      expect(window.location.search).toContain(
        'recipe=a1111111-1111-4111-8111-000000000002'
      );
      expect(
        screen.getByTestId('recipe-detail-view-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });

    // Giả lập bấm nút Back trình duyệt quay lại danh sách gợi ý
    await act(async () => {
      window.history.replaceState(
        { tab: 'recommendations', recipeId: null },
        '',
        '/?tab=recommendations'
      );
      window.dispatchEvent(new PopStateEvent('popstate'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('recommend-ready-section')).toBeInTheDocument();
      expect(
        screen.getByTestId('recommendation-card-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });
  });
});
