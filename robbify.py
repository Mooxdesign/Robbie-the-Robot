import json 
import spotipy 
import webbrowser 
  
# username = '24xml6hvucaw8orcqe2v450ip'
# username = 'mooxdesign@gmail.com'
client_id = "84e0e4cc64a04d0cb7d1b59835767339"
client_secret = "d10870e895624835936076bbe65bc279"
redirect_uri = "https://moxx.uk"
scope = "user-read-playback-state,user-modify-playback-state"

spotifyObject = spotipy.Spotify(
    auth_manager=spotipy.SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,  
        scope=scope, open_browser=False))


user_name = spotifyObject.current_user() 
  
# To print the JSON response from  
# browser in a readable format. 
# optional can be removed 
print(json.dumps(user_name, sort_keys=True, indent=4)) 
  
while True: 
    print("Welcome to the project, " + user_name['display_name']) 
    print("0 - Exit the console") 
    print("1 - Search for a Song") 
    user_input = int(input("Enter Your Choice: ")) 
    if user_input == 1: 
        search_song = input("Enter the song name: ") 
        results = spotifyObject.search(search_song, 1, 0, "track") 
        songs_dict = results['tracks'] 
        song_items = songs_dict['items'] 
        song = song_items[0]['external_urls']['spotify'] 
        print(song)
        webbrowser.open(song) 
        print('Song has opened in your browser.') 
    elif user_input == 0: 
        print("Good Bye, Have a great day!") 
        break
    else: 
        print("Please enter valid user-input.") 