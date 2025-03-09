from datetime import datetime
import qbittorrentapi
import os
import tomllib

with open('qb_trackers_fixer.toml', 'rb') as f:
    conf = tomllib.load(f)

trackers_good_conf = conf['qb_trackers_fixer']['trackers_good']
print(f'Got {len(trackers_good_conf)} trackers_good_conf trackers')

###

try:
    perform_cleanup = int(os.getenv('X_PERFORM_CLEANUP'))
except:
    perform_cleanup = -1

d_today = datetime.today()

try:
    filter_by_days = int(os.getenv('X_FILTER_BY_DAYS'))
except:
    filter_by_days = -1

if (filter_by_days > 0):
    print(f"Filtering by days GT 0 = {filter_by_days}, perform_cleanup = {perform_cleanup}")
else:
    print(f"Filtering by days LT 0 = {filter_by_days}, perform_cleanup = {perform_cleanup}")

print()

def torrents_info():
    conn_info = dict(
        host=os.getenv('X_LOCAL_IP'),
        port=os.getenv('X_QB_PORT'),
        username=os.getenv('X_QB_USER'),
        password=os.getenv('X_QB_PASS')
    )

    with qbittorrentapi.Client(**conn_info) as qb_client:
        qb_client.auth_log_in()
        return qb_client.torrents_info() # possible : (tag=tag_filter) , etc..

###

if (perform_cleanup > 0):
    print("Step 1, cleaning up pub trackers..")

    removed_count_total = 0
    removed_progress = 0

    torrentz = torrents_info()
    for torrent in torrentz:
        # ensure to not change private torrents' trackers!
        if torrent.private:
            continue

        delta1 = d_today - datetime.fromtimestamp(torrent.added_on)

        if (filter_by_days > 0 and delta1.days > filter_by_days):
            continue

        removed_progress = removed_progress + 1
        removed_count = 0
        print(f"Processing [ {torrent.name} ]")

        for tracker in torrent.trackers:
            if '[' not in tracker.url and tracker.url not in trackers_good_conf:
                print(f"  Removed [ {tracker.url} ]")
                torrent.remove_trackers(urls=[tracker.url])
                removed_count = removed_count + 1
                removed_count_total = removed_count_total + 1

        print(f" Total trackers removed {removed_count}, T {removed_progress} / {len(torrentz)}\n")


    print(f"\nTotal trackers removed {removed_count_total} Total\n")

###

print("Step 2, adding back pub trackers..")

added_count_total = 0
added_progress = 0

torrentz = torrents_info()

for torrent in torrentz:
    # ensure to not change private torrents' trackers!
    if torrent.private:
        continue

    delta1 = d_today - datetime.fromtimestamp(torrent.added_on)

    if (filter_by_days > 0 and delta1.days > filter_by_days):
        continue

    added_progress = added_progress + 1
    print(f"Processing [ {torrent.name} ]")

    torrent.add_trackers(trackers_good_conf)

    print(f" Total trackers added T {added_progress} / {len(torrentz)}\n")

print(f"\nTotal trackers added {added_count_total} Total\n")


#torrents_set_share_limits(ratio_limit=None, seeding_time_limit=None, inactive_seeding_time_limit=None, torrent_hashes=None, **kwargs) → None
# PARAMETERS:
# torrent_hashes (Optional[Iterable[str]]) – single torrent hash or list of torrent hashes. Or all for all torrents.
# ratio_limit (UnionType[str, int, None]) – max ratio to seed a torrent. (-2 means use the global value and -1 is no limit)
# seeding_time_limit (UnionType[str, int, None]) – minutes (-2 means use the global value and -1 is no limit)
# inactive_seeding_time_limit (UnionType[str, int, None]) – minutes (-2 means use the global value and -1 is no limit) (added in Web API v2.9.2)

# set_upload_limit(limit=None, torrent_hashes=None, **kwargs) → None
# Set the upload limit for one or more torrents.
# PARAMETERS:
# torrent_hashes (Optional[Iterable[str]]) – single torrent hash or list of torrent hashes. Or all for all torrents.
# limit (UnionType[str, int, None]) – bytes/second (-1 sets the limit to infinity)
