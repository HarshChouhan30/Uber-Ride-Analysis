# Uber Trips: Report and Insights

**Scope:** 50,000 trips, 1 Jan 2023 – 4 Feb 2023, six cities. Based on the cleaning steps in `analysis.ipynb` and the metrics shown in `streamlit_dashboard.py`. All figures below were recomputed from the CSV using the dashboard's logic (49,997 trips after removing 3 zero-duration / zero-distance rows).

---

## 1. Executive Summary

- The business completed **85.1%** of trips (42,538) and earned **$679,679** in sales, while **14.9%** (7,459 trips) were cancelled or no-shows, representing **$119,121** in lost sales (about 15% of potential revenue).
- Performance is **remarkably uniform** across cities, hours, weekdays and payment methods. No segment stands out as clearly stronger or weaker.
- The main findings are about **data quality**: the dataset is clearly synthetic, and the distance field used by the dashboard does not explain fares. These should be fixed before drawing business conclusions.

## 2. Key Performance Indicators

| KPI | Value |
|---|---|
| Total trips | 49,997 |
| Completed trips | 42,538 (85.1%) |
| Cancelled / No-show | 7,459 (14.9%) |
| – Cancelled | 4,984 (10.0%) |
| – No-show | 2,475 (5.0%) |
| Avg duration (completed) | 21.03 min |
| Avg distance, Haversine (completed) | 3.80 km |
| Sales | $679,678.85 |
| Lost sales | $119,121.42 |
| Avg fare (completed) | $15.98 (median $15.43) |

## 3. Insights

### 3.1 Operations: cancellations and no-shows
- Cancellations are twice as common as no-shows (10.0% vs 5.0%).
- Lost sales of ~$119K equal ~17.5% of completed sales. Reducing the cancel/no-show rate by even 2 percentage points would recover roughly $16K per 5 weeks at the current fare level.
- Fares are essentially identical for completed, cancelled and no-show trips (≈$15.97–15.98), so lost sales are driven purely by volume.

### 3.2 Time patterns
- **Hour of day:** completed trips range only from 1,719 to 1,821 per hour. There is **no rush-hour peak**; midnight (1,821) is marginally the highest and 9 pm (1,719) the lowest, a spread of ~6%.
- **Day of week:** Monday–Friday and Sunday each have ~6,100–6,150 completed trips. **Saturday looks lower (5,816), but this is an artefact**: the data ends on Saturday 4 Feb at 17:19, so there are only 4 complete-ish Saturdays vs. 5 for other days. The cancellation rate by weekday is also flat (14.4%–15.4%).
- **Coverage:** 44,637 trips fall in January and only 5,360 in February, so this is effectively a one-month snapshot.

### 3.3 Cities
All six cities are within ~2.5% of each other.

| City | Trips | Cancel / no-show % | Sales | Avg fare |
|---|---|---|---|---|
| Boston | 8,454 | 15.0% | $115,028 | $16.02 |
| San Francisco | 8,401 | 14.8% | $114,661 | $16.02 |
| Chicago | 8,344 | 15.0% | $112,787 | $15.91 |
| Los Angeles | 8,315 | 15.4% | $110,687 | $15.74 |
| New York | 8,247 | 14.7% | $113,175 | $16.09 |
| Seattle | 8,236 | 14.5% | $113,341 | $16.10 |

Los Angeles has the lowest sales and highest cancellation rate, and Boston the highest sales, but the gaps are small enough to be noise.

### 3.4 Payment methods
Card, Cash, UPI and Wallet each account for ~25% of trips (12.4K–12.5K each) and ~$169K–171K of sales. Cancellation rates are 14.8%–15.1%. There is no sign of a dominant or problematic payment channel, and cash is not associated with more cancellations.

### 3.5 Fares, distance and duration
- Fare is almost perfectly explained by the **source `distance_km`** field: roughly **fare ≈ $2.98 + $1.85 × distance_km** (correlation with fare 0.87).
- Duration is a perfect function of the source distance: every trip travels at exactly **20 km/h**.
- However, the dashboard's **Haversine distance has ~0 correlation with fare** (r ≈ −0.001). This is why the "Fare vs Distance" hexbin shows a flat cloud and a flat median line instead of an upward slope.

## 4. Data Quality Findings

| # | Finding | Impact |
|---|---|---|
| 1 | **Synthetic data pattern:** exactly one trip per minute from 1 Jan 00:00 (1,440/day), constant 20 km/h speed, near-equal splits across cities, payments and hours | Charts are flat; patterns cannot be treated as real demand behaviour |
| 2 | **Coordinates don't match cities:** all cities share lat 37–41 and lng −122 to −73 | City and geographic distance are unrelated, so Haversine distance is meaningless |
| 3 | **`distance_km` vs Haversine** differ by 3.76 km on average (up to 16.9 km); source mean is 7.01 km vs 3.80 km calculated | The notebook dropped `distance_km` in favour of Haversine, which removes the field that actually drives fare |
| 4 | **3 zero-duration, zero-distance rows** removed | Negligible |
| 5 | **Notebook vs dashboard differences:** the notebook computes duration from time-of-day only (breaks for trips crossing midnight), averages over all trips, and matches `Completed` exactly; the dashboard uses full timestamps, completed trips only, and normalised status | KPI values can differ slightly between the two |
| 6 | **Partial final period:** data ends 4 Feb 17:19 | Saturday under-counted; February is not comparable to January |
| 7 | **Cancelled / no-show trips carry a fare and a duration** | Fares on unfulfilled trips are presumably quoted estimates, so "Lost Sales" is potential, not realised revenue |

## 5. Recommendations

1. **Use `distance_km` (or reconcile the two distances) for fare analysis.** If coordinates are unreliable, make the dashboard's Fare vs Distance chart use the source distance, or show both and flag the discrepancy.
2. **Obtain real or realistic data** before drawing operational conclusions; with the current file the sensible takeaway is "no differences between segments".
3. **Focus on the cancellation rate** as the one meaningful lever: ~15% of demand is lost. With real data, investigate cancellation reasons by driver, rider and time-to-pickup.
4. **Fix the notebook/dashboard inconsistencies** (use full timestamps, normalise status, define which trips averages cover) so both report identical KPIs.
5. **Dashboard improvements:** add a date trend (trips/sales by day), a cancellation-rate chart by city/hour, driver and rider level views (8,963 drivers, 38,351 riders), and use bar charts for categorical axes (city, weekday), since the line charts imply a continuous order that doesn't exist. Note the notebook's city chart also has its axis labels swapped.
6. **Add a note on the dashboard** that Saturday and February are partial periods.

## 6. Method Notes
- Metrics replicate `load_data()` and the dashboard filters at their defaults (all cities, statuses, payments, full date range).
- "Sales" = sum of `fare_amount` for completed trips; "Lost Sales" = sum for cancelled and no-show trips.
- The notebook file contains no saved outputs, so every figure here was recomputed directly from the CSV.
