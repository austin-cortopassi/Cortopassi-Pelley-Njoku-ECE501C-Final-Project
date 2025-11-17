"""
index_performance.py

Script to measure query execution time before and after creating recommended indexes.
Saves a small CSV report with timings and prints summary to stdout.
"""
import sqlite3
import time
import csv

DB_PATH = "restaurant_order_recommender.db"
REPORT_CSV = "index_performance_report.csv"

RECOMMENDED_INDEXES = [
    ("idx_orders_restaurant", "orders", "restaurant_id"),
    ("idx_orders_datetime", "orders", "order_datetime"),
    ("idx_restaurants_loc", "restaurants", "location"),
    ("idx_restaurants_cuisine", "restaurants", "cuisine_type"),
]

TEST_QUERIES = {
    "join_group_by_restaurant": """
        SELECT r.restaurant_id, COUNT(o.order_id) as cnt
        FROM restaurants r
        JOIN orders o ON r.restaurant_id = o.restaurant_id
        GROUP BY r.restaurant_id
    """,
    "filter_by_datetime": """
        SELECT *
        FROM orders
        WHERE order_datetime >= '2020-01-01' AND order_datetime < '2020-02-01'
    """,
    "aggregate_revenue": """
        SELECT restaurant_id, SUM(subtotal) as revenue
        FROM orders
        GROUP BY restaurant_id
        ORDER BY revenue DESC
        LIMIT 100
    """
}

def time_query(conn, sql, repeat=3):
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA temp_store = MEMORY;")
    except Exception:
        pass
    # Warm-up
    cur.execute(sql).fetchall()
    times = []
    for _ in range(repeat):
        start = time.perf_counter()
        cur.execute(sql).fetchall()
        end = time.perf_counter()
        times.append((end-start)*1000.0)
    times.sort()
    return times[len(times)//2]

def apply_indexes(conn):
    cur = conn.cursor()
    for name, table, col in RECOMMENDED_INDEXES:
        sql = f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({col});"
        cur.execute(sql)
    conn.commit()

def run_analysis(db_path=DB_PATH, report_path=REPORT_CSV):
    conn = sqlite3.connect(db_path)
    results = []
    print("Running performance analysis on:", db_path)
    for key, q in TEST_QUERIES.items():
        print(f"Timing query (before): {key}")
        t_before = time_query(conn, q)
        apply_indexes(conn)
        print(f"Timing query (after): {key}")
        t_after = time_query(conn, q)
        improvement = t_before - t_after
        results.append({
            "query": key,
            "time_before_ms": round(t_before, 3),
            "time_after_ms": round(t_after, 3),
            "improvement_ms": round(improvement, 3)
        })
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["query","time_before_ms","time_after_ms","improvement_ms"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    conn.close()
    print("Analysis complete. Report saved to:", report_path)
    for r in results:
        print(r)

if __name__ == "__main__":
    run_analysis()
