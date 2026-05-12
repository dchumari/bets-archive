# Daily Football Bet Scraper

A GitHub Actions workflow that scrapes finished football bets from [ComboBets.com](https://combobets.com/football-predictions/most-popular-bets/) daily and stores them in JSON and CSV formats.

## Features

- ✅ Scrapes "Top Soccer Bets • Latest Results" list from ComboBets.com
- ✅ Extracts match, prediction, odds, and result status (WON/LOST)
- ✅ Stores data in both JSON and CSV formats
- ✅ Prevents duplicates using MD5 hash tracking
- ✅ Runs automatically once per day at 2:00 AM UTC
- ✅ Can be manually triggered for testing

## Files

- `bet_scraper.py` - Main Python scraper script
- `.github/workflows/daily_bet_scraper.yml` - GitHub Actions workflow configuration
- `data/finished_bets.json` - Output JSON file with all scraped bets
- `data/finished_bets.csv` - Output CSV file with all scraped bets

## Data Format

Each bet entry contains:
- `match` - Teams playing (e.g., "Barcelona – Real Madrid")
- `prediction` - Bet prediction (e.g., "1" for home win, "2" for away win)
- `odds` - Decimal odds (e.g., "1.61")
- `result` - Empty (reserved for future use)
- `status` - "WON" ✅ or "LOST" ✖️
- `scraped_at` - ISO timestamp when the bet was scraped
- `source_url` - URL where the bet was scraped from
- `hash` - Unique MD5 hash for duplicate detection

## Local Testing

```bash
# Install dependencies
pip install requests beautifulsoup4

# Run the scraper
python3 bet_scraper.py

# View results
cat data/finished_bets.json
cat data/finished_bets.csv
```

## GitHub Actions Setup

1. Push these files to your GitHub repository
2. Go to the "Actions" tab in your repository
3. Enable GitHub Actions if not already enabled
4. The workflow will run automatically every day at 2:00 AM UTC
5. To test manually:
   - Go to Actions → "Daily Bet Scraper"
   - Click "Run workflow"
   - Wait for completion
   - Download the artifact with results

## Duplicate Prevention

The scraper maintains a `.seen_hashes.txt` file that tracks all previously scraped bets. Each bet is hashed using MD5 based on:
- Match teams
- Prediction
- Odds
- Status

This ensures that even if the same bet appears on multiple days, it will only be stored once.

## Sample Output

```json
[
  {
    "match": "Barcelona – Real Madrid",
    "prediction": "1",
    "odds": "1.61",
    "result": "",
    "status": "WON",
    "scraped_at": "2024-01-15T02:00:00.000000",
    "source_url": "https://combobets.com/football-predictions/most-popular-bets/",
    "hash": "47f7f9d712d3cadd152cc1008808dad4"
  }
]
```

## License

MIT
