# Getting Started with F1 WebApp

## Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Internet connection (for downloading F1 data)

## Installation

### 1. Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### 2. Clone and Setup Project

```bash
# Navigate to project directory
cd f1_webapp

# Sync dependencies (creates virtual environment automatically)
uv sync

# Verify installation
uv run python --version
```

## Quick Test

### Test ESPN API

```bash
uv run python examples/example_espn.py
```

Expected output:
- Current season year
- Top 10 driver standings
- Driver profile for Max Verstappen
- Recent F1 events

### Test FastF1

```bash
uv run python examples/example_fastf1.py
```

**Note:** First run will download data and may take 30-60 seconds. Subsequent runs will be faster due to caching.

Expected output:
- 2024 season schedule
- Monaco qualifying session analysis
- Fastest lap details
- Telemetry data samples
- Driver comparison

### Quick Start (Combined)

```bash
uv run python examples/quick_start.py
```

This demonstrates both APIs working together.

## Start API Server

### Development Mode

```bash
# Start with auto-reload
uv run uvicorn src.f1_webapp.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Access the API

1. **API Root**: http://localhost:8000
2. **Interactive Docs**: http://localhost:8000/docs
3. **Alternative Docs**: http://localhost:8000/redoc

### Test API Endpoints

```bash
# Get 2024 driver standings
curl http://localhost:8000/espn/standings/2024

# Get Max Verstappen profile
curl http://localhost:8000/espn/drivers/4665

# Get Monaco 2024 Qualifying results
curl http://localhost:8000/fastf1/session/2024/Monaco/Q

# Get Verstappen's fastest lap telemetry
curl http://localhost:8000/fastf1/telemetry/2024/Monaco/Q/VER

# Compare Verstappen vs Leclerc
curl "http://localhost:8000/fastf1/compare/2024/Monaco/Q?driver1=VER&driver2=LEC"
```

## Using in Your Code

### ESPN API Only

```python
from f1_webapp.espn import ESPNClient

client = ESPNClient()

# Get current standings
standings = client.get_driver_standings(2024)
print(standings)

# Get driver profile
driver = client.get_driver("4665")  # Verstappen
print(f"{driver['fullName']} drives for {driver['vehicles'][0]['team']}")
```

### FastF1 Only

```python
from f1_webapp.fastf1 import FastF1Client

# Initialize with cache
client = FastF1Client(cache_dir="./f1_cache")

# Load a session
session = client.load_session(2024, "Monaco", "Q")

# Get fastest lap
fastest = client.get_fastest_lap(session)
print(f"Fastest: {fastest['Driver']} - {fastest['LapTime']}")

# Get telemetry
telemetry = client.get_lap_telemetry(fastest)
print(telemetry[["Speed", "Throttle", "Brake"]].describe())
```

### Both APIs Together

```python
from f1_webapp.espn import ESPNClient
from f1_webapp.fastf1 import FastF1Client

espn = ESPNClient()
ff1 = FastF1Client(cache_dir="./f1_cache")

# Get driver from ESPN
driver = espn.get_driver("4665")
print(f"Driver: {driver['fullName']}")

# Get their telemetry from FastF1
session = ff1.load_session(2024, "Monaco", "Q")
ver_fastest = ff1.get_fastest_lap(session, "VER")
telemetry = ff1.get_lap_telemetry(ver_fastest)

print(f"Top Speed: {telemetry['Speed'].max()} km/h")
```

## Common Issues & Solutions

### Issue: "Module not found"

**Solution:**
```bash
# Make sure you're using uv run
uv run python your_script.py

# Or activate the virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
python your_script.py
```

### Issue: FastF1 slow on first run

**Solution:** This is normal! FastF1 downloads and caches data on first use. Subsequent runs will be much faster.

```python
# Enable cache to avoid re-downloading
client = FastF1Client(cache_dir="./f1_cache")
```

### Issue: "No data available for session"

**Solution:**
- Check if the session has occurred yet
- For historical data before 2018, use ESPN API
- For 2018+ detailed data, use FastF1

### Issue: ESPN API returns 404

**Solution:**
- Verify event/driver IDs are correct
- Check if the season/event has occurred
- ESPN API is unofficial and may change

### Issue: Rate limiting or slow responses

**Solution:**
```python
# For ESPN: Add delays between requests
import time
time.sleep(0.5)  # 500ms between requests

# For FastF1: Always use caching
FastF1Client(cache_dir="./f1_cache")
```

## Next Steps

### 1. Explore the Documentation

- [ESPN F1 API Mapping](./ESPN_F1_API_MAPPING.md) - Complete ESPN API reference
- [FastF1 API Mapping](./FASTF1_API_MAPPING.md) - FastF1 usage guide
- [Integration Strategy](./API_INTEGRATION_STRATEGY.md) - Best practices for using both APIs

### 2. Run the Examples

```bash
# ESPN examples
uv run python examples/example_espn.py

# FastF1 examples
uv run python examples/example_fastf1.py

# Combined quick start
uv run python examples/quick_start.py
```

### 3. Start Building

Create your own scripts in the `examples/` directory:

```python
# examples/my_analysis.py
from f1_webapp.espn import ESPNClient
from f1_webapp.fastf1 import FastF1Client

# Your code here
```

Run with:
```bash
uv run python examples/my_analysis.py
```

### 4. Customize the API

Edit `src/f1_webapp/api/app.py` to add new endpoints:

```python
@app.get("/my-custom-endpoint")
def my_custom_endpoint():
    # Your logic here
    return {"message": "Hello F1!"}
```

### 5. Add Dependencies

```bash
# Add a new package
uv add matplotlib  # For plotting

# Add dev dependency
uv add --dev pytest  # For testing
```

## Development Workflow

### 1. Make Changes

Edit files in `src/f1_webapp/`

### 2. Test Changes

```bash
# Run your code
uv run python -m src.f1_webapp.api.app

# Or run examples
uv run python examples/your_example.py
```

### 3. Add New Features

```bash
# Add dependencies
uv add new-package

# Create new modules
touch src/f1_webapp/my_module.py
```

### 4. Format Code (Optional)

```bash
# Add formatters
uv add --dev black ruff

# Format code
uv run black src/
uv run ruff check src/
```

## Performance Tips

### 1. Always Use Caching for FastF1

```python
# Good
client = FastF1Client(cache_dir="./f1_cache")

# Bad
client = FastF1Client()  # No cache, slow!
```

### 2. Load Only What You Need

```python
# Load selectively for better performance
session = client.load_session(
    2024, "Monaco", "Q",
    laps=True,
    telemetry=True,
    weather=False,  # Skip if not needed
    messages=False   # Skip if not needed
)
```

### 3. Filter Before Getting Telemetry

```python
# Good - Filter first
quick_laps = session.laps.pick_quicklaps()
ver_laps = quick_laps.pick_driver("VER")
telemetry = ver_laps.pick_fastest().get_telemetry()

# Bad - Get all telemetry then filter
all_telemetry = session.laps.get_telemetry()  # Slow!
```

### 4. Batch ESPN API Calls

```python
import asyncio
import aiohttp

# Use async for multiple requests
async def get_multiple_drivers():
    async with aiohttp.ClientSession() as session:
        # Fetch multiple drivers concurrently
        tasks = [
            session.get(f"...drivers/{id}")
            for id in ["4665", "5579", "5498"]
        ]
        return await asyncio.gather(*tasks)
```

## Support & Resources

- **Documentation**: Check the `.md` files in project root
- **Examples**: See `examples/` directory
- **API Docs**: http://localhost:8000/docs (when server running)
- **FastF1 Docs**: https://docs.fastf1.dev/
- **ESPN API**: Unofficial, explore via examples

## Troubleshooting

If you encounter issues:

1. **Check Python version**: `python --version` (must be 3.12+)
2. **Verify uv installation**: `uv --version`
3. **Re-sync dependencies**: `uv sync`
4. **Clear FastF1 cache**: `rm -rf f1_cache/`
5. **Check internet connection**: Required for downloading data

## What's Next?

Now that you're set up, you can:

- ✅ Query historical F1 data with ESPN API
- ✅ Analyze detailed telemetry with FastF1
- ✅ Build visualizations and dashboards
- ✅ Create your own F1 analytics tools
- ✅ Integrate with web/mobile applications

Happy coding! 🏎️💨
