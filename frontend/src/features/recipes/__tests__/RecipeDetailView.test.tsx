import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { RecipeDetailView } from '../RecipeDetailView';

const EXPECTED_DISCLAIMER =
  'Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu (ước tính khi có khối lượng chuẩn), không suy diễn từ ảnh chụp, không thay thế tư vấn y tế và người dùng cần tự kiểm tra thành phần dị ứng thực phẩm.';

describe('RecipeDetailView (FR-02, FR-08, BR-03, BR-05, TC-03, TC-15)', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
  });

  it('TC-03 & BR-05: Hiển thị sơ chế, nấu & chờ, tổng thời gian, tách nguyên liệu/gia vị pantry và các bước chế biến', async () => {
    const onBack = vi.fn();
    render(
      <RecipeDetailView
        recipeId="a1111111-1111-4111-8111-000000000002"
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
    expect(timeStrip).toHaveTextContent('15');
    expect(timeStrip).toHaveTextContent('25');

    expect(screen.getByTestId('cook-time-br05-note')).toHaveTextContent(
      'bao gồm cả thời gian ướp và chờ chế biến'
    );

    // Tách bạch nguyên liệu và gia vị pantry
    const mainList = screen.getByTestId('recipe-main-ingredients');
    const pantryList = screen.getByTestId('recipe-pantry-ingredients');
    expect(within(mainList).getByText('Đậu hũ')).toBeInTheDocument();
    expect(within(mainList).getByText('Cà chua')).toBeInTheDocument();
    expect(within(mainList).queryByText('Muối')).not.toBeInTheDocument();

    expect(within(pantryList).getByText('Muối')).toBeInTheDocument();
    expect(within(pantryList).getByText('Dầu ăn')).toBeInTheDocument();
    expect(within(pantryList).queryByText('Đậu hũ')).not.toBeInTheDocument();

    // Các bước chế biến đánh số thứ tự
    const stepsList = screen.getByTestId('recipe-steps-list');
    expect(stepsList.querySelectorAll('li')).toHaveLength(3);
    expect(stepsList).toHaveTextContent('Thấm khô đậu hũ');

    // Nguồn & giấy phép
    expect(screen.getByTestId('recipe-source-footer')).toHaveTextContent(
      'CC-BY-4.0'
    );
  });

  it('TC-15: Hiển thị nhãn dinh dưỡng định tính kèm source_urls, hỗ trợ món chưa có tag, không bịa kcal/gram và hiển thị nguyên văn BR-03', async () => {
    const { rerender } = render(
      <RecipeDetailView
        recipeId="a1111111-1111-4111-8111-000000000002"
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

    // Chuyển sang món chưa có nhãn dinh dưỡng định tính (Bắp ngọt xào bơ tỏi kiểu Mỹ)
    rerender(
      <RecipeDetailView
        recipeId="a1111111-1111-4111-8111-000000000007"
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
