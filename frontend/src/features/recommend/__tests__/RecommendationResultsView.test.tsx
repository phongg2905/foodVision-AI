import React, { useState } from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  MOCK_MAIN_INGREDIENTS,
  MOCK_PANTRY_INGREDIENTS,
} from '../../../shared/api/mockData';
import { Ingredient, RecommendationItem } from '../../../shared/api/types';
import { RecommendationResultsView } from '../RecommendationResultsView';

const findIng = (slug: string): Ingredient => {
  const found = MOCK_MAIN_INGREDIENTS.find((item) => item.slug === slug);
  if (!found) throw new Error(`Missing mock ingredient ${slug}`);
  return found;
};

const findPantryId = (slug: string): string => {
  const found = MOCK_PANTRY_INGREDIENTS.find((item) => item.slug === slug);
  if (!found) throw new Error(`Missing pantry ${slug}`);
  return found.id;
};

const Harness: React.FC<{
  initialIngredients?: Ingredient[];
  initialExcludedPantry?: string[];
  initialMainIds?: string[];
  initialDesiredMinutes?: number | null;
  onSelectRecipe?: (id: string, item: RecommendationItem) => void;
  onBack?: () => void;
}> = ({
  initialIngredients = [findIng('dau-hu'), findIng('ca-chua')],
  initialExcludedPantry = [],
  initialMainIds = [],
  initialDesiredMinutes = null,
  onSelectRecipe = vi.fn(),
  onBack = vi.fn(),
}) => {
  const [mainIds, setMainIds] = useState<string[]>(initialMainIds);
  const [desiredMinutes, setDesiredMinutes] = useState<number | null>(
    initialDesiredMinutes
  );

  return (
    <RecommendationResultsView
      selectedIngredients={initialIngredients}
      excludedPantryIds={initialExcludedPantry}
      mainIngredientIds={mainIds}
      onMainIngredientIdsChange={setMainIds}
      desiredMinutes={desiredMinutes}
      onDesiredMinutesChange={setDesiredMinutes}
      onBackToKitchen={onBack}
      onSelectRecipe={onSelectRecipe}
    />
  );
};

describe('RecommendationResultsView (FR-06, FR-07, TC-09..TC-14, TC-32..TC-35)', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
  });

  it('TC-09: Hiển thị hướng dẫn chọn nguyên liệu khi danh sách rỗng', () => {
    const onBack = vi.fn();
    render(<Harness initialIngredients={[]} onBack={onBack} />);
    expect(
      screen.getByTestId('recommend-requires-ingredient')
    ).toBeInTheDocument();
  });

  it('TC-10, TC-11, TC-12: Tách bạch nhóm "Nấu được ngay" (ready) trước "Còn thiếu nguyên liệu" (missing) kèm nguyên liệu khớp/thiếu', async () => {
    render(<Harness />);

    await waitFor(() => {
      expect(screen.getByTestId('recommend-ready-section')).toBeInTheDocument();
    });

    const readySection = screen.getByTestId('recommend-ready-section');
    const missingSection = screen.getByTestId('recommend-missing-section');

    expect(
      within(readySection).getByText('Đậu hũ sốt cà chua')
    ).toBeInTheDocument();
    expect(
      within(readySection).getByTestId('availability-badge-dau-hu-sot-ca-chua')
    ).toHaveTextContent('Nấu được ngay');

    expect(
      within(missingSection).getByText('Canh cà chua trứng (Canh mây)')
    ).toBeInTheDocument();
    expect(
      within(missingSection).getByTestId(
        'missing-ingredients-canh-ca-chua-trung'
      )
    ).toHaveTextContent('Thiếu: Trứng gà');
  });

  it('TC-32: Bỏ chọn gia vị bắt buộc Nước mắm (excluded_pantry_ids) chuyển Canh cà chua trứng sang "Còn thiếu nguyên liệu" và báo thiếu Nước mắm', async () => {
    render(
      <Harness
        initialIngredients={[findIng('ca-chua'), findIng('trung-ga')]}
        initialExcludedPantry={[findPantryId('nuoc-mam')]}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByTestId('recommend-missing-section')
      ).toBeInTheDocument();
    });

    const missingSection = screen.getByTestId('recommend-missing-section');
    expect(
      within(missingSection).getByText('Canh cà chua trứng (Canh mây)')
    ).toBeInTheDocument();
    expect(
      within(missingSection).getByTestId(
        'missing-ingredients-canh-ca-chua-trung'
      )
    ).toHaveTextContent('Thiếu: Nước mắm');
  });

  it('TC-35: Chọn nguyên liệu chính ưu tiên (main_ingredient_ids) và thời gian mong muốn (15 phút -> 0.25h) cập nhật điểm MCDA XAI', async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await waitFor(() => {
      expect(
        screen.getByTestId('score-xai-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });

    // Ban đầu chưa chọn món chính & desired_hours mặc định 100.0 -> Thời gian đạt tối đa 15.0
    expect(
      screen.getByTestId('score-xai-dau-hu-sot-ca-chua')
    ).toHaveTextContent('15.0');

    // Chọn thời gian mong muốn 15 phút (0.25h) cho món 25 phút -> T = 0.25 / (25/60) = 0.6 -> đóng góp 9.0
    await user.click(screen.getByTestId('quick-desired-time-15'));

    await waitFor(() => {
      expect(
        screen.getByTestId('score-xai-dau-hu-sot-ca-chua')
      ).toHaveTextContent('9.0');
    });

    // Ưu tiên Đậu hũ làm món chính -> G = 0.85 -> 21.25 -> tổng = 50.0 + 21.25 + 9.0 + 5.0 = 85.25
    await user.click(screen.getByTestId('quick-main-dau-hu'));

    await waitFor(() => {
      expect(
        screen.getByTestId('recommendation-score-dau-hu-sot-ca-chua')
      ).toHaveTextContent('85.25 điểm');
    });

    // Nhập thời gian tùy chỉnh 20 phút (0.3333h) cho món 25 phút -> T = 20/25 = 0.8 -> đóng góp 12.0
    const customTimeInput = screen.getByTestId('quick-desired-time-custom-input');
    await user.type(customTimeInput, '20');
    await waitFor(() => {
      expect(
        screen.getByTestId('score-xai-dau-hu-sot-ca-chua')
      ).toHaveTextContent('12.0');
    });
  });

  it('TC-13, TC-14, TC-33, TC-34, DEF-10: Lọc ẩm thực, thời gian tối đa, chỉ hiện món nấu ngay, MMR và trạng thái rỗng', async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await waitFor(() => {
      expect(
        screen.getByTestId('recommendation-card-salad-dua-leo-ca-chua-kieu-au')
      ).toBeInTheDocument();
    });

    // TC-13: Lọc Món Việt -> ẩn món EU
    await user.click(screen.getByTestId('filter-cuisine-VN'));
    await waitFor(() => {
      expect(
        screen.queryByTestId(
          'recommendation-card-salad-dua-leo-ca-chua-kieu-au'
        )
      ).not.toBeInTheDocument();
    });

    // TC-33: Bật "Chỉ hiện món nấu được ngay" -> ẩn toàn bộ section missing
    await user.click(screen.getByTestId('toggle-only-ready'));
    await waitFor(() => {
      expect(
        screen.queryByTestId('recommend-missing-section')
      ).not.toBeInTheDocument();
      expect(
        screen.getByTestId('recommendation-card-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });

    // DEF-10: Bật đa dạng hóa thực đơn MMR vẫn giữ an toàn ready-only
    await user.click(screen.getByTestId('toggle-mmr-diversify'));
    await waitFor(() => {
      expect(
        screen.getByTestId('recommendation-card-dau-hu-sot-ca-chua')
      ).toBeInTheDocument();
    });

    // TC-14 & TC-34: Chọn <= 15 phút (món Đậu hũ sốt cà chua tốn 25p nên bị loại, còn 0 món ready)
    await user.selectOptions(screen.getByTestId('filter-max-minutes'), '15');
    await waitFor(() => {
      expect(
        screen.getByTestId('recommendations-empty-state')
      ).toBeInTheDocument();
    });
  });
});
