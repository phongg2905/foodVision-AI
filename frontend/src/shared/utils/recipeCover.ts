/**
 * Ảnh món ăn dự phòng theo slug chuẩn Backend (20 công thức trong seed_fixtures.py & seed.sql)
 * khi bản ghi trả về từ API chưa có cover_image_url (null).
 * Ưu tiên tuyệt đối cover_image_url thật từ API nếu có.
 */
const COVER_FALLBACK_BY_SLUG: Record<string, string> = {
  'dau-hu-sot-ca-chua':
    'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80',
  'canh-ca-chua-trung':
    'https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=800&q=80',
  'thit-kho-trung':
    'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80',
  'trung-xao-ca-chua':
    'https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=800&q=80',
  'mi-y-sot-ca-chua-thit-bam':
    'https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=800&q=80',
  'bong-cai-xanh-nam-ap-chao-bo-toi':
    'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80',
  'burger-bo-pho-mai-kieu-my':
    'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=800&q=80',
  'bap-ngot-khoai-tay-dut-lo-bo-toi':
    'https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80',
  'ga-hap-sa':
    'https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=800&q=80',
  'ga-kho-sa-nghe':
    'https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?auto=format&fit=crop&w=800&q=80',
  'ga-xao-sa-ot':
    'https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=800&q=80',
  'tom-rang-hanh-toi':
    'https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=800&q=80',
  'ca-kho-gung':
    'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=800&q=80',
  'thit-heo-ham-khoai-tay-ca-rot':
    'https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=800&q=80',
  'bo-xao-bong-cai-xanh-nam':
    'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=800&q=80',
  'bap-cai-xao-nam-toi':
    'https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80',
  'dua-leo-tron-toi-ot':
    'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80',
  'bo-xao-ot-chuong-hanh-tay':
    'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80',
  'bap-ngot-ap-chao-bo-toi-kieu-my':
    'https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80',
  'rau-muong-xao-toi':
    'https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80',
};

const DEFAULT_FALLBACK_COVERS = [
  'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=800&q=80',
];

export function resolveRecipeCoverUrl(
  slug: string,
  coverImageUrl: string | null | undefined
): string {
  if (coverImageUrl && coverImageUrl.trim().length > 0) {
    return coverImageUrl.trim();
  }
  if (COVER_FALLBACK_BY_SLUG[slug]) {
    return COVER_FALLBACK_BY_SLUG[slug];
  }
  let hash = 0;
  for (let i = 0; i < slug.length; i += 1) {
    hash = (hash * 31 + slug.charCodeAt(i)) >>> 0;
  }
  return DEFAULT_FALLBACK_COVERS[hash % DEFAULT_FALLBACK_COVERS.length];
}
