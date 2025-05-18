import pandas as pd
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from dotenv import load_dotenv, dotenv_values
import LikedVids
import PlaylistItems
import webbrowser

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

#TODO Started at 5/17/2025: Configure script to open Google Chrome for authentication. Problem: The authentication opens in Microsoft Edge by default
#Could not accomplish due to how flow.run_local_server() works. Changing the default browser to Google Chrome in Settings can resolve the problem

    chrome_path = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
    try:
        webbrowser.register("chrome", None, webbrowser.BackgroundBrowser(chrome_path))
        chrome_browser = webbrowser.get("chrome")
    except webbrowser.Error:
        print(f"Error: Could not open Google Chrome browser")
        chrome_browser = None

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)

#flow.run_local_server is not present in the Youtube API's code sample, this code was changed to allow the script to run on a laptop
    credentials = flow.run_local_server(port=0, open_browser=True)
    #flow.run_local_console does not work
    #credentials = flow.run_console(authorization_code_message='Enter the authorization code: ')

    #if chrome_browser:
    #    chrome_browser.open_new(flow.redirect_uri)
    #else:
    #    webbrowser.open_new(flow.redirect_uri)

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
        choice = input("Welcome: Select an option:\nv - view playlist items\nu - add new song\np - add song playlist\nl - update playlist with new liked videos\nd - delete song from playlist\nx- exit\n")

        #exit app
        if choice == "x":
            return 0
        #display playlist items
        elif choice == "v":
            print("Displaying playlist items:\n")
            idHash, vidHash = PlaylistItems.printPlaylist(currPL)
            print("Returning to main page...\n")
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
            currPL = PlaylistItems.deleteFromPlaylist(youtube, currPL)
            #return 0
        #searching for video tags for debugging
        #elif choice == "t":
            #LikedVids.getTags(youtube, currPL)
main()