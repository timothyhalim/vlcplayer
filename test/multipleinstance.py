import vlc
import time

files = ['./sample.mp4','./sample.mp4'] 
instances = []
medias = []
players = []


for idx, fname in enumerate(files):
    print("Loading",fname)
    instances.append(vlc.Instance())
    medias.append(instances[idx].media_new(fname))

    players.append(vlc.MediaPlayer())
    players[idx].set_media(medias[idx])
    players[idx].play() 

player_count = players # copy of the players list so we don't modify during iteration
still_playing = True
time.sleep(0.5) # Wait for players to start

while still_playing:
    time.sleep(1)
    for p in players:
        if p.is_playing():
            continue
        else:
            player_count.remove(p)
            players = player_count # no point iterating over players that have finished
            print("Finished - Still playing ", str(len(player_count)))

    if len(player_count) != 0:
        continue
    else:
        still_playing = False
