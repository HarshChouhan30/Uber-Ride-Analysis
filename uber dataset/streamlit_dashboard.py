
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


# ==================================================
# PAGE CONFIGURATION
# ==================================================

DATA_FILE = Path(__file__).with_name("uber_trips_dataset_50k.csv")

DAY_ORDER = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]

st.set_page_config(
    page_title="Uber Trips Dashboard",
    page_icon="🚕",
    layout="wide"
)


# ==================================================
# LOAD AND PREPARE DATA
# ==================================================

@st.cache_data
def load_data():

    trips = pd.read_csv(DATA_FILE)

    required_columns = {
        "city", "pickup_lat", "pickup_lng",
        "drop_lat", "drop_lng", "distance_km",
        "fare_amount", "status", "payment_method",
        "pickup_time", "drop_time"
    }

    missing_columns = required_columns.difference(trips.columns)

    if missing_columns:
        raise ValueError(
            f"Missing columns: {', '.join(sorted(missing_columns))}"
        )

    trips["pickup_time"] = pd.to_datetime(
        trips["pickup_time"], errors="coerce"
    )

    trips["drop_time"] = pd.to_datetime(
        trips["drop_time"], errors="coerce"
    )

    if trips[["pickup_time", "drop_time"]].isna().any().any():
        raise ValueError("Invalid pickup or drop time values found.")

    trips["duration_minutes"] = (
        trips["drop_time"] - trips["pickup_time"]
    ).dt.total_seconds() / 60

    # Haversine distance calculation

    lat1 = np.radians(trips["pickup_lat"])
    lon1 = np.radians(trips["pickup_lng"])
    lat2 = np.radians(trips["drop_lat"])
    lon2 = np.radians(trips["drop_lng"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    haversine = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    trips["calculated_distance_km"] = (
        6371 * 2 * np.arcsin(np.sqrt(haversine.clip(0, 1)))
    )

    # Remove zero-duration and zero-distance records

    trips = trips.loc[
        ~(
            (trips["duration_minutes"] == 0)
            & (trips["distance_km"] == 0)
        )
    ].copy()

    trips["pickup_hour"] = trips["pickup_time"].dt.hour
    trips["day_of_week"] = trips["pickup_time"].dt.day_name()

    trips["normalized_status"] = (
        trips["status"]
        .astype("string")
        .str.casefold()
        .str.replace(r"[-_]+", " ", regex=True)
        .str.strip()
    )

    return trips


def show_chart(fig):
    fig.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def show_empty_chart(ax, message="No matching data available"):
    ax.text(
        0.5, 0.5, message,
        ha="center",
        va="center",
        transform=ax.transAxes,
        fontsize=11
    )
    ax.set_axis_off()


# ==================================================
# DASHBOARD TITLE
# ==================================================

st.title("Uber Trips Dashboard")

st.caption(
    "Trip volume, operations, fare, and payment insights"
)

trips = load_data()


# ==================================================
# DASHBOARD FILTERS
# ==================================================

st.subheader("Dashboard Filters")

city_options = sorted(
    trips["city"].dropna().astype(str).unique().tolist()
)

status_options = sorted(
    trips["normalized_status"].dropna().unique().tolist()
)

payment_options = sorted(
    trips["payment_method"].dropna().astype(str).unique().tolist()
)

min_date = trips["pickup_time"].min().date()
max_date = trips["pickup_time"].max().date()

col1, col2, col3, col4 = st.columns(4)

with col1:
    selected_cities = st.multiselect(
        "Select City",
        options=city_options,
        default=city_options,
        key="city_filter"
    )

with col2:
    selected_status = st.multiselect(
        "Trip Status",
        options=status_options,
        default=status_options,
        format_func=lambda x: x.title(),
        key="status_filter"
    )

with col3:
    selected_payments = st.multiselect(
        "Payment Method",
        options=payment_options,
        default=payment_options,
        key="payment_filter"
    )

with col4:
    selected_dates = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_filter"
    )


# ==================================================
# APPLY FILTERS
# ==================================================

filtered_trips = trips.copy()

filtered_trips = filtered_trips[
    filtered_trips["city"].astype(str).isin(selected_cities)
]

filtered_trips = filtered_trips[
    filtered_trips["normalized_status"].isin(selected_status)
]

filtered_trips = filtered_trips[
    filtered_trips["payment_method"].astype(str).isin(selected_payments)
]

if len(selected_dates) == 2:

    start_date, end_date = selected_dates

    filtered_trips = filtered_trips[
        (filtered_trips["pickup_time"].dt.date >= start_date)
        & (filtered_trips["pickup_time"].dt.date <= end_date)
    ]

elif len(selected_dates) == 1:

    selected_date = selected_dates[0]

    filtered_trips = filtered_trips[
        filtered_trips["pickup_time"].dt.date == selected_date
    ]

st.divider()

st.write(
    f"Showing **{len(filtered_trips):,} trips** after applying filters."
)


# ==================================================
# FILTERED DATASETS
# ==================================================

completed_trips = filtered_trips[
    filtered_trips["normalized_status"] == "completed"
]

cancelled_no_show = filtered_trips[
    filtered_trips["normalized_status"].isin(
        ["cancelled", "no show"]
    )
]


# ==================================================
# KEY PERFORMANCE INDICATORS
# ==================================================

st.subheader("Key Performance Indicators")

avg_duration = completed_trips["duration_minutes"].mean()
avg_distance = completed_trips["calculated_distance_km"].mean()

kpis = [
    ("Total Trips", f"{len(filtered_trips):,}"),
    ("Completed Trips", f"{len(completed_trips):,}"),
    ("Cancelled / No Show", f"{len(cancelled_no_show):,}"),
    (
        "Avg Duration (min)",
        f"{avg_duration:,.2f}" if pd.notna(avg_duration) else "—"
    ),
    (
        "Avg Distance (km)",
        f"{avg_distance:,.2f}" if pd.notna(avg_distance) else "—"
    ),
    ("Sales", f"${completed_trips['fare_amount'].sum():,.2f}"),
    ("Lost Sales", f"${cancelled_no_show['fare_amount'].sum():,.2f}")
]

for row_start in (0, 4):

    row_kpis = kpis[row_start:row_start + 4]

    columns = st.columns(len(row_kpis))

    for column, (label, value) in zip(columns, row_kpis):
        column.metric(label, value)


st.divider()


# ==================================================
# ROW 1: TRIPS BY HOUR + TRIPS BY DAY
# ==================================================

col1, col2 = st.columns(2)


# ---------------- HOURLY TRIPS ----------------

with col1:

    st.subheader("Trips by Hour of the Day")

    hourly_trips = completed_trips["pickup_hour"].value_counts().reindex(
        range(24), fill_value=0
    )

    fig, ax = plt.subplots(figsize=(9, 4))

    ax.plot(
        hourly_trips.index,
        hourly_trips.values,
        marker="o",
        linewidth=2
    )

    for x, y in zip(hourly_trips.index, hourly_trips.values):

        ax.annotate(
            str(y),
            (x, y),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
            fontsize=8
        )

    ax.set(
        title="Trips by Hour of the Day",
        xlabel="Hour of the Day",
        ylabel="Number of Trips",
        xticks=range(24)
    )

    ax.grid(True, alpha=0.3)

    show_chart(fig)


# ---------------- DAILY TRIPS ----------------

with col2:

    st.subheader("Trips by Day of the Week")

    daily_trips = completed_trips["day_of_week"].value_counts().reindex(
        DAY_ORDER, fill_value=0
    )

    fig, ax = plt.subplots(figsize=(9, 4))

    ax.plot(
        range(len(daily_trips)),
        daily_trips.values,
        marker="o",
        linewidth=2
    )

    for x, y in enumerate(daily_trips.values):

        ax.annotate(
            str(y),
            (x, y),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
            fontsize=9
        )

    ax.set(
        title="Trips by Day of the Week",
        xlabel="Day of the Week",
        ylabel="Number of Trips",
        xticks=range(len(DAY_ORDER)),
        xticklabels=DAY_ORDER
    )

    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.3)

    show_chart(fig)


# ==================================================
# ROW 2: CITY COMPARISON + FARE VS DISTANCE
# ==================================================

col1, col2 = st.columns(2)


# ---------------- TOTAL TRIPS BY CITY ----------------

with col1:

    st.subheader("Total Trips by City")

    city_trips = completed_trips["city"].value_counts().sort_values(
        ascending=False
    )

    fig, ax = plt.subplots(figsize=(9, 4))

    if not city_trips.empty:

        ax.plot(
            city_trips.index,
            city_trips.values,
            marker="o",
            linewidth=2
        )

        for x, y in enumerate(city_trips.values):

            ax.annotate(
                f"{y:,}",
                (x, y),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                fontsize=9
            )

        ax.set(
            title="Total Trips by City",
            xlabel="City",
            ylabel="Number of Trips"
        )

        ax.tick_params(axis="x", rotation=30)
        ax.grid(True, alpha=0.3)

    else:
        show_empty_chart(ax)

    show_chart(fig)


# ---------------- FARE VS DISTANCE ----------------

with col2:

    st.subheader("Fare vs Distance")

    fare_data = completed_trips[
        ["calculated_distance_km", "fare_amount"]
    ].dropna()

    fig, ax = plt.subplots(figsize=(9, 4))

    if not fare_data.empty:

        hex_plot = ax.hexbin(
            fare_data["calculated_distance_km"],
            fare_data["fare_amount"],
            gridsize=35,
            mincnt=1,
            bins="log",
            cmap="Greens"
        )

        fig.colorbar(
            hex_plot,
            ax=ax,
            label="Number of Trips (log scale)"
        )

        # Median fare trend

        distance_bins = pd.cut(
            fare_data["calculated_distance_km"],
            bins=15
        )

        median_fare = fare_data.groupby(
            distance_bins,
            observed=True
        ).agg(
            average_distance=("calculated_distance_km", "median"),
            median_fare=("fare_amount", "median")
        ).dropna()

        ax.plot(
            median_fare["average_distance"],
            median_fare["median_fare"],
            color="red",
            marker="o",
            linewidth=2,
            label="Median Fare Trend"
        )

        # Labels for median fare trend

        for x, y in zip(
            median_fare["average_distance"],
            median_fare["median_fare"]
        ):

            ax.annotate(
                f"${y:.0f}",
                (x, y),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                fontsize=8,
                color="red"
            )

        ax.legend()

        ax.set(
            title="Fare vs Distance",
            xlabel="Distance (km)",
            ylabel="Fare Amount ($)"
        )

        ax.grid(True, alpha=0.2)

    else:
        show_empty_chart(ax)

    show_chart(fig)


# ==================================================
# ROW 3: TRIPS BY PAYMENT METHOD
# ==================================================

st.subheader("Trips by Payment Method")

payment_trips = filtered_trips[
    "payment_method"
].value_counts().sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(10, 4))

if not payment_trips.empty:

    bars = ax.barh(
        payment_trips.index.astype(str),
        payment_trips.values
    )

    ax.bar_label(
        bars,
        padding=5,
        fmt="%.0f",
        fontsize=10
    )

    ax.set(
        title="Trips by Payment Method",
        xlabel="Number of Trips",
        ylabel="Payment Method"
    )

    ax.grid(axis="x", alpha=0.3)

else:
    show_empty_chart(ax)

show_chart(fig)
