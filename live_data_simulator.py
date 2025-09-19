import pandas as pd
from faker import Faker
import random
from datetime import datetime
import time
import os
import argparse
import sqlite3

# Initialize Faker
fake = Faker()

def load_master_data(db_path):
    """Loads product and store master data from a SQLite database."""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at '{db_path}'.")
        print("Please run fake_data_generator.py first to create the database.")
        exit()

    try:
        with sqlite3.connect(db_path) as conn:
            products_df = pd.read_sql_query("SELECT * FROM products", conn)
            stores_df = pd.read_sql_query("SELECT * FROM stores", conn)
    except (sqlite3.OperationalError, pd.io.sql.DatabaseError) as e:
        print(f"Error reading from database: {e}")
        print("The database might be missing the 'products' or 'stores' tables.")
        print("Please run fake_data_generator.py first to create the master data.")
        exit()

    # Convert dataframes to list of dicts for easier processing
    product_list = products_df.to_dict('records')
    store_list = stores_df.to_dict('records')

    print(f"Loaded {len(product_list)} products and {len(store_list)} stores from '{db_path}'.")
    return product_list, store_list

def generate_new_sale(product_list, store_list):
    """Generates a single new sales transaction."""
    product = random.choice(product_list)
    store = random.choice(store_list)
    units_sold = random.randint(1, 5) # Live transactions might be smaller on average

    sale_record = {
        "TransactionID": fake.uuid4(),
        "Date": datetime.now(),
        "StoreID": store["StoreID"],
        "ProductID": product["ProductID"],
        "ProductName": product["ProductName"],
        "UnitsSold": units_sold,
        "Price": product["Price"],
        "TotalRevenue": round(units_sold * product["Price"], 2)
    }
    return sale_record

def append_to_sqlite(record_df, table_name, conn):
    """Appends a DataFrame to a table in the SQLite database."""
    record_df.to_sql(table_name, conn, if_exists='append', index=False)

def main():
    """Main function to run the live data simulator."""
    parser = argparse.ArgumentParser(description="Simulate live transactions by appending to a SQLite database.")
    parser.add_argument("--db-file", type=str, default="data/lt_walmart_data.db", help="Path to the SQLite database file (default: 'data/lt_walmart_data.db').")
    parser.add_argument("--interval", type=float, default=2.0, help="Average time in seconds between new transactions (default: 2.0).")
    args = parser.parse_args()

    print("--- Live Transaction Simulator ---")
    print(f"Appending to 'sales_data' table in '{args.db_file}'.")
    print(f"New transaction every ~{args.interval} seconds. Press Ctrl+C to stop.")

    product_list, store_list = load_master_data(args.db_file)

    try:
        with sqlite3.connect(args.db_file) as conn:
            while True:
                new_sale = generate_new_sale(product_list, store_list)
                new_sale_df = pd.DataFrame([new_sale])
                append_to_sqlite(new_sale_df, "sales_data", conn)

                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] New Sale: {new_sale['UnitsSold']}x '{new_sale['ProductName']}' at {new_sale['StoreID']}")

                sleep_time = random.uniform(args.interval / 2, args.interval * 1.5)
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n--- Simulator stopped by user. ---")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
