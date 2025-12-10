import requests
import json
import argparse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dateutil import parser
import pytz

def fetch_matches_from_wikipedia(url):
    print(f"Fetching matches from Wikipedia page: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Wikipedia page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    matches = []
    tables = soup.find_all("table", {"class": "vevent"})
    
    for table in tables:
        try:
            date_str = table.find("th", {"class": "dtstart"}).get("title")  
            date = parser.parse(date_str)

            teams = table.find_all("span", {"class": "fn"})
            home = teams[0].get_text(strip=True) if len(teams) > 0 else ""
            away = teams[1].get_text(strip=True) if len(teams) > 1 else ""

            score_tag = table.find("td", {"class": "score"})
            score = score_tag.get_text(strip=True) if score_tag else "vs"

            match = {
                "date": date.isoformat(),
                "home": home,
                "away": away,
                "score": score
            }
            matches.append(match)
        except:
            continue

    return matches


def group_matches(matches, timezone_str):
    tz = pytz.timezone(timezone_str)
    today = datetime.now(tz).date()

    data = {
        "yesterday": [],
        "today": [],
        "tomorrow": [],
        "generated_at": datetime.now(tz).isoformat()
    }

    for match in matches:
        match_date = parser.parse(match["date"]).astimezone(tz).date()

        if match_date == today:
            data["today"].append(match)
        elif match_date == today - timedelta(days=1):
            data["yesterday"].append(match)
        elif match_date == today + timedelta(days=1):
            data["tomorrow"].append(match)

    return data


def main():
    parser_arg = argparse.ArgumentParser()
    parser_arg.add_argument("--config", required=True)
    parser_arg.add_argument("--output", required=True)
    args = parser_arg.parse_args()

    with open(args.config, "r") as f:
        cfg = json.load(f)

    wiki_url = cfg["wikipedia_page"]
    timezone = cfg["timezone"]

    matches = fetch_matches_from_wikipedia(wiki_url)
    print(f"Fetched {len(matches)} matches")

    grouped = group_matches(matches, timezone)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(grouped, f, indent=4, ensure_ascii=False)

    print(f"Saved updated matches to {args.output}")


if __name__ == "__main__":
    main()
