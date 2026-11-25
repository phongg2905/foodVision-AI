/**
 * Bộ tiện ích chuẩn hóa chuỗi tiếng Việt không dấu và đối chiếu từ đồng nghĩa vùng miền (ADR-004, FR-18, AC-07).
 * Đồng bộ 1-1 khóa slug với backend/app/core/seed_fixtures.py & supabase/seed.sql.
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
 * Bảng từ đồng nghĩa vùng miền chuẩn theo ADR-004 (key: slug chuẩn của nguyên liệu trên Backend).
 */
export const REGIONAL_INGREDIENT_ALIASES: Record<string, string[]> = {
  'ca-chua': ['cà chua đỏ', 'ca chua do', 'tomato'],
  'trung-ga': ['trứng', 'trung', 'hột gà', 'hot ga', 'egg'],
  'dau-hu': ['đậu phụ', 'dau phu', 'tàu hũ', 'tau hu', 'đậu khuôn', 'dau khuon', 'tofu'],
  'thit-ba-chi': ['thịt ba rọi', 'thit ba roi', 'thịt heo ba chỉ', 'ba chỉ heo'],
  'hanh-la': ['hành hoa', 'hanh hoa', 'hành tươi'],
  'muoi': ['muối ăn', 'muối tinh'],
  'nuoc-mam': ['nước mắm truyền thống'],
  'dau-an': ['dầu thực vật'],
  'duong': ['đường cát', 'đường trắng'],
  'tieu-xay': ['hạt tiêu', 'hat tieu', 'tiêu đen', 'tieu den'],
  'khoai-tay': ['potato'],
  'ca-rot': ['củ cải đỏ', 'carrot'],
  'hanh-tay': ['củ hành tây', 'cu hanh tay', 'onion'],
  'toi': ['tỏi ta', 'tỏi khô', 'toi kho', 'tỏi tép', 'garlic'],
  'ot': ['ớt hiểm', 'ớt cay', 'chili pepper'],
  'dua-leo': ['dưa chuột', 'dua chuot', 'cucumber'],
  'bap-cai': ['cải bắp', 'cai bap', 'cabbage'],
  'bong-cai-xanh': ['súp lơ xanh', 'sup lo xanh', 'bông cải', 'broccoli'],
  'nam': ['nấm mỡ', 'nấm rơm', 'mushroom'],
  'thit-ga-song': ['thịt gà', 'thit ga', 'ức gà', 'uc ga', 'gà phi lê', 'chicken'],
  'thit-heo-song': ['thịt lợn', 'thit lon', 'thịt heo', 'thit heo', 'heo', 'lợn', 'pork'],
  'tom': ['tôm tươi', 'tom tuoi', 'tôm sú', 'tôm thẻ', 'tôm', 'shrimp'],
  'ca-nguyen-con': ['cá tươi', 'ca tuoi', 'fish'],
  'gung': ['gừng tươi', 'ginger'],
  'ot-chuong': ['ớt ngọt', 'ớt đà lạt', 'ot da lat', 'bell pepper'],
  'bap-ngot': ['ngô ngọt', 'ngo ngot', 'ngô', 'ngo', 'bắp', 'bap', 'bắp mỹ', 'sweet corn'],
  'thit-bo': ['thịt bò tươi', 'bò thăn', 'bò', 'bo', 'beef'],
  'mi-y': ['mì spaghetti', 'spaghetti', 'pasta'],
  'bo-lat': ['bơ nhạt', 'bo nhat', 'unsalted butter', 'butter'],
  'pho-mai-cheddar': ['phô mai lát', 'cheddar cheese', 'cheese'],
  'banh-mi-burger': ['bánh mì burger', 'burger bun'],
  'xa-lach': ['xà lách', 'lettuce'],
  'sa': ['củ sả', 'sả cây', 'sả băm', 'lemongrass'],
  'nghe': ['nghệ', 'củ nghệ', 'bột nghệ', 'turmeric'],
  'la-chanh': ['lá chanh tươi', 'lime leaf', 'kaffir lime leaf'],
  'hanh-tim': ['củ hành tím', 'hành khô', 'shallot'],
  'chanh': ['quả chanh', 'chanh ta', 'lime'],
  'rau-muong': ['rau muống nước', 'water spinach'],
  'cai-thia': ['cải chíp', 'cai chip', 'cải bẹ trắng', 'bok choy'],
  'bi-do': ['bí ngô', 'bi ngo', 'bí rợ', 'bi ro', 'pumpkin'],
  'muc-tuoi': ['mực ống', 'mực lá', 'squid'],
};

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
