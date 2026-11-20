# 🚕 Uber Trips Dashboard

An interactive Streamlit dashboard (plus the exploratory notebook behind it) for analysing a 50,000-trip Uber-style dataset: trip volume, operations (completed vs. cancelled / no-show), fares and payment methods.

## Project Structure

| File | Purpose |
|---|---|
| `streamlit_dashboard.py` | Streamlit app: filters, KPIs and charts |
| `analysis.ipynb` | Exploratory analysis and data-cleaning steps the dashboard is based on |
| `uber_trips_dataset_50k.csv` | Source data (50,000 trips) |
| `REPORT.md` | Written report with insights, data-quality findings and recommendations |

## Dataset

50,000 rows, no missing values, one row per trip.

| Column | Description |
|---|---|
| `trip_id`, `driver_id`, `rider_id` | Identifiers |
| `city` | Boston, Chicago, Los Angeles, New York, San Francisco, Seattle |
| `pickup_lat`, `pickup_lng`, `drop_lat`, `drop_lng` | Pickup / drop-off coordinates |
| `distance_km` | Distance recorded in the source file |
| `fare_amount` | Fare in USD |
| `status` | Completed, Cancelled, No-Show |
| `payment_method` | Card, Cash, UPI, Wallet |
| `pickup_time`, `drop_time` | Timestamps (2023-01-01 to 2023-02-04) |

## Data Preparation (done in `load_data()`)

1. **Validate** that all required columns exist and timestamps parse (raises an error otherwise).
2. **Duration**: `drop_time - pickup_time` in minutes (uses full timestamps, so trips crossing midnight are handled).
3. **Calculated distance**: Haversine (great-circle) distance from the coordinates, in km.
4. **Remove** records where both duration and `distance_km` are zero (3 rows).
5. **Derive** `pickup_hour`, `day_of_week`, and a `normalized_status` (lower-cased, `-`/`_` replaced with spaces, so `No-Show` becomes `no show`).

## Dashboard Features

**Filters:** city, trip status, payment method, date range.

**KPIs:** Total Trips, Completed Trips, Cancelled / No Show, Avg Duration (completed), Avg Distance (completed), Sales (fares of completed trips), Lost Sales (fares of cancelled / no-show trips).

**Charts:**
- Trips by hour of the day (completed trips)
- Trips by day of the week (completed trips)
- Total trips by city (completed trips)
- Fare vs. distance hexbin with median-fare trend line
- Trips by payment method (all trips matching the filters)

Empty filter selections show a "No matching data available" message instead of crashing.

## Getting Started

### Requirements
- Python 3.9+
- `streamlit` (a recent version, since `st.pyplot(width="stretch")` is used), `pandas`, `numpy`, `matplotlib`
- `seaborn` is only needed for the notebook

### Install and run

```bash
pip install streamlit pandas numpy matplotlib seaborn
streamlit run streamlit_dashboard.py
```

The CSV must sit in the **same folder** as `streamlit_dashboard.py` (the path is resolved relative to the script). The app opens at `http://localhost:8501`.

To explore the cleaning steps, open `analysis.ipynb` in Jupyter and run it from the same folder.

## Known Limitations

- **Synthetic data.** Trips occur at a perfectly regular rate and many fields behave uniformly, so charts look flat. See `REPORT.md`.
- **Coordinates do not match city names.** All six cities share the same coordinate range, so city is a label, not a real location.
- **Distance mismatch.** Source `distance_km` differs from the Haversine distance by ~3.76 km on average. The dashboard uses the Haversine value, which makes fare appear unrelated to distance (see `REPORT.md`).
- **Partial final day.** Data ends 2023-02-04 17:19, so Saturday is under-represented.
- The notebook and dashboard differ slightly (e.g. notebook averages use all trips and time-of-day only; dashboard averages use completed trips and full timestamps).
