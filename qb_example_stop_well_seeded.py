# stop torrents that have a number of seeds above a certain count

## EXAMPLE ONLY - DO NOT RUN AS IS ##

# Just leave unlimited ratio and time limits for all torrents, resume them all once in a while, so the peers count get updated,
# # and then on a schedule stop the ones that have lots of seeds.. it's really couple of lines of py.

import qbittorrentapi

conn_info = dict(host="", port="", username="", password="")

qbt_client = qbittorrentapi.Client(**conn_info)
qbt_client.auth_log_in()

# Run this let's say every n hours

qbt_client.torrents_resume("all")

# And then this every n minutes

MIN_SEEDS = 6

for torrent in qbt_client.torrents_info(status_filter="seeding"):

    tor_props = torrent.properties

    if tor_props.seeds_total > MIN_SEEDS:

        print("")
        print(f"TI [ {torrent.name} ] R [ {torrent.ratio} ] S [ {tor_props.seeds_total} ] SL [ {tor_props.seeds_total <= MIN_SEEDS} ]")
        torrent.pause()
        print(f"TP -")
