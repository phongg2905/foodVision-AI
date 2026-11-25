import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { RecipeCatalogView } from '../RecipeCatalogView';

describe('RecipeCatalogView (FR-01, AC-01, AC-02, F1)', () => {
  beforeEach(() => {
    import.meta.env.VITE_API_MOCK_MODE = 'true';
  });

  it('AC-01: Hiển thị danh sách công thức chuẩn Backend và lọc theo nền ẩm thực (cuisine_code) & thời gian tối đa (max_total_minutes)', async () => {
    const user = userEvent.setup();
    render(<RecipeCatalogView />);

    await waitFor(() => {
      expect(screen.getByText('Canh cà chua trứng')).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByLabelText('Chọn nền ẩm thực'), 'EU');

    await waitFor(() => {
      expect(
        screen.getByText('Bông cải xanh và nấm áp chảo bơ tỏi')
      ).toBeInTheDocument();
      expect(screen.getByText('Mì Ý sốt cà chua thịt băm')).toBeInTheDocument();
      expect(screen.queryByText('Canh cà chua trứng')).not.toBeInTheDocument();
    });

    await user.selectOptions(
      screen.getByLabelText('Chọn thời gian nấu tối đa'),
      '15'
    );

    await waitFor(() => {
      expect(
        screen.getByText('Bông cải xanh và nấm áp chảo bơ tỏi')
      ).toBeInTheDocument();
      expect(
        screen.queryByText('Mì Ý sốt cà chua thịt băm')
      ).not.toBeInTheDocument();
    });
  });

  it('AC-02: Tìm kiếm từ khóa tiếng Việt không dấu và hiển thị trạng thái rỗng kèm nút Xóa bộ lọc', async () => {
    const user = userEvent.setup();
    render(<RecipeCatalogView />);

    await waitFor(() => {
      expect(screen.getByText('Canh cà chua trứng')).toBeInTheDocument();
    });

    const searchInput = screen.getByLabelText('Tìm tên món ăn');

    await user.type(searchInput, 'mi y sot ca chua');

    await waitFor(() => {
      expect(screen.getByText('Mì Ý sốt cà chua thịt băm')).toBeInTheDocument();
      expect(screen.queryByText('Canh cà chua trứng')).not.toBeInTheDocument();
    });

    await user.clear(searchInput);
    await user.type(searchInput, 'mon an khong ton tai xyz');

    await waitFor(() => {
      expect(screen.getByTestId('recipes-empty-state')).toBeInTheDocument();
      expect(
        screen.getByText('Không tìm thấy công thức phù hợp')
      ).toBeInTheDocument();
    });

    const resetButtons = screen.getAllByRole('button', { name: /Xóa bộ lọc/i });
    await user.click(resetButtons[resetButtons.length - 1]);

    await waitFor(() => {
      expect(screen.getByText('Canh cà chua trứng')).toBeInTheDocument();
    });
  });
});
