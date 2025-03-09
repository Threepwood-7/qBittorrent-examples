## slow down upload when downloading
## EXAMPLE ONLY - DO NOT RUN AS IS ##

import qbittorrentapi

conn_info = dict(host="127.0.0.1", port="8080", username="admin", password="****")

qbt_client = qbittorrentapi.Client(**conn_info)
qbt_client.auth_log_in()

# if I'm downloading above a certain speed (512k in this case)

#   transfer_set_speed_limits_mode
#     True to enable alt speed and False to disable. Leaving None will toggle the current state.

### METHOD 1 - GLOBAL (EITHER TOGGLE SPEED LIMITS, OR SET IT EXPLICITELY)

if qbt_client.transfer_info().dl_info_speed > (1024 * 512):
    print("Slowing down upload..")
    # qbt_client.transfer_set_upload_limit(1024 * 128)
    qbt_client.transfer_set_speed_limits_mode(False)

else:
    print("Unleashing upload speed..")
    # qbt_client.transfer_set_upload_limit(-1)
    qbt_client.transfer_set_speed_limits_mode(True)


### METHOD 2 - EACH TORRENT
if qbt_client.transfer_info().dl_info_speed > (1024 * 512):

    for torrent in qbt_client.torrents_info("downloading"):
        torrent.set_upload_limit(1024 * 32)

    for torrent in qbt_client.torrents_info("completed"):
        torrent.set_upload_limit(-1)
