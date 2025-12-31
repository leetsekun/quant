# Quant Platform - Day of Week Analysis

A simple quantitative analysis platform that analyzes OHLC (Open-High-Low-Close) data to determine the best trading day of the week for any given period.

## Features

- 📊 Import Bloomberg CSV format OHLC data
- 📅 Analyze best day of week by average returns
- 📈 Detailed statistics for each day (average return, win rate, etc.)
- 🎯 Filter analysis by custom date ranges
- 🐳 Docker-ready deployment
- 🧪 Comprehensive unit tests with pytest

## CSV Format Requirements

**This platform only supports Bloomberg CSV format**. The CSV file must have the following structure:

```
Row 0: Security,SPX Index,,,,,,,,,,,
Row 1: Start Date,12/31/97 0:00,,,,,,,,,,,
Row 2: End Date,12/24/25 0:00,,,,,,,,,,,
Row 3: Period,D,,,,,,,,,,,
Row 4: Currency,USD,,,,,,,,,,,
Row 5: ,,,,,,,,,,,,
Row 6: Date,PX_LAST,Change,% Change,PX_OPEN,Change,% Change,PX_HIGH,Change,% Change,PX_LOW,Change,% Change
Row 7+: Data rows...
```

**Required columns** (starting at row 6):
- `Date` - Trading date
- `PX_OPEN` - Opening price
- `PX_HIGH` - High price
- `PX_LOW` - Low price
- `PX_LAST` - Closing price
- `% Change` - Percentage change (optional, will be calculated if missing)

The platform automatically:
- Skips the first 6 header rows
- Maps Bloomberg column names (PX_OPEN, PX_HIGH, PX_LOW, PX_LAST) to standard OHLC format
- Uses the existing % Change column for return calculations
- Parses dates and sorts data chronologically

## Project Structure

```
quant/
├── src/                    # Source code
│   ├── __init__.py
│   ├── app.py             # Flask web application
│   └── analysis.py        # Quantitative analysis engine
├── test/                   # Unit tests
│   ├── __init__.py
│   └── test_analyzer.py   # Tests for QuantAnalyzer
├── templates/
│   └── index.html         # Web interface
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
├── .dockerignore          # Docker ignore rules
├── run.py                 # Application entry point
├── spx500.csv            # Sample SPX500 data
└── README.md             # This file
```

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python run.py
```

Or using the module directly:
```bash
python -m src.app
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

### Running Tests

Run all unit tests:
```bash
python3 -m pytest test/
```

Run with verbose output:
```bash
python3 -m pytest test/ -v
```

Run a specific test file:
```bash
python3 -m pytest test/test_analyzer.py
```

Run a specific test:
```bash
python3 -m pytest test/test_analyzer.py::test_init
```

Run with coverage:
```bash
python3 -m pytest test/ --cov=src --cov-report=html
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t quant-platform .
```

2. Run the container:
```bash
docker run -p 5000:5000 quant-platform
```

3. Access the application at:
```
http://localhost:5000
```

## Usage

1. **Load Data**: 
   - Click "Load SPX500 Data" to use the included sample data (Bloomberg format)
   - Or upload your own Bloomberg CSV file

2. **Analyze**:
   - Optionally specify a date range for analysis
   - Click "Analyze" to see the best day of week

3. **View Results**:
   - See the best trading day highlighted
   - Review detailed statistics for all days of the week
   - Metrics include: average return, median return, standard deviation, win rate, and trading day counts

## API Endpoints

- `GET /` - Main web interface
- `POST /api/upload` - Upload Bloomberg CSV file
- `POST /api/load-default` - Load default SPX500 data (Bloomberg format)
- `POST /api/best-day-of-week` - Analyze best day of week

## Development

### Project Organization

- **src/**: Contains all source code modules
  - `analysis.py`: Core quantitative analysis logic
  - `app.py`: Flask web application and API endpoints

- **test/**: Contains all unit tests
  - `test_analyzer.py`: Comprehensive tests for QuantAnalyzer class

### Adding New Features

1. Add new analysis methods to `src/analysis.py`
2. Create corresponding unit tests in `test/`
3. Add API endpoints in `src/app.py` if needed
4. Update the frontend in `templates/index.html`

## Technology Stack

- **Backend**: Flask (Python)
- **Data Processing**: Pandas, NumPy
- **Frontend**: HTML, CSS, JavaScript
- **Testing**: unittest
- **Deployment**: Docker, Gunicorn

## License

MIT License
