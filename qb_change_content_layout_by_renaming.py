from datetime import datetime
import qbittorrentapi
import os
from pathlib import Path
import re


def sanitize_tname(tname="__"):
    # remove special chars
    s1 = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "_", tname)

    if len(s1) > 10 and s1.rfind(".") == len(s1) - 4:
        # removes the extension where the "Torrent name is like this.mkv"
        return s1.rpartition(".")[0].strip()
    else:
        return s1.strip()


conn_info = dict(host=os.getenv("X_LOCAL_IP"), port=os.getenv("X_QB_PORT"), username=os.getenv("X_QB_USER"), password=os.getenv("X_QB_PASS"))

qbt_client = qbittorrentapi.Client(**conn_info)
qbt_client.auth_log_in()

for torrent in qbt_client.torrents_info(status_filter="completed", sort="name"):  # you can add a tag filter tag="tag-name"

    should_move = True

    for torrent_file in qbt_client.torrents_files(torrent_hash=torrent.hash):

        if "/" in torrent_file.name:
            should_move = False
            break

    if should_move:
        tname = sanitize_tname(torrent.name)
        print()
        print(f"H [ {torrent.hash} ] T [ {torrent.name} ] A [ {datetime.fromtimestamp(torrent.added_on)} ]")
        print(f" TN [ {tname} ]")
        print(f" CP [ {torrent.content_path} ]")
        print(f" SP [ {torrent.save_path} ]")

        for torrent_file in qbt_client.torrents_files(torrent_hash=torrent.hash):
            print(f" RN [ {torrent_file.id} ] [ {tname}/{torrent_file.name} ]")
            proceed = input("    Proceed with renaming y/N ? ")

            if "y" == proceed:
                qbt_client.torrents_rename_file(torrent_hash=torrent.hash, file_id=torrent_file.id, new_file_name=f"{tname}/{torrent_file.name}")
