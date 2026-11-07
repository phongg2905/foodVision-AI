-- ============================================================================
-- Migration: 20261104000001_initial_schema.sql
-- Project  : FoodVision AI (v1.0.0 Official Baseline)
-- Scope    : Stage 1 (TP 03 Knowledge Base & TP 13 Vietnamese Trigram Search)
--            16 Core Tables (v1.0) + 4 Extended Tables (v1.1) + RPC Functions
-- Target   : Supabase PostgreSQL >= 15
-- ============================================================================

BEGIN;

-- 0. Verify PostgreSQL >= 15 (required for UNIQUE NULLS NOT DISTINCT)
DO $$
BEGIN
    IF current_setting('server_version_num')::int < 150000 THEN
        RAISE EXCEPTION 'FoodVision AI requires PostgreSQL >= 15 (detected version_num = %)',
            current_setting('server_version_num');
    END IF;
END
$$;

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Vietnamese Normalization Function (TP 13: Norm(s))
-- Converts string to lowercase, replaces đ/Đ -> d, strips accents via unaccent,
-- and collapses whitespace.
CREATE OR REPLACE FUNCTION public.norm_vi(input_text text)
RETURNS text
LANGUAGE sql
IMMUTABLE
STRICT
PARALLEL SAFE
AS $$
    SELECT trim(
        regexp_replace(
            public.unaccent(
                replace(replace(lower(input_text), 'đ', 'd'), 'Đ', 'd')
            ),
            '\s+',
            ' ',
            'g'
        )
    );
$$;

-- Helper trigger function for updated_at columns
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- ============================================================================
-- CORE TABLES (1..16) — Data Dictionary v1.0.0
-- ============================================================================

-- 1. profiles (linked to Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name varchar(100),
    role varchar(10) NOT NULL DEFAULT 'user'
        CONSTRAINT chk_profiles_role CHECK (role IN ('user', 'admin')),
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Trigger to auto-create profile when a new user signs up in auth.users
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, display_name, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data ->> 'display_name', split_part(NEW.email, '@', 1)),
        'user'
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();

-- 2. ingredients
CREATE TABLE IF NOT EXISTS public.ingredients (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug text NOT NULL UNIQUE
        CONSTRAINT chk_ingredients_slug_nonempty CHECK (btrim(slug) <> ''),
    name_vi text NOT NULL
        CONSTRAINT chk_ingredients_name_vi_nonempty CHECK (btrim(name_vi) <> ''),
    category varchar(40) NOT NULL
        CONSTRAINT chk_ingredients_category CHECK (
            category IN ('vegetable', 'protein', 'seafood', 'spice', 'pantry', 'other')
        ),
    fdc_id varchar(32),
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 3. ingredient_aliases (TP 13 — Regional synonyms & Vietnamese trigram search)
CREATE TABLE IF NOT EXISTS public.ingredient_aliases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ingredient_id uuid NOT NULL REFERENCES public.ingredients(id) ON DELETE CASCADE,
    alias text NOT NULL
        CONSTRAINT chk_ingredient_aliases_nonempty CHECK (btrim(alias) <> ''),
    normalized_alias text NOT NULL,
    locale varchar(10) NOT NULL DEFAULT 'vi'
        CONSTRAINT chk_ingredient_aliases_locale CHECK (locale IN ('vi', 'en')),
    CONSTRAINT uq_ingredient_aliases_norm UNIQUE (ingredient_id, normalized_alias, locale)
);

CREATE OR REPLACE FUNCTION public.sync_normalized_alias()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.normalized_alias := public.norm_vi(NEW.alias);
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_sync_normalized_alias ON public.ingredient_aliases;
CREATE TRIGGER trg_sync_normalized_alias
    BEFORE INSERT OR UPDATE OF alias, normalized_alias ON public.ingredient_aliases
    FOR EACH ROW EXECUTE FUNCTION public.sync_normalized_alias();

CREATE INDEX IF NOT EXISTS idx_alias_trgm
    ON public.ingredient_aliases
    USING GIN (normalized_alias gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_ingredients_name_trgm
    ON public.ingredients
    USING GIN (public.norm_vi(name_vi) gin_trgm_ops);

-- 4. ai_models
CREATE TABLE IF NOT EXISTS public.ai_models (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    version text NOT NULL UNIQUE
        CONSTRAINT chk_ai_models_version_nonempty CHECK (btrim(version) <> ''),
    family text NOT NULL,
    dataset_version text NOT NULL,
    artifact_ref text NOT NULL,
    class_count integer NOT NULL DEFAULT 20
        CONSTRAINT chk_ai_models_class_count CHECK (class_count > 0),
    confidence_threshold numeric(4,3) NOT NULL DEFAULT 0.250
        CONSTRAINT chk_ai_models_conf_threshold CHECK (
            confidence_threshold >= 0.000 AND confidence_threshold <= 1.000
        ),
    review_threshold numeric(4,3) NOT NULL DEFAULT 0.800
        CONSTRAINT chk_ai_models_review_threshold CHECK (
            review_threshold >= 0.000 AND review_threshold <= 1.000
        ),
    status varchar(12) NOT NULL DEFAULT 'draft'
        CONSTRAINT chk_ai_models_status CHECK (status IN ('draft', 'active', 'archived')),
    created_at timestamptz NOT NULL DEFAULT now()
);

-- At most 1 active AI model at any time (BR-02)
CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_models_single_active
    ON public.ai_models ((status))
    WHERE status = 'active';

-- 5. ai_labels
CREATE TABLE IF NOT EXISTS public.ai_labels (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id uuid NOT NULL REFERENCES public.ai_models(id) ON DELETE CASCADE,
    class_index integer NOT NULL
        CONSTRAINT chk_ai_labels_class_index CHECK (class_index >= 0),
    class_name text NOT NULL
        CONSTRAINT chk_ai_labels_class_name CHECK (btrim(class_name) <> ''),
    ingredient_id uuid NOT NULL REFERENCES public.ingredients(id) ON DELETE RESTRICT,
    CONSTRAINT uq_ai_labels_model_class UNIQUE (model_id, class_index)
);

-- 6. recipes
CREATE TABLE IF NOT EXISTS public.recipes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug text NOT NULL UNIQUE
        CONSTRAINT chk_recipes_slug_nonempty CHECK (btrim(slug) <> ''),
    name_vi text NOT NULL
        CONSTRAINT chk_recipes_name_vi_nonempty CHECK (btrim(name_vi) <> ''),
    description text,
    cuisine_code varchar(2) NOT NULL
        CONSTRAINT chk_recipes_cuisine_code CHECK (cuisine_code IN ('VN', 'EU', 'US')),
    country_code varchar(2),
    cooking_method varchar(30),
    required_equipment text[] NOT NULL DEFAULT '{}',
    base_servings smallint NOT NULL DEFAULT 2
        CONSTRAINT chk_recipes_base_servings CHECK (base_servings >= 1),
    prep_minutes integer NOT NULL
        CONSTRAINT chk_recipes_prep_minutes CHECK (prep_minutes >= 0),
    cook_minutes integer NOT NULL
        CONSTRAINT chk_recipes_cook_minutes CHECK (cook_minutes >= 0),
    quality_score numeric(4,3) NOT NULL DEFAULT 1.000
        CONSTRAINT chk_recipes_quality_score CHECK (quality_score >= 0.000 AND quality_score <= 1.000),
    cover_image_path text,
    source_name text,
    source_url text,
    content_license text,
    status varchar(12) NOT NULL DEFAULT 'draft'
        CONSTRAINT chk_recipes_status CHECK (status IN ('draft', 'published', 'archived')),
    author_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_recipes_updated_at ON public.recipes;
CREATE TRIGGER trg_recipes_updated_at
    BEFORE UPDATE ON public.recipes
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE INDEX IF NOT EXISTS idx_recipes_status_cuisine_time
    ON public.recipes (status, cuisine_code, (prep_minutes + cook_minutes));

CREATE INDEX IF NOT EXISTS idx_recipes_name_trgm
    ON public.recipes
    USING GIN (public.norm_vi(name_vi) gin_trgm_ops);

-- 7. recipe_ingredients
CREATE TABLE IF NOT EXISTS public.recipe_ingredients (
    recipe_id uuid NOT NULL REFERENCES public.recipes(id) ON DELETE CASCADE,
    ingredient_id uuid NOT NULL REFERENCES public.ingredients(id) ON DELETE RESTRICT,
    is_required boolean NOT NULL DEFAULT true,
    role varchar(16) NOT NULL DEFAULT 'essential'
        CONSTRAINT chk_recipe_ingredients_role CHECK (role IN ('primary', 'essential', 'secondary')),
    weight numeric(6,2) NOT NULL DEFAULT 1.00
        CONSTRAINT chk_recipe_ingredients_weight CHECK (weight > 0),
    grams numeric(8,2)
        CONSTRAINT chk_recipe_ingredients_grams CHECK (grams IS NULL OR grams > 0),
    display_quantity text,
    scaling_note text,
    sort_order integer NOT NULL DEFAULT 0,
    PRIMARY KEY (recipe_id, ingredient_id)
);

CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_ingredient_id
    ON public.recipe_ingredients (ingredient_id);

-- 8. recipe_steps
CREATE TABLE IF NOT EXISTS public.recipe_steps (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id uuid NOT NULL REFERENCES public.recipes(id) ON DELETE CASCADE,
    step_no integer NOT NULL
        CONSTRAINT chk_recipe_steps_step_no CHECK (step_no >= 1),
    instruction text NOT NULL
        CONSTRAINT chk_recipe_steps_instruction CHECK (btrim(instruction) <> ''),
    estimated_minutes integer
        CONSTRAINT chk_recipe_steps_estimated_minutes CHECK (
            estimated_minutes IS NULL OR estimated_minutes >= 0
        ),
    CONSTRAINT uq_recipe_steps_order UNIQUE (recipe_id, step_no)
);

-- 9. nutrition_tags (Tier 1 P0 Qualitative Nutrition)
CREATE TABLE IF NOT EXISTS public.nutrition_tags (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text NOT NULL UNIQUE
        CONSTRAINT chk_nutrition_tags_code CHECK (btrim(code) <> ''),
    name_vi text NOT NULL,
    description text NOT NULL,
    is_active boolean NOT NULL DEFAULT true
);

-- 10. ingredient_nutrition_tags
CREATE TABLE IF NOT EXISTS public.ingredient_nutrition_tags (
    ingredient_id uuid NOT NULL REFERENCES public.ingredients(id) ON DELETE CASCADE,
    nutrition_tag_id uuid NOT NULL REFERENCES public.nutrition_tags(id) ON DELETE RESTRICT,
    source_url text NOT NULL
        CONSTRAINT chk_ing_nutr_tags_source_url CHECK (source_url ~* '^https?://'),
    note text,
    reviewed_at timestamptz,
    PRIMARY KEY (ingredient_id, nutrition_tag_id)
);

-- 11. scan_sessions (Opt-in history only; never stores raw user images)
CREATE TABLE IF NOT EXISTS public.scan_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    model_id uuid NOT NULL REFERENCES public.ai_models(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scan_sessions_user_created
    ON public.scan_sessions (user_id, created_at DESC);

-- 12. scan_detections
CREATE TABLE IF NOT EXISTS public.scan_detections (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_session_id uuid NOT NULL REFERENCES public.scan_sessions(id) ON DELETE CASCADE,
    ai_label_id uuid NOT NULL REFERENCES public.ai_labels(id) ON DELETE RESTRICT,
    confidence numeric(4,3) NOT NULL
        CONSTRAINT chk_scan_detections_confidence CHECK (confidence >= 0.000 AND confidence <= 1.000),
    needs_confirmation boolean NOT NULL DEFAULT false,
    x1 numeric(6,5) NOT NULL,
    y1 numeric(6,5) NOT NULL,
    x2 numeric(6,5) NOT NULL,
    y2 numeric(6,5) NOT NULL,
    CONSTRAINT chk_scan_detections_bbox_x CHECK (x1 >= 0.00000 AND x1 < x2 AND x2 <= 1.00000),
    CONSTRAINT chk_scan_detections_bbox_y CHECK (y1 >= 0.00000 AND y1 < y2 AND y2 <= 1.00000)
);

-- 13. scan_ingredients
CREATE TABLE IF NOT EXISTS public.scan_ingredients (
    scan_session_id uuid NOT NULL REFERENCES public.scan_sessions(id) ON DELETE CASCADE,
    ingredient_id uuid NOT NULL REFERENCES public.ingredients(id) ON DELETE RESTRICT,
    provenance varchar(16) NOT NULL
        CONSTRAINT chk_scan_ingredients_provenance CHECK (
            provenance IN ('ai', 'clip_assisted', 'manual', 'corrected')
        ),
    PRIMARY KEY (scan_session_id, ingredient_id)
);

-- 14. favorites
CREATE TABLE IF NOT EXISTS public.favorites (
    user_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    recipe_id uuid NOT NULL REFERENCES public.recipes(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, recipe_id)
);

-- 15. recommendation_feedback (ADR-012: UNIQUE NULLS NOT DISTINCT & ON DELETE CASCADE)
CREATE TABLE IF NOT EXISTS public.recommendation_feedback (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    recipe_id uuid NOT NULL REFERENCES public.recipes(id) ON DELETE CASCADE,
    scan_session_id uuid REFERENCES public.scan_sessions(id) ON DELETE CASCADE,
    rating smallint NOT NULL
        CONSTRAINT chk_recommendation_feedback_rating CHECK (rating BETWEEN 1 AND 5),
    note varchar(500),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_feedback_user_recipe_scan
        UNIQUE NULLS NOT DISTINCT (user_id, recipe_id, scan_session_id)
);

DROP TRIGGER IF EXISTS trg_recommendation_feedback_updated_at ON public.recommendation_feedback;
CREATE TRIGGER trg_recommendation_feedback_updated_at
    BEFORE UPDATE ON public.recommendation_feedback
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- 16. audit_logs
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE RESTRICT,
    action text NOT NULL,
    entity_type text NOT NULL
        CONSTRAINT chk_audit_logs_entity_type CHECK (
            entity_type IN ('recipes', 'ingredients', 'ai_models', 'ai_labels', 'nutrition_tags')
        ),
    entity_id uuid NOT NULL,
    before_json jsonb,
    after_json jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
    ON public.audit_logs (created_at DESC);

-- ============================================================================
-- EXTENDED TABLES (17..20) — Stages 2–4 (Allergens, USDA Nutrients, User Prefs)
-- ============================================================================

-- 17. allergens
CREATE TABLE IF NOT EXISTS public.allergens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(30) NOT NULL UNIQUE
        CONSTRAINT chk_allergens_code CHECK (btrim(code) <> ''),
    name_vi text NOT NULL
);

-- 18. ingredient_allergens
CREATE TABLE IF NOT EXISTS public.ingredient_allergens (
    ingredient_id uuid NOT NULL REFERENCES public.ingredients(id) ON DELETE CASCADE,
    allergen_id uuid NOT NULL REFERENCES public.allergens(id) ON DELETE RESTRICT,
    PRIMARY KEY (ingredient_id, allergen_id)
);

-- Helper View: recipe_allergens (joins recipe_ingredients and ingredient_allergens)
CREATE OR REPLACE VIEW public.recipe_allergens AS
SELECT DISTINCT
    ri.recipe_id,
    ia.allergen_id,
    a.code AS allergen_code,
    a.name_vi AS allergen_name_vi
FROM public.recipe_ingredients ri
JOIN public.ingredient_allergens ia ON ia.ingredient_id = ri.ingredient_id
JOIN public.allergens a ON a.id = ia.allergen_id;

-- 19. ingredient_nutrients (Tier 2 P1 USDA per 100g edible portion)
CREATE TABLE IF NOT EXISTS public.ingredient_nutrients (
    ingredient_id uuid PRIMARY KEY REFERENCES public.ingredients(id) ON DELETE CASCADE,
    kcal_100g numeric(7,2) NOT NULL CONSTRAINT chk_nutr_kcal CHECK (kcal_100g >= 0),
    protein_100g numeric(6,2) NOT NULL CONSTRAINT chk_nutr_protein CHECK (protein_100g >= 0),
    fat_100g numeric(6,2) NOT NULL CONSTRAINT chk_nutr_fat CHECK (fat_100g >= 0),
    carb_100g numeric(6,2) NOT NULL CONSTRAINT chk_nutr_carb CHECK (carb_100g >= 0),
    source_url text NOT NULL CONSTRAINT chk_nutr_source_url CHECK (source_url ~* '^https?://'),
    reviewed_at timestamptz
);

-- 20. user_preferences (Stages 2 & 4: Diet/Equipment constraints & Logistic Regression weights)
CREATE TABLE IF NOT EXISTS public.user_preferences (
    user_id uuid PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    excluded_allergen_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    available_equipment jsonb,
    lr_weights jsonb,
    feedback_count integer NOT NULL DEFAULT 0
        CONSTRAINT chk_user_preferences_feedback_count CHECK (feedback_count >= 0),
    lr_model_version text,
    updated_at timestamptz NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_user_preferences_updated_at ON public.user_preferences;
CREATE TRIGGER trg_user_preferences_updated_at
    BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ============================================================================
-- ATOMIC RPC: activate_ai_model(target_model_id uuid)
-- Enforces FR-15 & BR-02:
-- 1. Verifies all class indices 0..class_count-1 are mapped in ai_labels.
-- 2. Verifies every mapped ingredient is currently active (is_active = true)
--    and not a pantry item (category <> 'pantry'), even on rollback from archived.
-- 3. Atomically archives the previous active model and sets target to active.
-- ============================================================================
CREATE OR REPLACE FUNCTION public.activate_ai_model(target_model_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_model record;
    v_unmapped integer[];
    v_invalid integer[];
BEGIN
    SELECT * INTO v_model
    FROM public.ai_models
    WHERE id = target_model_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'MODEL_NOT_FOUND' USING ERRCODE = 'P0002';
    END IF;

    -- Find unmapped class indices in 0 .. class_count - 1
    SELECT COALESCE(array_agg(idx ORDER BY idx), '{}'::integer[])
    INTO v_unmapped
    FROM generate_series(0, v_model.class_count - 1) AS idx
    WHERE NOT EXISTS (
        SELECT 1
        FROM public.ai_labels al
        WHERE al.model_id = target_model_id
          AND al.class_index = idx
    );

    -- Find mapped class indices pointing to inactive or pantry ingredients
    SELECT COALESCE(array_agg(al.class_index ORDER BY al.class_index), '{}'::integer[])
    INTO v_invalid
    FROM public.ai_labels al
    JOIN public.ingredients i ON i.id = al.ingredient_id
    WHERE al.model_id = target_model_id
      AND (i.is_active = false OR i.category = 'pantry');

    IF array_length(v_unmapped, 1) IS NOT NULL OR array_length(v_invalid, 1) IS NOT NULL THEN
        RETURN jsonb_build_object(
            'ok', false,
            'error_code', 'MODEL_NOT_ACTIVATABLE',
            'unmapped_class_indices', to_jsonb(v_unmapped),
            'invalid_mapped_class_indices', to_jsonb(v_invalid)
        );
    END IF;

    -- Demote existing active model to archived
    UPDATE public.ai_models
    SET status = 'archived'
    WHERE status = 'active'
      AND id <> target_model_id;

    -- Promote target model to active
    UPDATE public.ai_models
    SET status = 'active'
    WHERE id = target_model_id;

    RETURN jsonb_build_object(
        'ok', true,
        'model_id', target_model_id,
        'status', 'active'
    );
END;
$$;

COMMIT;

