from datetime import datetime
import qbittorrentapi
import os
import pathlib
import logging

logging.basicConfig(filename="qb_find_tor_no_sub_folder_DEBUG.log", encoding="utf-8", level=logging.DEBUG)

log_files_in_qb = logging.getLogger("qb_find_tor_no_sub_folder")
log_files_in_qb.setLevel(level=logging.INFO)
log_files_in_qb.addHandler(logging.FileHandler("qb_find_tor_no_sub_folder_INFO.log", encoding="utf-8"))

conn_info = dict(host=os.getenv("X_LOCAL_IP"), port=os.getenv("X_QB_PORT"), username=os.getenv("X_QB_USER"), password=os.getenv("X_QB_PASS"))

log_files_in_qb.debug("Connecting to QB..")
qbt_client = qbittorrentapi.Client(**conn_info)
qbt_client.auth_log_in()

log_files_in_qb.debug("Getting torrents list and their content..")

# ensure to stop all torrents before moving their content

for torrent in qbt_client.torrents_info(status_filter="completed"):

    should_move = True

    for torrent_file in qbt_client.torrents_files(torrent_hash=torrent.hash):

        if "/" in torrent_file.name:
            should_move = False
            break

    if should_move:
        log_files_in_qb.info(f"H [ {torrent.hash} ] T [ {torrent.name} ] A [ {datetime.fromtimestamp(torrent.added_on)} ]")
        log_files_in_qb.info(f" CP [ {torrent.content_path} ]")
        log_files_in_qb.info(f" SP [ {torrent.save_path} ]")
        log_files_in_qb.info("")

    # then it should
    # 1. export to temp location the .torrent file
    # 2. create a subfolder with torrent.save_path + torrent.name
    # 3. remove the torrent from qb without data deletion
    # 4. move the files of the torrent in the subfolder created above
    # 5. re-add the torrent with the content layout 'create subfolder' option and skip hashcheck
    # 6. assuming that the layout is identical, we are good, but there might be some problematic characters in the torrent name vs the subfolder name
