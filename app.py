"""
AI Disaster Response Intelligence Command Center.

Global satellite mapping with interactive incident markers,
worldwide location selection, classification, risk assessment,
data-quality monitoring, and analytical reporting.

This is a decision-support prototype, not an official
emergency reporting or dispatch system.
"""

from html import escape

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from src.data.incident import Incident
from src.data.storage import (
    deactivate_incident,
    get_incident,
    load_incidents,
    save_incident,
    update_incident,
)
from src.data.quality import assess_data_quality, audit_incidents
from src.intelligence.classifier import classify_incident
from src.intelligence.risk.assessment import assess_risk
from src.reports.analytics import generate_analytics_report


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Global Disaster Intelligence | Command Center",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

SEVERITY_LEVELS = [
    "unassessed",
    "low",
    "moderate",
    "high",
    "critical",
]

DISASTER_TYPES = [
    "Flood",
    "Earthquake",
    "Fire",
    "Wildfire",
    "Storm",
    "Landslide",
    "Drought",
    "Other",
]

SEVERITY_COLORS = {
    "critical": "#EF4444",
    "high": "#F97316",
    "moderate": "#EAB308",
    "low": "#22C55E",
    "unassessed": "#94A3B8",
}

RISK_COLORS = {
    "Critical": "#EF4444",
    "High": "#F97316",
    "Moderate": "#EAB308",
    "Low": "#22C55E",
    "Unavailable": "#94A3B8",
}

QUALITY_COLORS = {
    "Good quality": "#22C55E",
    "Needs review": "#EAB308",
    "Invalid data": "#EF4444",
}

CHART_TEMPLATE = "plotly_dark"

SATELLITE_TILES = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}"
)

SATELLITE_ATTRIBUTION = (
    "Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, "
    "and the GIS User Community"
)

LABEL_TILES = (
    "https://services.arcgisonline.com/ArcGIS/rest/services/"
    "Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
)


# ---------------------------------------------------------
# Styling
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1700px;
        }

        [data-testid="stSidebar"] {
            background-color: #0B1626;
            border-right: 1px solid #23334B;
        }

        .hero {
            padding: 28px 30px;
            border-radius: 18px;
            background:
                radial-gradient(circle at 85% 20%, #164E63 0%, transparent 35%),
                linear-gradient(120deg, #10243B, #0B1626 70%);
            border: 1px solid #29435F;
            margin-bottom: 24px;
        }

        .hero-label {
            color: #38BDF8;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        .hero h1 {
            color: #F1F5F9;
            font-size: 30px;
            margin: 8px 0;
        }

        .hero p {
            color: #A9BCD0;
            margin: 0;
            font-size: 14px;
        }

        .section-heading {
            font-size: 19px;
            font-weight: 700;
            color: #E5EDF7;
            margin: 8px 0 14px 0;
        }

        .incident-title {
            font-size: 16px;
            font-weight: 700;
            color: #E5EDF7;
        }

        .muted {
            color: #94A3B8;
            font-size: 12px;
        }

        div[data-testid="stMetric"] {
            background: #111D30;
            border: 1px solid #24364E;
            padding: 16px;
            border-radius: 14px;
        }

        div[data-testid="stMetricLabel"] {
            color: #A9BCD0;
        }

        div[data-testid="stMetricValue"] {
            color: #F1F5F9;
        }

        div[data-testid="stTabs"] button {
            font-weight: 600;
        }

        footer {
            visibility: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Global state
# ---------------------------------------------------------

if "global_map_center" not in st.session_state:
    st.session_state["global_map_center"] = [20.0, 0.0]

if "global_map_zoom" not in st.session_state:
    st.session_state["global_map_zoom"] = 2

if "registration_latitude" not in st.session_state:
    st.session_state["registration_latitude"] = 20.0

if "registration_longitude" not in st.session_state:
    st.session_state["registration_longitude"] = 0.0

if "registration_location_selected" not in st.session_state:
    st.session_state["registration_location_selected"] = False


# ---------------------------------------------------------
# Data functions
# ---------------------------------------------------------

def get_incidents():
    return load_incidents()


def make_dataframe(incidents):
    records = []

    for incident in incidents:
        record = incident.to_dict()
        risk = assess_risk(incident)

        record["risk_score"] = risk["risk_score"]
        record["risk_level"] = risk["risk_level"]
        record["needs_review"] = risk["needs_review"]

        record["reported_at"] = pd.to_datetime(
            record["reported_at"],
            utc=True,
            errors="coerce",
        )

        records.append(record)

    columns = [
        "incident_id",
        "disaster_type",
        "location",
        "affected_people",
        "damaged_houses",
        "latitude",
        "longitude",
        "active",
        "verified",
        "severity",
        "risk_score",
        "risk_level",
        "needs_review",
        "reported_at",
    ]

    return pd.DataFrame(records, columns=columns)


def filter_incidents(
    dataframe,
    disaster_types,
    severities,
    statuses,
    verification,
):
    filtered = dataframe.copy()

    if disaster_types:
        filtered = filtered[
            filtered["disaster_type"].isin(disaster_types)
        ]
    else:
        return filtered.iloc[0:0]

    if severities:
        filtered = filtered[
            filtered["severity"].isin(severities)
        ]
    else:
        return filtered.iloc[0:0]

    active_values = []

    if "Active" in statuses:
        active_values.append(True)

    if "Inactive" in statuses:
        active_values.append(False)

    filtered = filtered[
        filtered["active"].isin(active_values)
    ]

    if verification == "Verified":
        filtered = filtered[filtered["verified"]]
    elif verification == "Unverified":
        filtered = filtered[~filtered["verified"]]

    return filtered


def load_demo_data():
    """Insert synthetic reports across Pakistan for testing."""

    demo_records = [
        {
            "disaster_type": "Flood",
            "location": "Multan, Pakistan [DEMO]",
            "affected_people": 850,
            "damaged_houses": 190,
            "latitude": 30.1575,
            "longitude": 71.5249,
            "severity": "critical",
        },
        {
            "disaster_type": "Storm",
            "location": "Bahawalpur, Pakistan [DEMO]",
            "affected_people": 240,
            "damaged_houses": 55,
            "latitude": 29.3956,
            "longitude": 71.6836,
            "severity": "high",
        },
        {
            "disaster_type": "Flood",
            "location": "Lahore, Pakistan [DEMO]",
            "affected_people": 420,
            "damaged_houses": 80,
            "latitude": 31.5204,
            "longitude": 74.3587,
            "severity": "moderate",
        },
        {
            "disaster_type": "Earthquake",
            "location": "Quetta, Pakistan [DEMO]",
            "affected_people": 160,
            "damaged_houses": 35,
            "latitude": 30.1798,
            "longitude": 66.9750,
            "severity": "high",
        },
        {
            "disaster_type": "Landslide",
            "location": "Muzaffarabad, Pakistan [DEMO]",
            "affected_people": 90,
            "damaged_houses": 18,
            "latitude": 34.3700,
            "longitude": 73.4711,
            "severity": "moderate",
        },
        {
            "disaster_type": "Wildfire",
            "location": "Islamabad, Pakistan [DEMO]",
            "affected_people": 45,
            "damaged_houses": 8,
            "latitude": 33.6844,
            "longitude": 73.0479,
            "severity": "low",
        },
    ]

    existing = get_incidents()

    if any("[DEMO]" in item.location for item in existing):
        return False

    for record in demo_records:
        save_incident(Incident(**record))

    return True


# ---------------------------------------------------------
# Satellite map helpers
# ---------------------------------------------------------

def add_satellite_layers(incident_map):
    """Add satellite imagery and geographic labels."""

    folium.TileLayer(
        tiles=SATELLITE_TILES,
        attr=SATELLITE_ATTRIBUTION,
        name="Satellite imagery",
        overlay=False,
        control=True,
        max_zoom=19,
    ).add_to(incident_map)

    folium.TileLayer(
        tiles=LABEL_TILES,
        attr="Esri",
        name="Country and city labels",
        overlay=True,
        control=True,
        show=True,
        max_zoom=19,
    ).add_to(incident_map)


def make_global_map(center=None, zoom=None):
    """Create a worldwide satellite map."""

    if center is None:
        center = [20.0, 0.0]

    if zoom is None:
        zoom = 2

    incident_map = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
        min_zoom=2,
        max_zoom=19,
        world_copy_jump=True,
    )

    add_satellite_layers(incident_map)

    folium.LayerControl(
        position="topright",
        collapsed=True,
    ).add_to(incident_map)

    return incident_map


def make_incident_dot(color, critical=False):
    """Create a glowing, animated incident marker."""

    animation = (
        "animation: pulse 1.4s infinite;"
        if critical
        else ""
    )

    html = f"""
    <style>
        @keyframes pulse {{
            0% {{
                box-shadow: 0 0 0 0 {color}AA,
                            0 0 12px {color};
            }}
            70% {{
                box-shadow: 0 0 0 12px {color}00,
                            0 0 20px {color};
            }}
            100% {{
                box-shadow: 0 0 0 0 {color}00,
                            0 0 12px {color};
            }}
        }}
    </style>

    <div style="
        width:18px;
        height:18px;
        border-radius:50%;
        background:{color};
        border:2px solid white;
        box-shadow:0 0 8px {color}, 0 0 18px {color};
        {animation}
    "></div>
    """

    return folium.DivIcon(
        html=html,
        icon_size=(24, 24),
        icon_anchor=(12, 12),
        class_name="incident-dot",
    )


def add_incident_markers(incident_map, dataframe):
    """Add clustered glowing incident dots to the map."""

    cluster = MarkerCluster(
        name="Disaster incidents",
        options={
            "showCoverageOnHover": False,
            "spiderfyOnMaxZoom": True,
            "maxClusterRadius": 45,
        },
    ).add_to(incident_map)

    for _, incident in dataframe.iterrows():

        try:
            latitude = float(incident["latitude"])
            longitude = float(incident["longitude"])

            if not (-90 <= latitude <= 90):
                continue

            if not (-180 <= longitude <= 180):
                continue

            if pd.isna(latitude) or pd.isna(longitude):
                continue

        except (TypeError, ValueError):
            continue

        severity = str(incident["severity"]).lower()

        color = SEVERITY_COLORS.get(
            severity,
            "#94A3B8",
        )

        risk_level = str(incident["risk_level"])
        risk_score = int(incident["risk_score"])

        critical = (
            severity == "critical"
            or risk_level == "Critical"
        )

        location = escape(str(incident["location"]))
        incident_id = escape(str(incident["incident_id"]))
        disaster = escape(str(incident["disaster_type"]))

        status = "Active" if incident["active"] else "Inactive"

        verification = (
            "Verified" if incident["verified"]
            else "Unverified"
        )

        popup_html = f"""
        <div style="
            width:250px;
            font-family:Arial,sans-serif;
            color:#172033;
            padding:5px;
        ">
            <h3 style="margin-bottom:8px;">{disaster}</h3>

            <b>Incident ID:</b> {incident_id}<br>
            <b>Location:</b> {location}<br>
            <b>Severity:</b> {severity.title()}<br>
            <b>Risk score:</b> {risk_score}/100<br>
            <b>Risk level:</b> {risk_level}<br>
            <b>People affected:</b>
                {int(incident["affected_people"]):,}<br>
            <b>Damaged houses:</b>
                {int(incident["damaged_houses"]):,}<br>
            <b>Status:</b> {status}<br>
            <b>Verification:</b> {verification}<br>
            <b>Coordinates:</b>
                {latitude:.5f}, {longitude:.5f}
        </div>
        """

        folium.Marker(
            location=[latitude, longitude],
            icon=make_incident_dot(color, critical),
            popup=folium.Popup(
                popup_html,
                max_width=320,
            ),
            tooltip=(
                f"{disaster} | {location} | "
                f"{severity.title()} | {risk_level}"
            ),
        ).add_to(cluster)


# ---------------------------------------------------------
# Global map location search
# ---------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def geocode_location(query):
    """Find worldwide coordinates using OpenStreetMap Nominatim."""

    from geopy.geocoders import Nominatim

    geolocator = Nominatim(
        user_agent="ai_disaster_response_command_center"
    )

    result = geolocator.geocode(
        query,
        exactly_one=True,
        timeout=12,
    )

    if result is None:
        return None

    return {
        "latitude": float(result.latitude),
        "longitude": float(result.longitude),
        "address": result.address,
    }


def show_global_map_search():
    """Search for a country, city, or place."""

    with st.form("global_map_search"):
        first, second = st.columns([5, 1])

        with first:
            query = st.text_input(
                "Search anywhere in the world",
                placeholder=(
                    "Search a country, city, address, or landmark..."
                ),
            )

        with second:
            st.write("")
            st.write("")
            submitted = st.form_submit_button(
                "Find Location",
                type="primary",
                use_container_width=True,
            )

    if submitted:

        if not query.strip():
            st.warning("Enter a location to search.")
            return

        try:
            with st.spinner("Searching for location..."):
                result = geocode_location(query.strip())

            if result is None:
                st.warning("Location not found. Try another search.")
                return

            st.session_state["global_map_center"] = [
                result["latitude"],
                result["longitude"],
            ]

            st.session_state["global_map_zoom"] = 11

            st.success(f"Found: {result['address']}")
            st.rerun()

        except Exception as error:
            st.error(
                "Location search could not be completed. "
                f"Check your internet connection. Details: {error}"
            )


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

def show_header():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-label">
                Global Emergency Operations Intelligence
            </div>
            <h1>Global Disaster Response Command Center</h1>
            <p>
                Worldwide satellite monitoring, incident intelligence,
                risk assessment, and disaster response analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Dashboard metrics
# ---------------------------------------------------------

def show_metrics(dataframe):
    active = dataframe[dataframe["active"]]

    critical = active[
        active["severity"] == "critical"
    ]

    high_risk = active[
        active["risk_level"].isin(["High", "Critical"])
    ]

    affected = int(active["affected_people"].sum())
    damaged = int(active["damaged_houses"].sum())

    first, second, third, fourth, fifth, sixth = st.columns(6)

    first.metric("Total Reports", len(dataframe))
    second.metric("Active Incidents", len(active))
    third.metric("People Affected", f"{affected:,}")
    fourth.metric("Critical Severity", len(critical))
    fifth.metric("Houses Damaged", f"{damaged:,}")
    sixth.metric("High/Critical Risk", len(high_risk))


# ---------------------------------------------------------
# Geographic incident monitoring
# ---------------------------------------------------------

def show_map(dataframe):
    st.markdown(
        '<div class="section-heading">'
        'Global Satellite Incident Monitoring</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Explore the world, search for locations, zoom into regions, "
        "and inspect incident markers."
    )

    show_global_map_search()

    incident_map = make_global_map(
        center=st.session_state["global_map_center"],
        zoom=st.session_state["global_map_zoom"],
    )

    add_incident_markers(
        incident_map,
        dataframe,
    )

    st_folium(
        incident_map,
        width=None,
        height=650,
        key="global_satellite_incident_map",
    )

    # Marker legend.
    st.markdown("#### Incident Marker Legend")

    legend_columns = st.columns(5)

    legend_items = [
        ("Critical", "#EF4444"),
        ("High", "#F97316"),
        ("Moderate", "#EAB308"),
        ("Low", "#22C55E"),
        ("Unassessed", "#94A3B8"),
    ]

    for column, (label, color) in zip(
        legend_columns,
        legend_items,
    ):
        with column:
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:9px;">
                    <div style="
                        width:13px;
                        height:13px;
                        border-radius:50%;
                        background:{color};
                        box-shadow:0 0 10px {color};
                    "></div>
                    <span style="color:#CBD5E1;">{label}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.caption(
        "Satellite imagery: Esri World Imagery. "
        "Geographic labels: Esri. "
        "Incident markers are based on saved coordinates, "
        "not live satellite disaster detection."
    )


# ---------------------------------------------------------
# Analytics charts
# ---------------------------------------------------------

def show_charts(dataframe):
    st.markdown(
        '<div class="section-heading">Incident Analytics</div>',
        unsafe_allow_html=True,
    )

    if dataframe.empty:
        st.info("Register incidents to generate analytics.")
        return

    left, right = st.columns(2)

    with left:

        type_data = (
            dataframe.groupby("disaster_type")
            .size()
            .reset_index(name="Reports")
            .sort_values("Reports", ascending=False)
        )

        figure = px.bar(
            type_data,
            x="disaster_type",
            y="Reports",
            color="disaster_type",
            title="Reports by Disaster Type",
            template=CHART_TEMPLATE,
        )

        figure.update_layout(
            showlegend=False,
            xaxis_title="Disaster Type",
            yaxis_title="Number of Reports",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(figure, use_container_width=True)

    with right:

        severity_data = (
            dataframe.groupby("severity")
            .size()
            .reset_index(name="Reports")
        )

        figure = px.pie(
            severity_data,
            names="severity",
            values="Reports",
            hole=0.62,
            title="Incident Severity Distribution",
            color="severity",
            color_discrete_map=SEVERITY_COLORS,
            template=CHART_TEMPLATE,
        )

        figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(figure, use_container_width=True)

    trend_data = dataframe.dropna(
        subset=["reported_at"]
    ).copy()

    trend_data["Report Date"] = (
        trend_data["reported_at"].dt.strftime("%Y-%m-%d")
    )

    trend_data = (
        trend_data.groupby("Report Date")
        .size()
        .reset_index(name="Reports")
        .sort_values("Report Date")
    )

    if not trend_data.empty:

        figure = px.line(
            trend_data,
            x="Report Date",
            y="Reports",
            markers=True,
            title="Incident Reporting Timeline",
            template=CHART_TEMPLATE,
        )

        figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(figure, use_container_width=True)


# ---------------------------------------------------------
# Incident cards
# ---------------------------------------------------------

def show_incident_cards(dataframe):
    st.markdown(
        '<div class="section-heading">'
        'Incident Intelligence Feed</div>',
        unsafe_allow_html=True,
    )

    if dataframe.empty:
        st.info("No incident reports are available.")
        return

    ordered = dataframe.sort_values(
        "reported_at",
        ascending=False,
        na_position="last",
    )

    for start in range(0, len(ordered), 3):

        columns = st.columns(3)

        for column, (_, incident) in zip(
            columns,
            ordered.iloc[start:start + 3].iterrows(),
        ):

            severity = incident["severity"]

            color = SEVERITY_COLORS.get(
                severity,
                "#94A3B8",
            )

            with column:

                with st.container(border=True):

                    st.markdown(
                        f"""
                        <div style="border-left:4px solid {color};
                                    padding-left:12px;">
                            <div class="muted">
                                {escape(str(incident["incident_id"]))}
                            </div>
                            <div class="incident-title">
                                {escape(str(incident["disaster_type"]))}
                            </div>
                            <div class="muted">
                                {escape(str(incident["location"]))}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.write(f"Severity: **{severity.title()}**")
                    st.write(
                        f"Risk: **{incident['risk_level']} "
                        f"({int(incident['risk_score'])}/100)**"
                    )
                    st.write(
                        f"People affected: "
                        f"**{int(incident['affected_people']):,}**"
                    )
                    st.write(
                        f"Damaged houses: "
                        f"**{int(incident['damaged_houses']):,}**"
                    )

                    status = (
                        "Active" if incident["active"]
                        else "Inactive"
                    )

                    verified = (
                        "Verified" if incident["verified"]
                        else "Unverified"
                    )

                    st.caption(f"{status} · {verified}")

                    if incident["needs_review"]:
                        st.warning("Manual review recommended.")


# ---------------------------------------------------------
# AI classification
# ---------------------------------------------------------

def show_classification():
    st.subheader("AI-Powered Disaster Classification")

    st.markdown(
        "Enter an incident description to receive a suggested "
        "disaster category."
    )

    st.info(
        "This is an experimental keyword-based classification tool. "
        "It does not use a trained machine-learning model."
    )

    with st.form("disaster_classification_form"):

        description = st.text_area(
            "Incident description",
            placeholder=(
                "Example: Heavy rainfall caused river overflow "
                "and several homes are underwater."
            ),
            height=150,
        )

        submitted = st.form_submit_button(
            "Analyze Incident",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if not description.strip():
        st.error("Please enter an incident description.")
        return

    try:
        result = classify_incident(description)

    except (TypeError, ValueError) as error:
        st.error(f"Classification failed: {error}")
        return

    first, second = st.columns(2)

    first.metric(
        "Suggested Category",
        result["category"],
    )

    second.metric(
        "Rule-Based Match Score",
        f"{result['match_score']}%",
    )

    if result["needs_review"]:
        st.warning("Manual review recommended.")
    else:
        st.success(
            "A category was suggested. Verify it before use."
        )

    st.markdown("#### Matched Keywords")

    matched_keywords = result["matched_keywords"]

    if isinstance(matched_keywords, dict):
        for category, keywords in matched_keywords.items():
            st.write(f"**{category}:** {', '.join(keywords)}")
    elif matched_keywords:
        st.write(", ".join(matched_keywords))
    else:
        st.write("No matching keywords found.")

    st.markdown("#### Explanation")
    st.write(result["explanation"])

    st.caption(
        "The match score is not a probability or a measure "
        "of real-world classification accuracy."
    )


# ---------------------------------------------------------
# Risk assessment
# ---------------------------------------------------------

def show_risk_assessment(incidents):
    st.subheader("Disaster Risk Assessment")

    st.info(
        "Risk scores use transparent prototype rules. "
        "They are not scientifically validated predictions "
        "or official emergency priorities."
    )

    if not incidents:
        st.warning("No incidents are available.")
        return

    assessments = []

    for incident in incidents:

        result = assess_risk(incident)

        assessments.append({
            "Incident ID": incident.incident_id,
            "Disaster": incident.disaster_type,
            "Location": incident.location,
            "Risk Score": result["risk_score"],
            "Risk Level": result["risk_level"],
            "Manual Review": result["needs_review"],
            "Result": result,
        })

    assessments.sort(
        key=lambda item: item["Risk Score"],
        reverse=True,
    )

    critical_count = sum(
        item["Risk Level"] == "Critical"
        for item in assessments
    )

    high_count = sum(
        item["Risk Level"] == "High"
        for item in assessments
    )

    review_count = sum(
        item["Manual Review"]
        for item in assessments
    )

    first, second, third, fourth = st.columns(4)

    first.metric("Assessed Incidents", len(assessments))
    second.metric("Critical Risk", critical_count)
    third.metric("High Risk", high_count)
    fourth.metric("Needs Review", review_count)

    ranking_data = pd.DataFrame([
        {
            "Incident": item["Incident ID"],
            "Disaster": item["Disaster"],
            "Location": item["Location"],
            "Risk Score": item["Risk Score"],
            "Risk Level": item["Risk Level"],
            "Manual Review": (
                "Yes" if item["Manual Review"] else "No"
            ),
        }
        for item in assessments
    ])

    st.markdown("### Incident Risk Rankings")

    st.dataframe(
        ranking_data,
        use_container_width=True,
        hide_index=True,
    )

    figure = px.bar(
        ranking_data,
        x="Risk Score",
        y="Incident",
        color="Risk Level",
        orientation="h",
        title="Incident Risk Score Comparison",
        color_discrete_map=RISK_COLORS,
        template=CHART_TEMPLATE,
    )

    figure.update_layout(
        xaxis_range=[0, 100],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    figure.update_yaxes(autorange="reversed")

    st.plotly_chart(figure, use_container_width=True)

    st.divider()
    st.markdown("### Individual Risk Assessment")

    options = {
        (
            f"{item['Incident ID']} — "
            f"{item['Disaster']} — "
            f"{item['Location']}"
        ): item
        for item in assessments
    }

    selected_label = st.selectbox(
        "Select an incident",
        list(options.keys()),
        key="risk_assessment_selection",
    )

    selected = options[selected_label]
    result = selected["Result"]

    first, second = st.columns(2)

    first.metric(
        "Risk Score",
        f"{result['risk_score']}/100",
    )

    second.metric(
        "Risk Level",
        result["risk_level"],
    )

    st.progress(result["risk_score"] / 100)

    if result["needs_review"]:
        st.warning("Manual review is recommended.")

    st.markdown("#### Contributing Factors")

    factor_rows = []

    for name, details in result["factors"].items():
        factor_rows.append({
            "Factor": name.replace("_", " ").title(),
            "Input": str(details["value"]),
            "Points": details["points"],
            "Maximum Points": details["maximum"],
        })

    st.dataframe(
        pd.DataFrame(factor_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Assessment Explanation")

    for explanation in result["explanation"]:
        st.write(f"• {explanation}")


# ---------------------------------------------------------
# Data quality monitor
# ---------------------------------------------------------

def show_data_quality(incidents):
    st.subheader("Incident Data Quality Monitor")

    st.info(
        "Checks records for missing information, invalid values, "
        "incomplete coordinates, unverified reports, and duplicate IDs."
    )

    if not incidents:
        st.warning("No incident records are available.")
        return

    try:
        audit = audit_incidents(incidents)

    except (TypeError, ValueError, KeyError) as error:
        st.error(f"Data quality audit failed: {error}")
        return

    reports = audit["reports"]

    first, second, third, fourth = st.columns(4)

    first.metric(
        "Average Quality",
        f"{audit['average_quality_score']}/100",
    )
    second.metric("Good Quality", audit["good_quality"])
    third.metric("Needs Review", audit["needs_review"])
    fourth.metric("Invalid Data", audit["invalid_data"])

    st.progress(
        audit["average_quality_score"] / 100
    )

    quality_counts = pd.DataFrame([
        {
            "Status": "Good quality",
            "Incidents": audit["good_quality"],
        },
        {
            "Status": "Needs review",
            "Incidents": audit["needs_review"],
        },
        {
            "Status": "Invalid data",
            "Incidents": audit["invalid_data"],
        },
    ])

    quality_counts = quality_counts[
        quality_counts["Incidents"] > 0
    ]

    if not quality_counts.empty:

        figure = px.pie(
            quality_counts,
            names="Status",
            values="Incidents",
            hole=0.60,
            color="Status",
            color_discrete_map=QUALITY_COLORS,
            title="Incident Data Quality",
            template=CHART_TEMPLATE,
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )

    quality_rows = []

    for report in reports:
        quality_rows.append({
            "Incident ID": report["incident_id"] or "Missing ID",
            "Quality Score": report["quality_score"],
            "Status": report["status"],
            "Issue Count": report["issue_count"],
            "Needs Review": report["needs_review"],
        })

    quality_dataframe = pd.DataFrame(quality_rows)

    st.markdown("### Incident Quality Report")

    st.dataframe(
        quality_dataframe,
        use_container_width=True,
        hide_index=True,
    )

    options = {}

    for index, report in enumerate(reports):
        incident_id = report["incident_id"] or "Missing ID"

        label = (
            f"{incident_id} — {report['status']} — "
            f"Record {index + 1}"
        )

        options[label] = report

    st.markdown("### Inspect Quality Issues")

    selected_label = st.selectbox(
        "Select an incident",
        list(options.keys()),
        key="quality_incident_selection",
    )

    selected_report = options[selected_label]

    st.metric(
        "Quality Score",
        f"{selected_report['quality_score']}/100",
    )

    if selected_report["issues"]:

        issue_rows = []

        for issue in selected_report["issues"]:
            issue_rows.append({
                "Issue": issue["code"].replace("_", " ").title(),
                "Severity": issue["severity"].title(),
                "Explanation": issue["message"],
            })

        st.dataframe(
            pd.DataFrame(issue_rows),
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.success("No quality issues detected.")

    export_rows = []

    for report in reports:

        export_rows.append({
            "incident_id": report["incident_id"],
            "quality_score": report["quality_score"],
            "status": report["status"],
            "needs_review": report["needs_review"],
            "issue_count": report["issue_count"],
            "issues": "; ".join(
                issue["message"]
                for issue in report["issues"]
            ),
        })

    csv_data = pd.DataFrame(export_rows).to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "Download Data Quality Report (CSV)",
        data=csv_data,
        file_name="disaster_data_quality_report.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------------------------------
# Analytical reports
# ---------------------------------------------------------

def show_analytics_reports(incidents):
    st.subheader("Disaster Analytical Reports")

    st.info(
        "Reports summarize stored incident records. "
        "Synthetic demonstration records may be included."
    )

    if not incidents:
        st.warning("No incidents are available.")
        return

    timestamps = pd.to_datetime(
        [item.reported_at for item in incidents],
        utc=True,
        errors="coerce",
    )

    valid_dates = timestamps.dropna()

    if valid_dates.empty:
        st.warning("No valid incident timestamps are available.")
        return

    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    selected_period = st.date_input(
        "Select reporting date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="analytics_reporting_period",
    )

    if not isinstance(selected_period, (tuple, list)):
        st.warning("Select both a start date and an end date.")
        return

    if len(selected_period) != 2:
        st.warning("Select both a start date and an end date.")
        return

    start_date, end_date = selected_period

    if start_date > end_date:
        st.error("Start date cannot be after end date.")
        return

    try:
        report = generate_analytics_report(
            incidents,
            start_date=start_date,
            end_date=end_date,
        )

    except (TypeError, ValueError, KeyError) as error:
        st.error(f"Unable to generate report: {error}")
        return

    summary = report["summary"]
    quality = report["quality_summary"]

    st.caption(
        f"Period: {start_date} to {end_date} | "
        f"Generated: {report['generated_at']}"
    )

    st.markdown("### Incident Summary")

    first, second, third, fourth = st.columns(4)

    first.metric("Total Incidents", summary["total_incidents"])
    second.metric("Active Incidents", summary["active_incidents"])
    third.metric(
        "People Affected",
        f"{summary['affected_people']:,}",
    )
    fourth.metric(
        "Houses Damaged",
        f"{summary['damaged_houses']:,}",
    )

    first, second, third, fourth = st.columns(4)

    first.metric("Verified", summary["verified_incidents"])
    second.metric("Unverified", summary["unverified_incidents"])
    third.metric("Synthetic", summary["synthetic_incidents"])
    fourth.metric(
        "Average Quality",
        f"{quality['average_quality_score']}/100",
    )

    st.divider()
    st.markdown("### Disaster Type Distribution")

    disaster_data = pd.DataFrame([
        {"Disaster Type": name, "Incidents": count}
        for name, count
        in report["disaster_type_distribution"].items()
    ])

    if not disaster_data.empty:

        figure = px.bar(
            disaster_data,
            x="Disaster Type",
            y="Incidents",
            color="Disaster Type",
            title="Incidents by Disaster Type",
            template=CHART_TEMPLATE,
        )

        figure.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(figure, use_container_width=True)

    left, right = st.columns(2)

    with left:

        st.markdown("### Risk Distribution")

        risk_data = pd.DataFrame([
            {"Risk Level": level, "Incidents": count}
            for level, count
            in report["risk_distribution"].items()
        ])

        if not risk_data.empty:

            figure = px.pie(
                risk_data,
                names="Risk Level",
                values="Incidents",
                hole=0.55,
                color="Risk Level",
                color_discrete_map=RISK_COLORS,
                template=CHART_TEMPLATE,
            )

            st.plotly_chart(
                figure,
                use_container_width=True,
            )

    with right:

        st.markdown("### Data Quality Distribution")

        quality_data = pd.DataFrame([
            {
                "Status": "Good quality",
                "Incidents": quality["good_quality"],
            },
            {
                "Status": "Needs review",
                "Incidents": quality["needs_review"],
            },
            {
                "Status": "Invalid data",
                "Incidents": quality["invalid_data"],
            },
        ])

        quality_data = quality_data[
            quality_data["Incidents"] > 0
        ]

        if not quality_data.empty:

            figure = px.pie(
                quality_data,
                names="Status",
                values="Incidents",
                hole=0.55,
                color="Status",
                color_discrete_map=QUALITY_COLORS,
                template=CHART_TEMPLATE,
            )

            st.plotly_chart(
                figure,
                use_container_width=True,
            )

    st.divider()
    st.markdown("### Daily Incident Reporting Trend")

    trend_data = pd.DataFrame([
        {"Date": day, "Incidents": count}
        for day, count in report["daily_trend"].items()
    ])

    if not trend_data.empty:

        trend_data["Date"] = pd.to_datetime(
            trend_data["Date"]
        )

        figure = px.line(
            trend_data,
            x="Date",
            y="Incidents",
            markers=True,
            template=CHART_TEMPLATE,
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )

    st.divider()
    st.markdown("### Incident Risk Summary")

    risk_results = report["risk_results"]

    if risk_results:

        risk_dataframe = pd.DataFrame([
            {
                "Incident ID": item["incident_id"],
                "Risk Score": item["risk_score"],
                "Risk Level": item["risk_level"],
                "Manual Review": item["needs_review"],
            }
            for item in risk_results
        ])

        st.dataframe(
            risk_dataframe,
            use_container_width=True,
            hide_index=True,
        )

    # Export detailed records.
    quality_by_id = {
        str(item.get("incident_id")): item
        for item in quality["reports"]
    }

    risk_by_id = {
        str(item["incident_id"]): item
        for item in risk_results
    }

    export_rows = []

    for incident in incidents:

        incident_date = pd.to_datetime(
            incident.reported_at,
            utc=True,
            errors="coerce",
        )

        if pd.isna(incident_date):
            continue

        incident_date = incident_date.date()

        if incident_date < start_date or incident_date > end_date:
            continue

        record = incident.to_dict()
        incident_id = str(record.get("incident_id"))

        risk_result = risk_by_id.get(incident_id, {})
        quality_result = quality_by_id.get(incident_id, {})

        record["risk_score"] = risk_result.get("risk_score")
        record["risk_level"] = risk_result.get(
            "risk_level",
            "Unavailable",
        )
        record["data_quality_score"] = quality_result.get(
            "quality_score"
        )
        record["data_quality_status"] = quality_result.get(
            "status",
            "Unavailable",
        )
        record["manual_review_required"] = (
            risk_result.get("needs_review", True)
            or quality_result.get("needs_review", True)
        )

        export_rows.append(record)

    if export_rows:

        csv_data = pd.DataFrame(export_rows).to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "Download Analytical Report (CSV)",
            data=csv_data,
            file_name="disaster_analytical_report.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )

    else:
        st.info("No incident records exist in this reporting period.")


# ---------------------------------------------------------
# Worldwide location picker
# ---------------------------------------------------------

def show_registration_map():
    """Allow the user to click anywhere on the world map."""

    st.markdown("### Select an Incident Location")

    st.write(
        "Click anywhere on the satellite map to select the "
        "incident coordinates. You can select any country."
    )

    current_lat = float(
        st.session_state["registration_latitude"]
    )

    current_lon = float(
        st.session_state["registration_longitude"]
    )

    selected = st.session_state["registration_location_selected"]

    center = (
        [current_lat, current_lon]
        if selected
        else [20.0, 0.0]
    )

    zoom = 8 if selected else 2

    location_map = make_global_map(
        center=center,
        zoom=zoom,
    )

    if selected:

        folium.Marker(
            [current_lat, current_lon],
            tooltip="Selected incident location",
            icon=folium.Icon(
                color="red",
                icon="map-marker",
            ),
        ).add_to(location_map)

    map_result = st_folium(
        location_map,
        width=None,
        height=430,
        key="registration_location_picker",
    )

    if map_result and map_result.get("last_clicked"):

        clicked = map_result["last_clicked"]

        new_lat = float(clicked["lat"])
        new_lon = float(clicked["lng"])

        old_lat = st.session_state["registration_latitude"]
        old_lon = st.session_state["registration_longitude"]

        if (
            new_lat != old_lat
            or new_lon != old_lon
            or not st.session_state["registration_location_selected"]
        ):

            st.session_state["registration_latitude"] = new_lat
            st.session_state["registration_longitude"] = new_lon
            st.session_state["registration_location_selected"] = True

            st.rerun()

    if st.session_state["registration_location_selected"]:

        st.success(
            f"Selected coordinates: "
            f"{st.session_state['registration_latitude']:.6f}, "
            f"{st.session_state['registration_longitude']:.6f}"
        )

    else:

        st.info(
            "No map location selected yet. Click the map to choose one."
        )


# ---------------------------------------------------------
# Incident registration
# ---------------------------------------------------------

def show_registration():
    st.subheader("Register a New Incident")

    st.info(
        "You can register an incident anywhere in the world. "
        "Select its location on the satellite map below."
    )

    show_registration_map()

    st.divider()

    with st.form(
        "register_incident",
        clear_on_submit=True,
    ):

        first, second = st.columns(2)

        with first:

            disaster_type = st.selectbox(
                "Disaster type",
                DISASTER_TYPES,
            )

            location = st.text_input(
                "Location name",
                placeholder="e.g. Tokyo, Japan",
            )

            affected_people = st.number_input(
                "People affected",
                min_value=0,
                step=1,
            )

            damaged_houses = st.number_input(
                "Damaged houses",
                min_value=0,
                step=1,
            )

        with second:

            latitude = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=float(
                    st.session_state["registration_latitude"]
                ),
                format="%.6f",
            )

            longitude = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=float(
                    st.session_state["registration_longitude"]
                ),
                format="%.6f",
            )

            severity = st.selectbox(
                "Severity",
                SEVERITY_LEVELS,
            )

            verified = st.checkbox(
                "Report independently verified"
            )

        submitted = st.form_submit_button(
            "Save Incident",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            if not location.strip():
                st.error("Please enter a location name.")

            else:

                try:

                    incident = Incident(
                        disaster_type=disaster_type,
                        location=location.strip(),
                        affected_people=int(affected_people),
                        damaged_houses=int(damaged_houses),
                        latitude=latitude,
                        longitude=longitude,
                        severity=severity,
                        verified=verified,
                    )

                    incident_id = save_incident(incident)

                    st.session_state["registration_latitude"] = latitude
                    st.session_state["registration_longitude"] = longitude
                    st.session_state["registration_location_selected"] = True

                    st.success(
                        f"Incident saved successfully: {incident_id}"
                    )

                    st.rerun()

                except (
                    ValueError,
                    TypeError,
                    RuntimeError,
                ) as error:

                    st.error(f"Unable to save incident: {error}")


# ---------------------------------------------------------
# Incident search
# ---------------------------------------------------------

def show_search():
    st.subheader("Find an Incident")

    incident_id = st.text_input(
        "Incident ID",
        placeholder="DIS-XXXXXXXX",
    ).strip().upper()

    if incident_id:

        incident = get_incident(incident_id)

        if incident is None:
            st.warning("No incident found with this ID.")
            return

        st.json(incident.to_dict())

        risk = assess_risk(incident)

        first, second = st.columns(2)

        first.metric(
            "Risk Score",
            f"{risk['risk_score']}/100",
        )

        second.metric(
            "Risk Level",
            risk["risk_level"],
        )

        if risk["needs_review"]:
            st.warning("Manual review recommended.")

        quality = assess_data_quality(incident)

        first, second = st.columns(2)

        first.metric(
            "Quality Score",
            f"{quality['quality_score']}/100",
        )

        second.metric(
            "Data Status",
            quality["status"],
        )

        for issue in quality["issues"]:
            st.warning(
                f"{issue['severity'].title()}: {issue['message']}"
            )


# ---------------------------------------------------------
# Incident management
# ---------------------------------------------------------

def show_management(incidents):
    if not incidents:
        st.info("No incidents have been registered.")
        return

    options = {
        f"{item.incident_id} — {item.location}": item.incident_id
        for item in incidents
    }

    st.subheader("Update Incident Information")

    selected = st.selectbox(
        "Select incident",
        list(options.keys()),
        key="management_incident",
    )

    incident_id = options[selected]
    incident = get_incident(incident_id)

    if incident is None:
        st.error("Incident not found.")
        return

    with st.form("update_incident"):

        first, second = st.columns(2)

        with first:

            affected = st.number_input(
                "People affected",
                min_value=0,
                value=incident.affected_people,
                step=1,
            )

            damaged = st.number_input(
                "Damaged houses",
                min_value=0,
                value=incident.damaged_houses,
                step=1,
            )

        with second:

            severity = st.selectbox(
                "Severity",
                SEVERITY_LEVELS,
                index=SEVERITY_LEVELS.index(incident.severity),
            )

            verified = st.checkbox(
                "Verified",
                value=incident.verified,
            )

        submitted = st.form_submit_button(
            "Save Changes",
            type="primary",
        )

        if submitted:

            try:

                update_incident(
                    incident_id,
                    affected_people=int(affected),
                    damaged_houses=int(damaged),
                    severity=severity,
                    verified=verified,
                )

                st.success("Incident updated.")
                st.rerun()

            except (
                ValueError,
                TypeError,
                RuntimeError,
            ) as error:

                st.error(f"Update failed: {error}")

    st.divider()
    st.subheader("Incident Resolution")

    if incident.active:

        confirmed = st.checkbox(
            "I confirm this incident should be marked inactive.",
            key="confirm_resolution",
        )

        if st.button(
            "Mark Incident Resolved",
            type="secondary",
        ):

            if not confirmed:
                st.warning("Please confirm this action first.")

            else:
                deactivate_incident(incident_id)
                st.success("Incident marked inactive.")
                st.rerun()

    else:
        st.info("This incident is already inactive.")


# ---------------------------------------------------------
# Main application
# ---------------------------------------------------------

def main():
    show_header()

    st.warning(
        "Decision-support prototype. This dashboard uses manually "
        "entered and demonstration reports, not verified live emergency feeds."
    )

    try:

        incidents = get_incidents()
        dataframe = make_dataframe(incidents)

        # Sidebar filters.
        st.sidebar.title("🌍 Global Command Center")

        st.sidebar.caption(
            "Worldwide Disaster Response Intelligence"
        )

        st.sidebar.divider()
        st.sidebar.subheader("Dashboard Filters")

        if dataframe.empty:

            available_types = DISASTER_TYPES
            available_severities = SEVERITY_LEVELS

        else:

            available_types = sorted(
                dataframe["disaster_type"].dropna().unique().tolist()
            )

            available_severities = sorted(
                dataframe["severity"].dropna().unique().tolist()
            )

        selected_types = st.sidebar.multiselect(
            "Disaster types",
            available_types,
            default=available_types,
        )

        selected_severities = st.sidebar.multiselect(
            "Severity levels",
            available_severities,
            default=available_severities,
        )

        selected_statuses = st.sidebar.multiselect(
            "Incident status",
            ["Active", "Inactive"],
            default=["Active", "Inactive"],
        )

        verification = st.sidebar.selectbox(
            "Verification",
            ["All", "Verified", "Unverified"],
        )

        filtered = filter_incidents(
            dataframe,
            selected_types,
            selected_severities,
            selected_statuses,
            verification,
        )

        # Demo data.
        st.sidebar.divider()
        st.sidebar.subheader("Demonstration Data")

        st.sidebar.caption(
            "Synthetic reports are not real emergency events."
        )

        has_demo = any(
            "[DEMO]" in item.location
            for item in incidents
        )

        if st.sidebar.button(
            "Load Demo Dataset",
            use_container_width=True,
            disabled=has_demo,
        ):

            if load_demo_data():
                st.sidebar.success("Demo reports added.")
            else:
                st.sidebar.info("Demo reports already exist.")

            st.rerun()

        if has_demo:
            st.sidebar.caption("Demo dataset is already loaded.")

        st.sidebar.divider()

        st.sidebar.caption(
            f"Stored incident records: {len(incidents)}"
        )

        # Metrics.
        show_metrics(filtered)

        st.divider()

        # Seven dashboard sections.
        (
            overview_tab,
            registration_tab,
            management_tab,
            classification_tab,
            risk_tab,
            quality_tab,
            analytics_tab,
        ) = st.tabs([
            "🌐 Command Overview",
            "➕ Register Incident",
            "⚙️ Incident Management",
            "🧠 AI Classification",
            "📊 Risk Assessment",
            "🔍 Data Quality",
            "📈 Analytical Reports",
        ])

        with overview_tab:

            show_map(filtered)

            st.divider()
            show_charts(filtered)

            st.divider()
            show_incident_cards(filtered)

            st.divider()
            show_search()

        with registration_tab:
            show_registration()

        with management_tab:
            show_management(incidents)

        with classification_tab:
            show_classification()

        with risk_tab:
            show_risk_assessment(incidents)

        with quality_tab:
            show_data_quality(incidents)

        with analytics_tab:
            show_analytics_reports(incidents)

        st.divider()

        st.caption(
            "Global Disaster Response Intelligence | "
            "Open-source decision-support prototype"
        )

    except (
        RuntimeError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
    ) as error:

        st.error(
            f"The dashboard encountered a problem: {error}"
        )


if __name__ == "__main__":
    main()