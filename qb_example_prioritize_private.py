# What I want to do is to enable all of them for seeding, however, if one of the private torrents is active, stop or pause all the other public torrents?

## EXAMPLE ONLY - DO NOT RUN AS IS ##

trackers_str = str(torrent.trackers)
if 'private.tracker.com' in trackers_str or ..


import qbittorrentapi

are_private_tors_seeding = False

for torrent in qbt_client.torrents_info(status_filter='active'):
  if (torrent is private):
    # set a flag if there are active private torrents
    are_private_tors_seeding = True
    break

if (are_private_tors_seeding):
  for torrent in qbt_client.torrents_info(status_filter='seeding'):
    if (torrent is *not* private):
      print(f"TP [ {torrent.name} ] R [ {torrent.ratio} ]")
      torrent.pause()
