import React, { useState } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { Ingredient, RecommendDraftPayload } from '../../../shared/api/types';
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

describe('IngredientKitchenView (FR-18, FR-05, AC-07, AC-08)', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
  });

  it('AC-08: Khóa nút "Gợi ý món ăn" khi danh sách nguyên liệu chính (ingredient_ids) rỗng và mở khóa khi có >= 1 nguyên liệu', async () => {
    const user = userEvent.setup();
    render(<StatefulKitchenHarness />);

    const submitBtn = screen.getByTestId('recommend-submit-btn');
    expect(submitBtn).toBeDisabled();
    expect(screen.getByTestId('recommend-disabled-hint')).toBeInTheDocument();

    // Chờ gợi ý nguyên liệu chính hiển thị và chọn "Đậu hũ"
    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-dau-hu')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('suggestion-item-dau-hu'));

    // Nút Gợi ý món ăn lập tức được mở khóa
    expect(submitBtn).not.toBeDisabled();
    expect(screen.getByTestId('selected-chip-dau-hu')).toBeInTheDocument();

    // Xóa Đậu hũ khỏi danh sách đã chọn -> nút bị khóa trở lại
    await user.click(screen.getByRole('button', { name: 'Xóa Đậu hũ' }));
    expect(submitBtn).toBeDisabled();
  });

  it('AC-07: Tìm kiếm tiếng Việt có dấu, không dấu, đồng nghĩa vùng miền ("đậu phụ" -> Đậu hũ, "ngô" -> Bắp) và chống trùng lặp UUID trong ingredient_ids', async () => {
    const user = userEvent.setup();
    const onRecommend = vi.fn();
    render(<StatefulKitchenHarness onRecommend={onRecommend} />);

    const input = screen.getByLabelText('Nhập tên nguyên liệu chính');

    // 1. Tìm bằng từ đồng nghĩa miền Bắc "đậu phụ" -> phải trả về "Đậu hũ"
    await user.type(input, 'đậu phụ');
    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-dau-hu')).toBeInTheDocument();
    });

    // Chọn Đậu hũ lần 1
    await user.click(screen.getByTestId('suggestion-item-dau-hu'));
    expect(screen.getByTestId('selected-chip-dau-hu')).toBeInTheDocument();

    // 2. Tìm lại bằng không dấu "dau hu" và bấm chọn lần 2 -> không được tạo bản sao thứ 2
    await user.clear(input);
    await user.type(input, 'dau hu');
    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-dau-hu')).toBeInTheDocument();
    });
    await user.click(screen.getByTestId('suggestion-item-dau-hu'));

    expect(
      screen.getByTestId('duplicate-ingredient-notice')
    ).toBeInTheDocument();

    // 3. Tìm bằng từ đồng nghĩa "ngô" -> khớp "Bắp"
    await user.clear(input);
    await user.type(input, 'ngô');
    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-bap')).toBeInTheDocument();
    });
    await user.click(screen.getByTestId('suggestion-item-bap'));

    // Bấm Gợi ý món ăn và kiểm tra mảng ingredient_ids chỉ có đúng 2 UUID duy nhất
    await user.click(screen.getByTestId('recommend-submit-btn'));
    expect(onRecommend).toHaveBeenCalledTimes(1);
    expect(onRecommend).toHaveBeenCalledWith({
      ingredient_ids: [
        '11111111-1111-4111-8111-000000000001', // Đậu hũ
        '11111111-1111-4111-8111-000000000005', // Bắp
      ],
      excluded_pantry_ids: [],
    });
  });

  it('FR-05 & ADR-008: Thanh 5 gia vị sẵn có (Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu) mặc định checked (excluded_pantry_ids = []) và cập nhật đúng khi bỏ chọn', async () => {
    const user = userEvent.setup();
    const onRecommend = vi.fn();
    render(<StatefulKitchenHarness onRecommend={onRecommend} />);

    // Kiểm tra đủ 5 gia vị cơ bản hiển thị và mặc định đều được checked
    const pantrySlugs = ['muoi', 'duong', 'nuoc-mam', 'dau-an', 'hat-tieu'];
    for (const slug of pantrySlugs) {
      const label = screen.getByTestId(`pantry-toggle-${slug}`);
      const checkbox = label.querySelector('input[type="checkbox"]');
      expect(checkbox).toBeChecked();
    }

    // Chọn 1 nguyên liệu chính (Cà chua)
    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item-ca-chua')).toBeInTheDocument();
    });
    await user.click(screen.getByTestId('suggestion-item-ca-chua'));

    // Bỏ chọn "Nước mắm" và "Hạt tiêu"
    await user.click(screen.getByTestId('pantry-toggle-nuoc-mam'));
    await user.click(screen.getByTestId('pantry-toggle-hat-tieu'));

    // Gửi Gợi ý món ăn -> kiểm tra excluded_pantry_ids chứa đúng 2 UUID của Nước mắm và Hạt tiêu
    await user.click(screen.getByTestId('recommend-submit-btn'));
    expect(onRecommend).toHaveBeenCalledWith({
      ingredient_ids: ['11111111-1111-4111-8111-000000000002'],
      excluded_pantry_ids: [
        '22222222-2222-4222-8222-000000000003', // Nước mắm
        '22222222-2222-4222-8222-000000000005', // Hạt tiêu
      ],
    });
  });
});
