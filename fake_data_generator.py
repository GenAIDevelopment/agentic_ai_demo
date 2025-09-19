import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import sqlite3
import argparse
from tqdm import tqdm
import os

# Initialize Faker to generate realistic fake data
fake = Faker()

# --- Configuration ---
NUM_SALES_RECORDS = 10000
NUM_PRODUCTS = 100
NUM_STORES = 20
NUM_FEEDBACK_RECORDS = 500
START_DATE = datetime(2024, 1, 1)
DEFAULT_DATABASE = "data/lt_walmart_data.db"

def generate_real_product_name():
    """Generates a more realistic product name for our LT_Walmart simulation."""
    brands = ["Great-Value", "Marketside", "Mainstays", "onn.", "Equate", "George", "Time-and-Tru"]
    categories = {
        "Groceries": ["Milk", "Organic-Bananas", "Chicken-Breast", "Eggs", "Cereal", "Coffee", "Bread"],
        "Electronics": ["4K-TV", "Wireless-Headphones", "Laptop", "Smartphone", "Webcam", "Mouse"],
        "Home-Goods": ["Bath-Towel-Set", "Dinnerware", "Vacuum", "Air-Freshener", "Laundry-Detergent"],
        "Apparel": ["Mens-T-Shirt", "Womens-Jeans", "Socks-6-Pack", "Hoodie"],
        "Health": ["Ibuprofen", "Toothpaste", "Body-Wash", "Shampoo"]
    }
    
    category = random.choice(list(categories.keys()))
    product_type = random.choice(categories[category])
    brand = random.choice(brands)
    
    # Create some variation
    if category in ["Groceries", "Health"]:
        return f"{brand}-{product_type}"
    elif category == "Electronics":
        size = random.choice(["50-inch", "15-inch", "65-inch"])
        return f"{brand}-{size}-{product_type}"
    else:
        return f"{brand}-{product_type}"

def generate_master_data(num_products, num_stores):
    """Generates product and store master data with realistic, unique product names."""
    product_list = []
    generated_names = set()
    i = 0
    while len(product_list) < num_products:
        name = generate_real_product_name()
        if name not in generated_names:
            product_list.append({
                "ProductID": f"PROD{100+i}",
                "ProductName": name,
                "Price": round(random.uniform(5.0, 500.0), 2)
            })
            generated_names.add(name)
        i += 1

    store_list = [
        {"StoreID": f"STORE{10+i}", "StoreLocation": fake.city()}
        for i in range(num_stores)
    ]
    print("Generated Product and Store master data.")
    return product_list, store_list

def generate_sales_data(num_records, product_list, store_list, start_date, end_date):
    """Generates fake sales data."""
    sales_data = []
    for _ in tqdm(range(num_records), desc="Generating Sales Data"):
        product = random.choice(product_list)
        store = random.choice(store_list)
        transaction_date = fake.date_time_between(start_date=start_date, end_date=end_date)
        units_sold = random.randint(1, 10)

        sales_data.append({
            "TransactionID": fake.uuid4(),
            "Date": transaction_date,
            "StoreID": store["StoreID"],
            "ProductID": product["ProductID"],
            "ProductName": product["ProductName"],
            "UnitsSold": units_sold,
            "Price": product["Price"],
            "TotalRevenue": round(units_sold * product["Price"], 2)
        })
    return pd.DataFrame(sales_data)

def generate_inventory_data(product_list, store_list, start_date, end_date):
    """Generates fake inventory data."""
    inventory_data = []
    for product in tqdm(product_list, desc="Generating Inventory Data"):
        for store in store_list:
            # Let's assume not every product is in every store
            if random.random() > 0.2:  # 80% chance a product is in a given store
                inventory_data.append({
                    "ProductID": product["ProductID"],
                    "StoreID": store["StoreID"],
                    "StockLevel": random.randint(0, 500), # Some items might be out of stock
                    "LastRestockDate": fake.date_between(start_date=start_date, end_date=end_date)
                })
    return pd.DataFrame(inventory_data)

def generate_feedback_data(num_records, store_list, start_date, end_date):
    """Generates fake customer feedback data."""
    feedback_data = []
    positive_keywords = ["love", "excellent", "great", "happy", "satisfied", "fast", "amazing"]
    negative_keywords = ["bad", "slow", "disappointed", "broken", "poor", "unhappy", "terrible"]

    for _ in tqdm(range(num_records), desc="Generating Feedback Data"):
        store = random.choice(store_list)
        feedback_date = fake.date_time_between(start_date=start_date, end_date=end_date)
        
        if random.random() > 0.4:  # 60% positive feedback
            comment = f"I {random.choice(positive_keywords)} the service at the {store['StoreLocation']} store. The staff was very helpful."
            sentiment = round(random.uniform(0.5, 1.0), 2)
        else:  # 40% negative feedback
            comment = f"The product I bought was {random.choice(negative_keywords)}. The checkout process at the {store['StoreLocation']} store was too {random.choice(negative_keywords)}."
            sentiment = round(random.uniform(0.0, 0.49), 2)

        feedback_data.append({
            "FeedbackID": fake.uuid4(),
            "Date": feedback_date,
            "StoreID": store["StoreID"],
            "Comment": comment,
            "Sentiment": sentiment
        })
    return pd.DataFrame(feedback_data)

def save_to_sqlite(df, table_name, conn):
    """Saves a DataFrame to a table in the specified SQLite database."""
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    print(f"Successfully generated and saved data to table '{table_name}'.")

def main():
    """Main function to parse arguments and generate data."""
    parser = argparse.ArgumentParser(description="Generate fake e-commerce data.")
    parser.add_argument("--sales", type=int, default=NUM_SALES_RECORDS, help=f"Number of sales records to generate (default: {NUM_SALES_RECORDS}).")
    parser.add_argument("--products", type=int, default=NUM_PRODUCTS, help=f"Number of products to generate (default: {NUM_PRODUCTS}).")
    parser.add_argument("--stores", type=int, default=NUM_STORES, help=f"Number of stores to generate (default: {NUM_STORES}).")
    parser.add_argument("--feedback", type=int, default=NUM_FEEDBACK_RECORDS, help=f"Number of feedback records to generate (default: {NUM_FEEDBACK_RECORDS}).")
    parser.add_argument("--db-file", type=str, default=DEFAULT_DATABASE, help=f"Name of the SQLite database file (default: {DEFAULT_DATABASE}).")
    args = parser.parse_args()

    end_date = datetime.now()

    # Ensure the database directory exists
    db_path = args.db_file
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # --- Create SQLite Connection and generate data ---
    try:
        with sqlite3.connect(db_path) as conn:
            print(f"Opened connection to SQLite database: {db_path}")

            # --- Generate Master Data ---
            product_list, store_list = generate_master_data(args.products, args.stores)

            # --- Save Master Data ---
            products_df = pd.DataFrame(product_list)
            save_to_sqlite(products_df, "products", conn)
            stores_df = pd.DataFrame(store_list)
            save_to_sqlite(stores_df, "stores", conn)

            # --- Generate and Save Sales Data ---
            sales_df = generate_sales_data(args.sales, product_list, store_list, START_DATE, end_date)
            save_to_sqlite(sales_df, "sales_data", conn)

            # --- Generate and Save Inventory Data ---
            inventory_df = generate_inventory_data(product_list, store_list, START_DATE, end_date)
            save_to_sqlite(inventory_df, "inventory", conn)

            # --- Generate and Save Customer Feedback Data ---
            feedback_df = generate_feedback_data(args.feedback, store_list, START_DATE, end_date)
            save_to_sqlite(feedback_df, "customer_feedback", conn)

        print("\nAll data generation complete.")
    except sqlite3.Error as e:
        print(f"\nDatabase error: {e}")

if __name__ == "__main__":
    main()
