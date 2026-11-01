-- ============================================================================
-- FOODVISION AI - SEED DATA (12 NHÃN YOLO, NGUỒN DINH DƯỠNG & 5 MÓN MẪU TUẦN 1)
-- ============================================================================

-- 1. Nhập 12 nguyên liệu chính thuộc phạm vi nhận diện YOLO
INSERT INTO public.ingredients (id, name, normalized_name, yolo_class, is_active) VALUES
(1, 'Cà chua', 'ca_chua', 'tomato', TRUE),
(2, 'Cà rốt', 'ca_rot', 'carrot', TRUE),
(3, 'Khoai tây', 'khoai_tay', 'potato', TRUE),
(4, 'Hành tây', 'hanh_tay', 'onion', TRUE),
(5, 'Dưa leo', 'dua_leo', 'cucumber', TRUE),
(6, 'Trứng gà (nguyên vỏ)', 'trung_ga', 'egg', TRUE),
(7, 'Bắp cải', 'bap_cai', 'cabbage', TRUE),
(8, 'Ớt chuông', 'ot_chuong', 'bell_pepper', TRUE),
(9, 'Bí đỏ', 'bi_do', 'pumpkin', TRUE),
(10, 'Tỏi', 'toi', 'garlic', TRUE),
(11, 'Hành lá', 'hanh_la', 'green_onion', TRUE),
(12, 'Chanh', 'chanh', 'lemon', TRUE)
ON CONFLICT (id) DO NOTHING;

-- 2. Nhập 2 nguồn tham khảo dinh dưỡng chuẩn
INSERT INTO public.nutrition_sources (id, title, publisher, url_or_reference, accessed_at) VALUES
(1, 'Bảng thành phần thực phẩm Việt Nam (Vietnamese Food Composition Table)', 'Viện Dinh dưỡng Quốc gia - Bộ Y tế', 'https://viendinhduong.vn', '2026-11-01'),
(2, 'USDA FoodData Central (Foundation Foods & SR Legacy)', 'U.S. Department of Agriculture (USDA)', 'https://fdc.nal.usda.gov', '2026-11-01')
ON CONFLICT (id) DO NOTHING;

-- 3. Nhập danh mục các nhóm/chất dinh dưỡng tiêu biểu (Định tính)
INSERT INTO public.nutrients (id, code, name, nutrient_group) VALUES
(1, 'PROTEIN', 'Protein (Chất đạm)', 'Chất đa lượng'),
(2, 'LIPID', 'Chất béo (Lipid)', 'Chất đa lượng'),
(3, 'CARB', 'Carbohydrate (Chất bột đường)', 'Chất đa lượng'),
(4, 'FIBER', 'Chất xơ', 'Chất xơ'),
(5, 'VIT_A', 'Vitamin A / Beta-carotene', 'Vitamin'),
(6, 'VIT_C', 'Vitamin C', 'Vitamin'),
(7, 'VIT_B12', 'Vitamin B12', 'Vitamin'),
(8, 'POTASSIUM', 'Kali (Potassium)', 'Khoáng chất'),
(9, 'FOLATE', 'Folate (Vitamin B9)', 'Vitamin'),
(10, 'ALICIN_ANTIOX', 'Hợp chất lưu huỳnh tự nhiên & khoáng chất vi lượng', 'Vi chất thực vật')
ON CONFLICT (id) DO NOTHING;

-- 4. Ánh xạ Nguyên liệu - Chất dinh dưỡng có nguồn (ingredient_nutrients)
INSERT INTO public.ingredient_nutrients (ingredient_id, nutrient_id, source_id, food_form, note) VALUES
-- Cà chua (id=1)
(1, 6, 1, 'quả tươi', 'Có thể cung cấp Vitamin C'),
(1, 8, 2, 'quả tươi', 'Có thể cung cấp Kali'),
(1, 4, 1, 'quả tươi', 'Có thể cung cấp Chất xơ'),
-- Cà rốt (id=2)
(2, 5, 1, 'củ tươi', 'Có thể cung cấp Beta-carotene (tiền chất Vitamin A)'),
(2, 4, 1, 'củ tươi', 'Có thể cung cấp Chất xơ'),
(2, 8, 2, 'củ tươi', 'Có thể cung cấp Kali'),
-- Khoai tây (id=3)
(3, 3, 1, 'củ tươi (nấu chín)', 'Có thể cung cấp Carbohydrate'),
(3, 8, 2, 'củ tươi (nấu chín)', 'Có thể cung cấp Kali'),
(3, 6, 2, 'củ tươi (nấu chín)', 'Có thể cung cấp Vitamin C'),
-- Hành tây (id=4)
(4, 4, 1, 'củ tươi', 'Có thể cung cấp Chất xơ'),
(4, 6, 2, 'củ tươi', 'Có thể cung cấp Vitamin C'),
-- Dưa leo (id=5)
(5, 4, 1, 'quả tươi', 'Có thể cung cấp Chất xơ'),
(5, 8, 2, 'quả tươi', 'Có thể cung cấp Kali'),
-- Trứng gà (id=6)
(6, 1, 1, 'trứng gà nguyên quả', 'Có thể cung cấp Protein'),
(6, 2, 1, 'trứng gà nguyên quả', 'Có thể cung cấp Chất béo'),
(6, 7, 2, 'trứng gà nguyên quả', 'Có thể cung cấp Vitamin B12'),
-- Bắp cải (id=7)
(7, 4, 1, 'lá tươi', 'Có thể cung cấp Chất xơ'),
(7, 6, 1, 'lá tươi', 'Có thể cung cấp Vitamin C'),
(7, 9, 2, 'lá tươi', 'Có thể cung cấp Folate'),
-- Ớt chuông (id=8)
(8, 6, 2, 'quả tươi', 'Có thể cung cấp Vitamin C'),
(8, 5, 2, 'quả tươi', 'Có thể cung cấp Vitamin A'),
(8, 4, 1, 'quả tươi', 'Có thể cung cấp Chất xơ'),
-- Bí đỏ (id=9)
(9, 5, 1, 'thịt quả tươi', 'Có thể cung cấp Beta-carotene (tiền chất Vitamin A)'),
(9, 3, 1, 'thịt quả tươi', 'Có thể cung cấp Carbohydrate'),
(9, 4, 1, 'thịt quả tươi', 'Có thể cung cấp Chất xơ'),
-- Tỏi (id=10)
(10, 10, 1, 'tép tươi', 'Có thể cung cấp hợp chất lưu huỳnh tự nhiên và khoáng vi lượng'),
-- Hành lá (id=11)
(11, 6, 1, 'lá tươi', 'Có thể cung cấp Vitamin C'),
(11, 4, 1, 'lá tươi', 'Có thể cung cấp Chất xơ'),
-- Chanh (id=12)
(12, 6, 1, 'nước cốt tươi', 'Có thể cung cấp Vitamin C')
ON CONFLICT (ingredient_id, nutrient_id, food_form) DO NOTHING;

-- 5. Nhập 5 Công thức Món Việt Mẫu (Tuần 1)
INSERT INTO public.recipes (id, name, description, cooking_time, instructions) VALUES
(1, 'Trứng xào cà chua (Canh trứng cà chua)', 'Món ăn gia đình nhanh gọn, kết hợp vị chua dịu của cà chua và vị béo mềm của trứng gà.', 10, '1. Đập trứng ra bát, đánh tan với chút gia vị.\n2. Cà chua rửa sạch, bổ múi cau; hành lá cắt nhỏ.\n3. Phi thơm hành/tỏi, cho cà chua vào xào mềm, đổ trứng vào đảo đều tay đến khi chín tới, rắc hành lá.'),
(2, 'Trứng chiên hành tây', 'Trứng chiên vàng ươm dậy mùi thơm ngọt tự nhiên từ hành tây cắt lát.', 10, '1. Hành tây bóc vỏ, thái lát mỏng.\n2. Đánh tan trứng gà cùng hành lá cắt nhỏ.\n3. Xào sơ hành tây cho dậy mùi thơm, đổ trứng vào tráng đều hai mặt đến khi chín vàng.'),
(3, 'Canh cà rốt khoai tây', 'Món canh thanh ngọt tự nhiên từ củ quả, thích hợp cho bữa cơm gia đình.', 25, '1. Khoai tây, cà rốt gọt vỏ, rửa sạch và cắt miếng vừa ăn.\n2. Phi thơm hành tím/tỏi, cho cà rốt vào đảo sơ rồi thêm nước đun sôi.\n3. Cho khoai tây vào hầm mềm, nêm gia vị vừa ăn và rắc hành lá trước khi tắt bếp.'),
(4, 'Bắp cải xào cà chua tỏi', 'Món rau xào dân dã, giòn ngọt với màu sắc bắt mắt từ cà chua và hương thơm của tỏi.', 12, '1. Bắp cải thái sợi vừa ăn, rửa sạch để ráo; cà chua bổ múi cau; tỏi đập dập.\n2. Phi thơm tỏi trên lửa lớn, cho cà chua vào đảo sơ tạo màu.\n3. Cho bắp cải vào xào nhanh tay trên lửa lớn để giữ độ giòn, thêm hành lá rồi tắt bếp.'),
(5, 'Salad dưa leo cà chua sốt chanh', 'Món trộn thanh mát, chế biến nhanh không qua nhiệt, giữ trọn độ tươi của rau củ.', 8, '1. Dưa leo, cà chua rửa sạch, thái lát vừa ăn; hành tây thái mỏng ngâm nước đá cho bớt hăng.\n2. Pha nước cốt chanh với một chút tỏi băm và gia vị cơ bản.\n3. Trộn đều dưa leo, cà chua, hành tây với nước sốt chanh trước khi dùng 5 phút.')
ON CONFLICT (id) DO NOTHING;

-- 6. Liên kết Công thức - Nguyên liệu (recipe_ingredients) với Trọng số (3=Chính, 2=Phụ, 1=Tùy chọn)
INSERT INTO public.recipe_ingredients (recipe_id, ingredient_id, amount, unit, importance, is_optional) VALUES
-- Món 1: Trứng xào cà chua
(1, 6, '2', 'quả', 3, FALSE),   -- Trứng gà (Chính)
(1, 1, '2', 'quả', 3, FALSE),   -- Cà chua (Chính)
(1, 11, '2', 'nhánh', 1, TRUE), -- Hành lá (Tùy chọn)
-- Món 2: Trứng chiên hành tây
(2, 6, '3', 'quả', 3, FALSE),   -- Trứng gà (Chính)
(2, 4, '1/2', 'củ', 3, FALSE),  -- Hành tây (Chính)
(2, 11, '1', 'nhánh', 1, TRUE), -- Hành lá (Tùy chọn)
-- Món 3: Canh cà rốt khoai tây
(3, 2, '1', 'củ', 3, FALSE),    -- Cà rốt (Chính)
(3, 3, '2', 'củ', 3, FALSE),    -- Khoai tây (Chính)
(3, 11, '2', 'nhánh', 1, TRUE), -- Hành lá (Tùy chọn)
-- Món 4: Bắp cải xào cà chua tỏi
(4, 7, '300', 'g', 3, FALSE),   -- Bắp cải (Chính)
(4, 1, '1', 'quả', 2, FALSE),   -- Cà chua (Phụ)
(4, 10, '3', 'tép', 2, FALSE),  -- Tỏi (Phụ)
(4, 11, '1', 'nhánh', 1, TRUE), -- Hành lá (Tùy chọn)
-- Món 5: Salad dưa leo cà chua sốt chanh
(5, 5, '2', 'quả', 3, FALSE),   -- Dưa leo (Chính)
(5, 1, '2', 'quả', 3, FALSE),   -- Cà chua (Chính)
(5, 12, '1', 'quả', 2, FALSE),  -- Chanh (Phụ)
(5, 4, '1/4', 'củ', 1, TRUE)    -- Hành tây (Tùy chọn)
ON CONFLICT (recipe_id, ingredient_id) DO NOTHING;

