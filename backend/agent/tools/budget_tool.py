import math
from typing import Literal
from pydantic import BaseModel
from models.schemas import AttractionItem

# Travel styles and their corresponding statuses
TravelStyle = Literal["budget", "standard", "luxury"]
BudgetStatus = Literal["WITHIN_BUDGET", "NEAR_LIMIT", "OVER_BUDGET"]

class BudgetEstimateResult(BaseModel):
    accommodation_cost: float
    food_cost: float
    transportation_cost: float
    attraction_fees: float
    miscellaneous_cost: float
    total_cost: float
    remaining_budget: float
    budget_status: BudgetStatus

class BudgetTool:
    """
    BudgetTool estimates travel expenses locally based on trip duration,
    travelers, selected attractions, budget, and travel style.
    Calculations are deterministic and configurable.
    """

    # Configurable base rates (in INR) per room/person per day
    # Standard assumption: travelers share rooms (up to 2 people per room)
    ACCOMMODATION_RATES: dict[str, float] = {
        "budget": 1200.0,    # Hostels / homestays
        "standard": 3500.0,  # Mid-range hotels
        "luxury": 10000.0,   # Premium hotels/resorts
    }

    FOOD_RATES: dict[str, float] = {
        "budget": 500.0,     # Street food & local eateries
        "standard": 1500.0,  # Mid-range cafes/restaurants
        "luxury": 4500.0,    # Premium fine dining
    }

    TRANSPORT_RATES: dict[str, float] = {
        "budget": 200.0,     # Public transit (metro, bus)
        "standard": 800.0,   # Cabs / auto-rickshaws
        "luxury": 2500.0,    # Private rented vehicle with chauffeur
    }

    MISC_RATES: dict[str, float] = {
        "budget": 150.0,     # Basic needs
        "standard": 500.0,   # Some souvenirs & emergency stash
        "luxury": 1500.0,    # Extra services, high-end shopping
    }

    # Configurable base entry fees (in INR) for attraction categories
    CATEGORY_FEES: dict[str, float] = {
        "Theme Park": 1200.0,
        "Aquarium": 600.0,
        "Zoo": 350.0,
        "Museum": 200.0,
        "Castle": 250.0,
        "Fort": 200.0,
        "Theatre": 600.0,
        "Cinema": 350.0,
        "Archaeological Site": 150.0,
        "Historic Ruins": 100.0,
        "National Park": 200.0,
        "Nature Reserve": 100.0,
        "Garden": 50.0,
    }

    # Surcharges or factors
    ADVENTURE_SURCHARGE = 500.0         # Extra activity/guide fee for adventure categories
    FAMILY_TRANSPORT_MULTIPLIER = 1.3  # Extra transport cost for families/groups
    
    # Status thresholds (as fraction of budget)
    NEAR_LIMIT_THRESHOLD = 0.9  # 90% of budget

    def run(
        self,
        selected_attractions: list[AttractionItem],
        total_days: int,
        travelers: int,
        budget: float,
        travel_style: str,
    ) -> BudgetEstimateResult:
        """
        Estimate trip costs based on duration, traveler count, selected attractions,
        overall budget, and travel style.
        """
        # Ensure input values are within safe boundaries
        total_days = max(1, total_days)
        travelers = max(1, travelers)
        style = travel_style.lower() if travel_style else "standard"
        if style not in self.ACCOMMODATION_RATES:
            style = "standard"

        # 1. Accommodation estimation: assume 2 travelers share 1 room
        rooms = math.ceil(travelers / 2.0)
        daily_accom_rate = self.ACCOMMODATION_RATES[style]
        accommodation_cost = daily_accom_rate * total_days * rooms

        # 2. Food estimation: per person per day
        daily_food_rate = self.FOOD_RATES[style]
        food_cost = daily_food_rate * total_days * travelers

        # 3. Transportation estimation: per person per day
        daily_transport_rate = self.TRANSPORT_RATES[style]
        # Family/Group modifier: if travelers >= 3 or style == "family", increase local transport multiplier
        transport_mult = 1.0
        if travelers >= 3 or style == "family":
            transport_mult = self.FAMILY_TRANSPORT_MULTIPLIER
        transportation_cost = daily_transport_rate * total_days * travelers * transport_mult

        # 4. Attraction fees estimation
        attraction_fees = 0.0
        for item in selected_attractions:
            # Resolve entry fee based on category
            fee_per_person = self.CATEGORY_FEES.get(item.category, 0.0)

            # Adventure modifier: check if attraction category falls under adventure categories
            adventure_categories = {"Mountain Peak", "Waterfall", "National Park", "Nature Reserve", "Beach"}
            if item.category in adventure_categories or style == "adventure":
                fee_per_person += self.ADVENTURE_SURCHARGE

            # Travel style adjustments for attractions (e.g. VIP passes vs discounts)
            if style == "budget":
                fee_per_person *= 0.5  # Student/group discounts or choosing free slots
            elif style == "luxury":
                fee_per_person *= 1.5  # VIP entrance / guided private tour fees
            
            attraction_fees += fee_per_person * travelers

        # 5. Miscellaneous cost estimation: per person per day
        daily_misc_rate = self.MISC_RATES[style]
        miscellaneous_cost = daily_misc_rate * total_days * travelers

        # Total Cost Sum
        total_cost = (
            accommodation_cost
            + food_cost
            + transportation_cost
            + attraction_fees
            + miscellaneous_cost
        )

        # Budget Status Calculations
        remaining_budget = budget - total_cost
        
        if total_cost > budget:
            budget_status: BudgetStatus = "OVER_BUDGET"
        elif total_cost >= budget * self.NEAR_LIMIT_THRESHOLD:
            budget_status: BudgetStatus = "NEAR_LIMIT"
        else:
            budget_status: BudgetStatus = "WITHIN_BUDGET"

        return BudgetEstimateResult(
            accommodation_cost=round(accommodation_cost, 2),
            food_cost=round(food_cost, 2),
            transportation_cost=round(transportation_cost, 2),
            attraction_fees=round(attraction_fees, 2),
            miscellaneous_cost=round(miscellaneous_cost, 2),
            total_cost=round(total_cost, 2),
            remaining_budget=round(remaining_budget, 2),
            budget_status=budget_status,
        )
