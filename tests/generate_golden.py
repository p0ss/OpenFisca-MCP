"""Generate golden fixtures from the OpenFisca API.

Run with: poetry run python tests/generate_golden.py
Requires the OpenFisca server to be running on port 5050.
"""

import json
from pathlib import Path

import httpx

BASE_URL = "http://localhost:5050"
GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden"


def save_golden(name: str, request: dict | None, response: dict):
    """Save a golden fixture."""
    fixture = {"request": request, "response": response}
    path = GOLDEN_DIR / f"{name}.json"
    path.write_text(json.dumps(fixture, indent=2))
    print(f"Saved: {path}")


def main():
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # Entities
        response = client.get("/entities")
        save_golden("entities", None, response.json())

        # Variables list
        response = client.get("/variables")
        save_golden("variables_list", None, response.json())

        # Variable details
        for var in ["salary", "income_tax", "age", "housing_allowance"]:
            response = client.get(f"/variable/{var}")
            save_golden(f"variable_{var}", None, response.json())

        # Parameters list
        response = client.get("/parameters")
        save_golden("parameters_list", None, response.json())

        # Calculate - single person income tax
        request = {
            "persons": {
                "alice": {
                    "birth": {"ETERNITY": "1990-01-15"},
                    "salary": {"2024-01": 3000},
                    "income_tax": {"2024-01": None},
                }
            },
            "households": {
                "household1": {
                    "adults": ["alice"],
                    "rent": {"2024-01": 800},
                }
            },
        }
        response = client.post("/calculate", json=request)
        save_golden("calculate_income_tax", request, response.json())

        # Calculate - couple total taxes
        request = {
            "persons": {
                "alice": {
                    "birth": {"ETERNITY": "1985-03-20"},
                    "salary": {"2024-01": 4000},
                },
                "bob": {
                    "birth": {"ETERNITY": "1983-07-10"},
                    "salary": {"2024-01": 2500},
                },
            },
            "households": {
                "household1": {
                    "adults": ["alice", "bob"],
                    "rent": {"2024-01": 1200},
                    "total_taxes": {"2024-01": None},
                }
            },
        }
        response = client.post("/calculate", json=request)
        save_golden("calculate_couple_taxes", request, response.json())

        # Calculate - family with benefits
        request = {
            "persons": {
                "parent1": {
                    "birth": {"ETERNITY": "1980-05-12"},
                    "salary": {"2024-01": 5000},
                },
                "parent2": {
                    "birth": {"ETERNITY": "1982-09-25"},
                    "salary": {"2024-01": 3000},
                },
                "child1": {
                    "birth": {"ETERNITY": "2010-02-14"},
                    "salary": {"2024-01": 0},
                },
                "child2": {
                    "birth": {"ETERNITY": "2015-11-30"},
                    "salary": {"2024-01": 0},
                },
            },
            "households": {
                "household1": {
                    "adults": ["parent1", "parent2"],
                    "children": ["child1", "child2"],
                    "rent": {"2024-01": 1500},
                    "total_benefits": {"2024-01": None},
                    "disposable_income": {"2024-01": None},
                }
            },
        }
        response = client.post("/calculate", json=request)
        save_golden("calculate_family_benefits", request, response.json())

        # Trace - income tax dependencies
        request = {
            "persons": {
                "alice": {
                    "birth": {"ETERNITY": "1990-01-15"},
                    "salary": {"2024-01": 3000},
                    "income_tax": {"2024-01": None},
                }
            },
            "households": {
                "household1": {
                    "adults": ["alice"],
                    "rent": {"2024-01": 800},
                }
            },
        }
        response = client.post("/trace", json=request)
        save_golden("trace_income_tax", request, response.json())

    print("\nDone! Golden fixtures generated.")


if __name__ == "__main__":
    main()
