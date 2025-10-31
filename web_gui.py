import streamlit as st
import sqlite3
import pandas as pd

DB_PATH = "restaurant_order_recommender.db"

# Page Config
st.set_page_config(page_title="Restaurant Recommender", layout="centered")

st.title("Restaurant Recommender System")
st.markdown("Use DoorDash-like historical data to explore restaurant performance and find the best options for your preferences.")

# Sidebar Filters
st.sidebar.header("Filter Options")

# Cuisine Type
cuisine = st.sidebar.selectbox(
    "Select Cuisine Type",
    ["all", "american", "mexican", "asian", "italian", "indian"]
)

# Market / Region Filter
market = st.sidebar.number_input("Market ID (optional)", min_value=0, step=1, value=0)

# Preference Type (merged key analyses)
preference = st.sidebar.selectbox(
    "Select Analysis or Recommendation Type",
    [
        "Fast Delivery",
        "High Value",
        "Most Popular",
        "Top by Cuisine",
        "Low Busy Ratio (Efficient Dashers)",
        "Highest Revenue (Subtotal)",
        "Reliable Performers (Balanced Speed & Volume)",
        "Low Delivery Variance (Consistent Performance)"
    ]
)

# Number of Results
limit = st.sidebar.slider("Number of Results", 5, 50, 10)

# Explanations for Each Option
explanations = {
    "Fast Delivery": "Shows restaurants with the **lowest average delivery time**, ideal for customers who prioritize quick service.",
    "High Value": "Finds restaurants with **high average order value per item**, identifying places offering great value for money.",
    "Most Popular": "Lists restaurants with the **highest total number of orders**, showing customer favorites and demand leaders.",
    "Top by Cuisine": "Compares restaurants **within each cuisine type** by average order value and total orders.",
    "Low Busy Ratio (Efficient Dashers)": "Identifies restaurants where dashers are **less congested**, meaning faster, more reliable delivery.",
    "Highest Revenue (Subtotal)": "Ranks restaurants by **total revenue**, useful for business performance analysis.",
    "Reliable Performers (Balanced Speed & Volume)": "Highlights restaurants that balance **high order volume** with **low average delivery time**.",
    "Low Delivery Variance (Consistent Performance)": "Finds restaurants with the **most consistent delivery times**, showing operational reliability."
}

st.subheader("Analysis / Recommendation Description")
st.markdown(explanations.get(preference, "Select a type from the sidebar to see its description."))

# Query Builder
query = ""

if preference == "Fast Delivery":
    query = f"""
        SELECT r.restaurant_id, r.cuisine_type,
               AVG((julianday(o.delivery_time) - julianday(o.order_datetime)) * 24 * 60) AS avg_delivery_min
        FROM restaurants r
        JOIN orders o ON r.restaurant_id = o.restaurant_id
        WHERE o.delivery_time IS NOT NULL
        {"AND r.cuisine_type = '" + cuisine + "'" if cuisine != "all" else ""}
        {"AND r.location = " + str(market) if market > 0 else ""}
        GROUP BY r.restaurant_id
        HAVING COUNT(o.order_id) > 20
        ORDER BY avg_delivery_min ASC
        LIMIT {limit};
    """

elif preference == "High Value":
    query = f"""
        SELECT r.restaurant_id, r.cuisine_type,
               AVG(o.subtotal / NULLIF(o.total_items, 0)) AS avg_item_value
        FROM restaurants r
        JOIN orders o ON r.restaurant_id = o.restaurant_id
        {"WHERE r.cuisine_type = '" + cuisine + "'" if cuisine != "all" else ""}
        {"AND r.location = " + str(market) if market > 0 else ""}
        GROUP BY r.restaurant_id
        HAVING COUNT(o.order_id) > 20
        ORDER BY avg_item_value DESC
        LIMIT {limit};
    """

elif preference == "Most Popular":
    query = f"""
        SELECT r.restaurant_id, r.cuisine_type, COUNT(o.order_id) AS total_orders
        FROM restaurants r
        JOIN orders o ON r.restaurant_id = o.restaurant_id
        {"WHERE r.cuisine_type = '" + cuisine + "'" if cuisine != "all" else ""}
        {"AND r.location = " + str(market) if market > 0 else ""}
        GROUP BY r.restaurant_id
        ORDER BY total_orders DESC
        LIMIT {limit};
    """

elif preference == "Top by Cuisine":
    query = f"""
        SELECT r.cuisine_type AS cuisine, 
               r.restaurant_id, 
               AVG(o.subtotal) AS avg_order_value, 
               COUNT(o.order_id) AS total_orders
        FROM restaurants r
        JOIN orders o ON r.restaurant_id = o.restaurant_id
        {"WHERE r.cuisine_type = '" + cuisine + "'" if cuisine != "all" else ""}
        GROUP BY r.cuisine_type, r.restaurant_id
        ORDER BY avg_order_value DESC
        LIMIT {limit};
    """

elif preference == "Low Busy Ratio (Efficient Dashers)":
    query = f"""
        SELECT r.restaurant_id,
               AVG(o.total_busy_dashers) AS avg_busy,
               AVG(o.total_onshift_dashers) AS avg_onshift,
               AVG(CAST(o.total_busy_dashers AS FLOAT) / NULLIF(o.total_onshift_dashers, 0)) AS busy_ratio
        FROM restaurants r
        JOIN orders o ON r.restaurant_id = o.restaurant_id
        GROUP BY r.restaurant_id
        HAVING busy_ratio < 0.5
        ORDER BY busy_ratio ASC
        LIMIT {limit};
    """

elif preference == "Highest Revenue (Subtotal)":
    query = f"""
        SELECT restaurant_id,
               SUM(subtotal) AS total_revenue,
               COUNT(*) AS total_orders
        FROM orders
        GROUP BY restaurant_id
        ORDER BY total_revenue DESC
        LIMIT {limit};
    """

elif preference == "Reliable Performers (Balanced Speed & Volume)":
    query = f"""
        WITH stats AS (
            SELECT
                restaurant_id,
                COUNT(order_id) AS order_count,
                AVG((julianday(delivery_time) - julianday(order_datetime)) * 24 * 60) AS avg_delivery_min
            FROM orders
            WHERE delivery_time IS NOT NULL
            GROUP BY restaurant_id
        )
        SELECT
            restaurant_id,
            order_count,
            avg_delivery_min,
            (RANK() OVER (ORDER BY order_count DESC) + RANK() OVER (ORDER BY avg_delivery_min ASC)) AS combined_rank
        FROM stats
        ORDER BY combined_rank ASC
        LIMIT {limit};
    """

elif preference == "Low Delivery Variance (Consistent Performance)":
    query = f"""
        SELECT restaurant_id,
               (AVG((julianday(delivery_time) - julianday(order_datetime)) * 24 * 60 * 
                    (julianday(delivery_time) - julianday(order_datetime)) * 24 * 60)) -
               (AVG((julianday(delivery_time) - julianday(order_datetime)) * 24 * 60) *
                AVG((julianday(delivery_time) - julianday(order_datetime)) * 24 * 60)) AS variance_delivery_time
        FROM orders
        WHERE delivery_time IS NOT NULL
        GROUP BY restaurant_id
        ORDER BY variance_delivery_time ASC
        LIMIT {limit};
    """

# Query Preview
st.subheader("Generated SQL Query")
st.code(query, language="sql")

# Run Query
if st.button("Run Query"):
    if query.strip():
        try:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query(query, conn)
            conn.close()

            if df.empty:
                st.warning("No matching restaurants found for your filters.")
            else:
                st.success("Here are your top results:")
                st.dataframe(df)
        except Exception as e:
            st.error(f"Error running query: {e}")
    else:
        st.warning("Please select a valid option to build a query.")
