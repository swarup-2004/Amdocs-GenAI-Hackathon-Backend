def scrape_youtube(topic):
    url = f"https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{topic} courses",
        "type": "playlist",
        "maxResults": 5,
        "key": YOUTUBE_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        playlists = []
        for item in data.get("items", []):
            playlist = {
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/playlist?list={item['id']['playlistId']}"
            }
            playlists.append(playlist)
        return playlists
    else:
        print("Error fetching YouTube data:", response.text)
        return []
