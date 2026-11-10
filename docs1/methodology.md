# Project Methodology

## 1. Introduction

This document describes the methods used by the AI-Powered Disaster Management & Response Intelligence System.

The current prototype combines incident data validation, keyword-based classification, rule-based risk assessment, data quality evaluation, and analytical reporting.

The methods are designed to be understandable, testable, and transparent.

## 2. Incident Data Collection and Representation

The application accepts structured incident information through its dashboard.

An incident record contains:

- Unique incident identifier
- Disaster category
- Location
- Affected population
- Damaged houses
- Latitude and longitude
- Severity
- Active status
- Verification status
- Reporting timestamp

Incident records are represented using a Python data model and stored locally in JSON format.

The demonstration dataset contains synthetic records for testing and visualization.

## 3. Disaster Classification Method

**Implementation:** `src/intelligence/classifier.py`

### 3.1 Method

The current classifier uses keyword-based text matching.

It examines an incident description and searches for predefined keywords or phrases associated with supported disaster categories.

Supported categories:

- Flood
- Earthquake
- Fire
- Storm
- Landslide

### 3.2 Classification Process

1. Receive an incident description.
2. Normalize the text for consistent matching.
3. Search for category-related keywords and phrases.
4. Count matching terms for each category.
5. Select a suggested category based on the matching results.
6. Calculate a heuristic match score.
7. Flag ambiguous or insufficient descriptions for manual review.

### 3.3 Match Score

The classifier produces a rule-based match score between 0 and 100.

This score indicates the strength of keyword matching under the current rules. It is not a probability, model confidence, or measurement of real-world classification accuracy.

### 3.4 Manual Review

Descriptions may require manual review when:

- No supported category matches.
- Multiple categories have tied scores.
- The description provides insufficient evidence.

### 3.5 Current Limitation

The classifier does not use a trained machine-learning model, embeddings, or a large language model.

Its performance depends on the quality and coverage of its predefined keywords.

## 4. Risk Assessment Method

**Implementation:** `src/intelligence/risk/assessment.py`

### 4.1 Method

The risk engine calculates a score using predefined rules and incident attributes.

The assessment considers five factors:

1. Affected people
2. Damaged houses
3. Reported severity
4. Active status
5. Disaster type

### 4.2 Scoring Components

| Factor | Maximum Points |
|---|---:|
| Affected people | 30 |
| Damaged houses | 20 |
| Reported severity | 25 |
| Active status | 10 |
| Disaster context | 5 |
| **Maximum total** | **100** |

### 4.3 Risk Categories

| Risk Score | Risk Level |
|---|---|
| 0–24 | Low |
| 25–49 | Moderate |
| 50–74 | High |
| 75–100 | Critical |

### 4.4 Assessment Process

1. Receive an incident record.
2. Validate relevant incident attributes.
3. Assign points according to predefined thresholds.
4. Add the factor scores.
5. Cap the final score at 100.
6. Assign a risk category.
7. Generate an explanation of the contributing factors.
8. Flag records requiring manual review.

### 4.5 Interpretation

The risk score is a prototype decision-support indicator.

It is not a scientifically validated prediction of disaster impact, casualty numbers, or emergency response priority.

The scoring thresholds require evaluation against suitable real-world data before any operational use.

## 5. Data Quality Assessment Method

**Implementation:** `src/data/quality.py`

### 5.1 Objective

The data quality module identifies potential issues in incident records.

It checks important fields and evaluates whether the available information is suitable for further analysis.

### 5.2 Validation Checks

The module examines:

- Incident identifiers
- Disaster categories
- Location information
- Affected population values
- Damaged house values
- Geographic coordinates
- Verification status
- Severity information
- Active status
- Reporting timestamps

### 5.3 Quality Scoring

The quality score starts at 100.

Points are deducted according to the detected issue severity:

| Issue Severity | Deduction |
|---|---:|
| Error | 25 points |
| Warning | 10 points |
| Information | 3 points |

The resulting score cannot fall below zero.

Duplicate incident identifiers are also checked during the audit process and receive an additional penalty.

### 5.4 Quality Status

The module reports one of three statuses:

- **Good quality:** No errors or warnings were identified.
- **Needs review:** One or more warnings were identified without errors.
- **Invalid data:** One or more errors were identified.

A good quality score does not prove that an incident report is factually correct.

## 6. Analytical Reporting Method

**Implementation:** `src/reports/analytics.py`

The analytics module processes incident records to produce structured reports.

### 6.1 Summary Statistics

It calculates:

- Total incidents
- Active and inactive incidents
- Verified and unverified reports
- Affected people
- Damaged houses
- Synthetic demonstration records

### 6.2 Distribution Analysis

The module groups incidents by:

- Disaster category
- Risk category

### 6.3 Time-Based Analysis

Incident timestamps are used to generate daily reporting trends.

Optional start and end dates allow inclusive reporting-period filtering.

Records with invalid timestamps are excluded when date filtering is active.

### 6.4 Data Quality Integration

The analytics module also incorporates the data quality audit to provide an overview of the condition of the selected incident records.

## 7. Geographic Visualization

The dashboard uses Folium to visualize incidents with available geographic coordinates.

Incident markers provide a geographic representation of stored records.

The map is intended to help users explore incident locations, not to establish verified disaster boundaries or predict affected areas.

## 8. Testing Methodology

The project uses Python's built-in `unittest` framework.

Automated tests cover the major modules, including:

- Incident model validation
- Data storage operations
- Disaster classification
- Risk assessment
- Data quality assessment
- Analytical reporting

The latest recorded development test run completed with 55 passing tests.

Run the tests using:

```bash
python -m unittest discover -s tests -v
```

## 9. Ethical and Safety Considerations

The system is designed as a software engineering and decision-support prototype.

Important safeguards include:

- Synthetic data is identified as demonstration data.
- Unverified reports are distinguished from verified records.
- Uncertain classification results can be flagged for review.
- Risk scoring is presented transparently.
- Automated results are not treated as official emergency decisions.
- The system does not autonomously dispatch emergency services.

## 10. Future Research and Development

Potential research directions include:

- Training and evaluating disaster classification models.
- Testing risk assessment against labeled historical incident data.
- Evaluating classification precision, recall, and F1-score.
- Studying geographic and temporal disaster patterns.
- Integrating reliable external disaster datasets.
- Improving multilingual incident description processing.
- Comparing rule-based methods with machine-learning approaches.

