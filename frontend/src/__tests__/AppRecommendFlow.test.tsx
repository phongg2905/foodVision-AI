import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import { App } from '../App';

describe('Luồng End-to-End GĐ2 (Mockup A): Khám phá -> Gợi ý từ tủ bếp + Lưới 4 Cột -> Chi tiết', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
    window.sessionStorage.clear();
    window.history.replaceState(null, '', '/');
  });

  it('Cho phép mở chi tiết từ trang Khám phá công thức và quay lại bình thường', async () => {
    const user = userEvent.setup();
    render(<App />);

    await waitFor(() => {
      expect(
        screen.getByTestId('open-recipe-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
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

  it('Cập nhật trực tiếp lưới gợi ý 4 cột khi chọn Đậu hũ + Cà chua trên thanh tủ bếp ngang, đặt món chính & thời gian 30p rồi xem Chi tiết', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByTestId('nav-tab-kitchen'));

    await waitFor(() => {
      expect(
        screen.getByTestId('kitchen-studio-workspace')
      ).toBeInTheDocument();
      expect(screen.getByTestId('suggestion-item-dau-hu')).toBeInTheDocument();
    });

    // Chọn Đậu hũ & Cà chua ngay từ khay gợi ý nhanh
    await user.click(screen.getByTestId('suggestion-item-dau-hu'));
    await user.click(screen.getByTestId('suggestion-item-ca-chua'));

    await waitFor(() => {
      expect(screen.getByTestId('recommend-studio-grid')).toBeInTheDocument();
      expect(
        screen.getByTestId('recommendation-card-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });

    // Đánh dấu Đậu hũ làm món chính & mở dropdown thời gian chọn 30 phút
    await user.click(screen.getByTestId('toggle-main-dau-hu'));
    await user.click(screen.getByTestId('studio-time-trigger'));
    await user.click(screen.getByTestId('desired-time-preset-30'));

    // Chuyển thử tab Nấu được ngay (1) rồi quay về Tất cả
    await user.click(screen.getByTestId('studio-tab-ready'));
    expect(
      screen.getByTestId('recommendation-card-dau-hu-sot-ca-chua')
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId('recommendation-card-canh-ca-chua-trung')
    ).not.toBeInTheDocument();

    await user.click(screen.getByTestId('studio-tab-all'));

    // Mở Chi tiết công thức Đậu hũ sốt cà chua
    await user.click(
      screen.getByTestId('view-recipe-detail-dau-hu-sot-ca-chua')
    );

    await waitFor(() => {
      expect(
        screen.getByTestId('recipe-detail-view-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });
    expect(
      screen.getByTestId('detail-recommendation-summary')
    ).toBeInTheDocument();

    // Quay lại Gợi ý từ tủ bếp -> nguyên liệu & lưới kết quả giữ nguyên
    await user.click(screen.getByTestId('recipe-detail-back-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('recommend-studio-grid')).toBeInTheDocument();
      expect(screen.getByTestId('selected-chip-dau-hu')).toBeInTheDocument();
    });
  });

  it('Hỗ trợ chọn bộ nguyên liệu mẫu 1-chạm và xử lý nút Back trình duyệt (popstate)', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByTestId('nav-tab-kitchen'));
    expect(window.location.search).toBe('?tab=kitchen');

    await user.click(screen.getByTestId('starter-combo-tofu'));

    await waitFor(() => {
      expect(
        screen.getByTestId('view-recipe-detail-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });

    await user.click(
      screen.getByTestId('view-recipe-detail-dau-hu-sot-ca-chua')
    );
    await waitFor(() => {
      expect(window.location.search).toContain('tab=kitchen');
      expect(window.location.search).toContain(
        'recipe=a1111111-1111-4111-8111-000000000002'
      );
      expect(
        screen.getByTestId('recipe-detail-view-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });

    await act(async () => {
      window.history.replaceState(
        { tab: 'kitchen', recipeId: null },
        '',
        '/?tab=kitchen'
      );
      window.dispatchEvent(new PopStateEvent('popstate'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('recommend-studio-grid')).toBeInTheDocument();
      expect(
        screen.getByTestId('recommendation-card-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });
  });
});
