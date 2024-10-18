import requests
import json
import os
import logging

PLAYLIST_ID = "PLUp1t9SPBl6rKXX4uAYsmEZyBlGwKE6Tl"
PLAYLIST_ID_2 = "PLUp1t9SPBl6qrPT_W79HOeR6_n-hWsAbk"
PLAYLIST_ID_3 = "PLUp1t9SPBl6r4nqsQBg7HH7fPX2l9AGQk"
PLAYLIST_ID_4 = "PL1NeGg1woXqm0sfUXRVzr6srqOpMNPZDE"

PLAYLIST_URLS = [PLAYLIST_ID, PLAYLIST_ID_2, PLAYLIST_ID_3, PLAYLIST_ID_4]
SAVE_PATH = "data/music/titles.json"

logger = logging.getLogger('logo')

if not os.path.exists(os.path.dirname(SAVE_PATH)):
    os.makedirs(os.path.dirname(SAVE_PATH))

def load_titles_from_json(save_path):
    if not os.path.exists(save_path):
        return []
    
    with open(save_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("videos", [])

def save_titles_to_json(titles, save_path):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump({"videos": titles}, f, ensure_ascii=False, indent=4)
    
    print(f"Titles saved to {save_path}")

def scrape_playlist_titles_with_api(playlist_id, api_key):
    titles = []
    next_page_token = None
    
    while True:
        url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlist_id}&key={api_key}"
        if next_page_token:
            url += f"&pageToken={next_page_token}"
        
        response = requests.get(url)
        logger.debug(f"Successfully retrieved playlist: {playlist_id}")
        if response.status_code != 200:
            logger.debug(f"Failed to retrieve playlist: {response.status_code}")
            return []
        
        items = response.json().get("items", [])
        for item in items:
            title = item["snippet"]["title"]
            titles.append(title)
        
        next_page_token = response.json().get("nextPageToken")
        if not next_page_token:
            break
    
    print(titles)
    return titles