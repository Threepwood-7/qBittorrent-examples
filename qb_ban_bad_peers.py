import qbittorrentapi
import os
import re
import logging
from logging.handlers import RotatingFileHandler

# edit log path as needed
handler = RotatingFileHandler("qb_ban_peers_log.log", encoding="utf-8", maxBytes=5242880, backupCount=3)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger("qb_ban_peers_log")
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def is_blank(s):
    return not (bool(s and not s.isspace()))


# BT client IDs reference
# https://github.com/c0re100/qBittorrent-Enhanced-Edition/blob/v5_0_x/src/base/bittorrent/peer_blacklist.hpp
# https://github.com/anacrolix/torrent/issues/889
#  static const std::regex id_filter("-(XL|SD|XF|QD|BN|DL|TS|DT|HP|LT1220|LT2070|GT)(\\d+)-");
# https://www.bittorrent.org/beps/bep_0020.html
# https://github.com/webtorrent/bittorrent-peerid/blob/master/index.js


#
## 1. BAN LOGIC (LESS RESTRICTIVE, YOU LIST WHAT YOU WANT TO BAN, OTHERWISE ALLOW)
#

# you can ban specific clients..
ban_clients = re.compile("-(A0|AX|BF|BN|DL|DP|DT|HP|LT122|LT207|MG|MP|QD|RM|RT|RZ|SD|TS|UL|XF|XL|XT|WY)([A-Z0-9]{0,4})-", re.IGNORECASE)

# ..or countries..
ban_countries = re.compile("(cn)", re.IGNORECASE)


#
## 2. ALLOW LOGIC (MORE RESTRICTIVE, YOU LIST WHAT YOU WANT TO ALLOW, OTHERWISE BAN, PLEASE READ)
#

# you can allow only specific clients..
# please note, if you want to be more flexible you can edit the banning logic below and just rely on the ban_clients instead (POINT 1)

allow_clients = re.compile("-(AZ|BC|BI|BT|DE|LT|QB|SZ|TR|UT)([A-Z0-9]{0,4})-", re.IGNORECASE)

# ..or countries..
# it's up to you to decide https://www.countries-ofthe-world.com/TLD-list.html
# please note, if you want to be more flexible you can edit the banning logic below and just rely on the ban_countries instead (POINT 1)

allow_countries = re.compile(
    "(ad|ar|at|au|be|bg|br|by|ca|ch|cl|co|cy|cz|de|dk|ee|es|eu|fi|fo|fr|gb|gi|gr|hk|hr|hu|ie|il|im|is|it|jp|kr|kw|kz|li|lt|lu|lv|mc|md|me|mk|mt|mx|nl|no|nz|pa|pe|pl|pt|py|qa|ro|rs|ru|se|si|sk|sm|tw|ua|uk|us|uy|uz|va|za)",
    re.IGNORECASE,
)

# set to 1 to apply the filtering logic at POINT 1 (less restrictive), or set to 2 to apply the allow only logic at POINT 2 (more restrictive)
FILTERING_LOGIC = 2

#
## 3. ALWAYS ALLOW (OVERRIDE BAN)
#

# allow IP ranges
#  i.e. if you use a VPN you might want to avoid banning your IP ranges
#  it does not cause an issue per se but it will generate lots of messages in the "Execution Log" of qbit)
#  check your public IP and update as needed

# allow_IPs = re.compile("(^176.*|^185.*|^149.*)")

# if you don't need it, just use an invalid match
allow_IPs = re.compile("(^999.*)")


#
## QB connection info are read from the env variable, but you can put them in here
#

conn_info = dict(host=os.getenv("X_LOCAL_IP"), port=os.getenv("X_QB_PORT"), username=os.getenv("X_QB_USER"), password=os.getenv("X_QB_PASS"))

qbt_client = qbittorrentapi.Client(**conn_info)
qbt_client.auth_log_in()


# loop over active torrents
for torrent in qbt_client.torrents_info(status_filter="active"):
    # get peers info
    tor_peers = qbt_client.sync_torrent_peers(torrent.hash)

    # check peers
    for tor_peer in tor_peers.peers:
        tor_peer_info = tor_peers.peers[tor_peer]
        p_id = tor_peer_info.peer_id_client.strip()

        logger.info(f"TI [ {torrent.name} ] P [ {tor_peer} ] C [ {tor_peer_info.client} ] CI [ {p_id} ] CC [ {tor_peer_info.country_code} ] P [ {tor_peer_info.progress} ] FL [ {FILTERING_LOGIC} ]")

        # logger.info(f"   [ {tor_peer_info} ]\n\n")

        should_ban = False

        #
        ## Apply the filtering logic..
        #

        if FILTERING_LOGIC == 1:

            # first check of banned clients
            if "#@" == p_id or is_blank(p_id) or ban_clients.match(p_id):
                should_ban = True
                logger.info(f"     * Banning peer due to client C [ {tor_peer_info.client} ] CI [ {p_id} ]")

            # second check on countries
            if not should_ban and ban_countries.match(tor_peer_info.country_code):
                should_ban = True
                logger.info(f"     * Banning peer due to country [ {tor_peer_info.country_code} ]")

        elif FILTERING_LOGIC == 2:

            # only allow specific clients
            if not allow_clients.match(p_id):
                should_ban = True
                logger.info(f"     * Banning peer due to client C [ {tor_peer_info.client} ] CI [ {p_id} ]")

            # only allow specific countries
            if not should_ban and not allow_countries.match(tor_peer_info.country_code):
                should_ban = True
                logger.info(f"     * Banning peer due to country [ {tor_peer_info.country_code} ]")

        #
        ## 3. ALWAYS ALLOW (OVERRIDE BAN)
        #

        # override if the IP is in the allow pattern
        if should_ban and allow_IPs.match(tor_peer_info.ip):
            should_ban = False
            logger.info(f"     * Allowing peer due to IP [ {tor_peer_info.ip} ]")

        # override if the peer has more progress than me
        if should_ban and torrent.progress < 1.0 and tor_peer_info.progress > torrent.progress:
            should_ban = False
            logger.info("     * Allowing peer as it has more than me..")

        if should_ban:
            qbt_client.transfer_ban_peers(tor_peer)
