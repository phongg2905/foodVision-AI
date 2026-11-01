-- ============================================================================
-- FOODVISION AI - SUPABASE POSTGRESQL SCHEMA (9 TABLES + ROW LEVEL SECURITY)
-- ============================================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Bảng ingredients: Danh mục nguyên liệu chuẩn
CREATE TABLE IF NOT EXISTS public.ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    normalized_name VARCHAR(100) NOT NULL UNIQUE,
    yolo_class VARCHAR(50) UNIQUE, -- NULL nếu là gia vị/nguyên liệu phụ không nằm trong 12 class YOLO
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Bảng recipes: Thông tin món ăn và hướng dẫn chế biến
CREATE TABLE IF NOT EXISTS public.recipes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    cooking_time INTEGER NOT NULL DEFAULT 20, -- Thời gian nấu tham khảo (phút)
    instructions TEXT NOT NULL,
    image_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Bảng recipe_ingredients: Liên kết món ăn - nguyên liệu và trọng số
CREATE TABLE IF NOT EXISTS public.recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES public.recipes(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES public.ingredients(id) ON DELETE RESTRICT,
    amount VARCHAR(50),          -- Định lượng tham khảo (VD: "2", "150", "1/2")
    unit VARCHAR(50),            -- Đơn vị (VD: "quả", "g", "củ", "muỗng")
    importance SMALLINT NOT NULL DEFAULT 2 CHECK (importance IN (1, 2, 3)), -- 3: Chính, 2: Phụ, 1: Gia vị
    is_optional BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (recipe_id, ingredient_id)
);

-- 4. Bảng nutrients: Danh mục chất / nhóm chất dinh dưỡng
CREATE TABLE IF NOT EXISTS public.nutrients (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,        -- VD: PRO, FAT, CARB, FIB, VIT_C, VIT_A, VIT_B12, K, FE
    name VARCHAR(100) NOT NULL,              -- VD: Protein, Chất béo, Vitamin C, Kali, Chất xơ
    nutrient_group VARCHAR(50) NOT NULL      -- VD: Đa lượng, Vitamin, Khoáng chất, Chất xơ
);

-- 5. Bảng nutrition_sources: Nguồn tham khảo kiểm chứng thông tin dinh dưỡng
CREATE TABLE IF NOT EXISTS public.nutrition_sources (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    publisher VARCHAR(150) NOT NULL,
    url_or_reference TEXT NOT NULL,
    accessed_at DATE NOT NULL DEFAULT CURRENT_DATE
);

-- 6. Bảng ingredient_nutrients: Ánh xạ có căn cứ giữa nguyên liệu và chất dinh dưỡng
CREATE TABLE IF NOT EXISTS public.ingredient_nutrients (
    id SERIAL PRIMARY KEY,
    ingredient_id INTEGER NOT NULL REFERENCES public.ingredients(id) ON DELETE CASCADE,
    nutrient_id INTEGER NOT NULL REFERENCES public.nutrients(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES public.nutrition_sources(id) ON DELETE RESTRICT,
    food_form VARCHAR(50) NOT NULL DEFAULT 'sống/tươi', -- Trạng thái nguyên liệu khi tra cứu
    note TEXT,                                          -- Ghi chú an toàn định tính
    UNIQUE (ingredient_id, nutrient_id, food_form)
);

-- 7. Bảng inference_sessions: Nhật ký kỹ thuật mỗi lần suy luận ảnh
CREATE TABLE IF NOT EXISTS public.inference_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_version VARCHAR(50) NOT NULL DEFAULT 'yolov8n-foodvision-v1',
    processing_time_ms INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. Bảng session_ingredients: Danh sách nguyên liệu trước và sau khi người dùng xác nhận
CREATE TABLE IF NOT EXISTS public.session_ingredients (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES public.inference_sessions(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES public.ingredients(id) ON DELETE RESTRICT,
    confidence NUMERIC(4, 3) CHECK (confidence >= 0 AND confidence <= 1),
    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE
);

-- 9. Bảng recommendation_feedback: Phản hồi chất lượng gợi ý (FR-12 bổ sung)
CREATE TABLE IF NOT EXISTS public.recommendation_feedback (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES public.inference_sessions(id) ON DELETE SET NULL,
    recipe_id INTEGER NOT NULL REFERENCES public.recipes(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating IN (-1, 1)), -- 1: Hữu ích, -1: Không hữu ích
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- CẤU HÌNH BẢO MẬT ROW LEVEL SECURITY (RLS) TRÊN SUPABASE
-- ============================================================================

ALTER TABLE public.ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recipe_ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredient_nutrients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inference_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendation_feedback ENABLE ROW LEVEL SECURITY;

-- Chính sách đọc công khai (Public Read) cho các bảng danh mục tra cứu
CREATE POLICY "Allow public read on ingredients" ON public.ingredients FOR SELECT USING (true);
CREATE POLICY "Allow public read on recipes" ON public.recipes FOR SELECT USING (true);
CREATE POLICY "Allow public read on recipe_ingredients" ON public.recipe_ingredients FOR SELECT USING (true);
CREATE POLICY "Allow public read on nutrients" ON public.nutrients FOR SELECT USING (true);
CREATE POLICY "Allow public read on nutrition_sources" ON public.nutrition_sources FOR SELECT USING (true);
CREATE POLICY "Allow public read on ingredient_nutrients" ON public.ingredient_nutrients FOR SELECT USING (true);

-- Chính sách ghi nhật ký phiên suy luận và phản hồi thông qua Backend API
CREATE POLICY "Allow insert inference_sessions" ON public.inference_sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow select inference_sessions" ON public.inference_sessions FOR SELECT USING (true);
CREATE POLICY "Allow insert session_ingredients" ON public.session_ingredients FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow select session_ingredients" ON public.session_ingredients FOR SELECT USING (true);
CREATE POLICY "Allow insert recommendation_feedback" ON public.recommendation_feedback FOR INSERT WITH CHECK (true);

