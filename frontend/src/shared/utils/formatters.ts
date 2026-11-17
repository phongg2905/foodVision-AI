/**
 * Định dạng điểm MCDA thống nhất giữa thẻ gợi ý và trang chi tiết công thức.
 * Luôn giữ tối thiểu 1 chữ số thập phân (VD: 90 -> "90.0", 89.37 -> "89.37").
 */
export function formatScoreValue(value: number): string {
  const rounded = Math.round(value * 100) / 100;
  return Number.isInteger(rounded * 10)
    ? rounded.toFixed(1)
    : rounded.toFixed(2);
}
