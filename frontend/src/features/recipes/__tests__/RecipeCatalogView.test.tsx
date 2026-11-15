import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { RecipeCatalogView } from '../RecipeCatalogView';

describe('RecipeCatalogView (FR-01, AC-01, AC-02)', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
  });

  it('AC-01: Hiển thị danh sách công thức và lọc theo nền ẩm thực (cuisine_code) & thời gian tối đa (max_total_minutes)', async () => {
    const user = userEvent.setup();
    render(<RecipeCatalogView />);

    // Chờ danh sách công thức ban đầu được tải
    await waitFor(() => {
      expect(
        screen.getByText('Canh cà chua trứng (Canh mây)')
      ).toBeInTheDocument();
    });

    // Chọn bộ lọc Món Âu (EU) trực tiếp trên thanh lọc 4 cột Seatwave
    await user.selectOptions(screen.getByLabelText('Chọn nền ẩm thực'), 'EU');

    await waitFor(() => {
      expect(
        screen.getByText('Salad dưa leo cà chua kiểu Âu')
      ).toBeInTheDocument();
      expect(
        screen.queryByText('Canh cà chua trứng (Canh mây)')
      ).not.toBeInTheDocument();
    });

    // Chọn tiếp thời gian tối đa <= 15 phút trên thanh lọc 4 cột Seatwave
    await user.selectOptions(
      screen.getByLabelText('Chọn thời gian nấu tối đa'),
      '15'
    );

    await waitFor(() => {
      expect(
        screen.getByText('Salad dưa leo cà chua kiểu Âu')
      ).toBeInTheDocument();
      // Món Ức gà áp chảo (25 phút) phải bị ẩn
      expect(
        screen.queryByText('Ức gà áp chảo sốt bơ tỏi')
      ).not.toBeInTheDocument();
    });
  });

  it('AC-02: Tìm kiếm từ khóa tiếng Việt không dấu và hiển thị trạng thái rỗng kèm nút Xóa bộ lọc', async () => {
    const user = userEvent.setup();
    render(<RecipeCatalogView />);

    await waitFor(() => {
      expect(
        screen.getByText('Canh cà chua trứng (Canh mây)')
      ).toBeInTheDocument();
    });

    const searchInput = screen.getByLabelText('Tìm tên món ăn');

    // Nhập từ khóa không dấu "bo luc lac"
    await user.type(searchInput, 'bo luc lac');

    await waitFor(() => {
      expect(screen.getByText('Bò lúc lắc xào hành tây')).toBeInTheDocument();
      expect(
        screen.queryByText('Canh cà chua trứng (Canh mây)')
      ).not.toBeInTheDocument();
    });

    // Nhập từ khóa không khớp bất kỳ công thức nào
    await user.clear(searchInput);
    await user.type(searchInput, 'mon an khong ton tai xyz');

    await waitFor(() => {
      expect(screen.getByTestId('recipes-empty-state')).toBeInTheDocument();
      expect(
        screen.getByText('Không tìm thấy công thức phù hợp')
      ).toBeInTheDocument();
    });

    // Nhấn nút Xóa bộ lọc ở màn hình trống để khôi phục danh sách
    const resetButtons = screen.getAllByRole('button', { name: /Xóa bộ lọc/i });
    await user.click(resetButtons[resetButtons.length - 1]);

    await waitFor(() => {
      expect(
        screen.getByText('Canh cà chua trứng (Canh mây)')
      ).toBeInTheDocument();
    });
  });
});
