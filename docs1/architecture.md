# System Architecture

## 1. Introduction

The AI-Powered Disaster Management & Response Intelligence System is a Python-based decision-support prototype designed to organize disaster incident reports and provide analytical insights.

The application follows a modular architecture. Its dashboard handles user interaction, while separate modules manage incident data, classification, risk assessment, data quality, and analytical reporting.

## 2. High-Level Architecture

The system is organized into five main layers:

1. **Presentation Layer:** Displays the interactive Streamlit dashboard.
2. **Data Management Layer:** Creates, stores, retrieves, and updates incident records.
3. **Intelligence Layer:** Performs rule-based disaster classification and risk assessment.
4. **Quality Layer:** Checks incident records for data issues.
5. **Analytics Layer:** Generates summaries, distributions, and reporting trends.

### Architecture Flow

```text
                 USER
                   |
                   v
          STREAMLIT DASHBOARD
                 app.py
                   |
          +--------+---------+
          |        |         |
          v        v         v
       Incident  Disaster   Risk
       Management Classification Assessment
          |        |         |
          v        v         v
       JSON DATA  Keyword   Rule-Based
       STORAGE    Matching  Scoring
          |
          v
      DATA QUALITY
       ASSESSMENT
          |
          v
     ANALYTICAL REPORTS
          |
          v
     DASHBOARD OUTPUT
```

This diagram represents the logical flow of the current prototype. Individual modules may be called directly by the dashboard rather than through one strictly sequential pipeline.

## 3. Main Components

### 3.1 Presentation Layer

**File:** `app.py`

The Streamlit application provides the user interface.

Responsibilities:

- Display incident statistics.
- Register new incidents.
- Manage existing incident records.
- Show an interactive incident map.
- Display classification results.
- Display risk assessments.
- Show data quality reports.
- Generate analytical reports.

### 3.2 Incident Data Model

**File:** `src/data/incident.py`

Defines the incident structure.

Incident information includes:

- Incident ID
- Disaster type
- Location
- Number of affected people
- Number of damaged houses
- Geographic coordinates
- Active or inactive status
- Verification status
- Severity
- Reporting timestamp

The model also performs input validation and provides methods for converting incident objects into dictionaries.

### 3.3 Data Storage

**File:** `src/data/storage.py`

Handles local JSON-based incident storage.

Responsibilities:

- Save incident records.
- Load stored incidents.
- Retrieve an incident by ID.
- Update permitted incident fields.
- Deactivate incident records.
- Prevent duplicate incident IDs.

### 3.4 Disaster Classification

**File:** `src/intelligence/classifier.py`

Uses keyword matching to suggest a disaster category from an incident description.

Supported categories include:

- Flood
- Earthquake
- Fire
- Storm
- Landslide

Unknown or ambiguous descriptions can be flagged for manual review.

This is a rule-based classification system, not a trained machine-learning model.

### 3.5 Risk Assessment

**File:** `src/intelligence/risk/assessment.py`

Calculates a risk score using predefined rules.

The assessment considers:

- Affected population
- Damaged houses
- Reported severity
- Active incident status
- Disaster type

The resulting score is categorized as:

- Low
- Moderate
- High
- Critical

The scoring system is a transparent prototype and has not been validated as an operational emergency prioritization model.

### 3.6 Data Quality Assessment

**File:** `src/data/quality.py`

Evaluates incident records for potential data quality issues.

It checks:

- Required information
- Invalid values
- Geographic coordinates
- Verification status
- Severity information
- Duplicate incident IDs

The module produces quality scores and identifies records that may require review.

### 3.7 Analytical Reporting

**File:** `src/reports/analytics.py`

Generates structured reports from incident records.

Report information includes:

- Total incidents
- Active and inactive incidents
- Verified and unverified incidents
- Affected population
- Damaged houses
- Disaster type distribution
- Risk distribution
- Data quality summary
- Daily reporting trends
- Synthetic demonstration incident count

The reporting module also supports inclusive date-range filtering.

## 4. Data Flow

The typical application workflow is:

1. A user registers or views an incident through the dashboard.
2. The incident data model validates the information.
3. The storage module saves or retrieves records from JSON.
4. The classification module can suggest a disaster category.
5. The risk assessment module calculates a rule-based score.
6. The data quality module checks record completeness and consistency.
7. The analytics module generates reporting summaries.
8. The dashboard displays the results through metrics, charts, tables, and maps.

## 5. Technology Choices

| Technology | Architectural Role |
|---|---|
| Python | Core application development |
| Streamlit | User interface |
| Pandas | Data handling |
| Plotly | Data visualization |
| Folium | Geographic visualization |
| JSON | Local data persistence |
| unittest | Automated testing |

## 6. Design Principles

The architecture follows these principles:

- **Modularity:** Each major responsibility has a separate module.
- **Maintainability:** Components can be improved independently.
- **Transparency:** Classification and risk rules can be inspected.
- **Validation:** Incident inputs are checked before processing.
- **Testability:** Core components have automated tests.
- **Safety:** Results are presented as decision-support information rather than official emergency instructions.

## 7. Future Architecture Improvements

Potential improvements include:

- Replace local JSON storage with a persistent database.
- Introduce authenticated user accounts and role-based access.
- Add documented external disaster data integrations.
- Develop evaluated machine-learning models using labeled datasets.
- Add an API layer for external integrations.
- Improve deployment, monitoring, and data security.

