#!/usr/bin/env python3
"""
Daily Football Bet Scraper for ComboBets.com
Scrapes finished bets from the "Top Soccer Bets • Latest Results" list.
Stores results in JSON and CSV formats, avoiding duplicates.
Designed to run on GitHub Actions daily.
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import hashlib
import os
from datetime import datetime
from pathlib import Path

# Configuration
URL = "https://combobets.com/football-predictions/most-popular-bets/"
DATA_DIR = Path("data")
JSON_FILE = DATA_DIR / "finished_bets.json"
CSV_FILE = DATA_DIR / "finished_bets.csv"
SEEN_FILE = DATA_DIR / ".seen_hashes.txt"

def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)

def load_seen_hashes():
    """Load previously seen bet hashes to avoid duplicates."""
    if SEEN_FILE.exists():
        with open(SEEN_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_seen_hashes(seen_hashes):
    """Save seen bet hashes."""
    with open(SEEN_FILE, 'w') as f:
        for hash_val in seen_hashes:
            f.write(hash_val + '\n')

def generate_bet_hash(match, prediction, odds, status):
    """Generate a unique hash for a bet to detect duplicates."""
    bet_string = f"{match}|{prediction}|{odds}|{status}"
    return hashlib.md5(bet_string.encode('utf-8')).hexdigest()

def parse_bet_status(text_content):
    """Convert emoji in text to status string."""
    # Check if text contains check or cross emoji directly
    if '✅' in text_content or '✓' in text_content:
        return "WON"
    elif '✖️' in text_content or '✗' in text_content or '❌' in text_content:
        return "LOST"
    else:
        return "UNKNOWN"

def scrape_bets():
    """Scrape finished bets from the website."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the specific unordered list containing the bets
    # Looking for <ul class="wp-block-list"> with bet items
    bet_list = soup.find('ul', class_='wp-block-list')
    
    if not bet_list:
        print("Could not find bet list on the page")
        return []
    
    bets = []
    list_items = bet_list.find_all('li')
    
    print(f"Found {len(list_items)} bet items")
    
    for li in list_items:
        # Extract text content and clean it
        text_content = li.get_text(strip=True)
        
        # Parse status from emoji in text
        status = parse_bet_status(text_content)
        
        match_info = text_content
        
        # Parse match details
        # Expected format: "Team A – Team B: Prediction @ Odds"
        if ':' in match_info and '@' in match_info:
            try:
                # Split by colon to separate teams from prediction
                teams_part, pred_part = match_info.rsplit(':', 1)
                teams = teams_part.strip()
                
                # Split prediction part by @ to get prediction and odds
                if '@' in pred_part:
                    pred_odds_part = pred_part.strip()
                    # Find the last @ symbol to separate odds from emoji
                    # The format is "1 @ 1.86 ✖️" so we need to clean the emoji from odds
                    prediction, odds_with_emoji = pred_odds_part.rsplit('@', 1)
                    prediction = prediction.strip()
                    
                    # Clean the odds - remove emojis
                    odds_raw = odds_with_emoji.strip()
                    # Remove any non-numeric characters except dot (for decimal odds)
                    import re
                    odds = re.sub(r'[^\d.]', '', odds_raw.split()[0] if ' ' in odds_raw else odds_raw)
                    
                    bet_data = {
                        'match': teams,
                        'prediction': prediction,
                        'odds': odds,
                        'result': '',
                        'status': status,
                        'scraped_at': datetime.now().isoformat(),
                        'source_url': URL
                    }
                    
                    # Generate hash for duplicate detection
                    bet_hash = generate_bet_hash(
                        bet_data['match'],
                        bet_data['prediction'],
                        bet_data['odds'],
                        bet_data['status']
                    )
                    bet_data['hash'] = bet_hash
                    
                    bets.append(bet_data)
                    
            except Exception as e:
                print(f"Error parsing bet: {match_info}, Error: {e}")
                continue
    
    return bets

def load_existing_bets():
    """Load existing bets from JSON file."""
    if JSON_FILE.exists():
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_bets_json(bets):
    """Save all bets to JSON file."""
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(bets, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(bets)} bets to {JSON_FILE}")

def save_bets_csv(bets):
    """Save all bets to CSV file."""
    if not bets:
        return
    
    fieldnames = ['match', 'prediction', 'odds', 'result', 'status', 'scraped_at', 'source_url', 'hash']
    
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(bets)
    
    print(f"Saved {len(bets)} bets to {CSV_FILE}")

def main():
    """Main function to run the scraper."""
    print(f"Starting bet scraper at {datetime.now().isoformat()}")
    print(f"Scraping URL: {URL}")
    
    ensure_data_dir()
    
    # Load existing data
    existing_bets = load_existing_bets()
    seen_hashes = load_seen_hashes()
    
    print(f"Loaded {len(existing_bets)} existing bets")
    print(f"Loaded {len(seen_hashes)} seen hashes")
    
    # Scrape new bets
    new_bets = scrape_bets()
    print(f"Scraped {len(new_bets)} new bets from website")
    
    if not new_bets:
        print("No bets found or error occurred during scraping")
        return
    
    # Filter out duplicates
    unique_new_bets = []
    for bet in new_bets:
        if bet['hash'] not in seen_hashes:
            unique_new_bets.append(bet)
            seen_hashes.add(bet['hash'])
    
    print(f"Found {len(unique_new_bets)} unique new bets (filtered {len(new_bets) - len(unique_new_bets)} duplicates)")
    
    if unique_new_bets:
        # Combine with existing bets
        all_bets = existing_bets + unique_new_bets
        
        # Save updated data
        save_bets_json(all_bets)
        save_bets_csv(all_bets)
        save_seen_hashes(seen_hashes)
        
        print(f"\nSummary:")
        print(f"  Total bets in database: {len(all_bets)}")
        print(f"  New bets added: {len(unique_new_bets)}")
        
        # Print sample of new bets
        print(f"\nSample of new bets:")
        for i, bet in enumerate(unique_new_bets[:5]):
            print(f"  {i+1}. {bet['match']} - {bet['prediction']} @ {bet['odds']} [{bet['status']}]")
    else:
        print("No new unique bets to add")

if __name__ == "__main__":
    main()
