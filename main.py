import pandas as pd
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from dotenv import load_dotenv, dotenv_values
import LikedVids
import PlaylistItems

load_dotenv()

#Specific scope allows read and write access
scopes = ["https://www.googleapis.com/auth/youtube"]

#code for command line app 
def main():
#currPL stores a copy of the generated songs list
#quota stores the current amount of used quota units, maximum is 10,000 units
#For the Future: store quota count between sessions in a manner that resets the quota to 0 every day, perferably done without relying on local storage
    currPL = pd.DataFrame()
    quota = 0
    playlistID = os.getenv("PLAYLIST_ID")
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

#Code for credentials for Youtube API, done on browser, DEVELOPER_KEY, playlistID and client_secrets_file are stored in the .env file
    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = os.getenv("API_KEY")
    client_secrets_file = os.getenv("CLIENT_SECRET")  
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
#flow.run_local_server is not present in the Youtube API's code sample, this code was changed to allow the script to run on a laptop
    credentials = flow.run_local_server(port=0)
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials, developerKey=DEVELOPER_KEY)

#retrieves the generated song playlist when the script starts without storing it locally
    currPL = PlaylistItems.getPlaylist(youtube, playlistID)

    print("Playlist retrieved")
    dfLen = len(currPL)
    print(f"Number of videos in the playlist: {dfLen}")

    if DEVELOPER_KEY == None:
        print("Failed to retrieve API key")
        return -1
    if client_secrets_file == None:
        print("Failed to retrieve client secret")
        return -1
    if playlistID == None:
        print("Failed to retrieve playlist ID")
        return -1

    quota += len(currPL)
    prevLen = len(currPL)

#While loop for decision-making part of the code
    while True:
        choice = input("Welcome: Select an option:\nu - add new song\np - add song playlist\nl - update playlist with new liked videos\nd - delete song from playlist\nx- exit\n")

        #exit app
        if choice == "x":
            return 0
        #add new song to the generated playlist
        elif choice == "u":
            currPL = PlaylistItems.insertSong(youtube, currPL, playlistID)
        #add song playlist's videos to the generated playlist
        elif choice == "p":
            currPL = PlaylistItems.insertPlaylist(youtube, currPL)
        #adds liked video list's videos to the generated playlist
        elif choice == "l":
            currPL = LikedVids.insertLikedVids(youtube, currPL, quota)
        #deletes a song from the playlist, scrapped since it would likely increase the quota usage needlessly
        elif choice == "d":
            print("The delete function is currently not implemented\n")
            #return 0
        #searching for video tags for debugging
        #elif choice == "t":
            #LikedVids.getTags(youtube, currPL)
main()