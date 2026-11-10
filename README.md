# AI-Powered Disaster Management & Response Intelligence System

An interactive disaster management decision-support prototype built with Python and Streamlit. The system organizes incident reports, provides rule-based disaster classification, assesses incident risk, checks data quality, and generates analytical reports through an interactive dashboard.

> **Project status:** Portfolio prototype under development. This system is not an official emergency service, dispatch platform, or source of verified live disaster information.

## Overview

Disaster response requires timely access to organized incident information. This project demonstrates how software and transparent decision-support methods can help organize reported incidents and make their key details easier to review.

The application provides a centralized dashboard for registering, managing, filtering, visualizing, and analyzing disaster incident records.

## Key Features

- **Incident Management:** Register, view, update, and deactivate incident records.
- **Disaster Classification:** Suggest a disaster category using a keyword-based classification engine.
- **Risk Assessment:** Calculate a transparent rule-based risk score using incident information.
- **Data Quality Assessment:** Identify missing, invalid, or unverified incident information.
- **Analytical Reports:** Generate summaries, distributions, and daily reporting trends.
- **Interactive Dashboard:** Explore incident statistics, charts, maps, and filters.
- **Data Export:** Download data quality and analytical reports where supported.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Interactive dashboard |
| Pandas | Data processing |
| Plotly | Interactive charts |
| Folium | Interactive incident map |
| Streamlit-Folium | Map integration |
| JSON | Local incident data storage |
| unittest | Automated testing |

## Project Structure

```text
AI-Disaster-Response/
│
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── .streamlit/
│   └── config.toml
│
├── data/
│   ├── raw/
│   └── processed/
│       └── incidents.json
│
├── models/
│
├── src/
│   ├── data/
│   │   ├── incident.py
│   │   ├── storage.py
│   │   └── quality.py
│   │
│   ├── intelligence/
│   │   ├── classifier.py
│   │   └── risk/
│   │       └── assessment.py
│   │
│   └── reports/
│       └── analytics.py
│
├── tests/
│
└── docs1/
    ├── architecture.md
    ├── methodology.md
    └── limitations.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual GitHub repository URL.

### 2. Open the project directory

```bash
cd AI-Disaster-Response
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 6. Run the application

```bash
python -m streamlit run app.py
```

The dashboard should open in your browser at:

`http://localhost:8501`

## Running Automated Tests

Run the complete test suite:

```bash
python -m unittest discover -s tests -v
```

The project has reached **55 passing automated tests** in the current development environment.

## Classification and Risk Assessment

The current classification engine uses keyword matching to suggest disaster categories. Its match score is a rule-based indicator, not a calibrated probability.

The risk assessment engine uses predefined scoring rules and incident information to produce a risk score and risk category.

These methods are transparent prototypes. They have not been validated as scientifically accurate disaster predictions or official emergency prioritization methods.

## Data and Safety

- Sample incidents may contain synthetic demonstration data.
- Synthetic records should not be interpreted as verified real-world events.
- Incident records are stored locally using JSON in the current implementation.
- The application does not independently verify incident reports.
- The system does not automatically dispatch emergency personnel or services.
- Do not enter confidential or sensitive personal information into a public demonstration.

## Current Limitations

- Classification is keyword-based rather than a trained machine-learning model.
- Risk scores use predefined rules and require real-world validation before operational use.
- The application does not currently provide a verified live disaster-data feed.
- Local JSON storage is not designed for concurrent multi-user production use.
- Hosted deployment requires a persistent storage solution if incident data must survive application restarts.

See [docs1/limitations.md](docs1/limitations.md) for further details.

## Future Improvements

- Integrate reliable and documented real-world disaster datasets.
- Develop and evaluate machine-learning classification models using labeled data.
- Improve geographic visualization and location selection.
- Introduce persistent database storage.
- Add authentication and role-based access controls.
- Expand automated testing and model evaluation.
- Deploy a public demonstration with appropriate data safeguards.

## Project Documentation

- [System Architecture](docs1/architecture.md)
- [Methodology](docs1/methodology.md)
- [Limitations](docs1/limitations.md)

## Author

Developed as an independent AI and software engineering portfolio project.

## License

A license will be added before public release. Until then, no permission to reuse, modify, or redistribute this project is granted by this README.
