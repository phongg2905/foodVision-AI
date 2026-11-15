-- ============================================================================
-- Migration: 20261115000003_unified_mcda_and_personalization.sql
-- Project  : FoodVision AI (v1.1.0 Baseline — ADR-013)
-- Scope    : Idempotent schema upgrade for existing databases:
--            1. recipes: enforce prep_minutes + cook_minutes > 0 (t_r > 0 hours)
--            2. recipe_ingredients: role ('core'/'secondary'/'spice'/'optional'),
--               dish_role ('main'/'sub' for G), weight check (4-2-1-0 for C)
--            3. user_preferences: allergic_ingredient_ids, kitchen_spice_ids,
--               favorite_ingredient_ids
-- ============================================================================

BEGIN;

-- 1. Ensure recipes have positive total cooking time (t_r > 0)
ALTER TABLE public.recipes
    DROP CONSTRAINT IF EXISTS chk_recipes_positive_time;

ALTER TABLE public.recipes
    ADD CONSTRAINT chk_recipes_positive_time CHECK (prep_minutes + cook_minutes > 0);

-- 2. Upgrade recipe_ingredients for C (4-2-1-0 weights) and G (main/sub tag)
ALTER TABLE public.recipe_ingredients
    ADD COLUMN IF NOT EXISTS dish_role varchar(8) NOT NULL DEFAULT 'main';

ALTER TABLE public.recipe_ingredients
    DROP CONSTRAINT IF EXISTS chk_recipe_ingredients_role;

UPDATE public.recipe_ingredients
SET role = CASE
    WHEN is_required = false THEN 'optional'
    WHEN role = 'primary' THEN 'core'
    WHEN role = 'essential' THEN 'secondary'
    ELSE 'spice'
END
WHERE role NOT IN ('core', 'secondary', 'spice', 'optional');

ALTER TABLE public.recipe_ingredients
    ALTER COLUMN role SET DEFAULT 'core',
    ADD CONSTRAINT chk_recipe_ingredients_role
        CHECK (role IN ('core', 'secondary', 'spice', 'optional'));

ALTER TABLE public.recipe_ingredients
    DROP CONSTRAINT IF EXISTS chk_recipe_ingredients_dish_role;

ALTER TABLE public.recipe_ingredients
    ADD CONSTRAINT chk_recipe_ingredients_dish_role
        CHECK (dish_role IN ('main', 'sub'));

ALTER TABLE public.recipe_ingredients
    DROP CONSTRAINT IF EXISTS chk_recipe_ingredients_weight;

ALTER TABLE public.recipe_ingredients
    ALTER COLUMN weight SET DEFAULT 4.00,
    ADD CONSTRAINT chk_recipe_ingredients_weight
        CHECK ((is_required = true AND weight > 0) OR (is_required = false AND weight >= 0));

-- 3. Upgrade user_preferences with 3 ingredient personalization lists
ALTER TABLE public.user_preferences
    ADD COLUMN IF NOT EXISTS allergic_ingredient_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS kitchen_spice_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS favorite_ingredient_ids jsonb NOT NULL DEFAULT '[]'::jsonb;

COMMIT;
