# Libraries
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st


def load_trade_register(path: str) -> pd.DataFrame:
	"""
	Load the processed trade register data from a Parquet file.
	"""
	df = pd.read_parquet(path)
	return df.sort_values(by=["Supplier", "Delivery year start"], ascending=True)


def load_ukraine_imports(path: str) -> pd.DataFrame:
	"""
	Load the Ukraine importer rank data from a Parquet file.
	"""
	return pd.read_parquet(path)


def filter_by_delivery_year(df: pd.DataFrame, year_filter: str) -> pd.DataFrame:
	"""
	Filter the weapons delivery data by year range.
	"""
	if year_filter == "2014-2021":
		return df[
			(df["Delivery year start"] >= 2014) &
			(df["Delivery year start"] <= 2021)
		]
	elif year_filter == "2022-2024":
		return df[
			(df["Delivery year start"] >= 2022) &
			(df["Delivery year start"] <= 2024)
		]
	else:
		return df


def create_arms_flow_map(
    df: pd.DataFrame,
    kyiv_lat: float = 50.4501,
    kyiv_lon: float = 30.5234,
	base_color: tuple[int, int, int] = (65, 105, 225), # royalblue
    high_color: tuple[int, int, int] = (0, 128, 128),  # teal
    width_min: float = 0.5,
    width_max: float = 10,
    gamma: float = 3,
    map_style: str = "light"
) -> pdk.Deck:
    """
    Create a PyDeck map of the arms flows to Ukraine measured by the SIPRI TIV.
    """
	# Prepare the arc data
    arc_data = (
		df
		.groupby("Supplier", as_index=False)
		.agg(
			tiv=("SIPRI TIV of delivered weapons", "sum"),
			capital=("Supplier capital", "first"),
			source_lat=("capital_lat", "first"),
			source_lon=("capital_lon", "first")
		)
		.assign(
			target_lat=kyiv_lat,
			target_lon=kyiv_lon,
			log_tiv=lambda x: np.log10(x["tiv"]),
			tiv_str=lambda x: x["tiv"].map(lambda v: f"{v:,.2f}")
		)
	)

    # Normalize the log_tiv between [0, 1]
    min_log = arc_data["log_tiv"].min()
    max_log = arc_data["log_tiv"].max()
    
    # Apply the gamma correction and scale it to [width_min, width_max]
    norm = (arc_data["log_tiv"] - min_log) / (max_log - min_log)
    norm = norm.clip(0, 1).fillna(0)
    
    arc_data["width_scaled"] = width_min + (width_max - width_min) * (norm ** gamma)
    
    # Create the intensity values based on log_tiv
    t = (
        (arc_data["log_tiv"] - arc_data["log_tiv"].min()) /
        (arc_data["log_tiv"].max() - arc_data["log_tiv"].min())
    )
    t = t.clip(0, 1).fillna(0)
    arc_data["intensity"] = t
    
    # Build per-row colors with gradient from base to high color
    arc_data["arc_color"] = [
        [int(base_color[0] + (high_color[0] - base_color[0]) * v),
         int(base_color[1] + (high_color[1] - base_color[1]) * v),
         int(base_color[2] + (high_color[2] - base_color[2]) * v)]
        for v in arc_data["intensity"]
    ]
    
    # Create the ArcLayer
    arc_layer = pdk.Layer(
        "ArcLayer",
        data=arc_data,
        get_source_position=["source_lon", "source_lat"],
        get_target_position=["target_lon", "target_lat"],
        get_source_color="arc_color",
        get_target_color="arc_color",
        get_width="width_scaled",
        get_height=0.65,
        get_tilt=10,
        pickable=True,
        auto_highlight=True
    )
    
    # Create the ScatterplotLayer for cities
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=arc_data,
        get_position=["source_lon", "source_lat"],
        get_radius=50000,
        get_fill_color=[112, 128, 144, 192],  # Slate grey with some transparency
        pickable=True
    )
    
    # Add Kyiv as a larger point
    kyiv_point = pdk.Layer(
        "ScatterplotLayer",
        data=[{
            "lat": kyiv_lat,
            "lon": kyiv_lon,
            "Supplier": "Ukraine",
            "capital": "Kyiv",
            "tiv_str": None,
        }],
        get_position=["lon", "lat"],
        get_radius=100000,
        get_fill_color=[255, 69, 0, 192],  # Salmon with some transparency
        pickable=True
    )
    
    # Set the viewport
    view_state = pdk.ViewState(
        latitude=50,
        longitude=15,
        zoom=2.5,
        pitch=35,
        bearing=0
    )
    
    # Create the tooltip
    tooltip = {
        "html": "<b>{Supplier}</b><br/>"
                "Capital: {capital}<br/>"
                "TIV: {tiv_str}<br/>",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    }
    
    # Render the deck
    deck = pdk.Deck(
        layers=[arc_layer, scatter_layer, kyiv_point],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_provider="carto",
        map_style=map_style
    )
    
    return deck


@st.cache_data
def create_delivered_weapons_plots(
		df: pd.DataFrame,
		height: int,
		top_n: int
) -> tuple[go.Figure, go.Figure, go.Figure]:
	"""
	Create three bar plots showing the delivered weapons by country, category and TIV.
	"""
	country_delivered = df.groupby("Supplier")["Delivery number"].sum().sort_values(ascending=True).tail(top_n)
	category_delivered = df.groupby("Weapon category")["Delivery number"].sum().sort_values(ascending=True)
	tiv_delivered = df.groupby("Weapon category")["SIPRI TIV of delivered weapons"].sum().sort_values(ascending=True)

	# Delivered weapons by country
	fig_country = px.bar(
		x=country_delivered.values,
		y=country_delivered.index,
		orientation="h",
		labels={"x": "Delivered Weapons", "y": "Country"},
		title=f"Delivered Weapons by Country (Top {top_n})"
	)
	fig_country.update_layout(height=height, showlegend=True, xaxis_title=None, yaxis_title=None)
	fig_country.update_xaxes(tickformat=",d")
	
	# Delivered weapons by category
	fig_category = px.bar(
		x=category_delivered.values,
		y=category_delivered.index,
		orientation="h",
		labels={"x": "Delivered Weapons", "y": "Weapon Category"},
		title="Delivered Weapons by Category"
	)
	fig_category.update_layout(height=height, showlegend=False, xaxis_title=None, yaxis_title=None)
	fig_category.update_xaxes(tickformat=",d")
	
    # Delivered weapons by TIV
	fig_tiv = px.bar(
		x=tiv_delivered.values,
		y=tiv_delivered.index,
		orientation="h",
		labels={"x": "SIPRI TIV", "y": "Weapon Category"},
		title="SIPRI TIV of Delivered Weapons (Thousands)"
	)
	fig_tiv.update_layout(height=height, showlegend=False, xaxis_title=None, yaxis_title=None)

	return fig_country, fig_category, fig_tiv


# DATA LOAD
df_trade_register = load_trade_register("data/trade_register_processed.parquet")
df_ukraine_imports = load_ukraine_imports("data/ukraine_importer_rank_by_period.parquet")

# PAGE TITLE AND LAYOUT
st.set_page_config(page_title="Ukraine Arms Transfers", layout="wide")

# APP TITLE
st.title("Weapons Transferred to Ukraine")

# YEAR FILTER
year_filter = st.segmented_control(
	"**Delivery Year Range**",
	options=["All", "2014-2021", "2022-2024"],
	default="All"
)

# Filter the data based on user selection
df_filtered = filter_by_delivery_year(df_trade_register, year_filter)

# METRICS
if year_filter != "All":
	period_map = {
		"2014-2021": "2014-2021",
		"2022-2024": "2022-2024"
	}
	period_data = df_ukraine_imports[df_ukraine_imports["Period"] == period_map[year_filter]]
	
	if not period_data.empty:
		metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
		
		with metric_col1:
			st.metric(label="Number of Countries", value=df_filtered["Supplier"].nunique())
		
		with metric_col2:
			total_weapons = int(df_filtered["Delivery number"].sum())
			st.metric(label="Number of Weapons Delivered", value=f"{total_weapons:,}")
		
		with metric_col3:
			rank = int(period_data["Rank"].values[0])
			st.metric(label="Ukraine's Global Importer Rank", value=rank)
		
		with metric_col4:
			share = period_data["Share of global arms imports"].values[0]
			st.metric(label="Share of Global Weapons Imports", value=f"{share}%")
	else:
		metric_col1, metric_col2 = st.columns(2)
		
		with metric_col1:
			st.metric(label="Number of Countries", value=df_filtered["Supplier"].nunique())
		
		with metric_col2:
			total_weapons = int(df_filtered["Delivery number"].sum())
			st.metric(label="Number of Weapons Delivered", value=f"{total_weapons:,}")
else:
	metric_col1, metric_col2 = st.columns(2)
	
	with metric_col1:
		st.metric(label="Number of Countries", value=df_filtered["Supplier"].nunique())
	
	with metric_col2:
		total_weapons = int(df_filtered["Delivery number"].sum())
		st.metric(label="Number of Weapons Delivered", value=f"{total_weapons:,}")

# MAP

# Map style selector that persists in URL query params across refreshes
map_style_default = st.query_params.get("map_style", "light")
map_style_index = 0 if map_style_default == "light" else 1

map_style = st.radio(
	"Map style",
	["light", "dark"],
	horizontal=True,
	index=map_style_index,
	key="map_style"
)

# Update the URL query params when selection changes
if map_style != st.query_params.get("map_style", "light"):
	st.query_params["map_style"] = map_style

map_deck = create_arms_flow_map(df_filtered, map_style=map_style)
st.pydeck_chart(map_deck)

# BAR PLOTS
fig_country, fig_category, fig_tiv = create_delivered_weapons_plots(df_filtered, height=500, top_n=10)

# Display plots in three columns
col1, col2, col3 = st.columns(3)

with col1:
	st.plotly_chart(fig_country, use_container_width=True)

with col2:
	st.plotly_chart(fig_category, use_container_width=True)

with col3:
	st.plotly_chart(fig_tiv, use_container_width=True)

# DATAFRAME
columns = [
	"Supplier",
	"Delivery year start",
	"Delivery year end",
	"Weapon designation",
	"Weapon category",
	"Company",
	"Country of origin",
	"SIPRI TIV of delivered weapons"
]

st.dataframe(df_filtered[columns], hide_index=True, use_container_width=True)

# FOOTNOTE
st.markdown(
	"""
	**Data source**: [SIPRI Arms Transfers Database](https://www.sipri.org/databases/armstransfers), extracted in December 2025.
	
	The SIPRI Trend Indicator Value (TIV) estimates the volume of international arms transfers using standardised production-cost estimates. It is meant for comparing transfer scale across weapons and countries, not the actual monetary value.
	
	Note that 'Company' refers to the original manufacturer of the weapon system, which may differ from the supplying country. That is why the Russian state-owned conglomerate Rostec is overrepresented in the data.
	"""
)