# Bookmaker.eu WebSocket Scraper

## 📖 Quick Start

### **Prerequisites**

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation)
- Bookmaker.eu account
- OpenAI API key (for AI features)

### **Installation**

```bash
# 1. Clone repository
git clone https://github.com/AshkanGoharfar/bookmaker-scraper.git
cd bookmaker-scraper

# 2. Install dependencies
poetry install

# 3. Install Playwright browsers
poetry run playwright install chromium

# 4. Configure environment
cp .env.example .env
# Edit .env and add your credentials:
#   BOOKMAKER_USERNAME=your_username
#   BOOKMAKER_PASSWORD=your_password
#   OPENAI_API_KEY=your_api_key
```

### **Usage**

```bash
# Run the scraper
poetry run python main.py

# Run with debug logging
LOG_LEVEL=DEBUG poetry run python main.py

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src --cov-report=term-missing
```

---

## 🎯 What It Does

This scraper:
1. **Authenticates** with Bookmaker.eu (automated via Playwright)
2. **Connects** to WebSocket endpoint
3. **Maintains** connection with heartbeat mechanism
4. **Receives** real-time odds updates (deltas)
5. **Parses** and prints formatted odds to console

**Example Output:**
```
[2024-02-15 14:32:15] MLB - Toronto Blue Jays vs. New York Yankees
  Market: Moneyline
  Team: Toronto Blue Jays
  Odds: 2.30 → 2.50 (↑ 8.7%)
```

---

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=src --cov-report=term-missing

# Run specific test file
poetry run pytest tests/unit/test_parser.py -v

# Generate HTML coverage report
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 🔧 Troubleshooting

### **Common Issues**

**1. Playwright browser not installed**
```bash
poetry run playwright install chromium
```

**2. Authentication failure**
- Verify credentials in `.env`
- Check Bookmaker.eu website is accessible
- Try manual login first to ensure account works

**3. WebSocket connection fails**
- Check network connectivity
- Verify session cookie is valid
- Review logs in `logs/bookmaker_scraper.log`

**4. No odds deltas received**
- WebSocket endpoint may have changed
- Heartbeat mechanism may need adjustment
- Check browser DevTools (Network tab → WS) for current format

**5. Tests failing**
- Ensure all dependencies installed: `poetry install`
- Check Python version: `python --version` (3.10+ required)
- Run tests with verbose output: `pytest -vv`

---

## 📂 Project Structure

```
bookmaker-scraper/
├── src/                     # Source code
│   ├── auth/               # Authentication (Playwright)
│   ├── websocket/          # WebSocket client + heartbeat
│   ├── parser/             # Odds parser
│   ├── market/             # Market state management
│   ├── monitoring/         # Health monitoring
│   ├── ai/                 # AI features (optional)
│   └── utils/              # Utilities
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── logs/                    # Log files (gitignored)
├── main.py                 # Entry point
├── pyproject.toml          # Poetry dependencies
├── .env.example            # Environment template
└── README.md               # This file
```
