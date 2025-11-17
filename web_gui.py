import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

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

# Preference Type
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
        "Low Delivery Variance (Consistent Performance)",
        "Indexing Analysis (Before/After Performance)"
    ]
)

# Number of Results
limit = st.sidebar.slider("Number of Results", 5, 50, 10)

# Explanations
explanations = {
    "Fast Delivery": "Shows restaurants with the lowest average delivery time.",
    "High Value": "Finds restaurants with high average order value per item.",
    "Most Popular": "Lists restaurants with the highest total number of orders.",
    "Top by Cuisine": "Compares restaurants within each cuisine by order value and volume.",
    "Low Busy Ratio (Efficient Dashers)": "Identifies restaurants with low dasher congestion.",
    "Highest Revenue (Subtotal)": "Ranks restaurants by total revenue.",
    "Reliable Performers (Balanced Speed & Volume)": "Selects restaurants balancing speed and order volume.",
    "Low Delivery Variance (Consistent Performance)": "Finds restaurants with consistent delivery times.",
    "Indexing Analysis (Before/After Performance)": "Tests query speed before and after index creation."
}

st.subheader("Analysis / Recommendation Description")
st.markdown(explanations.get(preference, ""))

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
        SELECT r.cuisine_type AS cuisine, r.restaurant_id, 
               AVG(o.subtotal) AS avg_order_value, COUNT(o.order_id) AS total_orders
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
        SELECT restaurant_id, SUM(subtotal) AS total_revenue, COUNT(*) AS total_orders
        FROM orders
        GROUP BY restaurant_id
        ORDER BY total_revenue DESC
        LIMIT {limit};
    """

elif preference == "Reliable Performers (Balanced Speed & Volume)":
    query = f"""
        WITH stats AS (
            SELECT restaurant_id, COUNT(order_id) AS order_count,
                AVG((julianday(delivery_time) - julianday(order_datetime)) * 24 * 60) AS avg_delivery_min
            FROM orders
            WHERE delivery_time IS NOT NULL
            GROUP BY restaurant_id
        )
        SELECT restaurant_id, order_count, avg_delivery_min,
               (RANK() OVER (ORDER BY order_count DESC) + 
                RANK() OVER (ORDER BY avg_delivery_min ASC)) AS combined_rank
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

# Tabs for results + visualizations
results_tab, viz_tab = st.tabs(["Results Table", "Visualizations"])

# Run Query (normal analyses)
if preference != "Indexing Analysis (Before/After Performance)":

    with results_tab:
        st.subheader("Generated SQL Query")
        st.code(query, language="sql")

        if st.button("Run Query"):
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query(query, conn)
            conn.close()

            if df.empty:
                st.warning("No results found for your selection.")
            else:
                st.success("Query executed successfully.")
                st.dataframe(df)

                # Store for visualization tab
                st.session_state["latest_df"] = df

    with viz_tab:
        if "latest_df" in st.session_state:
            df = st.session_state["latest_df"]

            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

            if numeric_cols:
                st.subheader("Visualization Settings")

                x_axis = st.selectbox("Select X-axis Metric", numeric_cols)
                y_axis = st.selectbox("Select Y-axis Metric", numeric_cols)
                chart_type = st.selectbox("Select Chart Type", ["Bar Chart", "Scatter Plot"])

                fig, ax = plt.subplots(figsize=(7, 4))

                if chart_type == "Bar Chart":
                    ax.bar(df[x_axis], df[y_axis])
                else:
                    ax.scatter(df[x_axis], df[y_axis])

                ax.set_xlabel(x_axis)
                ax.set_ylabel(y_axis)
                ax.set_title(f"{chart_type}: {y_axis} vs {x_axis}")

                st.pyplot(fig)
        else:
            st.info("Run a query first to generate visualizations.")

# Indexing Performance Test
else:
    with results_tab:
        st.subheader("Indexing Performance Test")

        if st.button("Run Indexing Test"):
            test_query = """
                SELECT r.restaurant_id, COUNT(o.order_id)
                FROM restaurants r
                JOIN orders o ON r.restaurant_id = o.restaurant_id
                GROUP BY r.restaurant_id;
            """

            conn = sqlite3.connect(DB_PATH)

            start_before = pd.Timestamp.now()
            conn.execute(test_query).fetchall()
            before_ms = (pd.Timestamp.now() - start_before).total_seconds() * 1000

            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_restaurant ON orders (restaurant_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_datetime ON orders (order_datetime);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_location ON restaurants (location);")
            conn.commit()

            start_after = pd.Timestamp.now()
            conn.execute(test_query).fetchall()
            after_ms = (pd.Timestamp.now() - start_after).total_seconds() * 1000

            conn.close()

            st.session_state["index_data"] = (before_ms, after_ms)

            st.write(f"Before indexing: {before_ms:.2f} ms")
            st.write(f"After indexing: {after_ms:.2f} ms")
            st.write(f"Performance improvement: {before_ms - after_ms:.2f} ms")

    with viz_tab:
        if "index_data" in st.session_state:
            before_ms, after_ms = st.session_state["index_data"]

            st.subheader("Indexing Performance Visualization")
            st.markdown("""
                This visualization compares query execution time **before** and **after**
                database indexes are created.

                **Why this matters:**  
                - Before indexing: full table scans may slow down queries.  
                - After indexing: efficient lookups may reduce query time.  

                The chart below illustrates the performance difference.
            """)

            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(["Before Indexing", "After Indexing"], [before_ms, after_ms])
            ax.set_ylabel("Execution Time (ms)")
            ax.set_xlabel("Execution Phase")
            ax.set_title("Impact of Indexing on Query Performance")

            ax.text(0, before_ms, f"{before_ms:.2f} ms", ha='center', va='bottom')
            ax.text(1, after_ms, f"{after_ms:.2f} ms", ha='center', va='bottom')

            st.pyplot(fig)

        else:
            st.info("Run the indexing test first to generate visualization.")
