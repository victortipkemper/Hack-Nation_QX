#!/usr/bin/env python3
"""
Pipeline script to retrieve and store all relevant StVZO legal texts.
"""
import os
import sys
import time

# Ensure api directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from data.get_legal_text import get_legal_text

# The list of all required StVZO paragraphs requested by the user
PARAGRAPHS = sorted(list(set([
    # § 21 StVZO in Verbindung mit § 19 (2) StVZO
    "19", "21",
    # Fahrzeugbeschaffenheit, Maße und Gewichte
    "30", "30a", "30b", "30c", "32", "32b", "32d", "34",
    # Innenausstattung und Karosserie
    "35a", "35b", "35c", "35d", "35e", "40",
    # Fahrwerk, Lenkung und Bremsen
    "36", "36a", "38", "41", "41a", "41b",
    # Sicherheitseinrichtungen und Anlagen
    "38a", "38b", "39", "42", "43", "44", "45", "46",
    # Umwelt, Licht und Akustik
    "47", "47c", "47d", "47e", "48", "49", "49a",
    # Lighting systems (50ff range + 39a)
    "39a", "50", "51", "51a", "51b", "51c", "52", "52a", "53", "53a", "53b", "53c", "53d", "54", "54a", "54b",
    # Elektronik, Anzeigen und Kennzeichnung
    "55", "55a", "56", "57", "57a", "58", "59", "60", "62"
])))


def main():
    assets_dir = os.path.join(current_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    print(f"Retrieving {len(PARAGRAPHS)} StVZO legal texts into {assets_dir}...")
    
    success_count = 0
    failure_count = 0
    
    for i, p in enumerate(PARAGRAPHS, 1):
        url = f"https://www.gesetze-im-internet.de/stvzo_2012/__{p}.html"
        filename = f"stvzo_{p}.txt"
        filepath = os.path.join(assets_dir, filename)
        
        print(f"[{i}/{len(PARAGRAPHS)}] Fetching § {p} from {url}...")
        
        try:
            text = get_legal_text(url)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"  Saved to {filename} ({len(text)} characters)")
            success_count += 1
        except Exception as e:
            print(f"  ERROR fetching § {p}: {e}", file=sys.stderr)
            failure_count += 1
            
        # Add a small delay to be polite to the host server and avoid rate-limiting
        time.sleep(0.25)
        
    print("\nRetrieval completed.")
    print(f"Successfully retrieved: {success_count}/{len(PARAGRAPHS)}")
    if failure_count > 0:
        print(f"Failed: {failure_count}/{len(PARAGRAPHS)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
