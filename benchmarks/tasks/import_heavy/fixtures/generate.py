"""Generate fixtures for import_heavy tasks."""

import csv
import random
from pathlib import Path

def generate_fixtures():
    # Set seed for deterministic generation
    random.seed(42)
    
    fixtures_dir = Path(__file__).parent
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate sales.csv (1000 rows)
    regions = ["North", "South", "East", "West"]
    categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]
    statuses = ["Completed", "Pending", "Cancelled", "Refunded"]
    
    sales_path = fixtures_dir / "sales.csv"
    with open(sales_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "product_id", "region", "category", "amount", "status", "date"])
        
        for i in range(1, 1001):
            product_id = f"P{random.randint(100, 150)}"
            region = random.choice(regions)
            category = random.choice(categories)
            amount = round(random.uniform(10.0, 500.0), 2)
            
            # Weighted statuses
            weights = [0.7, 0.15, 0.1, 0.05]
            status = random.choices(statuses, weights=weights)[0]
            
            date = f"2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
            
            writer.writerow([i, product_id, region, category, amount, status, date])
            
    # 2. Generate products.csv (51 rows)
    products_path = fixtures_dir / "products.csv"
    with open(products_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "name", "price", "supplier"])
        
        for i in range(100, 151):
            product_id = f"P{i}"
            name = f"Product-{i}"
            price = round(random.uniform(5.0, 200.0), 2)
            supplier = f"Supplier-{random.randint(1, 5)}"
            writer.writerow([product_id, name, price, supplier])
            
    # 3. Generate users.json (unused by current tasks but good to have)
    import json
    users = []
    for i in range(1, 101):
        users.append({
            "id": i,
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "active": random.random() > 0.1,
            "tags": random.sample(["premium", "new", "beta", "churn_risk"], k=random.randint(0, 3))
        })
        
    with open(fixtures_dir / "users.json", "w") as f:
        json.dump(users, f, indent=2)

if __name__ == "__main__":
    generate_fixtures()
