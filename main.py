from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from fastapi.staticfiles import StaticFiles
from deta import Deta
import logging as log
import asyncio
import uuid
import time
import httpx
from operator import itemgetter
import secrets
import string
import os
from models import *
from config import *

log.basicConfig(level=log.INFO)

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# For Local Dev Throw Deta Project Key in .detakey
if os.path.isfile(".detakey"):
    with open(".detakey") as projectkey_file:
        projectkey = projectkey_file.read()
        deta = Deta(projectkey)
else:
    deta = Deta()
    
db = deta.Base(dbname)

def get_my_key():
    try:
        my_key_obj = db.get('my_key')
        private_key = my_key_obj['value']
    except TypeError:
        log.warning("No Private Key Exists! Creating key")
        created_key = uuid.uuid4().hex
        db.put({'key': 'my_key', 'value': created_key})
        private_key = created_key
        
    return private_key

def get_my_name():
    try:
        name_obj = db.get('my_name')
        username = name_obj['value']
    except:
        username = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        db.put({'key': 'my_name', 'value': username})
        
    return username

# Grab Personal Info to Keep it Handy
private_key = get_my_key()
username = get_my_name()

async def get_posts(name):
    friend = next(db.fetch({'name': name,'category': 'friend'}))
    key = friend[0]['key']
    bridge = friend[0]['bridge']
    posts_endpoint = f"https://{bridge}.deta.dev/shared-posts"
    params = {'access_key': key}
    
    async with httpx.AsyncClient() as client:
        friend_posts = await client.get(posts_endpoint, params=params)
    
    return friend_posts.json()

def check_usernames(friends):
    detected_change = False
    for friend in friends:
        stored_username = friend['name']
        bridge = friend['bridge']
        nameURL = f"https://{bridge}.deta.dev/my-name"
        latest_username = httpx.get(nameURL)
        new_name = latest_username.json()['name']

        if stored_username != new_name:
            db.update({'name': new_name, 'value': 'notified'}, friend['key'])
            detected_change = True

    return detected_change

async def get_posts_from_friend(friend):
    name = friend['name']
    key = friend['key']
    bridge = friend['bridge']
    posts_endpoint = f"https://{bridge}.deta.dev/shared-posts"
    params = {'access_key': key}

    async with httpx.AsyncClient() as client:
        friend_posts = await client.get(posts_endpoint, params=params)

    lists_of_posts = friend_posts.json()

    for post in lists_of_posts:
        post['name'] = name
        
    return lists_of_posts

async def get_my_posts():
    my_posts = next(db.fetch({'category': 'post'}))
    for post in my_posts:
        post['name'] = username
    
    print("got my posts")
    return my_posts

@app.post("/add-friend", status_code=200)
def add_friend(newfriend: NewFriend, response: Response):
    if newfriend.access_key == private_key:
        friend_json = {
            'key': newfriend.public_key,
            'name': newfriend.name,
            'category': 'friend',
            'bridge': newfriend.bridge,
            'value': 'notified'
            }
        
        added_friend = db.put(friend_json)
        
        if added_friend == friend_json:
            return friend_json
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return response

    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {response}

@app.delete("/remove-friend", status_code=200)
def remove_friend(deletedfriend: DeletedFriend, response: Response):
    unfriend = db.get(deletedfriend.key)
    if deletedfriend.access_key == private_key:
        if unfriend == []:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {response}
        
        elif unfriend['category'] == 'friend' or unfriend['category'] == 'pending_friend':
            unfriend_key = unfriend['key']
            db.delete(unfriend_key)
            response.body = "Unfriended Successfully"
            response.status_code = status.HTTP_200_OK
            return {response}
        
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {response}

    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {response}

@app.get("/shared-posts", status_code=200)
def read_post(access_key: str, response: Response):
    if access_key == private_key:
        my_posts = db.fetch({'category': 'post'})
        response = [item for sublist in my_posts for item in sublist]
        return response
    
    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {response}
    
@app.post("/create-post", status_code=200)
def create_post(newpost: NewPost, response: Response):
    if newpost.access_key == private_key:
        post_id = uuid.uuid4().hex
        timestamp_now = time.time()
        post_json = {"key": post_id, 'value': newpost.value, 'category': 'post', 'time': timestamp_now}
        create_post = db.put(post_json)

        if create_post == post_json:
            return {response}
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {response}

    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {response}
        
@app.get("/friend-posts", status_code=200)
async def read_friend_posts(name: str, access_key: str, response: Response):
    if access_key == private_key:
        friend_posts = await get_posts(name)
        return {'posts': friend_posts}

    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {response}

@app.get("/friend-list")
def friend_list(access_key: str, response: Response, pending: Optional[bool] = False):
    if access_key == private_key:
        try:
            if pending == True:
                friends = next(db.fetch([{'category': 'pending_friend'}, {'category': 'friend'}]))
                checked_friends = check_usernames(friends)
                if checked_friends == False:
                    return friends
                else:
                    updated_friends = next(db.fetch([{'category': 'pending_friend'}, {'category': 'friend'}]))
                    return updated_friends
                
            else:
                friends = next(db.fetch({'category': 'friend'}))
                checked_friends = check_usernames(friends)
                if checked_friends == False:
                    return friends
                else:
                    updated_friends = next(db.fetch({'category': 'friend'}))
                    return updated_friends
        except:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {response}
    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {response}
    
@app.get("/friend-feed")
async def friend_feed(access_key: str, response: Response):
    if access_key == private_key:
        posts = []
        friends = next(db.fetch({'category': 'friend'}))
        my_posts = asyncio.create_task(get_my_posts())

        for future in asyncio.as_completed(map(get_posts_from_friend, friends)):
            lists_of_posts = await future

        posts.append(lists_of_posts)
        posts.append(my_posts.result())

        combined = [item for sublist in posts for item in sublist]

        try:
            sorted_feed = sorted(combined, key=itemgetter('time'), reverse=True)
            return sorted_feed
        except Exception as e:
            return None
    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {response}
    

@app.put("/change-key", status_code=200)
def change_key(keys: NewKey, response: Response):
    # This very much needs to be private/authed to only the owner
    global private_key
    if keys.access_key == private_key:
        db.put({'key': 'my_key', 'value': keys.new_key.strip()})
        private_key = keys.new_key.strip()
        return {response}

    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {response}
    
@app.put("/change-name", status_code=200)
def change_key(namechange: NewName, response: Response):
    # This very much needs to be private/authed to only the owner
    if namechange.access_key == private_key:
        db.update({'value': namechange.new_name.strip()}, "my_name")
        return {response}

    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {response}
    
@app.get("/my-key", status_code=200)
def show_my_key():
    # This very much needs to be private/authed to only the owner
    return {'key': private_key}

@app.get("/my-name", status_code=200)
def show_my_key():
    # This very much needs to be private/authed to only the owner
    my_name = db.get('my_name')
    return {'name': my_name['value']}

@app.get("/bio", status_code=200)
def show_my_key():
    # This very much needs to be private/authed to only the owner
    try:
        my_bio = db.get('my_bio')
        return {my_bio['value']}
    except:
        return {"Nothing to see here..."}
    
@app.put("/change-bio", status_code=200)
def show_my_key(updated_bio: NewBio, response: Response):
    # This very much needs to be private/authed to only the owner
    db.put({'key': 'my_bio', 'value': updated_bio.bio})
    return {response}

@app.post("/accept", status_code=200)
def accept_friend(addfriend: AddFriend, response: Response):
    # This very much needs to be private/authed to only the owner
        try:
            checkFriendExists = db.get(addfriend.public_key)
            checkType = checkFriendExists['category']
            
            if checkType == "friend":
                response.body = "Already Connected"
            
            if checkType == "pending_friend":
                db.update(
                    {
                    'category': 'friend',
                    'name': addfriend.name,
                    'bridge': addfriend.bridge,
                    'value': 'notified'
                    }, addfriend.public_key
                        )
                
                response.body = "Connection Request Accepted"
            
            return {response}
        
        except:
            pending_friend_json = {
                'key': addfriend.public_key,
                'name': addfriend.name,
                'category': 'pending_friend',
                'bridge': addfriend.bridge,
                'value': 'notified'
                }
            
            pending_friend = db.update(pending_friend_json)
        
            if pending_friend == pending_friend_json:
                response.status_code = status.HTTP_201_CREATED
                return pending_friend_json

@app.post("/request", status_code=200)
def request_friend(addfriend: AddFriend, response: Response):
    # You can only lodge a friend request here, approval can only be done via /accept
        try:
            checkFriendExists = db.get(addfriend.public_key)
            checkType = checkFriendExists['category']
            
            if checkType == "friend":
                response.body = "Already a Friend"
                return {response}
            
            elif checkType == "pending_friend":
                response.body = "Already Pending"
                return {response}
            
            else:
                response.body = "Something is Wrong"
                response.status_code = status.HTTP_400_BAD_REQUEST
        
        except:
            pending_friend_json = {'key': addfriend.public_key, 'name': addfriend.name, 'category': 'pending_friend', 'bridge': addfriend.bridge}
            pending_friend = db.put(pending_friend_json)
        
            if pending_friend == pending_friend_json:
                response.status_code = status.HTTP_201_CREATED
                return pending_friend_json
            
@app.get("/notifications", status_code=200)
def check_notifications(clear: Optional[bool] = False):
    # This very much needs to be private/authed to only the owner
    friends = next(db.fetch({'category': 'friend'}))
    notified_friends = []
    
    for friend in friends:
        try:
            if friend['value'] == 'notified':
                notified_friends.append(friend)
        except:
            return {'notifications': 'Fetching Notifications Failed'}
        
    if clear == False:
        if len(notified_friends) > 0:
            return {'notifications': notified_friends}
        else:
            return {'notifications': 'No Notifications'}
    else:
        for friend in notified_friends:
            db.update({'value': 'inactive'}, friend['key'])
        return {'notifications': 'Notifications Cleared'}

@app.post("/notify", status_code=201)
def receive_notification(notification: ReceivedNotif, response: Response):
    friend_data = db.get(notification.key)
    bridge = friend_data['bridge']
    category = friend_data['category']
    key = friend_data['key']

    if category == 'friend' and bridge == notification.bridge and key == notification.key:
        update_check = db.update({'value': 'notified'}, key)
        
        if not update_check:
            response.body = "Notification Created"
            again = db.get(notification.key)
            return again

    elif key == private_key:
        response.body = "You Cannot Notify Yourself"
        return {response}
        
    elif key != notification.key:
        response.body = "Unknown or Incorrect Key"
        return {response}

    else:
        response.body = "Unable to Trigger Notification"
        response.status_code = status.HTTP_400_BAD_REQUEST

app.mount('', StaticFiles(directory="svelte/dist/", html=True), name="static")
