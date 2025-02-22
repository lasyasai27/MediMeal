import random
from typing import Dict, List, Optional

class PricingService:
    """Service to handle medication pricing from various sources"""
    
    # Demo pharmacy list - in production, this would come from a database
    PHARMACIES = [
        "CVS Pharmacy",
        "Walgreens",
        "Walmart Pharmacy",
        "Rite Aid",
        "Costco Pharmacy"
    ]

    @staticmethod
    async def get_goodrx_pricing(medication_name: str) -> Optional[Dict]:
        """
        Get pricing from GoodRx API (simulated)
        In production, replace with actual GoodRx API call
        """
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            # Generate realistic-looking demo data
            base_price = random.uniform(20, 200)
            return {
                "lowest_price": base_price * 0.8,
                "average_price": base_price,
                "highest_price": base_price * 1.2,
                "source": "GoodRx"
            }
        except Exception as e:
            print(f"Error getting GoodRx pricing: {e}")
            return None

    @staticmethod
    async def get_pharmacy_pricing(medication_name: str) -> List[Dict]:
        """
        Get pricing from various pharmacies (simulated)
        In production, replace with actual pharmacy API calls
        """
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            prices = []
            base_price = random.uniform(20, 200)
            
            for pharmacy in PricingService.PHARMACIES:
                # Generate slightly different prices for each pharmacy
                variation = random.uniform(0.8, 1.2)
                price = base_price * variation
                
                prices.append({
                    "pharmacy": pharmacy,
                    "price": round(price, 2),
                    "updated_at": "2024-03-20",  # In production, use real timestamp
                    "in_stock": random.choice([True, True, True, False])  # 75% chance of being in stock
                })
            
            return prices
        except Exception as e:
            print(f"Error getting pharmacy pricing: {e}")
            return []

    @staticmethod
    async def get_insurance_pricing(medication_name: str) -> Optional[Dict]:
        """
        Get insurance coverage and pricing (simulated)
        In production, replace with actual insurance API calls
        """
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            base_price = random.uniform(20, 200)
            covered = random.choice([True, True, False])  # 66% chance of being covered
            
            return {
                "covered": covered,
                "copay": round(base_price * 0.2, 2) if covered else None,
                "requires_prior_auth": random.choice([True, False]),
                "tier": random.randint(1, 4) if covered else None
            }
        except Exception as e:
            print(f"Error getting insurance pricing: {e}")
            return None

    @staticmethod
    async def get_combined_pricing(medication_name: str) -> Dict:
        """Combine pricing data from all sources"""
        try:
            # Gather all pricing data concurrently
            goodrx_data, pharmacy_prices, insurance_data = await asyncio.gather(
                PricingService.get_goodrx_pricing(medication_name),
                PricingService.get_pharmacy_pricing(medication_name),
                PricingService.get_insurance_pricing(medication_name)
            )
            
            # Calculate price statistics from pharmacy data
            if pharmacy_prices:
                prices = [p["price"] for p in pharmacy_prices]
                average_price = sum(prices) / len(prices)
                lowest_price = min(prices)
                highest_price = max(prices)
            else:
                # Fallback to GoodRx data or default values
                average_price = goodrx_data["average_price"] if goodrx_data else 0
                lowest_price = goodrx_data["lowest_price"] if goodrx_data else 0
                highest_price = goodrx_data["highest_price"] if goodrx_data else 0

            return {
                "average_price": round(average_price, 2),
                "lowest_price": round(lowest_price, 2),
                "highest_price": round(highest_price, 2),
                "price_sources": pharmacy_prices,
                "goodrx_data": goodrx_data,
                "insurance_data": insurance_data,
                "is_generic": random.choice([True, False]),  # In production, get from medication data
                "last_updated": "2024-03-20"  # In production, use real timestamp
            }
        except Exception as e:
            print(f"Error in get_combined_pricing: {e}")
            # Return default structure with zero prices
            return {
                "average_price": 0,
                "lowest_price": 0,
                "highest_price": 0,
                "price_sources": [],
                "goodrx_data": None,
                "insurance_data": None,
                "is_generic": False,
                "last_updated": "2024-03-20"
            }