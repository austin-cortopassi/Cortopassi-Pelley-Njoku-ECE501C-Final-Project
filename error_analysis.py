import sqlite3

def check_missing_delivery_times(cursor):
    cursor.execute("SELECT * FROM orders WHERE delivery_time IS NULL OR TRIM(delivery_time) = ''")
    return cursor.fetchall()

def check_invalid_subtotals(cursor):
    cursor.execute("SELECT * FROM orders WHERE subtotal <= 0")
    return cursor.fetchall()

def check_negative_item_prices(cursor):
    cursor.execute("""
        SELECT * FROM orders
        WHERE min_item_price <= 0 OR max_item_price <= 0
    """)
    return cursor.fetchall()

def check_invalid_item_counts(cursor):
    cursor.execute("""
        SELECT * FROM orders
        WHERE total_items <= 0 OR num_distinct_items <= 0
    """)
    return cursor.fetchall()

def main():
    conn = sqlite3.connect("restaurant_order_recommender.db")
    cursor = conn.cursor()

    issues = {
        "Missing Delivery Times": check_missing_delivery_times(cursor),
        "Invalid Subtotals (≤ 0)": check_invalid_subtotals(cursor),
        "Negative Item Prices": check_negative_item_prices(cursor),
        "Invalid Item Counts": check_invalid_item_counts(cursor)
    }

    conn.close()

    with open("error_report.txt", "w", encoding="utf-8") as f:
        for issue, rows in issues.items():
            f.write(f"\n=== {issue} ===\n")
            for row in rows:
                f.write(str(row) + "\n")
            f.write(f"Total: {len(rows)} issues found\n")

    print("✅ Error analysis complete. See 'error_report.txt' for details.")

if __name__ == "__main__":
    main()