import pandas as pd
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import BatchHttpRequest
from PlaylistItems import insertVids, insertPlaylist, getPlaylist

#Unit costs for Youtube API operations
LIST_QUOTA = 1
INSERT_QUOTA = 50

def getLikedVids(youtube, currIDs):
    nextPageToken = None
    data = []
#newQuota stores the estimated amount of units inserting the liked videos into the generated playlist will take
    newQuota = 0
#vidCount stores the position of the current video in the liked videos playlist
    vidCount = 1

#while loop runs until the request can no longer retrieve the next page of the liked video playlist
    while True:
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like",
            maxResults=50,
            pageToken=nextPageToken
            
        )

        response = request.execute()
        newQuota += 1

        items = response["items"]

#for loop goes over every video in the liked videos playlist
        for i in items:

            print(f"Video #{vidCount}\n")
            

            itemId = ""
            snippet = i.get("snippet", {})
            contentDetails = i.get("contentDetails", {})
            categoryId = snippet.get("categoryId")
            channelId = snippet.get("channelId")
            vId = i.get("id")
            title = snippet.get("title")
            tags = snippet.get("tags", [])
            desc = snippet.get("description")
            cTitle = snippet.get("channelTitle")


            

#filters out video that are not songs, filtering is not perfect
#TODO: Change filter conditionals to include a pormpt for music videos that cannot be verified - Done

            #if video is not music
            if categoryId != "10":
                print(f"Video #{vidCount} is not likely music\n")
            #if video is already in the playlist
            elif vId in currIDs:
                print(f"Video # {vidCount} is already in the playlist\n")
            else:
                vidChoice = input(f"Do you want to input {title} by {cTitle}? y for yes or n for no.\n URL: https://www.youtube.com/watch?v={vId}\n")
                if vidChoice == "y":
                    data.append({
                            "videoId": vId,
                            "title": title,
                            "categoryId" : categoryId,
                            "channelId" : channelId,
                            "itemId" : itemId,
                            "tags" : tags
                            })
                    
                else:
                    print(f"Video # {vidCount} not added\n")
            vidCount += 1

#The Tag filtering conditional might be causing the false positives in the liked video insertion

            """
            elif (
                " ost " not in title.lower() and "soundtrack" not in title.lower()
                ) and (
                all((" ost " not in t.lower() and t.lower != "ost") for t in tags)
                 and (
                all(("soundtrack" not in s.lower() and s.lower != "soundtrack") for s in tags))
                ) and (
                    "orchestra" not in title.lower()
                ) and (
                    "lofi" not in title.lower()
                ) and (
                    all("bgm" not in t.lower() for t in tags) and "bgm" not in title.lower()
                ) and (
                    all("video game music" not in t.lower() for t in tags)
                ) and (
                    "instrumental" not in title.lower()
                ) and ("off-vocal" not in title.lower() and "off vocal" not in title.lower()
                ) and (
                    vId not in currIDs
                ):
                    if tags != []:
                        data.append({
                            "videoId": vId,
                            "title": title,
                            "categoryId" : categoryId,
                            "channelId" : channelId,
                            "itemId" : itemId,
                            "tags" : tags
                            })
                        vidCount += 1
                    else:
                        noTagChoice = input(f"Do you want to input {title} by {cTitle}? y for yes or n for no.\n ID: {vId}")

                        if noTagChoice == "y":
                            data.append({
                            "videoId": vId,
                            "title": title,
                            "categoryId" : categoryId,
                            "channelId" : channelId,
                            "itemId" : itemId,
                            "tags" : tags
                            })
                            vidCount += 1
            else:
                print(f"Video # {vidCount} skipped\n")"""
#TODO: Filtering code that does not check the video's tags - Done, Works successfully without false positives
            
        nextPageToken = response.get("nextPageToken")
        if not nextPageToken:
            break


    likedVids = pd.DataFrame(data)

    return [likedVids, newQuota]

#inserts liekd videos into playlist
def insertLikedVids(youtube, currPL, quota):
    expectedCost = 0
    currQuota = quota
    currPLRows = currPL.get("videoId").tolist()
    addedVids = []
    genId = os.getenv("PLAYLIST_ID")
    idMap = {}
    getLikedRes = getLikedVids(youtube, currPLRows)    
    vidCount = 0

#Increments currQuota with the estimated quota from getLikedRes
    currQuota += getLikedRes[1]
    likedPL = getLikedRes[0]

    expectedCost = 50 * len(likedPL)

#Informs user of the estimated quota cost. The function will run into a quota error if this value exceeds 10,000, omitted for now
    """choice = input(f"The expected cost for this operation is {expectedCost} units. Your current quota is {currQuota}. Do you want to continue?\ny for yes or n for no?\n")
    if choice == "n":
        print("Operation cancelled\n")
        return currPL   
    """
#inserts filtered liked videos into the playlist
        
    for index, row in likedPL.iterrows():
        vId = row.get("videoId")
        print(f"Adding Video # {vidCount}")
        vidCount += 1

        #If statement checks if the video to be inserted into the playlist is already there
        if vId in currPLRows:
            print("Video is already in playlist. Skipping\n")
            continue
            #insert request: 50 units
            
        else:
            insertRequest = youtube.playlistItems().insert(
                        part="snippet",
                        body={
                        "snippet": {
                            "playlistId": genId,
                            "position": 0,
                            "resourceId": {
                            "kind": "youtube#video",
                            "videoId": vId
                            }
                        }
                        }
                    )

            try:
                insertResponse = insertRequest.execute()
            except Exception as e:
                temp = pd.concat([currPL, likedPL], ignore_index = True)
                return temp
            addedVids.append(vId)

#retrives the updated generated songs playlist           
    newPL = getPlaylist(youtube, genId)

#Merges the current playlist with the new liked videos added from the new playlist without running into any conflicts with playlist item ids
#Playlist item ids determine the video's position in the playlist
    for idx, row in newPL.iterrows():
        likedId = row.get("videoId")
        itemId = row.get("itemId")
        idMap[likedId] = itemId
        #if likedId not in currPLRows:
            #item = newPL.loc(newPL["videoId"] == likedId)
            #itemId = item.get("itemId")
            #idMap.append({likedId : itemId})
    likedPL["itemId"] = likedPL["videoId"].map(idMap)


    temp = pd.concat([currPL, likedPL], ignore_index = True)
    return temp

#gets a video's tags given a video id, for debugging only
def getTags(youtube, currPL):
    currPLRows = currPL.get("videoId").tolist()
    genId = os.getenv("PLAYLIST_ID")
    vId = input("Please enter the id of the video you want the tags from\n")

#request gets the given video's information based on the given id
    vidRequest = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=vId
        )
    
    vidResponse = vidRequest.execute()
    vidItems = vidResponse.get("items", [])

    if vidItems == []:
        print("Video not found\n")
        return -1

#retrieves necessary information from the request's response  
    vidSnippet = vidItems[0].get("snippet", {})
    tags = vidSnippet.get("tags", [])
    vidTitle = vidItems[0]["snippet"]["title"]

#videos can have no tags
    if tags == []:
        print(f"{vidTitle} has no tags")

    print(f"{vidTitle}'s tags:\n")
    for t in tags:
        print(t)
    return 0