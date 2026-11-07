-- ============================================================================
-- Migration: 20261104000002_rls_and_grants.sql
-- Project  : FoodVision AI (v1.0.0 Official Baseline)
-- Scope    : Row Level Security (RLS), Minimum Privilege Grants, Role Helper,
--            and Private Storage Bucket Configuration (NFR-04, NFR-05, ADR-011)
-- ============================================================================

BEGIN;

-- 1. Server-side Admin Check Helper Function (ADR-011: Admin --|> User --|> Guest)
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.profiles
        WHERE id = auth.uid()
          AND role = 'admin'
    );
$$;

-- 2. Enable Row Level Security on ALL 20 public tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredient_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_labels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recipe_ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recipe_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredient_nutrition_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendation_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.allergens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredient_allergens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredient_nutrients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;

-- 3. Revoke default overly broad privileges & grant minimum required privileges
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;

-- Public / Guest readable catalog tables (filtered by RLS policies below)
GRANT SELECT ON
    public.ingredients,
    public.ingredient_aliases,
    public.recipes,
    public.recipe_ingredients,
    public.recipe_steps,
    public.nutrition_tags,
    public.ingredient_nutrition_tags,
    public.allergens,
    public.ingredient_allergens,
    public.ingredient_nutrients,
    public.ai_models,
    public.ai_labels,
    public.recipe_allergens
TO anon, authenticated;

-- Authenticated user-owned tables
GRANT SELECT, UPDATE (display_name) ON public.profiles TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON
    public.favorites,
    public.scan_sessions,
    public.scan_detections,
    public.scan_ingredients,
    public.recommendation_feedback,
    public.user_preferences
TO authenticated;

-- Admin CRUD grants (protected by public.is_admin() RLS policies)
GRANT INSERT, UPDATE, DELETE ON
    public.ingredients,
    public.ingredient_aliases,
    public.recipes,
    public.recipe_ingredients,
    public.recipe_steps,
    public.nutrition_tags,
    public.ingredient_nutrition_tags,
    public.allergens,
    public.ingredient_allergens,
    public.ingredient_nutrients,
    public.ai_models,
    public.ai_labels
TO authenticated;

GRANT SELECT, INSERT ON public.audit_logs TO authenticated;

-- ============================================================================
-- 4. RLS POLICIES (NFR-05, SEC-01..SEC-07)
-- ============================================================================

-- 4.1. profiles: Users read/update own display_name (cannot escalate role); Admin reads all
DROP POLICY IF EXISTS profiles_select_own_or_admin ON public.profiles;
CREATE POLICY profiles_select_own_or_admin ON public.profiles
    FOR SELECT
    TO authenticated
    USING (id = auth.uid() OR public.is_admin());

DROP POLICY IF EXISTS profiles_update_own_display_name ON public.profiles;
CREATE POLICY profiles_update_own_display_name ON public.profiles
    FOR UPDATE
    TO authenticated
    USING (id = auth.uid())
    WITH CHECK (
        id = auth.uid()
        AND role = (SELECT p.role FROM public.profiles p WHERE p.id = auth.uid())
    );

-- 4.2. ingredients & ingredient_aliases: Public reads active; Admin full access
DROP POLICY IF EXISTS ingredients_select_active_or_admin ON public.ingredients;
CREATE POLICY ingredients_select_active_or_admin ON public.ingredients
    FOR SELECT
    TO anon, authenticated
    USING (is_active = true OR public.is_admin());

DROP POLICY IF EXISTS ingredients_admin_write ON public.ingredients;
CREATE POLICY ingredients_admin_write ON public.ingredients
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS aliases_select_public ON public.ingredient_aliases;
CREATE POLICY aliases_select_public ON public.ingredient_aliases
    FOR SELECT
    TO anon, authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.ingredients i
            WHERE i.id = ingredient_aliases.ingredient_id
              AND (i.is_active = true OR public.is_admin())
        )
    );

DROP POLICY IF EXISTS aliases_admin_write ON public.ingredient_aliases;
CREATE POLICY aliases_admin_write ON public.ingredient_aliases
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- 4.3. recipes, recipe_ingredients, recipe_steps: Public reads published only (TP 10); Admin full access
DROP POLICY IF EXISTS recipes_select_published_or_admin ON public.recipes;
CREATE POLICY recipes_select_published_or_admin ON public.recipes
    FOR SELECT
    TO anon, authenticated
    USING (status = 'published' OR public.is_admin());

DROP POLICY IF EXISTS recipes_admin_write ON public.recipes;
CREATE POLICY recipes_admin_write ON public.recipes
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS recipe_ingredients_select_published_or_admin ON public.recipe_ingredients;
CREATE POLICY recipe_ingredients_select_published_or_admin ON public.recipe_ingredients
    FOR SELECT
    TO anon, authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.recipes r
            WHERE r.id = recipe_ingredients.recipe_id
              AND (r.status = 'published' OR public.is_admin())
        )
    );

DROP POLICY IF EXISTS recipe_ingredients_admin_write ON public.recipe_ingredients;
CREATE POLICY recipe_ingredients_admin_write ON public.recipe_ingredients
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS recipe_steps_select_published_or_admin ON public.recipe_steps;
CREATE POLICY recipe_steps_select_published_or_admin ON public.recipe_steps
    FOR SELECT
    TO anon, authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.recipes r
            WHERE r.id = recipe_steps.recipe_id
              AND (r.status = 'published' OR public.is_admin())
        )
    );

DROP POLICY IF EXISTS recipe_steps_admin_write ON public.recipe_steps;
CREATE POLICY recipe_steps_admin_write ON public.recipe_steps
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- 4.4. nutrition_tags, ingredient_nutrition_tags, allergens, ingredient_allergens, ingredient_nutrients
DROP POLICY IF EXISTS nutrition_tags_select_active_or_admin ON public.nutrition_tags;
CREATE POLICY nutrition_tags_select_active_or_admin ON public.nutrition_tags
    FOR SELECT
    TO anon, authenticated
    USING (is_active = true OR public.is_admin());

DROP POLICY IF EXISTS nutrition_tags_admin_write ON public.nutrition_tags;
CREATE POLICY nutrition_tags_admin_write ON public.nutrition_tags
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS ing_nutrition_tags_select_public ON public.ingredient_nutrition_tags;
CREATE POLICY ing_nutrition_tags_select_public ON public.ingredient_nutrition_tags
    FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS ing_nutrition_tags_admin_write ON public.ingredient_nutrition_tags;
CREATE POLICY ing_nutrition_tags_admin_write ON public.ingredient_nutrition_tags
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS allergens_select_public ON public.allergens;
CREATE POLICY allergens_select_public ON public.allergens
    FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS allergens_admin_write ON public.allergens;
CREATE POLICY allergens_admin_write ON public.allergens
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS ing_allergens_select_public ON public.ingredient_allergens;
CREATE POLICY ing_allergens_select_public ON public.ingredient_allergens
    FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS ing_allergens_admin_write ON public.ingredient_allergens;
CREATE POLICY ing_allergens_admin_write ON public.ingredient_allergens
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS ing_nutrients_select_public ON public.ingredient_nutrients;
CREATE POLICY ing_nutrients_select_public ON public.ingredient_nutrients
    FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS ing_nutrients_admin_write ON public.ingredient_nutrients;
CREATE POLICY ing_nutrients_admin_write ON public.ingredient_nutrients
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- 4.5. ai_models & ai_labels: Public reads active model metadata; Admin full access
DROP POLICY IF EXISTS ai_models_select_active_or_admin ON public.ai_models;
CREATE POLICY ai_models_select_active_or_admin ON public.ai_models
    FOR SELECT
    TO anon, authenticated
    USING (status = 'active' OR public.is_admin());

DROP POLICY IF EXISTS ai_models_admin_write ON public.ai_models;
CREATE POLICY ai_models_admin_write ON public.ai_models
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS ai_labels_select_active_or_admin ON public.ai_labels;
CREATE POLICY ai_labels_select_active_or_admin ON public.ai_labels
    FOR SELECT
    TO anon, authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.ai_models m
            WHERE m.id = ai_labels.model_id
              AND (m.status = 'active' OR public.is_admin())
        )
    );

DROP POLICY IF EXISTS ai_labels_admin_write ON public.ai_labels;
CREATE POLICY ai_labels_admin_write ON public.ai_labels
    FOR ALL
    TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- 4.6. Strict User Ownership Policies: favorites, scan_sessions, scan_detections, scan_ingredients, feedback, preferences
DROP POLICY IF EXISTS favorites_owner_only ON public.favorites;
CREATE POLICY favorites_owner_only ON public.favorites
    FOR ALL
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS scan_sessions_owner_only ON public.scan_sessions;
CREATE POLICY scan_sessions_owner_only ON public.scan_sessions
    FOR ALL
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS scan_detections_owner_only ON public.scan_detections;
CREATE POLICY scan_detections_owner_only ON public.scan_detections
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.scan_sessions s
            WHERE s.id = scan_detections.scan_session_id
              AND s.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.scan_sessions s
            WHERE s.id = scan_detections.scan_session_id
              AND s.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS scan_ingredients_owner_only ON public.scan_ingredients;
CREATE POLICY scan_ingredients_owner_only ON public.scan_ingredients
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.scan_sessions s
            WHERE s.id = scan_ingredients.scan_session_id
              AND s.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.scan_sessions s
            WHERE s.id = scan_ingredients.scan_session_id
              AND s.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS feedback_owner_only ON public.recommendation_feedback;
CREATE POLICY feedback_owner_only ON public.recommendation_feedback
    FOR ALL
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (
        user_id = auth.uid()
        AND (
            scan_session_id IS NULL
            OR EXISTS (
                SELECT 1 FROM public.scan_sessions s
                WHERE s.id = recommendation_feedback.scan_session_id
                  AND s.user_id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS user_preferences_owner_only ON public.user_preferences;
CREATE POLICY user_preferences_owner_only ON public.user_preferences
    FOR ALL
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 4.7. audit_logs: Admin read/insert only
DROP POLICY IF EXISTS audit_logs_admin_select ON public.audit_logs;
CREATE POLICY audit_logs_admin_select ON public.audit_logs
    FOR SELECT
    TO authenticated
    USING (public.is_admin());

DROP POLICY IF EXISTS audit_logs_admin_insert ON public.audit_logs;
CREATE POLICY audit_logs_admin_insert ON public.audit_logs
    FOR INSERT
    TO authenticated
    WITH CHECK (public.is_admin() AND actor_id = auth.uid());

-- 5. Private Storage Bucket Configuration (scan-images)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'storage' AND table_name = 'buckets') THEN
        INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
        VALUES (
            'scan-images',
            'scan-images',
            false,
            5242880,
            ARRAY['image/jpeg', 'image/png', 'image/webp']
        )
        ON CONFLICT (id) DO UPDATE
        SET public = false,
            file_size_limit = 5242880,
            allowed_mime_types = ARRAY['image/jpeg', 'image/png', 'image/webp'];
    END IF;
END
$$;

COMMIT;

