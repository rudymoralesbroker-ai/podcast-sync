# -*- coding: utf-8 -*-
import requests
import base64
import json
from datetime import datetime

# ============================================================
# CONFIGURACION - todas las credenciales
# ============================================================
SPOTIFY_CLIENT_ID     = "2bd0951b432443a5a8e65bd2a333511f"
SPOTIFY_CLIENT_SECRET = "db30251f3627468db8fee35cc1e49eab"
SPOTIFY_SHOW_ID       = "033wCDhVHmDHll9SCmoCbf"

YOUTUBE_API_KEY    = "AIzaSyDsdwOYkzmdYBT4pYxJSm7yLQDkxsSrjFg"
YOUTUBE_CHANNEL_ID = "UC1njuK204SUHxpiiqorEZ3w"

WP_URL          = "https://rudymoralesbroker.com"
WP_USERNAME     = "claude-temp"
WP_APP_PASSWORD = "syuq 4KTA tehK VZul Iw4p wWhr"

# ============================================================
# SPOTIFY: Obtener token automaticamente (no requiere login)
# ============================================================
def get_spotify_token():
    credentials = base64.b64encode(
        "{}:{}".format(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET).encode("utf-8")
    ).decode("utf-8")
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": "Basic {}".format(credentials),
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"}
    )
    response.raise_for_status()
    return response.json()["access_token"]

# ============================================================
# SPOTIFY: Obtener ultimo episodio del podcast
# ============================================================
def get_latest_spotify_episode(token):
    response = requests.get(
        "https://api.spotify.com/v1/shows/{}/episodes".format(SPOTIFY_SHOW_ID),
        headers={"Authorization": "Bearer {}".format(token)},
        params={"limit": 10}
    )
    response.raise_for_status()
    items = [item for item in response.json().get("items", []) if item is not None]
    if not items:
        raise Exception("No se encontraron episodios en Spotify")
    return items[0]

# ============================================================
# YOUTUBE: Obtener ultimo video del canal
# ============================================================
def get_latest_youtube_video():
    response = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params={
            "channelId": YOUTUBE_CHANNEL_ID,
            "part": "snippet",
            "order": "date",
            "maxResults": 1,
            "type": "video",
            "key": YOUTUBE_API_KEY
        }
    )
    response.raise_for_status()
    items = response.json().get("items", [])
    if not items:
        raise Exception("No se encontraron videos en YouTube")
    return items[0]

# ============================================================
# WORDPRESS: Crear post con ambos embeds
# ============================================================
def create_wordpress_post(episode, video):
    title       = episode["name"]
    description = episode.get("description", "")
    spotify_id  = episode["id"]
    youtube_id  = video["id"]["videoId"]

    spotify_embed = (
        '<iframe style="border-radius:12px" '
        'src="https://open.spotify.com/embed/episode/{}" '
        'width="100%" height="232" frameBorder="0" allowfullscreen="" '
        'allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture">'
        '</iframe>'
    ).format(spotify_id)

    youtube_embed = (
        '<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;">'
        '<iframe style="position:absolute;top:0;left:0;width:100%;height:100%;" '
        'src="https://www.youtube.com/embed/{}" '
        'frameborder="0" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
        'allowfullscreen></iframe>'
        '</div>'
    ).format(youtube_id)

    content = """
<p>{description}</p>

<h3>Escucha en Spotify:</h3>
{spotify}

<h3>Mira en YouTube:</h3>
{youtube}

<p><strong>Siguenos:</strong></p>
<ul>
  <li><a href="https://open.spotify.com/show/{show_id}" target="_blank">Spotify Podcast</a></li>
  <li><a href="https://youtube.com/channel/{channel_id}" target="_blank">YouTube</a></li>
</ul>
""".format(
        description=description,
        spotify=spotify_embed,
        youtube=youtube_embed,
        show_id=SPOTIFY_SHOW_ID,
        channel_id=YOUTUBE_CHANNEL_ID
    )

    response = requests.post(
        "{}/wp-json/wp/v2/posts".format(WP_URL),
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        json={
            "title":   title,
            "content": content,
            "status":  "publish"
        }
    )
    response.raise_for_status()
    return response.json()

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("[{}] Iniciando sincronizacion...".format(datetime.now().strftime("%Y-%m-%d %H:%M")))

    try:
        print("Obteniendo token de Spotify...")
        token = get_spotify_token()

        print("Obteniendo ultimo episodio de Spotify...")
        episode = get_latest_spotify_episode(token)
        print("  Episodio: {}".format(episode["name"]))

        print("Obteniendo ultimo video de YouTube...")
        video = get_latest_youtube_video()
        print("  Video: {}".format(video["snippet"]["title"]))

        print("Publicando en WordPress...")
        post = create_wordpress_post(episode, video)
        print("Post publicado: {}".format(post["link"]))

    except requests.HTTPError as e:
        print("Error HTTP {}: {}".format(e.response.status_code, e.response.text))
        raise
    except Exception as e:
        print("Error: {}".format(e))
        raise
