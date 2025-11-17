# Restaurant Order Recommender System

This project analyzes DoorDash-style historical delivery data to recommend restaurants based on performance metrics such as delivery speed, order value, and popularity.

---

## How to Run Locally

1. Place `historical_data.csv` and these project files in the same folder.

2. **Create and populate the database:**
python load_data.py

This will create and populate `restaurant_order_recommender.db`.

3. **Check database health:**
python evaluate_db.py

4. **Explore SQL queries:**
sqlite3 restaurant_order_recommender.db < analysis_queries.sql

5. **Run recommendations:**
python recommend.py

---

## Insights You’ll Get

### From `analysis_queries.sql`

- **Top restaurants by average order value**
- **Restaurants with the fastest delivery times**
- **Dasher load by region (market congestion)**
- **Correlation between delivery time and dasher availability**
- **Best restaurants within each cuisine category**
- **Restaurants with low busy ratios (efficient dasher availability)**
- **High-revenue restaurants**
- **Consistent and reliable performers based on variance and volume**
- **Popularity-based rankings**

### From `recommend.py`
- `top_value()` — finds high-value restaurants  
- `top_fastest()` — finds fast delivery performers  

---

## Streamlit Interface

You can run an interactive Streamlit application to explore recommendations visually.

**Run the app:**
streamlit run web_gui.py


**In the app, users can:**
- Select cuisine type and market  
- Choose preferences such as *Fast Delivery*, *High Value*, or *Most Popular*  
- View data-driven restaurant recommendations dynamically  

**Multi-Tab UI**  
Results Table Tab – Shows a live query table based on user-selected filters  
Visualization Tab – Allows users to:  
- Select any two numeric metrics  
- Choose between Scatter or Bar visualizations  
- See relationships between delivery time, order value, popularity, etc.

**Indexing Analysis**  
User can select indexing analysis in left menu  
One-click test demonstrating the query time before and after adding indexes

---

## Future Enhancements

- Implement error analysis to detect data inconsistencies (e.g., missing delivery times or invalid subtotals) and assess recommendation accuracy.  
- Introduce query performance tracking to measure improvements before and after indexing.  
- Visualize performance and error metrics using Streamlit dashboards.  
- Incorporate user feedback and satisfaction tracking to validate recommendation effectiveness.  