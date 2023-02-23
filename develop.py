from spotdl import Spotdl

TEST_URL_1 = 'https://open.spotify.com/track/4cQSmw5ZwXXh8mJCa5L42S'
TEST_URL_2 = 'https://open.spotify.com/album/4VzzEviJGYUtAeSsJlI9QB?highlight=spotify:track:6QgjcU0zLnzq5OrUoSZ3OK'  # non funziona con spotdl
TEST_URL_3 = 'https://open.spotify.com/album/1IduB3mfHISAtpV1zQHpef?si=VoaJHvv-SD-EOkq2XvZ5Xw'  # restituisce una lista di url, una per traccia
TEST_URL_4 = 'https://open.spotify.com/track/56evvdIIJ3wVuBbeNm3ckS?si=wBMGfKEqSomjVwawWYVjJQ'
TEST_URL_5 = 'https://open.spotify.com/track/2DtXBP9JLhsCEBexYKgHKQ'

# Questi erano dentro il codice di spotdl
client_id = "5f573c9620494bae87890c0f08a60293"
client_secret = "212476d9b0f3472eaa762d90b19b0ba8"

spotdl = Spotdl(client_id, client_secret)

url = TEST_URL_2
if 'album' in url and 'spotify:track:' in url:
    song_uid = url.split('spotify:track:')[-1]
    url = f"https://open.spotify.com/track/{song_uid}"

songs = spotdl.search([url])

results = spotdl.get_download_urls(songs)

print(results)