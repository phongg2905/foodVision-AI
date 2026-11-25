import React, { useState } from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  MOCK_ALL_INGREDIENTS,
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
      knownCatalogIngredients={MOCK_ALL_INGREDIENTS}
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

describe('RecommendationResultsView (FR-06, FR-07, TC-09..TC-14, TC-32..TC-35, F1, F3)', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('TC-09: Hiển thị hướng dẫn chọn nguyên liệu khi danh sách rỗng', () => {
    const onBack = vi.fn();
    render(<Harness initialIngredients={[]} onBack={onBack} />);
    expect(
      screen.getByTestId('recommend-requires-ingredient')
    ).toBeInTheDocument();
  });

  it('TC-10, TC-11, TC-12 & F1: Tách bạch nhóm "Nấu được ngay" (ready) trước "Còn thiếu nguyên liệu" (missing) và hiển thị đúng tên tiếng Việt không bị lỗi "Nguyên liệu (111111)"', async () => {
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
      within(missingSection).getByText('Canh cà chua trứng')
    ).toBeInTheDocument();
    expect(
      within(missingSection).getByTestId(
        'missing-ingredients-canh-ca-chua-trung'
      )
    ).toHaveTextContent('Thiếu: Trứng gà');
    expect(missingSection.textContent).not.toContain('Nguyên liệu (111111)');
  });

  it('TC-32: Bỏ chọn gia vị bắt buộc Nước mắm (excluded_pantry_ids) chuyển Trứng xào cà chua sang "Còn thiếu nguyên liệu" và báo thiếu Nước mắm', async () => {
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
      within(missingSection).getByText('Trứng xào cà chua')
    ).toBeInTheDocument();
    expect(
      within(missingSection).getByTestId(
        'missing-ingredients-trung-xao-ca-chua'
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

    // Chọn thời gian mong muốn 15 phút (0.25h) cho món 30 phút (0.5h) -> T = 0.25 / 0.5 = 0.5 -> đóng góp 7.5
    await user.click(screen.getByTestId('quick-desired-time-15'));

    await waitFor(() => {
      expect(
        screen.getByTestId('score-xai-dau-hu-sot-ca-chua')
      ).toHaveTextContent('7.5');
    });

    // Ưu tiên Đậu hũ làm món chính -> G = 0.85 -> 21.25 -> tổng = 50.0 + 21.25 + 7.5 + 5.0 = 83.75
    await user.click(screen.getByTestId('quick-main-dau-hu'));

    await waitFor(() => {
      expect(
        screen.getByTestId('recommendation-score-dau-hu-sot-ca-chua')
      ).toHaveTextContent('83.75 điểm');
    });

    // Nhập thời gian tùy chỉnh 20 phút (0.3333h) cho món 30 phút (0.5h) -> T = 20/30 = 0.6667 -> đóng góp 10.0
    const customTimeInput = screen.getByTestId(
      'quick-desired-time-custom-input'
    );
    await user.type(customTimeInput, '20');
    await waitFor(() => {
      expect(
        screen.getByTestId('score-xai-dau-hu-sot-ca-chua')
      ).toHaveTextContent('10.0');
    });
  });

  it('TC-13, TC-14, TC-33, TC-34, DEF-10: Lọc ẩm thực, thời gian tối đa, chỉ hiện món nấu ngay, MMR và trạng thái rỗng', async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await waitFor(() => {
      expect(
        screen.getByTestId('recommendation-card-mi-y-sot-ca-chua-thit-bam')
      ).toBeInTheDocument();
    });

    // TC-13: Lọc Món Việt -> ẩn món EU
    await user.click(screen.getByTestId('filter-cuisine-VN'));
    await waitFor(() => {
      expect(
        screen.queryByTestId('recommendation-card-mi-y-sot-ca-chua-thit-bam')
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

    // TC-14 & TC-34: Chọn <= 15 phút (món Đậu hũ sốt cà chua tốn 30p nên bị loại, còn 0 món ready)
    await user.selectOptions(screen.getByTestId('filter-max-minutes'), '15');
    await waitFor(() => {
      expect(
        screen.getByTestId('recommendations-empty-state')
      ).toBeInTheDocument();
    });
  });

  it('F3: Không nuốt lỗi HTTP 500 có JSON ErrorResponse chuẩn sang dữ liệu mock và không gọi thừa API khi chỉ đổi tham chiếu mảng', async () => {
    import.meta.env.VITE_API_MOCK_MODE = 'false';
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          code: 'INTERNAL_ERROR',
          message: 'Lỗi kết nối cơ sở dữ liệu khi xếp hạng công thức.',
          request_id: 'req-500-audit-f3',
        }),
        {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        }
      )
    );

    const { rerender } = render(
      <Harness initialIngredients={[findIng('dau-hu'), findIng('ca-chua')]} />
    );

    await waitFor(() => {
      expect(
        screen.getByTestId('recommendations-error-alert')
      ).toHaveTextContent('Lỗi kết nối cơ sở dữ liệu khi xếp hạng công thức.');
    });

    // Tuyệt đối không nuốt lỗi 500 sang mock card
    expect(
      screen.queryByTestId('recommendation-card-dau-hu-sot-ca-chua')
    ).not.toBeInTheDocument();
    expect(
      screen.getByTestId('recommendations-retry-btn')
    ).toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    // Rerender với mảng mới cùng bộ UUID -> không được gọi lại API nhờ khóa primitive
    rerender(
      <Harness initialIngredients={[findIng('dau-hu'), findIng('ca-chua')]} />
    );
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});
