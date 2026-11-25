import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import { App } from '../App';

describe('Luồng End-to-End GĐ2..GĐ4 (Mockup A): Khám phá -> Gợi ý từ tủ bếp + Lưới 4 Cột -> Chi tiết', () => {
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

    await user.click(screen.getByTestId('suggestion-item-dau-hu'));
    await user.click(screen.getByTestId('suggestion-item-ca-chua'));

    await waitFor(() => {
      expect(screen.getByTestId('recommend-studio-grid')).toBeInTheDocument();
      expect(
        screen.getByTestId('recommendation-card-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('toggle-main-dau-hu'));
    await user.click(screen.getByTestId('studio-time-trigger'));
    await user.click(screen.getByTestId('desired-time-preset-30'));

    await user.click(screen.getByTestId('studio-tab-ready'));
    expect(
      screen.getByTestId('recommendation-card-dau-hu-sot-ca-chua')
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId('recommendation-card-canh-ca-chua-trung')
    ).not.toBeInTheDocument();

    await user.click(screen.getByTestId('studio-tab-all'));

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

    await user.click(screen.getByTestId('recipe-detail-back-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('recommend-studio-grid')).toBeInTheDocument();
      expect(screen.getByTestId('selected-chip-dau-hu')).toBeInTheDocument();
    });
  });

  it('Hỗ trợ chọn bộ nguyên liệu mẫu 1-chạm, làm sạch UUID cũ trong sessionStorage (F1) và xử lý nút Back trình duyệt (popstate)', async () => {
    // Gài thử UUID cũ không khớp chuẩn trong sessionStorage -> App phải tự ánh xạ sang UUID chuẩn Backend và loại bỏ rác
    window.sessionStorage.setItem(
      'foodvision_kitchen_draft_v1',
      JSON.stringify({
        selectedIngredients: [
          {
            id: '11111111-1111-4111-8111-000000000001',
            slug: 'dau-hu',
            name_vi: 'Đậu hũ',
            category: 'protein',
            is_active: true,
          },
          {
            id: '99999999-9999-4999-8999-999999999999',
            slug: 'nguyen-lieu-rac',
            name_vi: 'Nguyên liệu rác',
            category: 'other',
            is_active: true,
          },
        ],
        mainIngredientIds: ['11111111-1111-4111-8111-000000000001'],
        excludedPantryIds: [],
      })
    );

    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByTestId('nav-tab-kitchen'));
    expect(window.location.search).toBe('?tab=kitchen');

    await waitFor(() => {
      expect(screen.getByTestId('selected-chip-dau-hu')).toBeInTheDocument();
      expect(
        screen.queryByTestId('selected-chip-nguyen-lieu-rac')
      ).not.toBeInTheDocument();
    });

    // Bấm xóa hết để thử starter combo 1-chạm
    await user.click(screen.getByRole('button', { name: 'Xóa Đậu hũ' }));
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
        'recipe=22222222-2222-4222-8222-222222222201'
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
