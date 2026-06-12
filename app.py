import flask
import os
import re
import sqlite3
from difflib import get_close_matches
from datetime import datetime

import pandas as pd
from werkzeug.security import check_password_hash, generate_password_hash

app = flask.Flask(__name__)
app.secret_key = "college-project-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
CSV_PATH = os.path.join(BASE_DIR, "food_data.csv")

COMMON_INGREDIENTS = {
    "apple": {"Food": "Apple", "Serving": "1 medium apple (182 g)", "Calories": 95},
    "banana": {"Food": "Banana", "Serving": "1 medium banana (118 g)", "Calories": 105},
    "egg": {"Food": "Egg", "Serving": "1 large egg (50 g)", "Calories": 78},
    "eggs": {"Food": "Egg", "Serving": "1 large egg (50 g)", "Calories": 78},
    "milk": {"Food": "Milk", "Serving": "1 cup (244 ml)", "Calories": 122},
    "curd": {"Food": "Curd", "Serving": "1/2 cup (122 g)", "Calories": 98},
    "yogurt": {"Food": "Yogurt", "Serving": "1 cup (245 g)", "Calories": 149},
    "oats": {"Food": "Oats", "Serving": "1/2 cup (40 g)", "Calories": 150},
    "almond": {"Food": "Almonds", "Serving": "10 almonds (12 g)", "Calories": 70},
    "almonds": {"Food": "Almonds", "Serving": "10 almonds (12 g)", "Calories": 70},
    "peanut butter": {"Food": "Peanut Butter", "Serving": "1 tbsp (16 g)", "Calories": 94},
    "honey": {"Food": "Honey", "Serving": "1 tsp (7 g)", "Calories": 21},
    "chicken": {"Food": "Chicken Breast", "Serving": "1 piece (71 g)", "Calories": 116},
    "paneer": {"Food": "Paneer", "Serving": "1/2 cup (80 g)", "Calories": 220},
    "rice": {"Food": "Rice", "Serving": "1 cup (195 g)", "Calories": 206},
    "black rice": {"Food": "Black Rice", "Serving": "1 cup cooked (195 g)", "Calories": 205},
}

VALID_RECIPE_MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack"}
VALID_RECIPE_GOALS = {"lose", "maintain", "gain"}
RECIPE_SAMPLE_INGREDIENTS = "rice, chicken, oats, milk, yogurt, or almonds"
RECIPE_ALIASES = {
    "brocoli": "broccoli",
    "brown rice": "rice",
    "dahi": "curd",
    "oat": "oats",
    "peanuts": "peanut butter",
    "yougurt": "yogurt",
}
MEAL_GOAL_ADD_ONS = {
    "breakfast": {
        "lose": ["yogurt"],
        "maintain": ["oats", "milk", "almonds"],
        "gain": ["peanut butter", "oats"],
    },
    "lunch": {
        "lose": ["curd"],
        "maintain": ["curd", "rice"],
        "gain": ["rice", "paneer", "curd"],
    },
    "dinner": {
        "lose": ["curd"],
        "maintain": ["curd", "rice"],
        "gain": ["rice", "curd"],
    },
    "snack": {
        "lose": ["yogurt"],
        "maintain": ["almonds"],
        "gain": ["peanut butter", "almonds"],
    },
}

RECIPE_CATEGORY_ADD_ONS = {
    "breakfast": {
        "fruit": {
            "lose": ["yogurt"],
            "maintain": ["oats", "yogurt"],
            "gain": ["oats", "peanut butter"],
        },
        "grain": {
            "lose": ["yogurt"],
            "maintain": ["milk", "almonds"],
            "gain": ["milk", "peanut butter"],
        },
        "dairy": {
            "lose": ["banana"],
            "maintain": ["banana", "oats"],
            "gain": ["banana", "oats", "peanut butter"],
        },
        "protein": {
            "lose": ["spinach"],
            "maintain": ["spinach"],
            "gain": ["spinach", "paneer"],
        },
        "vegetable": {
            "lose": ["egg"],
            "maintain": ["egg"],
            "gain": ["egg", "paneer"],
        },
    },
    "lunch": {
        "protein": {
            "lose": ["broccoli"],
            "maintain": ["rice", "curd"],
            "gain": ["rice", "curd"],
        },
        "grain": {
            "lose": ["broccoli", "curd"],
            "maintain": ["curd", "broccoli"],
            "gain": ["paneer", "curd"],
        },
        "vegetable": {
            "lose": ["curd"],
            "maintain": ["rice", "curd"],
            "gain": ["rice", "paneer"],
        },
        "dairy": {
            "lose": ["broccoli"],
            "maintain": ["rice"],
            "gain": ["rice", "paneer"],
        },
    },
    "dinner": {
        "protein": {
            "lose": ["spinach"],
            "maintain": ["rice", "curd"],
            "gain": ["rice", "curd"],
        },
        "grain": {
            "lose": ["spinach", "curd"],
            "maintain": ["curd", "spinach"],
            "gain": ["paneer", "curd"],
        },
        "vegetable": {
            "lose": ["curd"],
            "maintain": ["rice", "curd"],
            "gain": ["rice", "paneer"],
        },
        "dairy": {
            "lose": ["spinach"],
            "maintain": ["rice"],
            "gain": ["rice", "paneer"],
        },
    },
    "snack": {
        "fruit": {
            "lose": ["yogurt"],
            "maintain": ["almonds"],
            "gain": ["peanut butter", "almonds"],
        },
        "dairy": {
            "lose": ["apple"],
            "maintain": ["almonds"],
            "gain": ["banana", "peanut butter"],
        },
        "fat": {
            "lose": ["apple"],
            "maintain": ["apple"],
            "gain": ["banana", "milk"],
        },
        "grain": {
            "lose": ["yogurt"],
            "maintain": ["milk"],
            "gain": ["milk", "peanut butter"],
        },
        "protein": {
            "lose": ["cucumber"],
            "maintain": ["curd"],
            "gain": ["milk"],
        },
    },
}

PLAN_MEAL_OPTIONS = {
    "lose": {
        "Breakfast": ["oats", "yogurt", "almonds"],
        "Lunch": ["chicken", "broccoli", "rice", "curd"],
        "Dinner": ["chicken", "sweet potato", "spinach", "curd"],
        "Snack": ["yogurt", "almonds"],
    },
    "maintain": {
        "Breakfast": ["oats", "milk", "almonds"],
        "Lunch": ["rice", "chicken", "curd", "broccoli"],
        "Dinner": ["chicken", "rice", "spinach", "curd"],
        "Snack": ["milk", "almonds"],
    },
    "gain": {
        "Breakfast": ["oats", "milk", "peanut butter", "almonds"],
        "Lunch": ["rice", "chicken", "curd", "sweet potato"],
        "Dinner": ["rice", "chicken", "curd", "broccoli"],
        "Snack": ["milk", "peanut butter", "almonds"],
    },
}

PLAN_GOAL_TIPS = {
    "lose": "Keep portions controlled and fill the plate with lean protein and vegetables.",
    "maintain": "Aim for steady portions with carbs, protein, and fiber in each main meal.",
    "gain": "Use extra servings of calorie-dense foods to increase intake gradually.",
}


def load_food_data():
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    df["Calories"] = df["Calories"].str.replace("cal", "", regex=False).str.strip()
    df["Calories"] = pd.to_numeric(df["Calories"], errors="coerce").fillna(0).astype(int)
    df["Food"] = df["Food"].str.strip()
    df["food_key"] = df["Food"].str.lower()
    return df


df = load_food_data()


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS food_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food TEXT NOT NULL,
            calories INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
        """
    )
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(food_log)").fetchall()
    }
    if "user_id" not in columns:
        conn.execute("ALTER TABLE food_log ADD COLUMN user_id INTEGER")
    if "created_at" not in columns:
        conn.execute("ALTER TABLE food_log ADD COLUMN created_at TEXT")
    conn.execute(
        "UPDATE food_log SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
    )
    conn.commit()
    conn.close()


def build_analytics(user_id):
    conn = get_db_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    daily_rows = conn.execute(
        """
        SELECT date(created_at) AS log_date, SUM(calories) AS total
        FROM food_log
        WHERE user_id = ?
        GROUP BY date(created_at)
        ORDER BY log_date DESC
        LIMIT 7
        """,
        (user_id,),
    ).fetchall()
    today_food_rows = conn.execute(
        """
        SELECT food, SUM(calories) AS total_calories, COUNT(*) AS entries
        FROM food_log
        WHERE user_id = ? AND date(created_at) = ?
        GROUP BY food
        ORDER BY total_calories DESC, food ASC
        LIMIT 8
        """,
        (user_id, today),
    ).fetchall()
    top_food_rows = conn.execute(
        """
        SELECT food, SUM(calories) AS total_calories, COUNT(*) AS entries
        FROM food_log
        WHERE user_id = ?
        GROUP BY food
        ORDER BY total_calories DESC, food ASC
        LIMIT 5
        """,
        (user_id,),
    ).fetchall()
    summary = conn.execute(
        """
        SELECT
            COUNT(*) AS total_entries,
            COALESCE(SUM(calories), 0) AS total_calories,
            COALESCE(AVG(calories), 0) AS avg_calories
        FROM food_log
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()
    conn.close()

    daily_data = [
        {"date": row["log_date"], "total": int(row["total"] or 0)}
        for row in reversed(daily_rows)
    ]
    top_foods = [
        {
            "food": row["food"],
            "total_calories": int(row["total_calories"] or 0),
            "entries": int(row["entries"] or 0),
        }
        for row in top_food_rows
    ]
    today_foods = [
        {
            "food": row["food"],
            "total_calories": int(row["total_calories"] or 0),
            "entries": int(row["entries"] or 0),
        }
        for row in today_food_rows
    ]
    today_calories = sum(item["total_calories"] for item in today_foods)

    return {
        "daily_data": daily_data,
        "today_foods": today_foods,
        "top_foods": top_foods,
        "summary": {
            "total_entries": int(summary["total_entries"] or 0),
            "total_calories": int(summary["total_calories"] or 0),
            "today_calories": today_calories,
            "avg_calories": int(round(summary["avg_calories"] or 0)),
            "active_days": len(daily_data),
            "best_day": max((item["total"] for item in daily_data), default=0),
        },
    }


def calculate_daily_calories(age, gender, weight, height, activity, goal):
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
    }
    total_calories = bmr * activity_factors.get(activity, 1.2)

    goal_adjustments = {
        "lose": -400,
        "maintain": 0,
        "gain": 300,
    }
    total_calories += goal_adjustments.get(goal, 0)

    return max(int(round(total_calories)), 1200)


def get_plan_food(term):
    term = term.strip().lower()
    if term in COMMON_INGREDIENTS:
        item = COMMON_INGREDIENTS[term]
        return {
            "food": item["Food"],
            "serving": item["Serving"],
            "calories": item["Calories"],
        }

    exact_match = df[df["food_key"] == term]
    if not exact_match.empty:
        return ingredient_from_row(exact_match.iloc[0])

    word_match = df[df["food_key"].str.contains(rf"\b{re.escape(term)}\b", regex=True, na=False)]
    if not word_match.empty:
        return ingredient_from_row(word_match.sort_values("Calories").iloc[0])

    return None


def build_plan_item(food):
    return {
        "food": food["food"],
        "serving": food["serving"],
        "calories": food["calories"],
        "portions": 1,
        "total_calories": food["calories"],
    }


def scale_plan_items(items, meal_target):
    if not items:
        return items

    calorie_floor = int(meal_target * 0.75)
    calorie_ceiling = int(meal_target * 1.15)

    while sum(item["total_calories"] for item in items) < calorie_floor:
        scalable_items = sorted(
            items,
            key=lambda item: (item["total_calories"], item["calories"]),
            reverse=True,
        )
        updated = False

        for item in scalable_items:
            if item["portions"] >= 3:
                continue

            next_total = sum(entry["total_calories"] for entry in items) + item["calories"]
            if next_total <= calorie_ceiling:
                item["portions"] += 1
                item["total_calories"] += item["calories"]
                updated = True
                break

        if not updated:
            break

    return items


def build_meal_plan(target_calories, goal):
    meal_distribution = {
        "lose": [
            ("Breakfast", 0.28),
            ("Lunch", 0.36),
            ("Dinner", 0.28),
            ("Snack", 0.08),
        ],
        "maintain": [
            ("Breakfast", 0.25),
            ("Lunch", 0.35),
            ("Dinner", 0.30),
            ("Snack", 0.10),
        ],
        "gain": [
            ("Breakfast", 0.27),
            ("Lunch", 0.34),
            ("Dinner", 0.29),
            ("Snack", 0.10),
        ],
    }.get(goal, [
        ("Breakfast", 0.25),
        ("Lunch", 0.35),
        ("Dinner", 0.30),
        ("Snack", 0.10),
    ])
    suggestions = []

    for meal_name, ratio in meal_distribution:
        meal_target = int(round(target_calories * ratio))
        foods = [
            get_plan_food(term)
            for term in PLAN_MEAL_OPTIONS.get(goal, PLAN_MEAL_OPTIONS["maintain"])[meal_name]
        ]
        items = [build_plan_item(food) for food in foods if food]
        items = scale_plan_items(items, meal_target)
        meal_total = sum(item["total_calories"] for item in items)

        suggestions.append(
            {
                "meal": meal_name,
                "target": meal_target,
                "food": ", ".join(item["food"] for item in items),
                "serving": " + ".join(
                    f"{item['portions']} x {item['serving']}" if item["portions"] > 1 else item["serving"]
                    for item in items
                ),
                "calories": meal_total,
                "items": items,
                "gap": meal_total - meal_target,
                "tip": PLAN_GOAL_TIPS.get(goal, PLAN_GOAL_TIPS["maintain"]),
            }
        )

    return suggestions


def parse_ingredient_terms(main_ingredient):
    cleaned = normalize_recipe_term(main_ingredient).replace("&", " and ")
    terms = re.split(r"\s*(?:,|\+|/|\band\b|\bwith\b)\s*", cleaned)
    return [term.strip() for term in terms if term.strip()]


def normalize_recipe_term(term):
    cleaned = re.sub(r"[^a-z0-9\s-]", " ", term.lower())
    cleaned = re.sub(
        r"\b(fresh|raw|cooked|boiled|grilled|roasted|fried|chopped|sliced)\b",
        " ",
        cleaned,
    )
    return re.sub(r"\s+", " ", cleaned).strip()


def recipe_search_terms(term):
    normalized = normalize_recipe_term(term)
    terms = [normalized]
    if normalized in RECIPE_ALIASES:
        terms.append(RECIPE_ALIASES[normalized])
    if normalized.endswith("es"):
        terms.append(normalized[:-2])
    if normalized.endswith("s"):
        terms.append(normalized[:-1])
    return [candidate for candidate in dict.fromkeys(terms) if candidate]


def categorize_ingredient(food_name):
    name = food_name.lower()
    category_keywords = {
        "protein": ["chicken", "egg", "fish", "salmon", "tuna", "turkey", "paneer"],
        "dairy": ["milk", "curd", "yogurt"],
        "grain": ["rice", "oats", "bread", "wrap"],
        "vegetable": ["broccoli", "spinach", "carrot", "cabbage", "pepper", "tomato", "potato", "beans"],
        "fat": ["almond", "peanut butter", "olive"],
        "fruit": ["apple", "banana"],
        "sweetener": ["honey"],
    }

    for category, keywords in category_keywords.items():
        if any(keyword in name for keyword in keywords):
            return category

    return "other"


def ingredient_from_row(row):
    food_name = row["Food"]
    return {
        "food": food_name,
        "serving": row["Serving"],
        "calories": int(row["Calories"]),
        "category": categorize_ingredient(food_name),
    }


def find_ingredient(term):
    for search_term in recipe_search_terms(term):
        if search_term in COMMON_INGREDIENTS:
            item = COMMON_INGREDIENTS[search_term]
            return {
                "food": item["Food"],
                "serving": item["Serving"],
                "calories": item["Calories"],
                "category": categorize_ingredient(item["Food"]),
            }

        exact_match = df[df["food_key"] == search_term]
        if not exact_match.empty:
            return ingredient_from_row(exact_match.iloc[0])

        word_match = df[df["food_key"].str.contains(rf"\b{re.escape(search_term)}\b", regex=True, na=False)]
        if not word_match.empty:
            return ingredient_from_row(word_match.sort_values("Calories").iloc[0])

        close_matches = get_close_matches(search_term, df["food_key"].tolist(), n=1, cutoff=0.86)
        if close_matches:
            fuzzy_match = df[df["food_key"] == close_matches[0]]
            if not fuzzy_match.empty:
                return ingredient_from_row(fuzzy_match.iloc[0])

    return None


def add_goal_ingredients(ingredients, meal_type, goal):
    if len(ingredients) >= 2:
        return ingredients

    primary_category = ingredients[0].get("category", "other")
    add_ons = (
        RECIPE_CATEGORY_ADD_ONS
        .get(meal_type, {})
        .get(primary_category, {})
        .get(goal)
    )
    if add_ons is None:
        add_ons = MEAL_GOAL_ADD_ONS.get(meal_type, {}).get(goal, [])

    used_foods = {item["food"].lower() for item in ingredients}
    used_categories = {item.get("category", "other") for item in ingredients}

    for term in add_ons:
        if len(ingredients) >= 4:
            break
        item = find_ingredient(term)
        if item and item.get("category") in used_categories and item.get("category") in {"protein", "grain", "dairy"}:
            continue
        if item and item["food"].lower() not in used_foods:
            item = dict(item)
            item["source"] = "addon"
            ingredients.append(item)
            used_foods.add(item["food"].lower())
            used_categories.add(item.get("category", "other"))

    return ingredients


def order_recipe_ingredients(ingredients, meal_type):
    priorities = {
        "breakfast": ["fruit", "grain", "dairy", "protein", "fat", "sweetener", "vegetable", "other"],
        "lunch": ["protein", "grain", "vegetable", "dairy", "fat", "fruit", "sweetener", "other"],
        "dinner": ["protein", "grain", "vegetable", "dairy", "fat", "fruit", "sweetener", "other"],
        "snack": ["fruit", "dairy", "fat", "grain", "protein", "vegetable", "sweetener", "other"],
    }
    meal_priority = priorities.get(meal_type, priorities["lunch"])
    priority_rank = {category: index for index, category in enumerate(meal_priority)}

    return sorted(
        ingredients,
        key=lambda item: priority_rank.get(item.get("category", "other"), len(meal_priority)),
    )


def format_recipe_list(items):
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


def ingredient_names_for(ingredients, categories):
    category_set = set(categories)
    return [
        item["food"].lower()
        for item in ingredients
        if item.get("category", "other") in category_set
    ]


def build_breakfast_steps(ingredients, finish):
    fruits = ingredient_names_for(ingredients, ["fruit"])
    grains = ingredient_names_for(ingredients, ["grain"])
    dairy = ingredient_names_for(ingredients, ["dairy"])
    proteins = ingredient_names_for(ingredients, ["protein"])
    vegetables = ingredient_names_for(ingredients, ["vegetable"])
    toppings = ingredient_names_for(ingredients, ["fat", "sweetener"])

    if grains:
        base = format_recipe_list(grains)
        liquid = format_recipe_list(dairy)
        topping_text = format_recipe_list(fruits + toppings)
        return [
            f"Cook or soak {base} with {liquid} until soft." if liquid else f"Cook or soak {base} until soft.",
            f"Top it with {topping_text}." if topping_text else "Stir it well so the bowl is even.",
            "Serve warm for a porridge-style breakfast, or chill it for an overnight bowl.",
            finish,
        ]

    if dairy and fruits:
        blend_items = format_recipe_list(fruits + toppings)
        return [
            f"Pour {format_recipe_list(dairy)} into a blender.",
            f"Add {blend_items} and blend until smooth." if blend_items else "Blend until smooth.",
            "Serve chilled as a smoothie or pour into a bowl.",
            finish,
        ]

    if proteins:
        extras = format_recipe_list(vegetables + toppings)
        return [
            f"Cook {format_recipe_list(proteins)} on low to medium heat.",
            f"Add {extras} and cook until just combined." if extras else "Season lightly while it cooks.",
            "Serve it warm as a simple protein breakfast.",
            finish,
        ]

    primary = ingredients[0]["food"].lower()
    extras = format_recipe_list([item["food"].lower() for item in ingredients[1:]])
    return [
        f"Prepare {primary} in a bowl.",
        f"Add {extras} and mix gently." if extras else "Keep the portion simple and ready to serve.",
        "Serve it as a quick breakfast bowl.",
        finish,
    ]


def build_lunch_steps(ingredients, finish):
    proteins = ingredient_names_for(ingredients, ["protein"])
    grains = ingredient_names_for(ingredients, ["grain"])
    vegetables = ingredient_names_for(ingredients, ["vegetable"])
    cool_sides = ingredient_names_for(ingredients, ["dairy", "fat"])

    steps = []
    if proteins:
        steps.append(f"Cook {format_recipe_list(proteins)} with salt, pepper, and simple spices until done.")
    elif grains:
        steps.append(f"Use cooked {format_recipe_list(grains)} as the lunch base.")
    elif vegetables:
        steps.append(f"Steam or saute {format_recipe_list(vegetables)} until tender but not mushy.")
    else:
        steps.append(f"Prepare {ingredients[0]['food'].lower()} as the lunch base.")

    if grains and proteins:
        steps.append(f"Serve the cooked protein over {format_recipe_list(grains)}.")
    elif grains and vegetables:
        steps.append(f"Mix {format_recipe_list(grains)} with the vegetables.")
    elif vegetables and proteins:
        steps.append(f"Add {format_recipe_list(vegetables)} beside the protein.")

    if cool_sides:
        steps.append(f"Add {format_recipe_list(cool_sides)} after cooking, either on top or on the side.")

    steps.extend([
        "Finish with lemon juice, herbs, or light spices for flavor.",
        finish,
    ])
    return steps


def build_dinner_steps(ingredients, finish):
    proteins = ingredient_names_for(ingredients, ["protein"])
    grains = ingredient_names_for(ingredients, ["grain"])
    vegetables = ingredient_names_for(ingredients, ["vegetable"])
    cool_sides = ingredient_names_for(ingredients, ["dairy", "fat"])

    steps = []
    if proteins:
        steps.append(f"Cook {format_recipe_list(proteins)} first with simple spices until fully done.")
    elif grains:
        steps.append(f"Warm cooked {format_recipe_list(grains)} as the base of the dinner plate.")
    elif vegetables:
        steps.append(f"Saute or steam {format_recipe_list(vegetables)} until tender.")
    else:
        steps.append(f"Warm {ingredients[0]['food'].lower()} gently before serving.")

    warm_items = []
    if grains and not proteins:
        warm_items.extend(grains)
    elif grains and proteins:
        warm_items.extend(grains)
    if vegetables and not set(vegetables).issubset(set(warm_items)):
        warm_items.extend(vegetables)

    warm_text = format_recipe_list(list(dict.fromkeys(warm_items).keys()))
    if warm_text:
        steps.append(f"Add or plate it with {warm_text} while everything is warm.")

    if cool_sides:
        steps.append(f"Keep {format_recipe_list(cool_sides)} as a cool side instead of cooking it.")

    steps.extend([
        "Serve as a balanced dinner plate with controlled portions.",
        finish,
    ])
    return steps


def build_snack_steps(ingredients, finish):
    fruits = ingredient_names_for(ingredients, ["fruit"])
    dairy = ingredient_names_for(ingredients, ["dairy"])
    fats = ingredient_names_for(ingredients, ["fat"])
    grains = ingredient_names_for(ingredients, ["grain"])
    proteins = ingredient_names_for(ingredients, ["protein"])
    user_categories = {
        item.get("category", "other")
        for item in ingredients
        if item.get("source") == "user"
    }

    if dairy and "dairy" in user_categories:
        toppings = format_recipe_list(fruits + fats + grains)
        return [
            f"Spoon {format_recipe_list(dairy)} into a small bowl.",
            f"Top it with {toppings}." if toppings else "Keep it plain or add a pinch of spice.",
            "Serve chilled as a quick snack.",
            finish,
        ]

    if fruits:
        pairings = format_recipe_list(dairy + fats + grains)
        return [
            f"Slice {format_recipe_list(fruits)} into bite-sized pieces.",
            f"Pair it with {pairings}." if pairings else "Serve it fresh.",
            "Keep the snack light and easy to eat.",
            finish,
        ]

    if dairy:
        toppings = format_recipe_list(fats + grains)
        return [
            f"Spoon {format_recipe_list(dairy)} into a small bowl.",
            f"Top it with {toppings}." if toppings else "Keep it plain or add a pinch of spice.",
            "Serve chilled as a quick snack.",
            finish,
        ]

    if proteins:
        extras = format_recipe_list(fats + grains)
        return [
            f"Prepare {format_recipe_list(proteins)} in small portions.",
            f"Pair it with {extras}." if extras else "Season it lightly.",
            "Serve it as a protein-rich snack.",
            finish,
        ]

    primary = ingredients[0]["food"].lower()
    extras = format_recipe_list([item["food"].lower() for item in ingredients[1:]])
    return [
        f"Portion {primary} into a small serving.",
        f"Pair it with {extras}." if extras else "Serve it as a quick snack.",
        "Add light seasoning only if needed.",
        finish,
    ]


def build_recipe_steps(ingredients, meal_type, goal):
    goal_finishes = {
        "lose": "Keep oil, sugar, and heavy toppings low so the meal stays light.",
        "maintain": "Balance the portion so it has enough carbs, protein, and fiber.",
        "gain": "Add calorie-dense ingredients gradually so the meal is filling without feeling too heavy.",
    }
    finish = goal_finishes.get(goal, goal_finishes["maintain"])

    if meal_type == "breakfast":
        return build_breakfast_steps(ingredients, finish)
    if meal_type == "lunch":
        return build_lunch_steps(ingredients, finish)
    if meal_type == "dinner":
        return build_dinner_steps(ingredients, finish)
    return build_snack_steps(ingredients, finish)


def generate_recipe(main_ingredient, meal_type, goal):
    ingredient_terms = parse_ingredient_terms(main_ingredient)
    if not ingredient_terms:
        return None

    goal_tips = {
        "lose": "Use less oil and add more vegetables for a lighter meal.",
        "maintain": "Keep the portion balanced with protein, fiber, and healthy carbs.",
        "gain": "Add nuts, dairy, or whole grains to increase calories in a healthy way.",
    }

    meal_titles = {
        "breakfast": "Power Breakfast Bowl",
        "lunch": "Balanced Lunch Plate",
        "dinner": "Smart Dinner Combo",
        "snack": "Quick Energy Snack",
    }
    prep_times = {
        "breakfast": "8-10 min",
        "lunch": "15-20 min",
        "dinner": "18-25 min",
        "snack": "5-8 min",
    }

    ingredients = []
    used_foods = set()
    for term in ingredient_terms:
        item = find_ingredient(term)
        if item and item["food"].lower() not in used_foods:
            item = dict(item)
            item["source"] = "user"
            ingredients.append(item)
            used_foods.add(item["food"].lower())

    if not ingredients:
        return None

    ingredients = add_goal_ingredients(ingredients, meal_type, goal)
    ingredients = order_recipe_ingredients(ingredients, meal_type)

    total_calories = sum(item["calories"] for item in ingredients)
    title_items = [item["food"] for item in ingredients if item.get("source") == "user"]
    title_items.extend(
        item["food"]
        for item in ingredients
        if item.get("source") != "user" and item["food"] not in title_items
    )
    title_ingredients = format_recipe_list(title_items[:2])
    recipe_name = f"{title_ingredients.title()} {meal_titles.get(meal_type, 'Recipe')}"

    steps = build_recipe_steps(ingredients, meal_type, goal)

    return {
        "name": recipe_name,
        "meal_type": meal_type.title(),
        "goal": goal.title(),
        "tip": goal_tips.get(goal, goal_tips["maintain"]),
        "prep_time": prep_times.get(meal_type, "10-15 min"),
        "summary": f"Recipe generated with {format_recipe_list([item['food'] for item in ingredients])}.",
        "estimated_calories": total_calories,
        "ingredients": ingredients,
        "steps": steps,
    }


def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    bmi = weight / (height_m * height_m)

    if bmi < 18.5:
        category = "Underweight"
        advice = "Increase calorie intake with balanced meals rich in protein and healthy fats."
    elif bmi < 25:
        category = "Normal"
        advice = "Maintain your current lifestyle with regular exercise and a balanced diet."
    elif bmi < 30:
        category = "Overweight"
        advice = "Focus on portion control, regular activity, and nutrient-dense foods."
    else:
        category = "Obese"
        advice = "Work on gradual weight reduction through a structured diet and exercise plan."

    return {
        "bmi": round(bmi, 1),
        "category": category,
        "advice": advice,
    }


def get_current_user():
    user_id = flask.session.get("user_id")
    if not user_id:
        return None

    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, name, email FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return user


def require_login():
    if not flask.session.get("user_id"):
        return flask.jsonify({"error": "Please login first."}), 401
    return None


init_db()


@app.route("/")
def index():
    current_user = get_current_user()
    if not current_user:
        return flask.redirect(flask.url_for("auth"))

    conn = get_db_connection()
    food_log = conn.execute(
        "SELECT * FROM food_log WHERE user_id = ? ORDER BY id DESC",
        (current_user["id"],),
    ).fetchall()
    conn.close()

    total = sum(row["calories"] for row in food_log)

    food_names = sorted(df["Food"].dropna().unique().tolist())
    analytics = build_analytics(current_user["id"])

    return flask.render_template(
        "index.html",
        data=food_log,
        total=total,
        food_names=food_names,
        current_user=current_user,
        analytics=analytics,
    )


@app.route("/planner")
def planner_page():
    current_user = get_current_user()
    if not current_user:
        return flask.redirect(flask.url_for("auth"))

    return flask.render_template("planner.html", current_user=current_user)


@app.route("/bmi-page")
def bmi_page():
    current_user = get_current_user()
    if not current_user:
        return flask.redirect(flask.url_for("auth"))

    return flask.render_template("bmi.html", current_user=current_user)


@app.route("/recipe-page")
def recipe_page():
    current_user = get_current_user()
    if not current_user:
        return flask.redirect(flask.url_for("auth"))

    food_names = sorted(df["Food"].dropna().unique().tolist())
    return flask.render_template(
        "recipe.html",
        current_user=current_user,
        food_names=food_names,
    )


@app.route("/auth")
def auth():
    current_user = get_current_user()
    if current_user:
        return flask.redirect(flask.url_for("index"))
    return flask.render_template("auth.html")


@app.route("/signup", methods=["POST"])
def signup():
    name = flask.request.form.get("name", "").strip()
    email = flask.request.form.get("email", "").strip().lower()
    password = flask.request.form.get("password", "").strip()

    if not name or not email or not password:
        return flask.jsonify({"error": "All signup fields are required."}), 400

    conn = get_db_connection()
    existing_user = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,),
    ).fetchone()

    if existing_user:
        conn.close()
        return flask.jsonify({"error": "Email already exists. Please login."}), 400

    cursor = conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (name, email, generate_password_hash(password)),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    flask.session["user_id"] = user_id
    return flask.jsonify({"message": "Signup successful."})


@app.route("/login", methods=["POST"])
def login():
    email = flask.request.form.get("email", "").strip().lower()
    password = flask.request.form.get("password", "").strip()

    if not email or not password:
        return flask.jsonify({"error": "Email and password are required."}), 400

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password"], password):
        return flask.jsonify({"error": "Invalid email or password."}), 400

    flask.session["user_id"] = user["id"]
    return flask.jsonify({"message": f"Welcome back, {user['name']}."})


@app.route("/logout", methods=["POST"])
def logout():
    flask.session.clear()
    return flask.jsonify({"message": "Logged out successfully."})


@app.route("/add", methods=["POST"])
def add():
    auth_error = require_login()
    if auth_error:
        return auth_error

    food = flask.request.form.get("food", "").strip()
    calories = flask.request.form.get("calories", "0").strip()

    if not food:
        return flask.jsonify({"error": "Food name is required."}), 400

    try:
        calories = int(calories)
    except ValueError:
        return flask.jsonify({"error": "Calories must be a number."}), 400

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO food_log (food, calories, user_id, created_at) VALUES (?, ?, ?, ?)",
        (
            food,
            calories,
            flask.session["user_id"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()
    conn.close()

    return flask.jsonify({"message": "Food added successfully."})


@app.route("/get_calories")
def get_calories():
    food = flask.request.args.get("food_name", "").strip().lower()

    if not food:
        return flask.jsonify({"calories": 0, "serving": ""})

    result = df[df["food_key"] == food]
    if result.empty:
        return flask.jsonify({"calories": 0, "serving": ""})

    row = result.iloc[0]
    return flask.jsonify({"calories": int(row["Calories"]), "serving": row["Serving"]})


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete(item_id):
    auth_error = require_login()
    if auth_error:
        return auth_error

    conn = get_db_connection()
    conn.execute(
        "DELETE FROM food_log WHERE id = ? AND user_id = ?",
        (item_id, flask.session["user_id"]),
    )
    conn.commit()
    conn.close()
    return flask.jsonify({"message": "Item deleted."})


@app.route("/plan", methods=["POST"])
def plan():
    auth_error = require_login()
    if auth_error:
        return auth_error

    data = flask.request.get_json(silent=True) or flask.request.form

    try:
        age = int(data.get("age", 0))
        weight = float(data.get("weight", 0))
        height = float(data.get("height", 0))
        gender = data.get("gender", "male")
        activity = data.get("activity", "sedentary")
        goal = data.get("goal", "maintain")
    except (TypeError, ValueError):
        return flask.jsonify({"error": "Please enter valid details."}), 400

    if age <= 0 or weight <= 0 or height <= 0:
        return flask.jsonify({"error": "Age, weight and height must be greater than 0."}), 400

    if gender not in {"male", "female"}:
        return flask.jsonify({"error": "Please choose a valid gender."}), 400

    if activity not in {"sedentary", "light", "moderate", "active"}:
        return flask.jsonify({"error": "Please choose a valid activity level."}), 400

    if goal not in {"lose", "maintain", "gain"}:
        return flask.jsonify({"error": "Please choose a valid goal."}), 400

    target_calories = calculate_daily_calories(age, gender, weight, height, activity, goal)
    suggestions = build_meal_plan(target_calories, goal)

    return flask.jsonify(
        {
            "target_calories": target_calories,
            "goal": goal,
            "advice": PLAN_GOAL_TIPS.get(goal, PLAN_GOAL_TIPS["maintain"]),
            "meals": suggestions,
        }
    )


@app.route("/recipe", methods=["POST"])
def recipe():
    auth_error = require_login()
    if auth_error:
        return auth_error

    data = flask.request.get_json(silent=True) or flask.request.form
    main_ingredient = (data.get("ingredient") or "").strip()
    meal_type = (data.get("meal_type") or "lunch").lower()
    goal = (data.get("goal") or "maintain").lower()

    if not main_ingredient:
        return flask.jsonify({"error": "Please enter a main ingredient."}), 400

    if meal_type not in VALID_RECIPE_MEAL_TYPES:
        return flask.jsonify({"error": "Please choose a valid meal type."}), 400

    if goal not in VALID_RECIPE_GOALS:
        return flask.jsonify({"error": "Please choose a valid goal."}), 400

    recipe_data = generate_recipe(main_ingredient, meal_type, goal)
    if not recipe_data:
        return flask.jsonify({"error": f"Ingredient not found. Try {RECIPE_SAMPLE_INGREDIENTS}."}), 400

    return flask.jsonify(recipe_data)


@app.route("/bmi", methods=["POST"])
def bmi():
    auth_error = require_login()
    if auth_error:
        return auth_error

    data = flask.request.get_json(silent=True) or flask.request.form

    try:
        weight = float(data.get("weight", 0))
        height = float(data.get("height", 0))
    except (TypeError, ValueError):
        return flask.jsonify({"error": "Please enter valid weight and height."}), 400

    if weight <= 0 or height <= 0:
        return flask.jsonify({"error": "Weight and height must be greater than 0."}), 400

    return flask.jsonify(calculate_bmi(weight, height))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
