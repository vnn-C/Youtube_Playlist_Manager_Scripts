import pandas as pd
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import BatchHttpRequest

#helper function for inserting a video into playlist, youtube credentials are one of the parameters
def insertVids(youtube, pId, vId, items):

#insert request: 50 units
    insertRequest = youtube.playlistItems().insert(
                part="snippet",
                body={
                "snippet": {
                    "playlistId": pId,
                    "position": 0,
                    "resourceId": {
                    "kind": "youtube#video",
                    "videoId": vId
                    }
                }
                }
            )

#try:catch statement for the insert request
    try:
        insertResponse = insertRequest.execute()
    except Exception as e:
        print(e)
        return []
            
    print("Song inserted into playlist")

#code for formatting video data for inserting into currPL
    i = items[0]
    itemId = i.get("id")
    snippet = i.get("snippet", {})
    contentDetails = i.get("contentDetails", {})
    categoryId = snippet.get("categoryId")
    channelId = snippet.get("channelId")
    title = snippet.get("title")
    tags = snippet.get("tags", [])

    videoData = {
        "videoId": vId,
        "title": title,
        "categoryId" : categoryId,
        "channelId" : channelId,
        "itemId" : itemId,
        "tags" : tags
    }

    return videoData

#retrieves the given playlist's items using pId
def getPlaylist(youtube, pId):

    print("Getting playlist\n")
    data = []
    genId = os.getenv("PLAYLIST_ID")
    nextPageToken = None
    rCounter = 0

#while loop executes the requests
#The requests are paginated to reduce the total number of requests
#Each request gets 50 playlit items at a time
#pageToken gets the nextPageToken in order for the request to get the next 50 playlist items in the playlist
    while True:

        #print("Request Counter: " + str(rCounter) + "\n")
#list request - 1 unit * # of playlist items
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=pId,                
            maxResults=50,
            pageToken=nextPageToken
        )

#try:catch statement for the request
        try:
            response = request.execute()
        except Exception as e:
            print("Playlist does not exist\n")
            return pd.DataFrame()
        

#code for formatting the response's items to insert into currPL
        items = response.get("items", [])

        if pId != genId:

#titleRequest will be used to retrieve the playlist's title            
            titleRequest = youtube.playlists().list(
                part="snippet",
                id=pId
            )

            titleResponse = titleRequest.execute()

            plTitle = titleResponse['items'][0]['snippet']['title']
            choice = input(f"Are you sure you want to add {plTitle}? y for yes or n for no.\n")
            if choice == "n":
                print("Playlist insertion cancelled")
                return pd.DataFrame()

#for loop inserts given playlist's items into the generated playlist
        for i in items:
            snippet = i.get("snippet", {})
            contentDetails = i.get("contentDetails", {})
            title = snippet.get("title")
            tags = snippet.get("tags", [])
            itemId = i.get("id")

#dataframe structure can be changed without affecting any preexisting stored versions
            data.append({
                "videoId": contentDetails.get("videoId"),
                "title": title,
                "channelId" : snippet.get("channelId"),
                "categoryId" : snippet.get("categoryId"),
                "itemId" : itemId,
                "tags" : tags
            })

        nextPageToken = response.get('nextPageToken')
        rCounter+=1

        if not nextPageToken:
            break        

    df = pd.DataFrame(data)

    return df

#inserts existing playlist's videos into the generated playlist
def insertPlaylist(youtube, currPL):

    temp = currPL
    playlistID = os.getenv("PLAYLIST_ID")
    quota = 0

    pId = input("Please insert the playlist id of the playlist you want to add\n")

#calls getPlaylist for the playlist to insert into the grenerated playlist    
    pData = getPlaylist(youtube, pId)

    print("Retrieving playlist")
    if pData.empty:
        return currPL
    
    print("Playlist retrieved")

#code for handling quota tracking
    quota = (50 * len(pData)) + len(pData)

    print("Inserting videos")

#successful loop will cost 51 units, unsuccessful loop will cost 1 unit
#For loop handles retrieved playlist items
    for idx, r in pData.iterrows():
        currPLRows = currPL.get("videoId").tolist()
        #print(currPLRows)
        rowId = r.get("videoId")
        rowTitle = r.get("title")
        rowChannel = r.get("channelId")
        playlistData = []
        
        #for debigging
       # print(f"To add: {rowId}, {rowTitle}\n")

        if rowId in currPLRows:
            print("Video is already in the palylist\n")
            continue

#video list request cost: 1 * # of videos in the playlist
#vidRequest handles inserting videos into the generated playlists
        vidRequest = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=rowId
        )

        vidResponse = vidRequest.execute()

        tags = r.get("tags") if isinstance(r.get("tags"), list) else []
        rowCategory = r.get("categoryId")

        vidItems = vidResponse.get("items", [])

        if vidItems == []:
            print("Video not found\n")
            continue

        tags = vidItems[0].get("tags") if isinstance(r.get("tags"), list) else []
        vidSnippet = vidItems[0].get("snippet", {})
        rowCategory = vidSnippet.get("categoryId")

#conditional for filtering out instrumentals, non-music, and off-vocal songs
#code generally assumes that the given playlist are dedicated towards albums or a collection of songs
        if (rowCategory == "10") and (
            "instrumental" not in rowTitle.lower() and "off-vocal" not in rowTitle.lower() and "off vocal" not in rowTitle.lower()
        ):
            print(f"{rowId}: {rowTitle} added\n")
#insert video into the playlist
#formatted video data for inserting into currPL is returned by insertVids
            vData = insertVids(youtube, playlistID, rowId, vidItems)

            playlistData.append(vData)
    newDf = pd.DataFrame(playlistData)

    temp = pd.concat([currPL, newDf], ignore_index = True)

    return temp

#inserts a single song into the generated palylist
#successful instance will cost 51 units 
def insertSong(youtube, currPL, pId):
    temp = currPL
    idList = currPL["videoId"].values
    newVid = input("Please insert the video id of the song you want to add\n")

#exits function if the given song's id is already in the generated playlist
    if newVid in idList:
        print("Video is already in the generated playlist\n")
        return currPL

#gets video using the given video id through a Youtube API request
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=newVid
    )

    try:
        response = request.execute()
    except Exception as e:
        print("Error in getting video\n")
        print(e)
        return currPL
    
    items = response.get("items", [])

    if items == []:
        print("Error: video id not found\n")
        return currPL
    
#Confirmation for inserting video into the generated playlist
    vidTitle = items[0]["snippet"]["title"]
    choice = input(f"Are you sure you want to add {vidTitle}? y for yes or n for no.\n")

    if choice == "n":
        print("Song insertion cancelled")
        return currPL
    
#inserts video into generated playlist
    insertRequest = youtube.playlistItems().insert(
        part="snippet",
        body={
          "snippet": {
            "playlistId": pId,
            "position": 0,
            "resourceId": {
              "kind": "youtube#video",
              "videoId": newVid
            }
          }
        }
    )

#try:catch statement for insertRequest
    try:
        insertResponse = insertRequest.execute()
    except Exception as e:
        print("Error in inserting video\n")
        print(e)
        return currPL
    
    print("Song inserted into playlist")

#Code formats the response of the request to retrieve the video to be inserted for inserting into currPL
    i = items[0]
    snippet = i.get("snippet", {})
    itemId = i.get("id")
    contentDetails = i.get("contentDetails", {})
    categoryId = snippet.get("categoryId")
    title = snippet.get("title")
    tags = snippet.get("tags", [])
    channelId = snippet.get("channelId")
            

    newRow = []
    newRow.append({
        "videoId": newVid,
        "title": title,
        "categoryId" : categoryId,
        "channelId" : channelId,
        "itemId" : itemId,
        "tags" : tags
     })

    newDf = pd.DataFrame(newRow)

    temp = pd.concat([currPL, newDf], ignore_index = True)

    return temp

#prints playlist items, returns two dictionaries of video titles and video ids for delete function's use
def printPlaylist(playlist):
    idHash = dict()
    vidHash = dict()
    for idx, row in playlist.iterrows():
        title = row["title"]
        print(f"Video #{idx}: {title}")
        idHash[idx] = row["itemId"]
        vidHash[idx] = title
    
    return idHash, vidHash
#Function requires data on the playlist item's position in the playlist?
#TODO: Started May 17, 2025 Add Delete functionality. - Done
#Playlist Item IDs for every video is already stored in CurrPL
#Delete Request Body does not need the playlist's ID

#deletes video from generated playlist
def deleteFromPlaylist(youtube, currPL):
    genId = os.getenv("PLAYLIST_ID")
    idHash, vidHash = printPlaylist(currPL)
    delChoice = input("Enter the video number of the video you want to delete or press x to exit:\n")

    if delChoice == "x":
        print("Exiting video deletion...\n")
        return currPL
    elif int(delChoice) in idHash.keys():
        delConfirm = input(f"Are you sure you want to delete {vidHash[int(delChoice)]}?\ny for yes\nn for no\n")
        if delConfirm == "y":
            try:
                request = youtube.playlistItems().delete(
                    id=idHash[int(delChoice)]
                )
                request.execute()
                currPL = currPL[currPL["itemId"] != idHash[int(delChoice)]]
            except Exception as e:
                print(f"Error with deleting video\n{e}")
            
            print("Successfully deleted video\n")
            
    else:
        print("Video not found.\nExiting video deletion...\n")
    
    print("Returning to main page...\n")
    return currPL