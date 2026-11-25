import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { RecipeDetailView } from '../RecipeDetailView';

const EXPECTED_DISCLAIMER =
  'Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu (ước tính khi có khối lượng chuẩn), không suy diễn từ ảnh chụp, không thay thế tư vấn y tế và người dùng cần tự kiểm tra thành phần dị ứng thực phẩm.';

describe('RecipeDetailView (FR-02, FR-08, BR-03, BR-05, TC-03, TC-15, DEF-09, F5)', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('TC-03 & BR-05: Hiển thị sơ chế, nấu & chờ, tổng thời gian, tách nguyên liệu/gia vị pantry và các bước chế biến', async () => {
    const onBack = vi.fn();
    render(
      <RecipeDetailView
        recipeId="22222222-2222-4222-8222-222222222201"
        backLabel="Quay lại Danh mục công thức"
        onBack={onBack}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: 'Đậu hũ sốt cà chua' })
      ).toBeInTheDocument();
    });

    const timeStrip = screen.getByTestId('recipe-time-strip');
    expect(timeStrip).toHaveTextContent('10');
    expect(timeStrip).toHaveTextContent('20');
    expect(timeStrip).toHaveTextContent('30');

    expect(screen.getByTestId('cook-time-br05-note')).toHaveTextContent(
      'bao gồm cả thời gian ướp và chờ chế biến'
    );

    const mainList = screen.getByTestId('recipe-main-ingredients');
    const pantryList = screen.getByTestId('recipe-pantry-ingredients');
    expect(within(mainList).getByText('Đậu hũ')).toBeInTheDocument();
    expect(within(mainList).getByText('Cà chua')).toBeInTheDocument();
    expect(within(mainList).queryByText('Muối')).not.toBeInTheDocument();

    expect(within(pantryList).getByText('Muối')).toBeInTheDocument();
    expect(within(pantryList).getByText('Dầu ăn')).toBeInTheDocument();
    expect(within(pantryList).queryByText('Đậu hũ')).not.toBeInTheDocument();

    const stepsList = screen.getByTestId('recipe-steps-list');
    expect(stepsList.querySelectorAll('li')).toHaveLength(2);
    expect(stepsList).toHaveTextContent('Cắt đậu hũ thành miếng vuông vừa ăn');

    expect(screen.getByTestId('recipe-source-footer')).toHaveTextContent(
      'CC-BY-4.0'
    );
  });

  it('TC-15: Hiển thị nhãn dinh dưỡng định tính Tầng 1 kèm source_urls, hỗ trợ món chưa có tag, không bịa kcal trong Tầng 1 và giữ nguyên BR-03', async () => {
    const { rerender } = render(
      <RecipeDetailView
        recipeId="22222222-2222-4222-8222-222222222201"
        backLabel="Quay lại"
        onBack={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByTestId('nutrition-tag-HIGH_PROTEIN_PLANT')
      ).toBeInTheDocument();
    });

    const sourceLink = screen.getByRole('link', { name: /Tham khảo #1/i });
    expect(sourceLink).toHaveAttribute('href', 'https://fdc.nal.usda.gov/');
    expect(sourceLink).toHaveAttribute('target', '_blank');

    const nutritionSection = screen.getByTestId('nutrition-evidence-section');
    expect(nutritionSection.textContent).not.toMatch(/\d+\s*kcal/i);
    expect(screen.getByTestId('nutrition-disclaimer')).toHaveTextContent(
      EXPECTED_DISCLAIMER
    );

    // Chuyển sang món chưa có nhãn dinh dưỡng định tính (Bắp ngọt áp chảo bơ tỏi kiểu Mỹ - 2219)
    rerender(
      <RecipeDetailView
        recipeId="22222222-2222-4222-8222-222222222219"
        backLabel="Quay lại"
        onBack={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('nutrition-empty-note')).toBeInTheDocument();
    });
    expect(screen.getByTestId('nutrition-disclaimer')).toHaveTextContent(
      EXPECTED_DISCLAIMER
    );
  });

  it('DEF-09, ADR-004 & F5: Quy đổi khẩu phần (2 -> 4 người) nhân đôi kcal + grams kèm scaling_warning_vi, và ẩn hoàn toàn khối USDA khi usda_nutrition == null', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <RecipeDetailView
        recipeId="22222222-2222-4222-8222-222222222201"
        backLabel="Quay lại"
        onBack={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('usda-nutrition-section')).toBeInTheDocument();
    });

    // Khẩu phần gốc 2 người: kcal = 316.4, Đậu hũ = 2 bìa (200g), chưa có cảnh báo nhân khẩu phần
    expect(screen.getByTestId('usda-kcal-value')).toHaveTextContent('316.4');
    expect(screen.getByTestId('usda-protein-value')).toHaveTextContent(
      '17.75g'
    );
    expect(
      screen.getByTestId('ingredient-qty-11111111-1111-4111-8111-111111111103')
    ).toHaveTextContent('2 bìa (200g)');
    expect(
      screen.queryByTestId('usda-scaling-warning')
    ).not.toBeInTheDocument();

    // Đổi khẩu phần từ 2 sang 4 người -> kcal nhân đôi = 632.8, Đậu hũ = 400g, xuất hiện scaling_warning_vi
    await user.selectOptions(screen.getByTestId('servings-selector'), '4');

    await waitFor(() => {
      expect(screen.getByTestId('usda-kcal-value')).toHaveTextContent('632.8');
    });
    expect(screen.getByTestId('usda-protein-value')).toHaveTextContent('35.5g');
    expect(
      screen.getByTestId('ingredient-qty-11111111-1111-4111-8111-111111111103')
    ).toHaveTextContent('400g');
    expect(screen.getByTestId('usda-scaling-warning')).toHaveTextContent(
      'không tăng/giảm tuyến tính hoàn toàn'
    );

    // Chuyển sang công thức chưa có dữ liệu USDA (Mì Ý sốt cà chua thịt băm - 2205) -> ẩn hoàn toàn khối USDA (ADR-004)
    rerender(
      <RecipeDetailView
        recipeId="22222222-2222-4222-8222-222222222205"
        backLabel="Quay lại"
        onBack={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: 'Mì Ý sốt cà chua thịt băm' })
      ).toBeInTheDocument();
    });
    expect(
      screen.queryByTestId('usda-nutrition-section')
    ).not.toBeInTheDocument();
  });

  it('TC-03 (404): Hiển thị thông báo lỗi thân thiện khi công thức không tồn tại', async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();

    render(
      <RecipeDetailView
        recipeId="00000000-0000-0000-0000-000000000000"
        backLabel="Quay lại Danh sách gợi ý"
        onBack={onBack}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('recipe-detail-error')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('recipe-detail-back-btn'));
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});
