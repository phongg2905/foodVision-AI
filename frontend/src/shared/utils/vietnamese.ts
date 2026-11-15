/**
 * Bộ tiện ích chuẩn hóa chuỗi tiếng Việt không dấu và đối chiếu từ đồng nghĩa vùng miền (ADR-004, FR-18, AC-07).
 */

/**
 * Chuẩn hóa chuỗi tiếng Việt về chữ thường không dấu, gộp khoảng trắng thừa.
 * Ví dụ: "Đậu Hũ / Đậu Phụ" -> "dau hu / dau phu"
 */
export function normalizeVietnamese(input: string): string {
  if (!input) return '';
  return input
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Bảng từ đồng nghĩa vùng miền chuẩn theo ADR-004 (key: slug của nguyên liệu chuẩn).
 */
export const REGIONAL_INGREDIENT_ALIASES: Record<string, string[]> = {
  'dau-hu': ['đậu phụ', 'dau phu', 'tàu hũ', 'tau hu', 'đậu khuôn', 'dau khuon', 'tofu'],
  'bap': ['ngô', 'ngo', 'bắp mỹ', 'bap my', 'bắp ngọt', 'bap ngot', 'ngô ngọt'],
  'dua-leo': ['dưa chuột', 'dua chuot'],
  'thit-heo': ['thịt lợn', 'thit lon', 'thịt ba chỉ', 'thit ba chi', 'heo', 'lợn'],
  'ca-chua': ['cà chua đỏ', 'ca chua do', 'tomato'],
  'trung-ga': ['trứng', 'trung', 'hột gà', 'hot ga'],
  'hanh-la': ['hành hoa', 'hanh hoa', 'hành tươi'],
  'hanh-tay': ['củ hành tây', 'cu hanh tay', 'onion'],
  'toi': ['tỏi khô', 'toi kho', 'tỏi tép'],
  'thom': ['dứa', 'dua', 'khóm', 'khom'],
  'thit-bo': ['bò', 'bo', 'thịt bò thăn'],
  'uc-ga': ['thịt gà', 'thit ga', 'gà phi lê'],
  'tom-tuoi': ['tôm', 'tom', 'tôm sú', 'tôm thẻ'],
  'bong-cai-xanh': ['súp lơ xanh', 'sup lo xanh', 'bông cải'],
};

/**
 * Kiểm tra xem một nguyên liệu (với name_vi và slug) có khớp với từ khóa tìm kiếm tiếng Việt
 * (hỗ trợ có dấu, không dấu và từ đồng nghĩa vùng miền) hay không.
 */
export function matchesIngredientQuery(
  ingredient: { slug: string; name_vi: string },
  rawQuery: string
): boolean {
  const normalizedQuery = normalizeVietnamese(rawQuery);
  if (!normalizedQuery) return true;

  const normalizedName = normalizeVietnamese(ingredient.name_vi);
  const normalizedSlug = ingredient.slug.replace(/-/g, ' ').toLowerCase();

  if (
    normalizedName.includes(normalizedQuery) ||
    normalizedSlug.includes(normalizedQuery)
  ) {
    return true;
  }

  const aliases = REGIONAL_INGREDIENT_ALIASES[ingredient.slug] ?? [];
  return aliases.some((alias) =>
    normalizeVietnamese(alias).includes(normalizedQuery)
  );
}

/**
 * Tìm tên đồng nghĩa vùng miền tiêu biểu để hiển thị gợi ý phụ cho người dùng dễ nhận biết.
 */
export function getMatchedAliasHint(
  slug: string,
  rawQuery: string
): string | null {
  const normalizedQuery = normalizeVietnamese(rawQuery);
  if (!normalizedQuery) return null;

  const aliases = REGIONAL_INGREDIENT_ALIASES[slug] ?? [];
  const matched = aliases.find(
    (alias) =>
      alias.includes(' ') &&
      normalizeVietnamese(alias).includes(normalizedQuery)
  );
  return matched ?? aliases[0] ?? null;
}
