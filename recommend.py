"""
recommend.py (historical_data adaptation)
Generates basic performance-based restaurant recommendations.
"""
import sqlite3

DB_PATH = "restaurant_order_recommender.db"


# Fast Delivery
def fast_delivery(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
        SELECT r.restaurant_id, r.cuisine_type,
               AVG((julianday(o.delivery_time) - julianday(o.order_datetime)) * 24 * 60)
                   AS avg_delivery_min
        FROM restaurants r
        JOIN orders o ON r.restaurant_id = o.restaurant_id
        WHERE o.delivery_time IS NOT NULL
        GROUP BY r.restaurant_id
        HAVING COUNT(o.order_id) > 20
        ORDER BY avg_delivery_min ASC
        LIMIT ?;
    """

    cur.execute(query, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# High Value Restaurants (highest avg item price)
def high_value(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
        SELECT r.restaurant_id, r.cuisine_type,
               AVG(o.subtotal / NULLIF(o.total_items, 0)) AS avg_item_value
        FROM restaurants r
        JOIN orders o ON r.restaurant_id = o.restaurant_id
        GROUP BY r.restaurant_id
        HAVING COUNT(o.order_id) > 20
        ORDER BY avg_item_value DESC
        LIMIT ?;
    """

    cur.execute(query, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# Most Popular Restaurants by Total Orders
def most_popular(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
        SELECT r.restaurant_id, r.cuisine_type,
               COUNT(o.order_id) AS total_orders
        FROM restaurants r
        JOIN orders o ON r.restaurant_id = o.restaurant_id
        GROUP BY r.restaurant_id
        ORDER BY total_orders DESC
        LIMIT ?;
    """

    cur.execute(query, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# Top Restaurants by Cuisine Based on Avg Order Value
def top_by_cuisine(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
        SELECT r.cuisine_type,
               r.restaurant_id,
               AVG(o.subtotal) AS avg_order_value,
               COUNT(o.order_id) AS total_orders
        FROM restaurants r
        JOIN orders o ON r.restaurant_id = o.restaurant_id
        GROUP BY r.cuisine_type, r.restaurant_id
        ORDER BY avg_order_value DESC
        LIMIT ?;
    """

    cur.execute(query, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# Restaurants With Low Busy Ratio (Efficient Dasher Allocation)
def low_busy_ratio(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
        SELECT r.restaurant_id,
               AVG(o.total_busy_dashers) AS avg_busy,
               AVG(o.total_onshift_dashers) AS avg_onshift,
               AVG(CAST(o.total_busy_dashers AS FLOAT) / NULLIF(o.total_onshift_dashers, 0))
                   AS busy_ratio
        FROM restaurants r
        JOIN orders o ON r.restaurant_id = o.restaurant_id
        GROUP BY r.restaurant_id
        HAVING busy_ratio < 0.5
        ORDER BY busy_ratio ASC
        LIMIT ?;
    """

    cur.execute(query, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# Highest Revenue Restaurants
def highest_revenue(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
        SELECT restaurant_id,
               SUM(subtotal) AS total_revenue,
               COUNT(*) AS total_orders
        FROM orders
        GROUP BY restaurant_id
        ORDER BY total_revenue DESC
        LIMIT ?;
    """

    cur.execute(query, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# Reliable Performers: High Volume + Fast Delivery
def reliable_performers(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
        WITH stats AS (
            SELECT restaurant_id,
                   COUNT(order_id) AS order_count,
                   AVG((julianday(delivery_time) - julianday(order_datetime)) * 24 * 60)
                       AS avg_delivery_min
            FROM orders
            WHERE delivery_time IS NOT NULL
            GROUP BY restaurant_id
        )
        SELECT restaurant_id,
               order_count,
               avg_delivery_min,
               (RANK() OVER (ORDER BY order_count DESC) +
                RANK() OVER (ORDER BY avg_delivery_min ASC)) AS combined_rank
        FROM stats
        ORDER BY combined_rank ASC
        LIMIT ?;
    """

    cur.execute(query, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# Restaurants With Lowest Delivery Variance (Most Consistent)
def low_delivery_variance(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
        SELECT restaurant_id,
               (AVG((julianday(delivery_time) - julianday(order_datetime)) * 24 * 60 *
                    (julianday(delivery_time) - julianday(order_datetime)) * 24 * 60))
               -
               (AVG((julianday(delivery_time) - julianday(order_datetime)) * 24 * 60) *
                AVG((julianday(delivery_time) - julianday(order_datetime)) * 24 * 60))
               AS variance_delivery_time
        FROM orders
        WHERE delivery_time IS NOT NULL
        GROUP BY restaurant_id
        ORDER BY variance_delivery_time ASC
        LIMIT ?;
    """

    cur.execute(query, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
