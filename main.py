from dotenv import load_dotenv
from os import getenv
from requests import post, get
from datetime import datetime, timedelta
import subprocess

load_dotenv()

client_id = getenv("CLIENT_ID")
client_secret = getenv("CLIENT_SECRET")
spotify_api_url = "https://accounts.spotify.com/api/token"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = (
    f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"
)


class Token:
    def __init__(
        self,
        val,
        exp_time,
        type,
    ):
        self.value = val
        self.type = type
        self.expires_at = exp_time

    def __str__(self):
        return self.value + "\n" + self.expires_at.isoformat() + "\n" + self.type

    def call(self, dir, id):
        uri = f"https://api.spotify.com/v1/{dir}/{id}"
        header = {"Authorization": f"{self.type} {self.value}"}
        return get(uri, headers=header)


def queryAuthToken() -> Token:
    response = post(spotify_api_url, data=data, headers=headers).json()
    token = response["access_token"]
    time = datetime.now() + timedelta(seconds=response["expires_in"])
    type = response["token_type"]
    token = Token(token, time, type)

    return token


def writeToken(token: Token):
    f = open("auth.txt", "w+")
    f.writelines([token.value, "\n", token.expires_at.isoformat(), "\n", token.type])
    f.close()


def getAuthToken() -> Token:
    token = None

    try:
        f = open("auth.txt", "r")
        lines = f.readlines()

        assert len(lines) == 3

        for i in range(0, 3):
            lines[i] = lines[i].strip("\n")

        token = Token(lines[0], lines[1], lines[2])

        token.expires_at = datetime.fromisoformat(token.expires_at)

        if token.expires_at < datetime.now():
            print("Auth token has expired, querying new token...")

            token = queryAuthToken()

            writeToken(token)
            
            print("New token: ", token)
        else:
            print("Token found:", token, sep="\n")

        f.close()

    except FileNotFoundError:
        print("file not found, querying new auth token...")

        token = queryAuthToken()
        print(token.value, token.expires_at, token.type, sep="\n")

        writeToken(token)
    except Exception as e:
        print("Oh no, different error!")
        print(e, e.__traceback__)

        exit(-1)

    return token


auth_token = None

if __name__ == "__main__":
    path = input("Where would you like to store the playlist: ")
    playlist_id = input("Enter playlist id: ")
    
    auth_token = getAuthToken()
    playlist = auth_token.call("playlists", playlist_id).json()

    for track in playlist["tracks"]["items"]:
        success = subprocess.run(["yt-dlp", "-x", "--audio-format", "wav", "-P", path, f"ytsearch:{track["track"]["name"]} {track["track"]["artists"][0]["name"]}"])
        
        if success.returncode != 0:
            print(f"subprocess.run exited with code {success.returncode}!")
            exit(success.returncode)
        
