import React, { useState } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Ingredient, RecommendDraftPayload } from '../../../shared/api/types';
import * as ingredientsApi from '../../../shared/api/ingredientsApi';
import { MOCK_MAIN_INGREDIENTS } from '../../../shared/api/mockData';
import { IngredientKitchenView } from '../IngredientKitchenView';

const StatefulKitchenHarness: React.FC<{
  onRecommend?: (payload: RecommendDraftPayload) => void;
}> = ({ onRecommend }) => {
  const [selectedIngredients, setSelectedIngredients] = useState<Ingredient[]>(
    []
  );
  const [excludedPantryIds, setExcludedPantryIds] = useState<string[]>([]);

  return (
    <IngredientKitchenView
      selectedIngredients={selectedIngredients}
      onSelectedIngredientsChange={setSelectedIngredients}
      excludedPantryIds={excludedPantryIds}
      onExcludedPantryIdsChange={setExcludedPantryIds}
      onTriggerRecommend={onRecommend}
    />
  );
};

describe('IngredientKitchenView (FR-18, FR-05, AC-07, AC-08, F1)', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('AC-08: Khóa nút "Gợi ý món ăn" khi danh sách nguyên liệu chính (ingredient_ids) rỗng và mở khóa khi có >= 1 nguyên liệu', async () => {
    const user = userEvent.setup();
    render(<StatefulKitchenHarness />);

    const submitBtn = screen.getByTestId('recommend-submit-btn');
    expect(submitBtn).toBeDisabled();
    expect(screen.getByTestId('recommend-disabled-hint')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-dau-hu')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('suggestion-item-dau-hu'));

    expect(submitBtn).not.toBeDisabled();
    expect(screen.getByTestId('selected-chip-dau-hu')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Xóa Đậu hũ' }));
    expect(submitBtn).toBeDisabled();
  });

  it('AC-07 & F1: Tìm kiếm tiếng Việt có dấu, không dấu, đồng nghĩa vùng miền ("đậu phụ" -> Đậu hũ, "ngô" -> Bắp ngọt) đúng UUID chuẩn Backend', async () => {
    const user = userEvent.setup();
    const onRecommend = vi.fn();
    render(<StatefulKitchenHarness onRecommend={onRecommend} />);

    const input = screen.getByLabelText('Nhập tên nguyên liệu chính');

    // 1. Tìm bằng từ đồng nghĩa miền Bắc "đậu phụ" -> trả về "Đậu hũ"
    await user.type(input, 'đậu phụ');
    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-dau-hu')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('suggestion-item-dau-hu'));
    expect(screen.getByTestId('selected-chip-dau-hu')).toBeInTheDocument();

    // 2. Tìm lại bằng không dấu "dau hu" và bấm chọn lần 2 -> không tạo bản sao thứ 2
    await user.clear(input);
    await user.type(input, 'dau hu');
    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-dau-hu')).toBeInTheDocument();
    });
    await user.click(screen.getByTestId('suggestion-item-dau-hu'));

    expect(
      screen.getByTestId('duplicate-ingredient-notice')
    ).toBeInTheDocument();

    // 3. Tìm bằng từ đồng nghĩa "ngô" -> khớp "Bắp ngọt" (bap-ngot)
    await user.clear(input);
    await user.type(input, 'ngô');
    await waitFor(() => {
      expect(
        screen.getByTestId('suggestion-item-bap-ngot')
      ).toBeInTheDocument();
    });
    await user.click(screen.getByTestId('suggestion-item-bap-ngot'));

    await user.click(screen.getByTestId('recommend-submit-btn'));
    expect(onRecommend).toHaveBeenCalledTimes(1);
    expect(onRecommend).toHaveBeenCalledWith({
      ingredient_ids: [
        '11111111-1111-4111-8111-111111111103', // Đậu hũ
        '11111111-1111-4111-8111-111111111219', // Bắp ngọt
      ],
      excluded_pantry_ids: [],
    });
  });

  it('FR-05, ADR-008 & F1: Thanh 5 gia vị sẵn có (Muối, Đường, Nước mắm, Dầu ăn, Tiêu xay) mặc định checked và gửi đúng UUID chuẩn Backend', async () => {
    const user = userEvent.setup();
    const onRecommend = vi.fn();
    render(<StatefulKitchenHarness onRecommend={onRecommend} />);

    const pantrySlugs = ['muoi', 'duong', 'nuoc-mam', 'dau-an', 'tieu-xay'];
    for (const slug of pantrySlugs) {
      const label = screen.getByTestId(`pantry-toggle-${slug}`);
      const checkbox = label.querySelector('input[type="checkbox"]');
      expect(checkbox).toBeChecked();
    }

    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-ca-chua')).toBeInTheDocument();
    });
    await user.click(screen.getByTestId('suggestion-item-ca-chua'));

    await user.click(screen.getByTestId('pantry-toggle-nuoc-mam'));
    await user.click(screen.getByTestId('pantry-toggle-tieu-xay'));

    await user.click(screen.getByTestId('recommend-submit-btn'));
    expect(onRecommend).toHaveBeenCalledWith({
      ingredient_ids: ['11111111-1111-4111-8111-111111111101'],
      excluded_pantry_ids: [
        '11111111-1111-4111-8111-111111111107', // Nước mắm
        '11111111-1111-4111-8111-111111111110', // Tiêu xay
      ],
    });
  });

  it('F1: Lọc cứng category !== "pantry" khi nạp danh mục nguyên liệu chính từ API', async () => {
    vi.spyOn(ingredientsApi, 'searchMainIngredients').mockResolvedValue({
      items: [
        ...MOCK_MAIN_INGREDIENTS.slice(0, 4),
        {
          id: '11111111-1111-4111-8111-111111111106',
          slug: 'muoi',
          name_vi: 'Muối',
          category: 'pantry',
          is_active: true,
        },
      ],
      total: 5,
      limit: 50,
      offset: 0,
    });

    render(<StatefulKitchenHarness />);
    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-ca-chua')).toBeInTheDocument();
    });
    expect(
      screen.queryByTestId('suggestion-item-muoi')
    ).not.toBeInTheDocument();
  });

  it('Điều hướng bàn phím (ArrowDown + Enter chọn và tự đóng dropdown; Escape đóng dropdown)', async () => {
    const user = userEvent.setup();
    render(<StatefulKitchenHarness />);

    const input = screen.getByLabelText('Nhập tên nguyên liệu chính');
    await user.type(input, 'đậu phụ');

    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-dau-hu')).toBeInTheDocument();
    });

    await user.keyboard('{ArrowDown}{Enter}');

    expect(screen.getByTestId('selected-chip-dau-hu')).toBeInTheDocument();
    expect(
      screen.queryByTestId('ingredient-search-dropdown')
    ).not.toBeInTheDocument();
    expect(input).toHaveValue('');

    await user.type(input, 'bắp');
    await waitFor(() => {
      expect(
        screen.getByTestId('suggestion-item-bap-ngot')
      ).toBeInTheDocument();
    });

    await user.keyboard('{Escape}');
    expect(
      screen.queryByTestId('ingredient-search-dropdown')
    ).not.toBeInTheDocument();
  });
});
