-- ============================================================================
-- Seed File : supabase/seed.sql
-- Project   : FoodVision AI (v1.1.0 Baseline — Stage 1 Seed Data & ADR-013)
-- Owner     : TV1 (Minh Thanh — AI, ML & Data Content Lead) & TV2 (DB Sync)
-- References: docs/04-ai-model/label-catalog.md
--             docs/05-recommendation/nutrition-and-content.md
--             docs/05-recommendation/recommendation-design.md (ADR-013: 4-2-1-0 & main/sub)
--             supabase/migrations/20261104000001_initial_schema.sql
-- Notes     : Idempotent (ON CONFLICT DO UPDATE). Safe to re-run (OPS-02).
-- ============================================================================

BEGIN;

-- THUẬT TOÁN: Khởi tạo tài khoản biên tập hệ thống phục vụ khóa ngoại recipes.author_id
-- trên cơ sở dữ liệu trống (OPS-02) mà không lưu bất kỳ mật khẩu hay khóa bí mật nào.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'auth' AND table_name = 'users'
    ) THEN
        INSERT INTO auth.users (
            id,
            instance_id,
            aud,
            role,
            email,
            encrypted_password,
            email_confirmed_at,
            raw_app_meta_data,
            raw_user_meta_data,
            created_at,
            updated_at
        )
        VALUES (
            '00000000-0000-4000-8000-000000000001',
            '00000000-0000-0000-0000-000000000000',
            'authenticated',
            'authenticated',
            'editorial-seed@foodvision.local',
            '',
            now(),
            '{"provider":"email","providers":["email"]}'::jsonb,
            '{"display_name":"FoodVision Editorial"}'::jsonb,
            now(),
            now()
        )
        ON CONFLICT (id) DO NOTHING;
    END IF;
END
$$;

INSERT INTO public.profiles (id, display_name, role)
VALUES ('00000000-0000-4000-8000-000000000001', 'FoodVision Editorial', 'admin')
ON CONFLICT (id) DO UPDATE
SET display_name = EXCLUDED.display_name,
    role = 'admin';

-- ============================================================================
-- 1. ALLERGENS (DietOK Hard Constraint — TP 04)
-- ============================================================================
INSERT INTO public.allergens (id, code, name_vi)
VALUES
    ('44444444-4444-4444-8444-444444444401', 'egg', 'Trứng gia cầm'),
    ('44444444-4444-4444-8444-444444444402', 'soy', 'Đậu nành'),
    ('44444444-4444-4444-8444-444444444403', 'fish', 'Cá và chế phẩm từ cá'),
    ('44444444-4444-4444-8444-444444444404', 'shellfish', 'Giáp xác (tôm, cua)'),
    ('44444444-4444-4444-8444-444444444405', 'milk', 'Sữa và chế phẩm từ sữa'),
    ('44444444-4444-4444-8444-444444444406', 'gluten', 'Ngũ cốc chứa gluten'),
    ('44444444-4444-4444-8444-444444444407', 'peanut', 'Đậu phộng (lạc)')
ON CONFLICT (code) DO UPDATE
SET name_vi = EXCLUDED.name_vi;

-- ============================================================================
-- 2. INGREDIENTS: 20 YOLO Classes (0..19) + 7 Culinary Extras + 5 Pantry Spices
--    Strictly NO water record in pantry (BR-04, BR-12, ADR-008).
-- ============================================================================
INSERT INTO public.ingredients (id, slug, name_vi, category, fdc_id, is_active)
VALUES
    -- 20 YOLO Candidate Classes (0..19 in docs/04-ai-model/label-catalog.md)
    ('11111111-1111-4111-8111-111111111101', 'ca-chua', 'Cà chua', 'vegetable', '170457', true),
    ('11111111-1111-4111-8111-111111111102', 'trung-ga', 'Trứng gà', 'protein', '171287', true),
    ('11111111-1111-4111-8111-111111111202', 'khoai-tay', 'Khoai tây', 'vegetable', '170026', true),
    ('11111111-1111-4111-8111-111111111203', 'ca-rot', 'Cà rốt', 'vegetable', '170393', true),
    ('11111111-1111-4111-8111-111111111204', 'hanh-tay', 'Hành tây', 'vegetable', '170000', true),
    ('11111111-1111-4111-8111-111111111205', 'toi', 'Tỏi', 'spice', '169230', true),
    ('11111111-1111-4111-8111-111111111206', 'ot', 'Ớt', 'spice', '170106', true),
    ('11111111-1111-4111-8111-111111111207', 'dua-leo', 'Dưa leo', 'vegetable', '168409', true),
    ('11111111-1111-4111-8111-111111111208', 'bap-cai', 'Bắp cải', 'vegetable', '169975', true),
    ('11111111-1111-4111-8111-111111111209', 'bong-cai-xanh', 'Bông cải xanh', 'vegetable', '170379', true),
    ('11111111-1111-4111-8111-111111111210', 'nam', 'Nấm', 'vegetable', '169251', true),
    ('11111111-1111-4111-8111-111111111103', 'dau-hu', 'Đậu hũ', 'protein', '172475', true),
    ('11111111-1111-4111-8111-111111111212', 'thit-ga-song', 'Thịt gà sống', 'protein', '171077', true),
    ('11111111-1111-4111-8111-111111111213', 'thit-heo-song', 'Thịt heo sống', 'protein', '167820', true),
    ('11111111-1111-4111-8111-111111111214', 'tom', 'Tôm', 'seafood', '175180', true),
    ('11111111-1111-4111-8111-111111111215', 'ca-nguyen-con', 'Cá nguyên con', 'seafood', '175159', true),
    ('11111111-1111-4111-8111-111111111216', 'gung', 'Gừng', 'spice', '169231', true),
    ('11111111-1111-4111-8111-111111111105', 'hanh-la', 'Hành lá', 'vegetable', '170005', true),
    ('11111111-1111-4111-8111-111111111218', 'ot-chuong', 'Ớt chuông', 'vegetable', '170427', true),
    ('11111111-1111-4111-8111-111111111219', 'bap-ngot', 'Bắp ngọt', 'vegetable', '169998', true),
    -- Extra non-pantry ingredients for VN / EU / US dishes
    ('11111111-1111-4111-8111-111111111104', 'thit-ba-chi', 'Thịt ba chỉ', 'protein', '167814', true),
    ('11111111-1111-4111-8111-111111111301', 'thit-bo', 'Thịt bò', 'protein', '174032', true),
    ('11111111-1111-4111-8111-111111111302', 'mi-y', 'Mì Ý', 'other', '169736', true),
    ('11111111-1111-4111-8111-111111111303', 'bo-lat', 'Bơ lạt', 'other', '173430', true),
    ('11111111-1111-4111-8111-111111111304', 'pho-mai-cheddar', 'Phô mai Cheddar', 'other', '173414', true),
    ('11111111-1111-4111-8111-111111111305', 'banh-mi-burger', 'Vỏ bánh Burger', 'other', '172684', true),
    ('11111111-1111-4111-8111-111111111306', 'xa-lach', 'Rau xà lách', 'vegetable', '169248', true),
    ('11111111-1111-4111-8111-111111111307', 'sa', 'Sả', 'spice', '168573', true),
    ('11111111-1111-4111-8111-111111111308', 'nghe', 'Nghệ tươi', 'spice', '172231', true),
    ('11111111-1111-4111-8111-111111111309', 'la-chanh', 'Lá chanh', 'spice', '172232', true),
    ('11111111-1111-4111-8111-111111111310', 'hanh-tim', 'Hành tím', 'spice', '170499', true),
    ('11111111-1111-4111-8111-111111111311', 'chanh', 'Chanh tươi', 'vegetable', '168155', true),
    ('11111111-1111-4111-8111-111111111312', 'rau-muong', 'Rau muống', 'vegetable', '169297', true),
    ('11111111-1111-4111-8111-111111111313', 'cai-thia', 'Cải thìa', 'vegetable', '170390', true),
    ('11111111-1111-4111-8111-111111111314', 'bi-do', 'Bí đỏ', 'vegetable', '168448', true),
    ('11111111-1111-4111-8111-111111111315', 'muc-tuoi', 'Mực tươi', 'seafood', '174222', true),
    -- Exact 5 Pantry Spices (category = 'pantry')
    ('11111111-1111-4111-8111-111111111106', 'muoi', 'Muối', 'pantry', '173468', true),
    ('11111111-1111-4111-8111-111111111107', 'nuoc-mam', 'Nước mắm', 'pantry', '172235', true),
    ('11111111-1111-4111-8111-111111111108', 'dau-an', 'Dầu ăn', 'pantry', '171028', true),
    ('11111111-1111-4111-8111-111111111109', 'duong', 'Đường', 'pantry', '169655', true),
    ('11111111-1111-4111-8111-111111111110', 'hat-tieu', 'Hạt tiêu', 'pantry', '170931', true)
ON CONFLICT (id) DO UPDATE
SET slug = EXCLUDED.slug,
    name_vi = EXCLUDED.name_vi,
    category = EXCLUDED.category,
    fdc_id = EXCLUDED.fdc_id,
    is_active = EXCLUDED.is_active;

INSERT INTO public.ingredient_allergens (ingredient_id, allergen_id)
VALUES
    ('11111111-1111-4111-8111-111111111102', '44444444-4444-4444-8444-444444444401'),
    ('11111111-1111-4111-8111-111111111103', '44444444-4444-4444-8444-444444444402'),
    ('11111111-1111-4111-8111-111111111214', '44444444-4444-4444-8444-444444444404'),
    ('11111111-1111-4111-8111-111111111215', '44444444-4444-4444-8444-444444444403'),
    ('11111111-1111-4111-8111-111111111107', '44444444-4444-4444-8444-444444444403'),
    ('11111111-1111-4111-8111-111111111302', '44444444-4444-4444-8444-444444444406'),
    ('11111111-1111-4111-8111-111111111303', '44444444-4444-4444-8444-444444444405'),
    ('11111111-1111-4111-8111-111111111304', '44444444-4444-4444-8444-444444444405'),
    ('11111111-1111-4111-8111-111111111305', '44444444-4444-4444-8444-444444444406'),
    ('11111111-1111-4111-8111-111111111315', '44444444-4444-4444-8444-444444444404')
ON CONFLICT (ingredient_id, allergen_id) DO NOTHING;

-- ============================================================================
-- 3. ACTIVE AI MODEL & 20 CLASS LABELS (0..19 -> Non-Pantry Ingredients, BR-12)
--    Weights artifact: backend/weights/yolo/ingredients_best.pt
--    SHA-256 (64 hex): f72e4c58607722028f247002d6cc7afe63c6c5a4b6519118a045f14f761e03e5
-- ============================================================================
INSERT INTO public.ai_models (
    id, version, family, dataset_version, artifact_ref,
    class_count, confidence_threshold, review_threshold, status
)
VALUES (
    '55555555-5555-4555-8555-555555555501',
    'yolo11n-foodvision-v1.0',
    'yolo11n',
    'food-ingredients-v1.0',
    'weights/yolo/ingredients_best.pt',
    20, 0.250, 0.800, 'active'
)
ON CONFLICT (id) DO UPDATE
SET version = EXCLUDED.version,
    artifact_ref = EXCLUDED.artifact_ref,
    class_count = EXCLUDED.class_count,
    confidence_threshold = EXCLUDED.confidence_threshold,
    review_threshold = EXCLUDED.review_threshold,
    status = EXCLUDED.status;

INSERT INTO public.ai_labels (model_id, class_index, class_name, ingredient_id)
VALUES
    ('55555555-5555-4555-8555-555555555501', 0, 'tomato', '11111111-1111-4111-8111-111111111101'),
    ('55555555-5555-4555-8555-555555555501', 1, 'egg', '11111111-1111-4111-8111-111111111102'),
    ('55555555-5555-4555-8555-555555555501', 2, 'potato', '11111111-1111-4111-8111-111111111202'),
    ('55555555-5555-4555-8555-555555555501', 3, 'carrot', '11111111-1111-4111-8111-111111111203'),
    ('55555555-5555-4555-8555-555555555501', 4, 'onion', '11111111-1111-4111-8111-111111111204'),
    ('55555555-5555-4555-8555-555555555501', 5, 'garlic', '11111111-1111-4111-8111-111111111205'),
    ('55555555-5555-4555-8555-555555555501', 6, 'chili_pepper', '11111111-1111-4111-8111-111111111206'),
    ('55555555-5555-4555-8555-555555555501', 7, 'cucumber', '11111111-1111-4111-8111-111111111207'),
    ('55555555-5555-4555-8555-555555555501', 8, 'cabbage', '11111111-1111-4111-8111-111111111208'),
    ('55555555-5555-4555-8555-555555555501', 9, 'broccoli', '11111111-1111-4111-8111-111111111209'),
    ('55555555-5555-4555-8555-555555555501', 10, 'mushroom', '11111111-1111-4111-8111-111111111210'),
    ('55555555-5555-4555-8555-555555555501', 11, 'tofu', '11111111-1111-4111-8111-111111111103'),
    ('55555555-5555-4555-8555-555555555501', 12, 'raw_chicken', '11111111-1111-4111-8111-111111111212'),
    ('55555555-5555-4555-8555-555555555501', 13, 'raw_pork', '11111111-1111-4111-8111-111111111213'),
    ('55555555-5555-4555-8555-555555555501', 14, 'raw_shrimp', '11111111-1111-4111-8111-111111111214'),
    ('55555555-5555-4555-8555-555555555501', 15, 'whole_fish', '11111111-1111-4111-8111-111111111215'),
    ('55555555-5555-4555-8555-555555555501', 16, 'ginger', '11111111-1111-4111-8111-111111111216'),
    ('55555555-5555-4555-8555-555555555501', 17, 'scallion', '11111111-1111-4111-8111-111111111105'),
    ('55555555-5555-4555-8555-555555555501', 18, 'bell_pepper', '11111111-1111-4111-8111-111111111218'),
    ('55555555-5555-4555-8555-555555555501', 19, 'sweet_corn', '11111111-1111-4111-8111-111111111219')
ON CONFLICT (model_id, class_index) DO UPDATE
SET class_name = EXCLUDED.class_name,
    ingredient_id = EXCLUDED.ingredient_id;

-- ============================================================================
-- 4. REGIONAL SYNONYMS & BILINGUAL ALIASES (TP 13 — pg_trgm + norm_vi)
-- ============================================================================
INSERT INTO public.ingredient_aliases (ingredient_id, alias, normalized_alias, locale)
VALUES
    ('11111111-1111-4111-8111-111111111101', 'cà chua đỏ', public.norm_vi('cà chua đỏ'), 'vi'),
    ('11111111-1111-4111-8111-111111111101', 'tomato', public.norm_vi('tomato'), 'en'),
    ('11111111-1111-4111-8111-111111111102', 'hột gà', public.norm_vi('hột gà'), 'vi'),
    ('11111111-1111-4111-8111-111111111102', 'trứng', public.norm_vi('trứng'), 'vi'),
    ('11111111-1111-4111-8111-111111111102', 'egg', public.norm_vi('egg'), 'en'),
    ('11111111-1111-4111-8111-111111111202', 'potato', public.norm_vi('potato'), 'en'),
    ('11111111-1111-4111-8111-111111111203', 'củ cải đỏ', public.norm_vi('củ cải đỏ'), 'vi'),
    ('11111111-1111-4111-8111-111111111203', 'carrot', public.norm_vi('carrot'), 'en'),
    ('11111111-1111-4111-8111-111111111204', 'onion', public.norm_vi('onion'), 'en'),
    ('11111111-1111-4111-8111-111111111205', 'tỏi ta', public.norm_vi('tỏi ta'), 'vi'),
    ('11111111-1111-4111-8111-111111111205', 'garlic', public.norm_vi('garlic'), 'en'),
    ('11111111-1111-4111-8111-111111111206', 'ớt hiểm', public.norm_vi('ớt hiểm'), 'vi'),
    ('11111111-1111-4111-8111-111111111206', 'chili pepper', public.norm_vi('chili pepper'), 'en'),
    ('11111111-1111-4111-8111-111111111103', 'đậu phụ', public.norm_vi('đậu phụ'), 'vi'),
    ('11111111-1111-4111-8111-111111111103', 'tàu hũ', public.norm_vi('tàu hũ'), 'vi'),
    ('11111111-1111-4111-8111-111111111103', 'đậu khuôn', public.norm_vi('đậu khuôn'), 'vi'),
    ('11111111-1111-4111-8111-111111111103', 'tofu', public.norm_vi('tofu'), 'en'),
    ('11111111-1111-4111-8111-111111111207', 'dưa chuột', public.norm_vi('dưa chuột'), 'vi'),
    ('11111111-1111-4111-8111-111111111207', 'cucumber', public.norm_vi('cucumber'), 'en'),
    ('11111111-1111-4111-8111-111111111208', 'cải bắp', public.norm_vi('cải bắp'), 'vi'),
    ('11111111-1111-4111-8111-111111111208', 'cabbage', public.norm_vi('cabbage'), 'en'),
    ('11111111-1111-4111-8111-111111111209', 'súp lơ xanh', public.norm_vi('súp lơ xanh'), 'vi'),
    ('11111111-1111-4111-8111-111111111209', 'broccoli', public.norm_vi('broccoli'), 'en'),
    ('11111111-1111-4111-8111-111111111210', 'nấm mỡ', public.norm_vi('nấm mỡ'), 'vi'),
    ('11111111-1111-4111-8111-111111111210', 'mushroom', public.norm_vi('mushroom'), 'en'),
    ('11111111-1111-4111-8111-111111111212', 'thịt gà', public.norm_vi('thịt gà'), 'vi'),
    ('11111111-1111-4111-8111-111111111212', 'ức gà', public.norm_vi('ức gà'), 'vi'),
    ('11111111-1111-4111-8111-111111111212', 'chicken', public.norm_vi('chicken'), 'en'),
    ('11111111-1111-4111-8111-111111111213', 'thịt lợn', public.norm_vi('thịt lợn'), 'vi'),
    ('11111111-1111-4111-8111-111111111213', 'thịt heo', public.norm_vi('thịt heo'), 'vi'),
    ('11111111-1111-4111-8111-111111111213', 'thịt heo băm', public.norm_vi('thịt heo băm'), 'vi'),
    ('11111111-1111-4111-8111-111111111213', 'pork', public.norm_vi('pork'), 'en'),
    ('11111111-1111-4111-8111-111111111104', 'thịt ba rọi', public.norm_vi('thịt ba rọi'), 'vi'),
    ('11111111-1111-4111-8111-111111111214', 'tôm tươi', public.norm_vi('tôm tươi'), 'vi'),
    ('11111111-1111-4111-8111-111111111214', 'shrimp', public.norm_vi('shrimp'), 'en'),
    ('11111111-1111-4111-8111-111111111215', 'cá tươi', public.norm_vi('cá tươi'), 'vi'),
    ('11111111-1111-4111-8111-111111111216', 'gừng tươi', public.norm_vi('gừng tươi'), 'vi'),
    ('11111111-1111-4111-8111-111111111216', 'ginger', public.norm_vi('ginger'), 'en'),
    ('11111111-1111-4111-8111-111111111105', 'hành hoa', public.norm_vi('hành hoa'), 'vi'),
    ('11111111-1111-4111-8111-111111111105', 'scallion', public.norm_vi('scallion'), 'en'),
    ('11111111-1111-4111-8111-111111111218', 'ớt ngọt', public.norm_vi('ớt ngọt'), 'vi'),
    ('11111111-1111-4111-8111-111111111218', 'ớt đà lạt', public.norm_vi('ớt đà lạt'), 'vi'),
    ('11111111-1111-4111-8111-111111111219', 'ngô ngọt', public.norm_vi('ngô ngọt'), 'vi'),
    ('11111111-1111-4111-8111-111111111219', 'ngô', public.norm_vi('ngô'), 'vi'),
    ('11111111-1111-4111-8111-111111111219', 'bắp', public.norm_vi('bắp'), 'vi'),
    ('11111111-1111-4111-8111-111111111219', 'sweet corn', public.norm_vi('sweet corn'), 'en'),
    ('11111111-1111-4111-8111-111111111302', 'mì spaghetti', public.norm_vi('mì spaghetti'), 'vi'),
    ('11111111-1111-4111-8111-111111111302', 'spaghetti', public.norm_vi('spaghetti'), 'en'),
    ('11111111-1111-4111-8111-111111111106', 'muối ăn', public.norm_vi('muối ăn'), 'vi'),
    ('11111111-1111-4111-8111-111111111107', 'nước mắm truyền thống', public.norm_vi('nước mắm truyền thống'), 'vi'),
    ('11111111-1111-4111-8111-111111111108', 'dầu thực vật', public.norm_vi('dầu thực vật'), 'vi'),
    ('11111111-1111-4111-8111-111111111109', 'đường cát', public.norm_vi('đường cát'), 'vi'),
    ('11111111-1111-4111-8111-111111111110', 'tiêu xay', public.norm_vi('tiêu xay'), 'vi'),
    ('11111111-1111-4111-8111-111111111307', 'củ sả', public.norm_vi('củ sả'), 'vi'),
    ('11111111-1111-4111-8111-111111111307', 'sả cây', public.norm_vi('sả cây'), 'vi'),
    ('11111111-1111-4111-8111-111111111307', 'lemongrass', public.norm_vi('lemongrass'), 'en'),
    ('11111111-1111-4111-8111-111111111308', 'nghệ', public.norm_vi('nghệ'), 'vi'),
    ('11111111-1111-4111-8111-111111111308', 'củ nghệ', public.norm_vi('củ nghệ'), 'vi'),
    ('11111111-1111-4111-8111-111111111308', 'turmeric', public.norm_vi('turmeric'), 'en'),
    ('11111111-1111-4111-8111-111111111309', 'lá chanh tươi', public.norm_vi('lá chanh tươi'), 'vi'),
    ('11111111-1111-4111-8111-111111111309', 'lime leaf', public.norm_vi('lime leaf'), 'en'),
    ('11111111-1111-4111-8111-111111111310', 'củ hành tím', public.norm_vi('củ hành tím'), 'vi'),
    ('11111111-1111-4111-8111-111111111310', 'shallot', public.norm_vi('shallot'), 'en'),
    ('11111111-1111-4111-8111-111111111311', 'chanh', public.norm_vi('chanh'), 'vi'),
    ('11111111-1111-4111-8111-111111111311', 'lime', public.norm_vi('lime'), 'en'),
    ('11111111-1111-4111-8111-111111111312', 'water spinach', public.norm_vi('water spinach'), 'en'),
    ('11111111-1111-4111-8111-111111111313', 'cải chíp', public.norm_vi('cải chíp'), 'vi'),
    ('11111111-1111-4111-8111-111111111313', 'bok choy', public.norm_vi('bok choy'), 'en'),
    ('11111111-1111-4111-8111-111111111314', 'bí ngô', public.norm_vi('bí ngô'), 'vi'),
    ('11111111-1111-4111-8111-111111111314', 'pumpkin', public.norm_vi('pumpkin'), 'en'),
    ('11111111-1111-4111-8111-111111111315', 'mực ống', public.norm_vi('mực ống'), 'vi'),
    ('11111111-1111-4111-8111-111111111315', 'squid', public.norm_vi('squid'), 'en')
ON CONFLICT (ingredient_id, normalized_alias, locale) DO UPDATE
SET alias = EXCLUDED.alias;

-- ============================================================================
-- 5. TIER-1 NUTRITION TAGS (P0) & TIER-2 USDA PER-100G NUTRIENTS (P1 — TP 11)
-- ============================================================================
INSERT INTO public.nutrition_tags (id, code, name_vi, description, is_active)
VALUES
    ('33333333-3333-4333-8333-333333333301', 'HIGH_PROTEIN_PLANT', 'Giàu đạm thực vật', 'Cung cấp protein thực vật lành mạnh từ họ đậu.', true),
    ('33333333-3333-4333-8333-333333333302', 'HIGH_PROTEIN_ANIMAL', 'Giàu đạm động vật', 'Cung cấp axit amin thiết yếu từ thịt, cá, trứng và hải sản.', true),
    ('33333333-3333-4333-8333-333333333303', 'HIGH_FIBER_VITAMIN', 'Giàu chất xơ và vitamin', 'Hỗ trợ tiêu hóa và bổ sung vi chất tự nhiên từ rau củ tươi.', true),
    ('33333333-3333-4333-8333-333333333304', 'ANTIOXIDANT_LYCOPENE', 'Giàu chất chống oxy hóa', 'Chứa hợp chất thực vật như lycopene và beta-carotene.', true),
    ('33333333-3333-4333-8333-333333333305', 'COMPLEX_CARB_ENERGY', 'Nguồn tinh bột cung cấp năng lượng', 'Cung cấp carbohydrate phục vụ hoạt động thể chất hằng ngày.', true)
ON CONFLICT (id) DO UPDATE
SET code = EXCLUDED.code,
    name_vi = EXCLUDED.name_vi,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active;

INSERT INTO public.ingredient_nutrition_tags (ingredient_id, nutrition_tag_id, source_url, note, reviewed_at)
VALUES
    ('11111111-1111-4111-8111-111111111101', '33333333-3333-4333-8333-333333333304', 'https://fdc.nal.usda.gov/food-details/170457/nutrients', 'Cà chua cung cấp lycopene và vitamin C tự nhiên.', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111102', '33333333-3333-4333-8333-333333333302', 'https://fdc.nal.usda.gov/food-details/171287/nutrients', 'Trứng gà cung cấp protein hoàn chỉnh và choline.', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111103', '33333333-3333-4333-8333-333333333301', 'https://fdc.nal.usda.gov/food-details/172475/nutrients', 'Đậu hũ giàu đạm thực vật và canxi.', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111209', '33333333-3333-4333-8333-333333333303', 'https://fdc.nal.usda.gov/food-details/170379/nutrients', 'Bông cải xanh giàu chất xơ, vitamin C và vitamin K.', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111213', '33333333-3333-4333-8333-333333333302', 'https://fdc.nal.usda.gov/food-details/167820/nutrients', 'Thịt heo nạc giàu protein và vitamin nhóm B.', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111301', '33333333-3333-4333-8333-333333333302', 'https://fdc.nal.usda.gov/food-details/174032/nutrients', 'Thịt bò cung cấp đạm động vật, sắt heme và kẽm.', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111202', '33333333-3333-4333-8333-333333333305', 'https://fdc.nal.usda.gov/food-details/170026/nutrients', 'Khoai tây cung cấp tinh bột phức và kali.', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111219', '33333333-3333-4333-8333-333333333305', 'https://fdc.nal.usda.gov/food-details/169998/nutrients', 'Bắp ngọt bổ sung chất xơ và năng lượng tự nhiên.', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111302', '33333333-3333-4333-8333-333333333305', 'https://fdc.nal.usda.gov/food-details/169736/nutrients', 'Mì Ý cung cấp năng lượng tinh bột cho bữa chính.', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111306', '33333333-3333-4333-8333-333333333303', 'https://fdc.nal.usda.gov/food-details/169248/nutrients', 'Xà lách bổ sung chất xơ và vitamin A.', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111212', '33333333-3333-4333-8333-333333333302', 'https://fdc.nal.usda.gov/food-details/171077/nutrients', 'Thịt gà sống giàu protein nạc, ít chất béo bão hòa.', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111214', '33333333-3333-4333-8333-333333333302', 'https://fdc.nal.usda.gov/food-details/175180/nutrients', 'Tôm tươi giàu đạm biển, selen và ít chất béo.', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111215', '33333333-3333-4333-8333-333333333302', 'https://fdc.nal.usda.gov/food-details/175159/nutrients', 'Cá nguyên con cung cấp đạm chất lượng cao và omega-3.', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111312', '33333333-3333-4333-8333-333333333303', 'https://fdc.nal.usda.gov/food-details/169297/nutrients', 'Rau muống cung cấp chất xơ, vitamin A và sắt thực vật.', '2026-11-23T00:00:00Z')
ON CONFLICT (ingredient_id, nutrition_tag_id) DO UPDATE
SET source_url = EXCLUDED.source_url,
    note = EXCLUDED.note,
    reviewed_at = EXCLUDED.reviewed_at;

-- Tier 2 USDA FoodData Central per 100g edible raw portion (MATH-07 verified)
INSERT INTO public.ingredient_nutrients (
    ingredient_id, kcal_100g, protein_100g, fat_100g, carb_100g, source_url, reviewed_at
)
VALUES
    ('11111111-1111-4111-8111-111111111101', 18.00, 0.88, 0.20, 3.89, 'https://fdc.nal.usda.gov/food-details/170457/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111102', 144.00, 12.56, 9.51, 0.72, 'https://fdc.nal.usda.gov/food-details/171287/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111202', 77.00, 2.05, 0.09, 17.49, 'https://fdc.nal.usda.gov/food-details/170026/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111203', 41.00, 0.93, 0.24, 9.58, 'https://fdc.nal.usda.gov/food-details/170393/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111204', 40.00, 1.10, 0.10, 9.34, 'https://fdc.nal.usda.gov/food-details/170000/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111205', 149.00, 6.36, 0.50, 33.06, 'https://fdc.nal.usda.gov/food-details/169230/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111206', 40.00, 1.87, 0.44, 8.81, 'https://fdc.nal.usda.gov/food-details/170106/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111207', 15.00, 0.65, 0.11, 3.63, 'https://fdc.nal.usda.gov/food-details/168409/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111208', 25.00, 1.28, 0.10, 5.80, 'https://fdc.nal.usda.gov/food-details/169975/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111209', 34.00, 2.82, 0.37, 6.64, 'https://fdc.nal.usda.gov/food-details/170379/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111210', 22.00, 3.09, 0.34, 3.26, 'https://fdc.nal.usda.gov/food-details/169251/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111103', 76.00, 8.08, 4.78, 1.87, 'https://fdc.nal.usda.gov/food-details/172475/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111212', 120.00, 22.50, 2.62, 0.00, 'https://fdc.nal.usda.gov/food-details/171077/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111213', 143.00, 21.40, 5.66, 0.00, 'https://fdc.nal.usda.gov/food-details/167820/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111214', 85.00, 20.10, 0.51, 0.00, 'https://fdc.nal.usda.gov/food-details/175180/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111215', 96.00, 20.08, 1.70, 0.00, 'https://fdc.nal.usda.gov/food-details/175159/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111216', 80.00, 1.82, 0.75, 17.77, 'https://fdc.nal.usda.gov/food-details/169231/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111105', 32.00, 1.83, 0.19, 7.34, 'https://fdc.nal.usda.gov/food-details/170005/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111218', 26.00, 0.99, 0.30, 6.03, 'https://fdc.nal.usda.gov/food-details/170427/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111219', 86.00, 3.27, 1.35, 18.70, 'https://fdc.nal.usda.gov/food-details/169998/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111104', 518.00, 9.34, 53.01, 0.00, 'https://fdc.nal.usda.gov/food-details/167814/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111301', 217.00, 19.00, 15.00, 0.00, 'https://fdc.nal.usda.gov/food-details/174032/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111302', 371.00, 13.04, 1.51, 74.67, 'https://fdc.nal.usda.gov/food-details/169736/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111303', 717.00, 0.85, 81.11, 0.06, 'https://fdc.nal.usda.gov/food-details/173430/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111304', 403.00, 24.90, 33.14, 1.28, 'https://fdc.nal.usda.gov/food-details/173414/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111305', 279.00, 9.40, 4.30, 50.20, 'https://fdc.nal.usda.gov/food-details/172684/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111306', 15.00, 1.36, 0.15, 2.87, 'https://fdc.nal.usda.gov/food-details/169248/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111307', 99.00, 1.82, 0.49, 25.31, 'https://fdc.nal.usda.gov/food-details/168573/nutrients', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111308', 312.00, 9.68, 3.25, 67.14, 'https://fdc.nal.usda.gov/food-details/172231/nutrients', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111309', 30.00, 0.70, 0.20, 10.54, 'https://fdc.nal.usda.gov/food-details/172232/nutrients', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111310', 72.00, 2.50, 0.10, 16.80, 'https://fdc.nal.usda.gov/food-details/170499/nutrients', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111311', 30.00, 0.70, 0.20, 10.54, 'https://fdc.nal.usda.gov/food-details/168155/nutrients', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111312', 19.00, 2.60, 0.20, 3.14, 'https://fdc.nal.usda.gov/food-details/169297/nutrients', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111313', 13.00, 1.50, 0.20, 2.18, 'https://fdc.nal.usda.gov/food-details/170390/nutrients', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111314', 26.00, 1.00, 0.10, 6.50, 'https://fdc.nal.usda.gov/food-details/168448/nutrients', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111315', 92.00, 15.58, 1.38, 3.08, 'https://fdc.nal.usda.gov/food-details/174222/nutrients', '2026-11-23T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111106', 0.00, 0.00, 0.00, 0.00, 'https://fdc.nal.usda.gov/food-details/173468/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111107', 35.00, 5.07, 0.01, 3.64, 'https://fdc.nal.usda.gov/food-details/172235/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111108', 884.00, 0.00, 100.00, 0.00, 'https://fdc.nal.usda.gov/food-details/171028/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111109', 387.00, 0.00, 0.00, 99.98, 'https://fdc.nal.usda.gov/food-details/169655/nutrients', '2026-11-04T00:00:00Z'),
    ('11111111-1111-4111-8111-111111111110', 251.00, 10.39, 3.26, 63.95, 'https://fdc.nal.usda.gov/food-details/170931/nutrients', '2026-11-04T00:00:00Z')
ON CONFLICT (ingredient_id) DO UPDATE
SET kcal_100g = EXCLUDED.kcal_100g,
    protein_100g = EXCLUDED.protein_100g,
    fat_100g = EXCLUDED.fat_100g,
    carb_100g = EXCLUDED.carb_100g,
    source_url = EXCLUDED.source_url,
    reviewed_at = EXCLUDED.reviewed_at;

-- ============================================================================
-- 6. PUBLISHED SAMPLE RECIPES ACROSS VN / EU / US (TP 10, BR-01, BR-05, ADR-013)
--    Includes "Cà chua nhồi thịt sốt trứng" (Card #7), "Đậu hũ sốt cà chua" (30m)
--    & "Trứng xào cà chua" (15m) matching Table E.1 (S=95.0 / 100.0 / 90.0 / 75.0 / 83.75).
-- ============================================================================
INSERT INTO public.recipes (
    id, slug, name_vi, description, cuisine_code, country_code, cooking_method,
    required_equipment, base_servings, prep_minutes, cook_minutes, quality_score,
    source_name, source_url, content_license, status, author_id
)
VALUES
    ('22222222-2222-4222-8222-222222222201', 'dau-hu-sot-ca-chua', 'Đậu hũ sốt cà chua', 'Món đậu hũ chiên rim sốt cà chua thanh đạm, đưa cơm gia đình Việt.', 'VN', 'VN', 'braise', ARRAY['pan', 'stove'], 2, 10, 20, 0.950, 'FoodVision Editorial', 'https://foodvision.local/recipes/dau-hu-sot-ca-chua', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222202', 'canh-ca-chua-trung', 'Canh cà chua trứng', 'Canh trứng vân mây nấu cà chua thanh mát hoàn tất trong 15 phút.', 'VN', 'VN', 'boil', ARRAY['pot', 'stove'], 2, 5, 10, 0.920, 'FoodVision Editorial', 'https://foodvision.local/recipes/canh-ca-chua-trung', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222203', 'ca-chua-nhoi-thit-sot-trung', 'Cà chua nhồi thịt sốt trứng', 'Món chuẩn kiểm chứng: cà chua chín nhồi thịt heo băm quyện sốt trứng sánh mịn.', 'VN', 'VN', 'braise', ARRAY['pan', 'stove'], 2, 10, 15, 0.980, 'FoodVision Editorial', 'https://foodvision.local/recipes/ca-chua-nhoi-thit-sot-trung', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222204', 'trung-xao-ca-chua', 'Trứng xào cà chua', 'Món trứng gà xào cà chua mềm mọng hoàn thành trong 15 phút (chuẩn kiểm chứng MCDA ADR-013).', 'VN', 'VN', 'stir_fry', ARRAY['pan', 'stove'], 2, 5, 10, 1.000, 'FoodVision Editorial', 'https://foodvision.local/recipes/trung-xao-ca-chua', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222205', 'mi-y-sot-ca-chua-thit-bam', 'Mì Ý sốt cà chua thịt băm', 'Mì Spaghetti kiểu Âu nấu sốt cà chua, hành tây, tỏi và thịt bò băm.', 'EU', 'IT', 'simmer', ARRAY['pot', 'pan', 'stove'], 2, 10, 20, 0.950, 'FoodVision Editorial', 'https://foodvision.local/recipes/mi-y-sot-ca-chua-thit-bam', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222206', 'bong-cai-xanh-nam-ap-chao-bo-toi', 'Bông cải xanh và nấm áp chảo bơ tỏi', 'Món rau củ kiểu Âu nhanh gọn 14 phút giữ trọn độ giòn ngọt tự nhiên.', 'EU', 'FR', 'pan_sear', ARRAY['pan', 'stove'], 2, 6, 8, 0.930, 'FoodVision Editorial', 'https://foodvision.local/recipes/bong-cai-xanh-nam-ap-chao-bo-toi', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222207', 'burger-bo-pho-mai-kieu-my', 'Burger bò phô mai kiểu Mỹ', 'Bánh burger nhân thịt bò áp chảo phủ phô mai Cheddar, cà chua và xà lách.', 'US', 'US', 'grill', ARRAY['pan', 'stove'], 2, 10, 12, 0.940, 'FoodVision Editorial', 'https://foodvision.local/recipes/burger-bo-pho-mai-kieu-my', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222208', 'bap-ngot-khoai-tay-dut-lo-bo-toi', 'Bắp ngọt và khoai tây đút lò bơ tỏi', 'Món ăn kèm kiểu Mỹ nướng lò thơm ngậy bơ lạt, tỏi và tiêu đen.', 'US', 'US', 'bake', ARRAY['oven'], 2, 10, 25, 0.910, 'FoodVision Editorial', 'https://foodvision.local/recipes/bap-ngot-khoai-tay-dut-lo-bo-toi', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222209', 'ga-hap-sa', 'Gà hấp sả', 'Thịt gà hấp cùng sả đập dập thơm thanh, giữ trọn vị ngọt tự nhiên.', 'VN', 'VN', 'steam', ARRAY['pot', 'stove'], 2, 10, 20, 0.970, 'FoodVision Editorial', 'https://foodvision.local/recipes/ga-hap-sa', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222210', 'ga-kho-sa-nghe', 'Gà kho sả nghệ', 'Thịt gà kho đậm đà với sả băm và nghệ tươi vàng ươm đưa cơm.', 'VN', 'VN', 'braise', ARRAY['pot', 'stove'], 2, 10, 25, 0.950, 'FoodVision Editorial', 'https://foodvision.local/recipes/ga-kho-sa-nghe', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222211', 'ga-xao-sa-ot', 'Gà xào sả ớt', 'Thịt gà xào sả ớt thơm nồng, cay ấm chuẩn cơm gia đình Việt.', 'VN', 'VN', 'stir_fry', ARRAY['pan', 'stove'], 2, 10, 12, 0.960, 'FoodVision Editorial', 'https://foodvision.local/recipes/ga-xao-sa-ot', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222212', 'tom-rang-hanh-toi', 'Tôm rang hành tỏi', 'Tôm tươi rang mặn ngọt bóng đẹp cùng tỏi phi và hành lá thơm lừng.', 'VN', 'VN', 'stir_fry', ARRAY['pan', 'stove'], 2, 8, 10, 0.950, 'FoodVision Editorial', 'https://foodvision.local/recipes/tom-rang-hanh-toi', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222213', 'ca-kho-gung', 'Cá kho gừng', 'Cá tươi kho gừng thái sợi ấm bụng, khử tanh và đậm đà vị mắm tiêu.', 'VN', 'VN', 'braise', ARRAY['pot', 'stove'], 3, 10, 30, 0.940, 'FoodVision Editorial', 'https://foodvision.local/recipes/ca-kho-gung', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222214', 'thit-heo-ham-khoai-tay-ca-rot', 'Thịt heo hầm khoai tây cà rốt', 'Canh hầm thịt heo mềm ngọt kết hợp khoai tây bùi béo và cà rốt thanh mát.', 'VN', 'VN', 'simmer', ARRAY['pot', 'stove'], 3, 15, 30, 0.940, 'FoodVision Editorial', 'https://foodvision.local/recipes/thit-heo-ham-khoai-tay-ca-rot', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222215', 'bo-xao-bong-cai-xanh-nam', 'Thịt bò xào bông cải xanh nấm', 'Thịt bò xào mềm cùng bông cải xanh giòn ngọt và nấm tươi giàu dinh dưỡng.', 'VN', 'VN', 'stir_fry', ARRAY['pan', 'stove'], 2, 8, 10, 0.960, 'FoodVision Editorial', 'https://foodvision.local/recipes/bo-xao-bong-cai-xanh-nam', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222216', 'bap-cai-xao-nam-toi', 'Bắp cải xào nấm tỏi', 'Bắp cải xào giòn ngọt cùng nấm tươi và tỏi phi thanh đạm hoàn tất trong 14 phút.', 'VN', 'VN', 'stir_fry', ARRAY['pan', 'stove'], 2, 6, 8, 0.930, 'FoodVision Editorial', 'https://foodvision.local/recipes/bap-cai-xao-nam-toi', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222217', 'dua-leo-tron-toi-ot', 'Dưa leo trộn tỏi ớt', 'Dưa leo đập dập trộn tỏi ớt chua ngọt giòn rụm giải ngấy trong 10 phút.', 'VN', 'VN', 'mix', ARRAY[]::text[], 2, 10, 0, 0.920, 'FoodVision Editorial', 'https://foodvision.local/recipes/dua-leo-tron-toi-ot', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222218', 'bo-xao-ot-chuong-hanh-tay', 'Thịt bò xào ớt chuông hành tây kiểu Âu', 'Thịt bò áp chảo bơ tỏi cùng ớt chuông giòn ngọt và hành tây kiểu Âu.', 'EU', 'FR', 'stir_fry', ARRAY['pan', 'stove'], 2, 8, 12, 0.950, 'FoodVision Editorial', 'https://foodvision.local/recipes/bo-xao-ot-chuong-hanh-tay', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222219', 'bap-ngot-ap-chao-bo-toi-kieu-my', 'Bắp ngọt áp chảo bơ tỏi kiểu Mỹ', 'Bắp ngọt tách hạt áp chảo thơm ngậy bơ lạt và tỏi phi kiểu Mỹ trong 15 phút.', 'US', 'US', 'pan_sear', ARRAY['pan', 'stove'], 2, 5, 10, 0.930, 'FoodVision Editorial', 'https://foodvision.local/recipes/bap-ngot-ap-chao-bo-toi-kieu-my', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001'),
    ('22222222-2222-4222-8222-222222222220', 'rau-muong-xao-toi', 'Rau muống xào tỏi', 'Rau muống xào tỏi xanh giòn chuẩn bữa cơm gia đình Việt trong 12 phút.', 'VN', 'VN', 'stir_fry', ARRAY['pan', 'stove'], 2, 5, 7, 0.950, 'FoodVision Editorial', 'https://foodvision.local/recipes/rau-muong-xao-toi', 'CC-BY-4.0', 'published', '00000000-0000-4000-8000-000000000001')
ON CONFLICT (id) DO UPDATE
SET slug = EXCLUDED.slug,
    name_vi = EXCLUDED.name_vi,
    description = EXCLUDED.description,
    cuisine_code = EXCLUDED.cuisine_code,
    country_code = EXCLUDED.country_code,
    cooking_method = EXCLUDED.cooking_method,
    required_equipment = EXCLUDED.required_equipment,
    base_servings = EXCLUDED.base_servings,
    prep_minutes = EXCLUDED.prep_minutes,
    cook_minutes = EXCLUDED.cook_minutes,
    quality_score = EXCLUDED.quality_score,
    source_name = EXCLUDED.source_name,
    source_url = EXCLUDED.source_url,
    content_license = EXCLUDED.content_license,
    status = EXCLUDED.status;

-- CONFLICT-RESOLVED: Synchronize TV1 Stage 1 seed rows with PR #11 & PR #12 (ADR-013 v1.1.0):
-- role IN ('core', 'secondary', 'spice', 'optional'), dish_role IN ('main', 'sub'), weight scale 4.00 / 2.00 / 1.00 / 0.00.
INSERT INTO public.recipe_ingredients (
    recipe_id, ingredient_id, is_required, role, dish_role, weight, grams, display_quantity, sort_order
)
VALUES
    -- 1. Đậu hũ sốt cà chua (VN — 30m = 0.50h, Table E.1 S=83.75)
    ('22222222-2222-4222-8222-222222222201', '11111111-1111-4111-8111-111111111103', true, 'core', 'main', 4.00, 200.00, '2 bìa', 1),
    ('22222222-2222-4222-8222-222222222201', '11111111-1111-4111-8111-111111111101', true, 'secondary', 'sub', 2.00, 150.00, '2 quả', 2),
    ('22222222-2222-4222-8222-222222222201', '11111111-1111-4111-8111-111111111105', false, 'optional', 'sub', 0.00, 15.00, '2 nhánh', 3),
    ('22222222-2222-4222-8222-222222222201', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 5.00, '1 muỗng cà phê', 4),
    ('22222222-2222-4222-8222-222222222201', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 15.00, '1 muỗng canh', 5),
    -- 2. Canh cà chua trứng (VN — 15m = 0.25h)
    ('22222222-2222-4222-8222-222222222202', '11111111-1111-4111-8111-111111111101', true, 'core', 'main', 4.00, 100.00, '1 quả lớn', 1),
    ('22222222-2222-4222-8222-222222222202', '11111111-1111-4111-8111-111111111102', true, 'core', 'main', 4.00, 60.00, '1 quả lớn', 2),
    ('22222222-2222-4222-8222-222222222202', '11111111-1111-4111-8111-111111111105', false, 'optional', 'sub', 0.00, 10.00, '1 nhánh', 3),
    ('22222222-2222-4222-8222-222222222202', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 4.00, '1/2 muỗng cà phê', 4),
    ('22222222-2222-4222-8222-222222222202', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 5.00, '1 muỗng cà phê', 5),
    -- 3. Cà chua nhồi thịt sốt trứng (VN — Canonical Card #7 dish, 25m)
    ('22222222-2222-4222-8222-222222222203', '11111111-1111-4111-8111-111111111101', true, 'core', 'main', 4.00, 200.00, '3 quả vừa', 1),
    ('22222222-2222-4222-8222-222222222203', '11111111-1111-4111-8111-111111111213', true, 'core', 'main', 4.00, 150.00, '150 g băm nhuyễn', 2),
    ('22222222-2222-4222-8222-222222222203', '11111111-1111-4111-8111-111111111102', true, 'secondary', 'sub', 2.00, 60.00, '1 quả', 3),
    ('22222222-2222-4222-8222-222222222203', '11111111-1111-4111-8111-111111111105', false, 'optional', 'sub', 0.00, 15.00, '2 nhánh', 4),
    ('22222222-2222-4222-8222-222222222203', '11111111-1111-4111-8111-111111111107', true, 'spice', 'sub', 1.00, 10.00, '1 muỗng canh', 5),
    ('22222222-2222-4222-8222-222222222203', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 10.00, '2 muỗng cà phê', 6),
    ('22222222-2222-4222-8222-222222222203', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/2 muỗng cà phê', 7),
    -- 4. Trứng xào cà chua (VN — 15m = 0.25h, Table E.1 S=95.0 / 100.0 / 90.0 / 75.0)
    ('22222222-2222-4222-8222-222222222204', '11111111-1111-4111-8111-111111111101', true, 'core', 'main', 4.00, 150.00, '2 quả', 1),
    ('22222222-2222-4222-8222-222222222204', '11111111-1111-4111-8111-111111111102', true, 'core', 'main', 4.00, 120.00, '2 quả', 2),
    ('22222222-2222-4222-8222-222222222204', '11111111-1111-4111-8111-111111111105', false, 'optional', 'sub', 0.00, 10.00, '1 nhánh', 3),
    ('22222222-2222-4222-8222-222222222204', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 10.00, '2 muỗng cà phê', 4),
    ('22222222-2222-4222-8222-222222222204', '11111111-1111-4111-8111-111111111107', true, 'spice', 'sub', 1.00, 8.00, '1.5 muỗng cà phê', 5),
    -- 5. Mì Ý sốt cà chua thịt băm (EU — 30m)
    ('22222222-2222-4222-8222-222222222205', '11111111-1111-4111-8111-111111111302', true, 'core', 'main', 4.00, 160.00, '160 g mì khô', 1),
    ('22222222-2222-4222-8222-222222222205', '11111111-1111-4111-8111-111111111301', true, 'core', 'main', 4.00, 150.00, '150 g băm', 2),
    ('22222222-2222-4222-8222-222222222205', '11111111-1111-4111-8111-111111111101', true, 'secondary', 'sub', 2.00, 200.00, '3 quả chín', 3),
    ('22222222-2222-4222-8222-222222222205', '11111111-1111-4111-8111-111111111204', true, 'spice', 'sub', 1.00, 50.00, '1/2 củ', 4),
    ('22222222-2222-4222-8222-222222222205', '11111111-1111-4111-8111-111111111205', false, 'optional', 'sub', 0.00, 10.00, '2 tép', 5),
    ('22222222-2222-4222-8222-222222222205', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 10.00, '2 muỗng cà phê', 6),
    ('22222222-2222-4222-8222-222222222205', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 4.00, '1/2 muỗng cà phê', 7),
    ('22222222-2222-4222-8222-222222222205', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/2 muỗng cà phê', 8),
    -- 6. Bông cải xanh và nấm áp chảo bơ tỏi (EU — 14m)
    ('22222222-2222-4222-8222-222222222206', '11111111-1111-4111-8111-111111111209', true, 'core', 'main', 4.00, 180.00, '1 bông vừa', 1),
    ('22222222-2222-4222-8222-222222222206', '11111111-1111-4111-8111-111111111210', true, 'secondary', 'sub', 2.00, 120.00, '120 g nấm tươi', 2),
    ('22222222-2222-4222-8222-222222222206', '11111111-1111-4111-8111-111111111303', true, 'secondary', 'sub', 2.00, 15.00, '1 muỗng canh', 3),
    ('22222222-2222-4222-8222-222222222206', '11111111-1111-4111-8111-111111111205', true, 'spice', 'sub', 1.00, 10.00, '2 tép', 4),
    ('22222222-2222-4222-8222-222222222206', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 3.00, '1/2 muỗng cà phê', 5),
    ('22222222-2222-4222-8222-222222222206', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/3 muỗng cà phê', 6),
    -- 7. Burger bò phô mai kiểu Mỹ (US — 22m)
    ('22222222-2222-4222-8222-222222222207', '11111111-1111-4111-8111-111111111301', true, 'core', 'main', 4.00, 200.00, '2 viên thịt bò xay', 1),
    ('22222222-2222-4222-8222-222222222207', '11111111-1111-4111-8111-111111111305', true, 'core', 'main', 4.00, 120.00, '2 vỏ bánh', 2),
    ('22222222-2222-4222-8222-222222222207', '11111111-1111-4111-8111-111111111304', true, 'secondary', 'sub', 2.00, 40.00, '2 lát', 3),
    ('22222222-2222-4222-8222-222222222207', '11111111-1111-4111-8111-111111111101', true, 'spice', 'sub', 1.00, 60.00, '4 lát tròn', 4),
    ('22222222-2222-4222-8222-222222222207', '11111111-1111-4111-8111-111111111306', true, 'spice', 'sub', 1.00, 40.00, '4 lá tươi', 5),
    ('22222222-2222-4222-8222-222222222207', '11111111-1111-4111-8111-111111111204', false, 'optional', 'sub', 0.00, 30.00, '3 khoanh mỏng', 6),
    ('22222222-2222-4222-8222-222222222207', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 5.00, '1 muỗng cà phê', 7),
    ('22222222-2222-4222-8222-222222222207', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 3.00, '1/2 muỗng cà phê', 8),
    ('22222222-2222-4222-8222-222222222207', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/2 muỗng cà phê', 9),
    -- 8. Bắp ngọt và khoai tây đút lò bơ tỏi (US — requires oven, 35m)
    ('22222222-2222-4222-8222-222222222208', '11111111-1111-4111-8111-111111111219', true, 'core', 'main', 4.00, 150.00, '1 trái tách hạt', 1),
    ('22222222-2222-4222-8222-222222222208', '11111111-1111-4111-8111-111111111202', true, 'core', 'main', 4.00, 200.00, '2 củ cắt múi cau', 2),
    ('22222222-2222-4222-8222-222222222208', '11111111-1111-4111-8111-111111111303', true, 'secondary', 'sub', 2.00, 20.00, '1.5 muỗng canh', 3),
    ('22222222-2222-4222-8222-222222222208', '11111111-1111-4111-8111-111111111205', true, 'spice', 'sub', 1.00, 10.00, '2 tép băm', 4),
    ('22222222-2222-4222-8222-222222222208', '11111111-1111-4111-8111-111111111105', false, 'optional', 'sub', 0.00, 10.00, '1 nhánh cắt nhỏ', 5),
    ('22222222-2222-4222-8222-222222222208', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 4.00, '1/2 muỗng cà phê', 6),
    ('22222222-2222-4222-8222-222222222208', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/3 muỗng cà phê', 7),
    -- 9. Gà hấp sả (VN — 30m)
    ('22222222-2222-4222-8222-222222222209', '11111111-1111-4111-8111-111111111212', true, 'core', 'main', 4.00, 350.00, '350 g', 1),
    ('22222222-2222-4222-8222-222222222209', '11111111-1111-4111-8111-111111111307', true, 'core', 'main', 4.00, 40.00, '2 củ đập dập', 2),
    ('22222222-2222-4222-8222-222222222209', '11111111-1111-4111-8111-111111111309', false, 'optional', 'sub', 0.00, 5.00, '4 lá', 3),
    ('22222222-2222-4222-8222-222222222209', '11111111-1111-4111-8111-111111111216', false, 'optional', 'sub', 0.00, 10.00, '3 lát mỏng', 4),
    ('22222222-2222-4222-8222-222222222209', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 4.00, '1/2 muỗng cà phê', 5),
    ('22222222-2222-4222-8222-222222222209', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/2 muỗng cà phê', 6),
    -- 10. Gà kho sả nghệ (VN — 35m)
    ('22222222-2222-4222-8222-222222222210', '11111111-1111-4111-8111-111111111212', true, 'core', 'main', 4.00, 350.00, '350 g chặt miếng', 1),
    ('22222222-2222-4222-8222-222222222210', '11111111-1111-4111-8111-111111111307', true, 'secondary', 'sub', 2.00, 30.00, '2 củ băm nhỏ', 2),
    ('22222222-2222-4222-8222-222222222210', '11111111-1111-4111-8111-111111111308', true, 'secondary', 'sub', 2.00, 15.00, '1 nhánh giã nhuyễn', 3),
    ('22222222-2222-4222-8222-222222222210', '11111111-1111-4111-8111-111111111107', true, 'spice', 'sub', 1.00, 15.00, '1 muỗng canh', 4),
    ('22222222-2222-4222-8222-222222222210', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 10.00, '2 muỗng cà phê', 5),
    ('22222222-2222-4222-8222-222222222210', '11111111-1111-4111-8111-111111111109', true, 'spice', 'sub', 1.00, 5.00, '1 muỗng cà phê', 6),
    -- 11. Gà xào sả ớt (VN — 22m)
    ('22222222-2222-4222-8222-222222222211', '11111111-1111-4111-8111-111111111212', true, 'core', 'main', 4.00, 300.00, '300 g', 1),
    ('22222222-2222-4222-8222-222222222211', '11111111-1111-4111-8111-111111111307', true, 'secondary', 'sub', 2.00, 30.00, '2 củ băm', 2),
    ('22222222-2222-4222-8222-222222222211', '11111111-1111-4111-8111-111111111206', true, 'secondary', 'sub', 2.00, 10.00, '1 quả cắt lát', 3),
    ('22222222-2222-4222-8222-222222222211', '11111111-1111-4111-8111-111111111205', true, 'spice', 'sub', 1.00, 10.00, '2 tép băm', 4),
    ('22222222-2222-4222-8222-222222222211', '11111111-1111-4111-8111-111111111107', true, 'spice', 'sub', 1.00, 15.00, '1 muỗng canh', 5),
    ('22222222-2222-4222-8222-222222222211', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 10.00, '2 muỗng cà phê', 6),
    -- 12. Tôm rang hành tỏi (VN — 18m)
    ('22222222-2222-4222-8222-222222222212', '11111111-1111-4111-8111-111111111214', true, 'core', 'main', 4.00, 250.00, '250 g', 1),
    ('22222222-2222-4222-8222-222222222212', '11111111-1111-4111-8111-111111111205', true, 'secondary', 'sub', 2.00, 12.00, '3 tép băm', 2),
    ('22222222-2222-4222-8222-222222222212', '11111111-1111-4111-8111-111111111105', true, 'spice', 'sub', 1.00, 15.00, '2 nhánh', 3),
    ('22222222-2222-4222-8222-222222222212', '11111111-1111-4111-8111-111111111107', true, 'spice', 'sub', 1.00, 12.00, '1 muỗng canh', 4),
    ('22222222-2222-4222-8222-222222222212', '11111111-1111-4111-8111-111111111109', true, 'spice', 'sub', 1.00, 8.00, '1.5 muỗng cà phê', 5),
    ('22222222-2222-4222-8222-222222222212', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 10.00, '2 muỗng cà phê', 6),
    ('22222222-2222-4222-8222-222222222212', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/3 muỗng cà phê', 7),
    -- 13. Cá kho gừng (VN — 40m)
    ('22222222-2222-4222-8222-222222222213', '11111111-1111-4111-8111-111111111215', true, 'core', 'main', 4.00, 400.00, '1 con làm sạch cắt khúc', 1),
    ('22222222-2222-4222-8222-222222222213', '11111111-1111-4111-8111-111111111216', true, 'secondary', 'sub', 2.00, 25.00, '1 củ thái sợi', 2),
    ('22222222-2222-4222-8222-222222222213', '11111111-1111-4111-8111-111111111206', false, 'optional', 'sub', 0.00, 8.00, '1 quả', 3),
    ('22222222-2222-4222-8222-222222222213', '11111111-1111-4111-8111-111111111105', false, 'optional', 'sub', 0.00, 15.00, '2 nhánh', 4),
    ('22222222-2222-4222-8222-222222222213', '11111111-1111-4111-8111-111111111107', true, 'spice', 'sub', 1.00, 25.00, '2 muỗng canh', 5),
    ('22222222-2222-4222-8222-222222222213', '11111111-1111-4111-8111-111111111109', true, 'spice', 'sub', 1.00, 10.00, '2 muỗng cà phê', 6),
    ('22222222-2222-4222-8222-222222222213', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 10.00, '2 muỗng cà phê', 7),
    ('22222222-2222-4222-8222-222222222213', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/2 muỗng cà phê', 8),
    -- 14. Thịt heo hầm khoai tây cà rốt (VN — 45m)
    ('22222222-2222-4222-8222-222222222214', '11111111-1111-4111-8111-111111111213', true, 'core', 'main', 4.00, 300.00, '300 g cắt khối', 1),
    ('22222222-2222-4222-8222-222222222214', '11111111-1111-4111-8111-111111111202', true, 'secondary', 'sub', 2.00, 200.00, '2 củ cắt khối', 2),
    ('22222222-2222-4222-8222-222222222214', '11111111-1111-4111-8111-111111111203', true, 'secondary', 'sub', 2.00, 120.00, '1 củ cắt khoanh', 3),
    ('22222222-2222-4222-8222-222222222214', '11111111-1111-4111-8111-111111111204', true, 'spice', 'sub', 1.00, 60.00, '1/2 củ bổ múi', 4),
    ('22222222-2222-4222-8222-222222222214', '11111111-1111-4111-8111-111111111105', false, 'optional', 'sub', 0.00, 15.00, '2 nhánh', 5),
    ('22222222-2222-4222-8222-222222222214', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 5.00, '1 muỗng cà phê', 6),
    ('22222222-2222-4222-8222-222222222214', '11111111-1111-4111-8111-111111111107', true, 'spice', 'sub', 1.00, 10.00, '1 muỗng canh', 7),
    ('22222222-2222-4222-8222-222222222214', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/2 muỗng cà phê', 8),
    -- 15. Thịt bò xào bông cải xanh nấm (VN — 18m)
    ('22222222-2222-4222-8222-222222222215', '11111111-1111-4111-8111-111111111301', true, 'core', 'main', 4.00, 200.00, '200 g thái mỏng', 1),
    ('22222222-2222-4222-8222-222222222215', '11111111-1111-4111-8111-111111111209', true, 'core', 'main', 4.00, 200.00, '1 bông tách nhánh', 2),
    ('22222222-2222-4222-8222-222222222215', '11111111-1111-4111-8111-111111111210', true, 'secondary', 'sub', 2.00, 100.00, '100 g thái lát', 3),
    ('22222222-2222-4222-8222-222222222215', '11111111-1111-4111-8111-111111111205', true, 'spice', 'sub', 1.00, 10.00, '2 tép băm', 4),
    ('22222222-2222-4222-8222-222222222215', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 12.00, '1 muỗng canh', 5),
    ('22222222-2222-4222-8222-222222222215', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 4.00, '1/2 muỗng cà phê', 6),
    ('22222222-2222-4222-8222-222222222215', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/3 muỗng cà phê', 7),
    -- 16. Bắp cải xào nấm tỏi (VN — 14m)
    ('22222222-2222-4222-8222-222222222216', '11111111-1111-4111-8111-111111111208', true, 'core', 'main', 4.00, 250.00, '1/4 bắp thái sợi', 1),
    ('22222222-2222-4222-8222-222222222216', '11111111-1111-4111-8111-111111111210', true, 'secondary', 'sub', 2.00, 100.00, '100 g thái lát', 2),
    ('22222222-2222-4222-8222-222222222216', '11111111-1111-4111-8111-111111111205', true, 'spice', 'sub', 1.00, 10.00, '2 tép đập dập', 3),
    ('22222222-2222-4222-8222-222222222216', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 10.00, '2 muỗng cà phê', 4),
    ('22222222-2222-4222-8222-222222222216', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 4.00, '1/2 muỗng cà phê', 5),
    -- 17. Dưa leo trộn tỏi ớt (VN — 10m)
    ('22222222-2222-4222-8222-222222222217', '11111111-1111-4111-8111-111111111207', true, 'core', 'main', 4.00, 250.00, '2 quả đập dập', 1),
    ('22222222-2222-4222-8222-222222222217', '11111111-1111-4111-8111-111111111205', true, 'spice', 'sub', 1.00, 10.00, '2 tép băm', 2),
    ('22222222-2222-4222-8222-222222222217', '11111111-1111-4111-8111-111111111206', true, 'spice', 'sub', 1.00, 8.00, '1 quả băm', 3),
    ('22222222-2222-4222-8222-222222222217', '11111111-1111-4111-8111-111111111311', false, 'optional', 'sub', 0.00, 20.00, '1/2 quả vắt nước', 4),
    ('22222222-2222-4222-8222-222222222217', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 3.00, '1/2 muỗng cà phê', 5),
    ('22222222-2222-4222-8222-222222222217', '11111111-1111-4111-8111-111111111109', true, 'spice', 'sub', 1.00, 8.00, '1.5 muỗng cà phê', 6),
    -- 18. Thịt bò xào ớt chuông hành tây kiểu Âu (EU — 20m)
    ('22222222-2222-4222-8222-222222222218', '11111111-1111-4111-8111-111111111301', true, 'core', 'main', 4.00, 220.00, '220 g cắt khối', 1),
    ('22222222-2222-4222-8222-222222222218', '11111111-1111-4111-8111-111111111218', true, 'core', 'main', 4.00, 160.00, '1 quả cắt miếng vuông', 2),
    ('22222222-2222-4222-8222-222222222218', '11111111-1111-4111-8111-111111111204', true, 'secondary', 'sub', 2.00, 80.00, '1/2 củ cắt múi', 3),
    ('22222222-2222-4222-8222-222222222218', '11111111-1111-4111-8111-111111111205', true, 'spice', 'sub', 1.00, 10.00, '2 tép băm', 4),
    ('22222222-2222-4222-8222-222222222218', '11111111-1111-4111-8111-111111111303', true, 'spice', 'sub', 1.00, 15.00, '1 muỗng canh', 5),
    ('22222222-2222-4222-8222-222222222218', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 4.00, '1/2 muỗng cà phê', 6),
    ('22222222-2222-4222-8222-222222222218', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/2 muỗng cà phê', 7),
    -- 19. Bắp ngọt áp chảo bơ tỏi kiểu Mỹ (US — 15m)
    ('22222222-2222-4222-8222-222222222219', '11111111-1111-4111-8111-111111111219', true, 'core', 'main', 4.00, 200.00, '1 trái tách hạt', 1),
    ('22222222-2222-4222-8222-222222222219', '11111111-1111-4111-8111-111111111303', true, 'secondary', 'sub', 2.00, 20.00, '1.5 muỗng canh', 2),
    ('22222222-2222-4222-8222-222222222219', '11111111-1111-4111-8111-111111111205', true, 'spice', 'sub', 1.00, 8.00, '2 tép băm', 3),
    ('22222222-2222-4222-8222-222222222219', '11111111-1111-4111-8111-111111111105', false, 'optional', 'sub', 0.00, 10.00, '1 nhánh cắt nhỏ', 4),
    ('22222222-2222-4222-8222-222222222219', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 3.00, '1/3 muỗng cà phê', 5),
    ('22222222-2222-4222-8222-222222222219', '11111111-1111-4111-8111-111111111110', true, 'spice', 'sub', 1.00, 2.00, '1/3 muỗng cà phê', 6),
    -- 20. Rau muống xào tỏi (VN — 12m)
    ('22222222-2222-4222-8222-222222222220', '11111111-1111-4111-8111-111111111312', true, 'core', 'main', 4.00, 300.00, '1 bó nhặt sạch', 1),
    ('22222222-2222-4222-8222-222222222220', '11111111-1111-4111-8111-111111111205', true, 'secondary', 'sub', 2.00, 15.00, '4 tép đập dập', 2),
    ('22222222-2222-4222-8222-222222222220', '11111111-1111-4111-8111-111111111108', true, 'spice', 'sub', 1.00, 12.00, '1 muỗng canh', 3),
    ('22222222-2222-4222-8222-222222222220', '11111111-1111-4111-8111-111111111106', true, 'spice', 'sub', 1.00, 3.00, '1/2 muỗng cà phê', 4),
    ('22222222-2222-4222-8222-222222222220', '11111111-1111-4111-8111-111111111107', true, 'spice', 'sub', 1.00, 8.00, '1.5 muỗng cà phê', 5)
ON CONFLICT (recipe_id, ingredient_id) DO UPDATE
SET is_required = EXCLUDED.is_required,
    role = EXCLUDED.role,
    dish_role = EXCLUDED.dish_role,
    weight = EXCLUDED.weight,
    grams = EXCLUDED.grams,
    display_quantity = EXCLUDED.display_quantity,
    sort_order = EXCLUDED.sort_order;

-- Every step estimated_minutes <= prep_minutes + cook_minutes (BR-01, BR-05)
INSERT INTO public.recipe_steps (recipe_id, step_no, instruction, estimated_minutes)
VALUES
    -- 1. Đậu hũ sốt cà chua (total = 30m)
    ('22222222-2222-4222-8222-222222222201', 1, 'Cắt đậu hũ thành miếng vuông vừa ăn, chiên vàng đều các mặt với dầu ăn.', 10),
    ('22222222-2222-4222-8222-222222222201', 2, 'Băm nhỏ cà chua, xào nhừ với muối rồi cho đậu hũ vào rim lửa nhỏ 20 phút và rắc hành lá.', 20),
    -- 2. Canh cà chua trứng (total = 15m)
    ('22222222-2222-4222-8222-222222222202', 1, 'Thái múi cau cà chua, xào sơ với dầu ăn và muối rồi thêm nước đun sôi.', 7),
    ('22222222-2222-4222-8222-222222222202', 2, 'Đánh tan trứng gà, rót từ từ vào nồi nước sôi khuấy nhẹ tạo vân mây, thêm hành lá rồi tắt bếp.', 5),
    -- 3. Cà chua nhồi thịt sốt trứng (total = 25m)
    ('22222222-2222-4222-8222-222222222203', 1, 'Cắt nắp cà chua, khoét ruột giữ lại phần thịt cà; trộn thịt heo sống băm nhuyễn với tiêu và nước mắm rồi nhồi đều vào quả cà chua.', 10),
    ('22222222-2222-4222-8222-222222222203', 2, 'Áp chảo mặt thịt của cà chua cho săn chín kỹ ở tâm, sau đó thêm phần ruột cà chua băm vào rim lửa nhỏ cho thịt chín hoàn toàn.', 11),
    ('22222222-2222-4222-8222-222222222203', 3, 'Đánh tan trứng gà rưới nhẹ vào phần nước sốt cà chua đang sôi lăn tăn để tạo sốt sánh mịn, rắc hành lá trước khi dọn.', 4),
    -- 4. Trứng xào cà chua (total = 15m)
    ('22222222-2222-4222-8222-222222222204', 1, 'Đánh tan trứng gà với 1/2 muỗng cà phê nước mắm, xào chín tới trên chảo dầu nóng rồi trút riêng ra đĩa.', 5),
    ('22222222-2222-4222-8222-222222222204', 2, 'Xào mềm cà chua thái múi với phần nước mắm còn lại, trút trứng vào đảo đều trên lửa vừa rồi thêm hành lá.', 10),
    -- 5. Mì Ý sốt cà chua thịt băm (total = 30m)
    ('22222222-2222-4222-8222-222222222205', 1, 'Luộc mì Ý trong nước sôi có pha chút muối khoảng 9 phút cho chín dẻo rồi để ráo.', 10),
    ('22222222-2222-4222-8222-222222222205', 2, 'Phi thơm hành tây và tỏi băm với dầu ăn, cho thịt bò băm vào đảo tơi đến khi chín săn.', 8),
    ('22222222-2222-4222-8222-222222222205', 3, 'Thêm cà chua băm nhuyễn, muối và hạt tiêu vào đun sánh 10 phút rồi trộn đều cùng mì Ý.', 12),
    -- 6. Bông cải xanh và nấm áp chảo bơ tỏi (total = 14m)
    ('22222222-2222-4222-8222-222222222206', 1, 'Rửa sạch bông cải xanh và nấm tươi, cắt miếng vừa ăn và để thật ráo nước.', 6),
    ('22222222-2222-4222-8222-222222222206', 2, 'Đun chảy bơ lạt cùng tỏi băm, cho nấm và bông cải xanh vào áp chảo lửa vừa với muối tiêu đến khi chín kỹ.', 8),
    -- 7. Burger bò phô mai kiểu Mỹ (total = 22m)
    ('22222222-2222-4222-8222-222222222207', 1, 'Ướp nhẹ thịt bò xay với muối và hạt tiêu, nắn thành 2 viên dẹt đều nhau; rửa sạch xà lách, cắt lát cà chua và hành tây.', 10),
    ('22222222-2222-4222-8222-222222222207', 2, 'Áp chảo viên thịt bò chín kỹ hai mặt, đặt lát phô mai Cheddar lên mặt thịt nóng cho chảy nhẹ rồi kẹp vào vỏ bánh Burger đã áp chảo cùng rau.', 12),
    -- 8. Bắp ngọt và khoai tây đút lò bơ tỏi (total = 35m)
    ('22222222-2222-4222-8222-222222222208', 1, 'Gọt vỏ khoai tây cắt múi cau, tách hạt bắp ngọt rồi trộn đều cùng bơ lạt đun chảy, tỏi băm, muối và tiêu.', 10),
    ('22222222-2222-4222-8222-222222222208', 2, 'Dàn đều khoai tây và bắp ngọt lên khay, đút lò ở 200 độ C trong 25 phút cho chín vàng thơm rồi rắc hành lá.', 25),
    -- 9. Gà hấp sả (total = 30m)
    ('22222222-2222-4222-8222-222222222209', 1, 'Xát muối rửa sạch thịt gà, ướp với muối và hạt tiêu 10 phút; đập dập sả lót đáy nồi.', 10),
    ('22222222-2222-4222-8222-222222222209', 2, 'Đặt gà lên lớp sả, thêm lá chanh và gừng nếu có rồi hấp cách thủy lửa vừa 20 phút cho chín kỹ.', 20),
    -- 10. Gà kho sả nghệ (total = 35m)
    ('22222222-2222-4222-8222-222222222210', 1, 'Ướp thịt gà chặt miếng cùng nghệ tươi giã nhuyễn, nửa phần sả băm, nước mắm và đường 10 phút.', 10),
    ('22222222-2222-4222-8222-222222222210', 2, 'Phi thơm phần sả còn lại với dầu ăn, cho gà vào đảo săn rồi rim lửa nhỏ 25 phút đến khi sánh vị.', 25),
    -- 11. Gà xào sả ớt (total = 22m)
    ('22222222-2222-4222-8222-222222222211', 1, 'Cắt thịt gà miếng vừa ăn, ướp nhanh với nước mắm; băm nhỏ sả, tỏi và cắt lát ớt.', 10),
    ('22222222-2222-4222-8222-222222222211', 2, 'Phi thơm sả, tỏi và ớt trong dầu nóng rồi xào gà lửa lớn 12 phút cho săn vàng thơm.', 12),
    -- 12. Tôm rang hành tỏi (total = 18m)
    ('22222222-2222-4222-8222-222222222212', 1, 'Cắt râu, rút chỉ lưng tôm tươi, rửa sạch để ráo; băm tỏi và cắt khúc hành lá.', 8),
    ('22222222-2222-4222-8222-222222222212', 2, 'Phi thơm tỏi với dầu ăn, đảo tôm săn đỏ rồi nêm nước mắm, đường rim cạn sốt, rắc hành tiêu.', 10),
    -- 13. Cá kho gừng (total = 40m)
    ('22222222-2222-4222-8222-222222222213', 1, 'Làm sạch cá cắt khúc, ướp với nước mắm, tiêu và nửa phần gừng thái sợi trong 10 phút.', 10),
    ('22222222-2222-4222-8222-222222222213', 2, 'Thắng nhẹ đường với dầu ăn tạo màu cánh gián, xếp cá và phần gừng còn lại kho lửa nhỏ 30 phút.', 30),
    -- 14. Thịt heo hầm khoai tây cà rốt (total = 45m)
    ('22222222-2222-4222-8222-222222222214', 1, 'Sơ chế thịt heo, gọt vỏ cắt khối khoai tây, cà rốt và hành tây; chần sơ thịt cho trong nước.', 15),
    ('22222222-2222-4222-8222-222222222214', 2, 'Hầm thịt heo 15 phút rồi thêm khoai tây, cà rốt, hành tây nấu mềm thêm 15 phút, nêm muối mắm tiêu.', 30),
    -- 15. Thịt bò xào bông cải xanh nấm (total = 18m)
    ('22222222-2222-4222-8222-222222222215', 1, 'Ướp thịt bò thái mỏng với chút tỏi băm, muối tiêu; chần nhanh bông cải xanh 2 phút giữ màu xanh.', 8),
    ('22222222-2222-4222-8222-222222222215', 2, 'Xào nhanh thịt bò lửa lớn rồi trút riêng; xào nấm và bông cải xanh chín tới rồi đảo đều cùng bò.', 10),
    -- 16. Bắp cải xào nấm tỏi (total = 14m)
    ('22222222-2222-4222-8222-222222222216', 1, 'Thái sợi bắp cải, rửa sạch nấm và đập dập tỏi.', 6),
    ('22222222-2222-4222-8222-222222222216', 2, 'Phi thơm tỏi với dầu ăn, cho nấm và bắp cải vào xào nhanh lửa lớn 8 phút, nêm muối vừa ăn.', 8),
    -- 17. Dưa leo trộn tỏi ớt (total = 10m)
    ('22222222-2222-4222-8222-222222222217', 1, 'Rửa sạch dưa leo, đập dập cắt khúc vừa ăn rồi trộn đều cùng tỏi ớt băm, muối, đường và nước cốt chanh.', 10),
    -- 18. Thịt bò xào ớt chuông hành tây kiểu Âu (total = 20m)
    ('22222222-2222-4222-8222-222222222218', 1, 'Cắt thịt bò, ớt chuông và hành tây thành miếng vuông đồng đều; ướp thịt bò với muối và hạt tiêu.', 8),
    ('22222222-2222-4222-8222-222222222218', 2, 'Đun chảy bơ lạt với tỏi băm, áp chảo thịt bò săn mặt rồi đảo nhanh cùng ớt chuông và hành tây.', 12),
    -- 19. Bắp ngọt áp chảo bơ tỏi kiểu Mỹ (total = 15m)
    ('22222222-2222-4222-8222-222222222219', 1, 'Tách hạt bắp ngọt, rửa sạch để ráo; băm nhỏ tỏi và cắt nhỏ hành lá.', 5),
    ('22222222-2222-4222-8222-222222222219', 2, 'Đun chảy bơ lạt, phi thơm tỏi rồi áp chảo bắp ngọt lửa vừa 10 phút với muối tiêu, rắc hành lá.', 10),
    -- 20. Rau muống xào tỏi (total = 12m)
    ('22222222-2222-4222-8222-222222222220', 1, 'Nhặt sạch rau muống, rửa ráo và đập dập tỏi.', 5),
    ('22222222-2222-4222-8222-222222222220', 2, 'Phi thơm nửa phần tỏi, xào rau muống trên lửa lớn 7 phút với muối, nước mắm rồi thêm phần tỏi còn lại.', 7)
ON CONFLICT (recipe_id, step_no) DO UPDATE
SET instruction = EXCLUDED.instruction,
    estimated_minutes = EXCLUDED.estimated_minutes;

COMMIT;
