# ============================================================
# AUTOMATIC RECOMMENDATION ENGINE
# DermaAI - Local Ollama Recommendation System
# ============================================================

import requests
import json
import re


# ============================================================
# OLLAMA SETTINGS
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

MODEL_NAME = "llama3.2:1b"


# ============================================================
# EXTRACT JSON FROM OLLAMA RESPONSE
# ============================================================

def extract_json(text):

    if not text:
        return None

    text = text.strip()

    # Remove markdown code blocks
    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```",
        "",
        text
    )

    text = text.strip()

    # Find JSON object
    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if not match:
        return None

    json_text = match.group(0)

    try:

        return json.loads(json_text)

    except json.JSONDecodeError:

        return None


# ============================================================
# CLEAN RECOMMENDATION TEXT
# ============================================================

def clean_recommendation(item):

    if not isinstance(item, str):
        return ""

    item = item.strip()

    # Remove unwanted numbering
    item = re.sub(
        r"^\s*\d+[\.\)\-:]\s*",
        "",
        item
    )

    # Remove quotes
    item = item.strip('"').strip("'")

    return item.strip()


# ============================================================
# VALIDATE RECOMMENDATIONS
# ============================================================

def validate_recommendations(data, condition):

    if not isinstance(data, dict):

        data = {}


    food = data.get(
        "food",
        []
    )

    clothing = data.get(
        "clothing",
        []
    )

    home_remedy = data.get(
        "home_remedy",
        []
    )


    # --------------------------------------------------------
    # Make sure values are lists
    # --------------------------------------------------------

    if not isinstance(food, list):

        food = []


    if not isinstance(clothing, list):

        clothing = []


    if not isinstance(home_remedy, list):

        home_remedy = []


    # --------------------------------------------------------
    # Clean values
    # --------------------------------------------------------

    food = [
        clean_recommendation(item)
        for item in food
        if clean_recommendation(item)
    ]


    clothing = [
        clean_recommendation(item)
        for item in clothing
        if clean_recommendation(item)
    ]


    home_remedy = [
        clean_recommendation(item)
        for item in home_remedy
        if clean_recommendation(item)
    ]


    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    food = list(
        dict.fromkeys(food)
    )


    clothing = list(
        dict.fromkeys(clothing)
    )


    home_remedy = list(
        dict.fromkeys(home_remedy)
    )


    # --------------------------------------------------------
    # EXACTLY 5 MAXIMUM
    # --------------------------------------------------------

    food = food[:5]

    clothing = clothing[:5]

    home_remedy = home_remedy[:5]


    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "condition": condition,

        "food": food,

        "clothing": clothing,

        "home_remedy": home_remedy
    }


# ============================================================
# GET AUTOMATIC RECOMMENDATIONS
# ============================================================

def get_automatic_recommendations(condition):

    print()
    print("Generating condition-specific recommendations...")
    print("Condition:", condition)
    print()


    # ========================================================
    # NORMALIZE CONDITION
    # ========================================================

    condition_key = (
        str(condition)
        .strip()
        .lower()
        .replace("_", " ")
    )


    # ========================================================
    # CONDITION-SPECIFIC PROMPT
    # ========================================================

    prompt = f"""
You are a supportive-care recommendation assistant
inside a skin-condition classification application.

The AI image classification model predicted:

{condition}

Your task is to provide supportive-care suggestions
ONLY for the predicted condition above.

IMPORTANT:

The predicted condition is:
{condition}

Do NOT provide recommendations for another disease.

Do NOT mix recommendations from different skin conditions.

For example:
If the condition is Eczema, recommendations must be
appropriate for Eczema only.

If the condition is Psoriasis, recommendations must be
appropriate for Psoriasis only.

If the condition is Contact Dermatitis, recommendations
must be appropriate for Contact Dermatitis only.

If the condition is Urticaria, recommendations must be
appropriate for Urticaria only.


============================================================
FOOD
============================================================

Give exactly 5 practical food suggestions.

Use normal everyday food names.

Examples of acceptable style:

"Fresh fruits such as apples and oranges"

"Vegetables such as carrots and spinach"

"Plain yogurt"

"Whole grains"

"Foods rich in healthy fats such as nuts"

Do NOT use scientific names.

Do NOT use botanical names.

Do NOT use chemical names.

Do NOT use Latin species names.

Do NOT recommend medicines or supplements.

Do NOT claim that food cures the skin condition.

Food suggestions should be supportive only.


============================================================
CLOTHING
============================================================

Give exactly 5 clothing suggestions.

Recommendations must relate to reducing irritation,
friction, sweating, or skin discomfort where relevant
to the predicted condition.

Use simple everyday language.

Examples of style:

"Wear loose-fitting cotton clothes"

"Choose soft breathable fabrics"

"Avoid tight clothing over irritated skin"

Do not use scientific terminology unnecessarily.


============================================================
HOME REMEDIES / SUPPORTIVE CARE
============================================================

Give exactly 5 simple supportive-care suggestions.

They must be relevant to:

{condition}

Do not claim that they cure the disease.

Do not prescribe medicines.

Do not recommend prescription medication.

Do not suggest unsafe treatments.

Do not suggest harsh chemicals.

Do not suggest treatments for another disease.


============================================================
IMPORTANT OUTPUT RULES
============================================================

Return exactly:

5 food suggestions

5 clothing suggestions

5 home-remedy suggestions

Total = 15 suggestions.


Each suggestion must be short.

Use simple English.

Use common everyday food names.

Do NOT use scientific food names.

Do NOT use botanical names.

Do NOT use Latin names.

Do NOT use medical prescriptions.

Do NOT include URLs.

Do NOT include citations.

Do NOT include sources.

Do NOT include dermatologist information.

Do NOT include clinic information.

Do NOT include emergency instructions.

Do NOT diagnose the patient.

Do NOT say that the recommendations cure the condition.

Return ONLY valid JSON.

Do not use Markdown.

Do not write anything before the JSON.

Do not write anything after the JSON.


Return exactly this structure:

{{
    "food": [
        "Food suggestion 1",
        "Food suggestion 2",
        "Food suggestion 3",
        "Food suggestion 4",
        "Food suggestion 5"
    ],

    "clothing": [
        "Clothing suggestion 1",
        "Clothing suggestion 2",
        "Clothing suggestion 3",
        "Clothing suggestion 4",
        "Clothing suggestion 5"
    ],

    "home_remedy": [
        "Home remedy suggestion 1",
        "Home remedy suggestion 2",
        "Home remedy suggestion 3",
        "Home remedy suggestion 4",
        "Home remedy suggestion 5"
    ]
}}
"""


    # ========================================================
    # CALL OLLAMA
    # ========================================================

    try:

        response = requests.post(

            OLLAMA_URL,

            json={

                "model": MODEL_NAME,

                "prompt": prompt,

                "stream": False,

                "options": {

                    "temperature": 0,

                    "num_predict": 700
                }
            },

            timeout=180
        )


        # ====================================================
        # CHECK RESPONSE
        # ====================================================

        response.raise_for_status()


        result = response.json()


        ollama_text = result.get(
            "response",
            ""
        ).strip()


        if not ollama_text:

            print(
                "Ollama returned an empty response."
            )

            return {

                "condition": condition,

                "food": [],

                "clothing": [],

                "home_remedy": []
            }


        # ====================================================
        # PARSE JSON
        # ====================================================

        recommendation_data = extract_json(
            ollama_text
        )


        if recommendation_data is None:

            print(
                "Could not parse Ollama response."
            )

            print()

            print(
                "Raw Ollama response:"
            )

            print(
                ollama_text
            )

            print()

            return {

                "condition": condition,

                "food": [],

                "clothing": [],

                "home_remedy": []
            }


        # ====================================================
        # VALIDATE
        # ====================================================

        recommendation_data = validate_recommendations(

            recommendation_data,

            condition
        )


        # ====================================================
        # CHECK WHETHER 5 EACH WERE GENERATED
        # ====================================================

        if (

            len(recommendation_data["food"]) < 5

            or

            len(recommendation_data["clothing"]) < 5

            or

            len(recommendation_data["home_remedy"]) < 5

        ):

            print(
                "Warning: Ollama did not generate 5 "
                "recommendations in every category."
            )


        # ====================================================
        # DISPLAY RESULT IN TERMINAL
        # ====================================================

        print(
            "AI recommendations generated successfully."
        )

        print()

        print(
            json.dumps(

                recommendation_data,

                indent=4,

                ensure_ascii=False
            )
        )

        print()


        return recommendation_data


    # ========================================================
    # TIMEOUT ERROR
    # ========================================================

    except requests.exceptions.Timeout:

        print(
            "Ollama recommendation request timed out."
        )

        return {

            "condition": condition,

            "food": [],

            "clothing": [],

            "home_remedy": []
        }


    # ========================================================
    # CONNECTION ERROR
    # ========================================================

    except requests.exceptions.ConnectionError:

        print(
            "Could not connect to Ollama."
        )

        print(
            "Make sure Ollama is running."
        )

        return {

            "condition": condition,

            "food": [],

            "clothing": [],

            "home_remedy": []
        }


    # ========================================================
    # OTHER ERROR
    # ========================================================

    except Exception as e:

        print(
            "Ollama recommendation error:",
            e
        )

        return {

            "condition": condition,

            "food": [],

            "clothing": [],

            "home_remedy": []
        }


# ============================================================
# TEST THE ENGINE
# ============================================================

if __name__ == "__main__":

    test_condition = "Psoriasis"


    recommendations = get_automatic_recommendations(

        test_condition
    )


    print(
        "Final recommendation data:"
    )


    print(

        json.dumps(

            recommendations,

            indent=4,

            ensure_ascii=False
        )
    )