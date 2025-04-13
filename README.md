# qBittorrent-examples
A collection of qBittorrent python scripts that relies on [qbittorrent-api](https://pypi.org/project/qbittorrent-api/). These scripts are meant to be more efficient on the public trackers, as there are lots of bad beers and leechers.

# Installation
Just run `pip install -r requirements.txt` or `S01_install_reqs.cmd`

# Scripts

## qb_ban_bad_peers
A script to run on a schedule to ban bad peers. The logic is based on a list of BT client IDs to allow or ban, and a list of countries to allow or ban. Please read the python closely, to make the adjustements you want.

QB connection info are read from the env, please see `qb_ban_bad_peers_loop.cmd`. This script is meant to be run manually, if the script works for you, then create a scheduled task that runs every n-minutes.

### cleanup
To cleanup banned IPs you can change the .ini file *before* running QB, by removing the row `BannedIPs`. This can be done once in a while, to avoid the list becoming too large, or to give peers a second chance. Example in cmd

```
REM REMOVE THE BANNED IPs FROM PREVIOUS SESSION
CD /D %APPDATA%\qBittorrent
COPY /Y qBittorrent.ini z_bak_qBittorrent.ini
findstr /V BannedIPs z_bak_qBittorrent.ini > qBittorrent.ini
```

## qb_change_content_layout_by_renaming
Thanks to this [comment](https://old.reddit.com/r/qBittorrent/comments/1j92buv/fun_fact_you_can_arbitrarily_adjust_torrent) it is possible to change the content layout of downloaded content with little effort, by renaming torrents' files to "subdir/file". The subdir would be the torrent name itself, and its files would be move to the subdir. This does not require re-importing the torrent or changing its location. QB connection info are read from the env, or just edit the script and hard-code them.

## qb_generate_ipfilter
A script to generate an IP filter dat file to ban specific countries. Country information is taken from [mailfud](https://mailfud.org/geoip-legacy/GeoIP-legacy.csv.gz). Please ensure to update it once in a while. Load the filter in QB from the Menu Options > Connection > IP Filtering. The script can be automated, example provided in `qb_generate_ipfilter_updater.cmd`, you would need wget and 7z on the `PATH`. IPv4 only, as I have disabled IPv6 everywhere.

|File|Name|
|---|---|
|Input|GeoIP-legacy.csv|
|Output|ipfilter.dat|

## qb_trackers_fixer
A script to reset trackers on torrents. Filters can be applied, check the API the docs of `torrents_info`. Be sure to read the source, as this is mostly an example.

Before launching it, you can set
* `SET X_PERFORM_CLEANUP=1` to remove torrents that are not in the `qb_trackers_fixer.toml`
* `SET X_FILTER_BY_DAYS=7` to process only torrents added in the last n days

## libtorrent ltor_dht_scraper
An example of how to use libtorrent python bindings. Yeah you could build your own torrent client with few lines of python.
