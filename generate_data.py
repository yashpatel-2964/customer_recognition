import json
import random
import datetime
import os
from pymongo import MongoClient
from db_connection import get_database

def generate_customer_data():
    # Connect to database to get existing customer IDs
    db = get_database()
    customers_collection = db['customers']
    
    # Get existing customer IDs from MongoDB
    existing_customers = list(customers_collection.find({}, {"customer_id": 1}))
    customer_ids = [customer["customer_id"] for customer in existing_customers]
    
    # Add sample IDs if needed
    sample_ids = ["C1743108678", "C1743108464", "C100001", "C100002"]
    for sample_id in sample_ids:
        if sample_id not in customer_ids:
            customer_ids.append(sample_id)
    
    print(f"Generating data for {len(customer_ids)} customers: {customer_ids}")
    
    customer_data = {}
    
    for customer_id in customer_ids:
        # Generate random purchase patterns for each customer
        avg_bill = random.uniform(50, 200)  # Average bill amount
        bill_variance = avg_bill * 0.2      # Variance in bills
        purchase_frequency = random.randint(10, 30)  # Days between purchases
        
        # Generate purchase history (last 10 purchases)
        purchases = []
        
        # Starting date (about a year ago)
        current_date = datetime.datetime.now() - datetime.timedelta(days=365)
        
        for i in range(10):
            # Generate purchase date
            purchase_date = current_date + datetime.timedelta(
                days=random.randint(purchase_frequency - 5, purchase_frequency + 5) * i
            )
            
            # Don't exceed current date
            if purchase_date > datetime.datetime.now():
                break
                
            # Generate bill amount based on pattern
            weekday_factor = 1.0 + 0.2 * (purchase_date.weekday() == 5 or purchase_date.weekday() == 6)  # Weekend bonus
            season_factor = 1.0 + 0.1 * (purchase_date.month in [11, 12])  # Holiday season bonus
            
            bill_amount = random.normalvariate(
                avg_bill * weekday_factor * season_factor, 
                bill_variance
            )
            
            purchases.append({
                "date": purchase_date.strftime("%Y-%m-%d"),
                "amount": round(bill_amount, 2),
                "items_count": random.randint(1, 20)
            })
        
        # Store customer data
        customer_data[customer_id] = {
            "customer_id": customer_id,
            "first_seen": purchases[0]["date"] if purchases else datetime.datetime.now().strftime("%Y-%m-%d"),
            "visit_count": len(purchases),
            "avg_bill": round(sum(p["amount"] for p in purchases) / len(purchases) if purchases else 0, 2),
            "purchases": purchases,
            "features": {
                "avg_bill": round(sum(p["amount"] for p in purchases) / len(purchases) if purchases else 0, 2),
                "max_bill": round(max([p["amount"] for p in purchases]) if purchases else 0, 2),
                "min_bill": round(min([p["amount"] for p in purchases]) if purchases else 0, 2),
                "avg_items": round(sum(p["items_count"] for p in purchases) / len(purchases) if purchases else 0, 2),
                "frequency_days": purchase_frequency
            }
        }
    
    # Ensure directory exists
    os.makedirs("data", exist_ok=True)
    
    # Save to file
    with open('data/customer_data.json', 'w') as f:
        json.dump(customer_data, f, indent=4)
    
    print("Synthetic data generated and saved to data/customer_data.json")
    
    # Also update MongoDB with purchase history
    for customer_id, data in customer_data.items():
        customers_collection.update_one(
            {"customer_id": customer_id},
            {"$set": {"purchase_history": data["purchases"],
                     "billing_features": data["features"]}},
            upsert=True
        )
    
    print("MongoDB updated with purchase history data")
    return customer_data

if __name__ == "__main__":
    generate_customer_data()