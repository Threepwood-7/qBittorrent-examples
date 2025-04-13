from datetime import datetime
import libtorrent as lt
import time
import os
import sys
import ast
import queue
from lib_common import sanitize_from_lib
import signal
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler("ltor_dht_scraper.log", encoding="utf-8", maxBytes=19000000, backupCount=3)
handler_seen_hashes = RotatingFileHandler("ltor_dht_scraper_seen_hashes.log", encoding="utf-8", maxBytes=19000000, backupCount=3)

handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)8s - %(message)s"))
handler_seen_hashes.setFormatter(logging.Formatter("%(message)s"))

logger = logging.getLogger("ltor_dht_scraper")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

logger_seen_hashes = logging.getLogger("ltor_dht_scraper_seen_hashes")
logger_seen_hashes.setLevel(logging.INFO)
logger_seen_hashes.addHandler(handler_seen_hashes)

BASE_PATH = "./ltor_dht_scraper"
HASHES_PROCESSED_F = "./ltor_dht_scraper_hashes_processed.txt"
SESSION_F = "./ltor_dht_scraper_session.txt"

# Flag to handle graceful termination
terminate = False


def signal_handler(sig, frame):
    print("Exiting..")
    global terminate
    terminate = True


signal.signal(signal.SIGINT, signal_handler)


def extract_between_braces(input_string):
    if len(input_string) > 4096:
        return None

    input_string = input_string.replace("\\", "\\\\")

    first_brace = input_string.find("{")
    last_brace = input_string.rfind("}")

    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        return input_string[first_brace : last_brace + 1]
    else:
        return None


def handle_dht(a, hashes_to_process):
    logger.debug(f"C [ {a.category()} ] M [ {a.message()} ] W [ {a.what()} ]")

    jmsg = {}

    try:
        jmsg = ast.literal_eval(extract_between_braces(a.message()))
    except Exception as ex:
        logger.error(f"ast.literal_eval {ex}")
        return

    info_hash = None

    # if (jmsg.get("q", None) == "announce_peer") and not jmsg.get("a", None) is None and not jmsg.get("a", None).get("info_hash", None) is None:

    if (jmsg.get("q", None) == "get_peers" or jmsg.get("q", None) == "announce_peer") and not jmsg.get("a", None) is None and not jmsg.get("a", None).get("info_hash", None) is None:
        info_hash = jmsg["a"]["info_hash"]

    info_hash = info_hash.strip() if info_hash else None

    if info_hash:
        logger_seen_hashes.info(f"{info_hash} {jmsg.get("q", None):>20} {a.message()}")

    # if info_hash and len(info_hash) == 40 and jmsg.get("q", None) == "announce_peer":
    if info_hash and len(info_hash) == 40:

        if info_hash not in hashes_to_process:  # and info_hash.find("44b") != 0:
            logger.debug(f"H [ {info_hash} ]")
            hashes_to_process.add(info_hash)


def process_alerts(ses, hashes_to_process):
    alerts = ses.pop_alerts()

    # 1. process LT alerts
    for a in alerts:
        logger.debug(f"C [ {a.category():>6} ] W [ {a.what():>22} ] A [ {a} ]")

        # if "dht_" not in a.what():
        #    logger.debug(f"C [ {a.category():>6} ] W [ {a.what():>22} ] A [ {a} ]")
        #    continue

        if a.what() == "dht_pkt":
            handle_dht(a, hashes_to_process)

        elif a.what() == "state_changed":
            logger.info(f"TSS [ {a.torrent_name} ] S [ {a.state} ]")

        elif a.what() == "metadata_received":
            logger.info(f"TSM [ {a.handle.torrent_file().name()} ] S [ {a.handle.status().state} ]")

            # with open(f"OUTZK_{sanitize_from_lib(a.handle.torrent_file().name())}.torrent", "wb") as file:
            # file.write(a.handle.torrent_file().info_section())

            tfname = sanitize_from_lib(a.handle.torrent_file().name())

            try:
                with open(f"{BASE_PATH}\\OUTOK_{tfname}.torrent", "wb") as file:
                    file.write(b"d8:announce33:udp://open.stealth.si:80/announce13:announce-listll33:udp://open.stealth.si:80/announceee4:info")
                    file.write(a.handle.torrent_file().info_section())
                    file.write(b"e")

            except Exception as ex:
                logger.error(f"Unable to write F [ {tfname} ] {ex}")

            # a.handle.save_resume_data(lt.save_resume_flags_t.flush_disk_cache | lt.save_resume_flags_t.save_info_dict)
            # a.handle.save_resume_data(lt.save_resume_flags_t.save_info_dict)

            ses.remove_torrent(a.handle, 1)


def has_been_processed(info_hash):
    with open(HASHES_PROCESSED_F, "r", encoding="ascii") as file:
        while line := file.readline():
            if info_hash == line:
                return True

    return False


def has_been_processed_save(info_hash):
    with open(HASHES_PROCESSED_F, "a", encoding="ascii") as file:
        file.write(f"{info_hash}\n")


def de_queue(ses, hashes_to_process, hashes_processed_wdate):
    # 2. de-queue
    for info_hash in hashes_to_process:

        if has_been_processed(info_hash):
            continue

        has_been_processed_save(info_hash)

        add_torrent_params = lt.parse_magnet_uri("magnet:?xt=urn:btih:" + info_hash + "&tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce&tr=udp%3A%2F%2Fns-1.x-fins.com%3A6969%2Fannounce")
        add_torrent_params.save_path = BASE_PATH

        # The add_torrent_params class has a flags field. It can be used to control what state the new torrent will be added in.
        # Common flags to want to control are torrent_flags::paused and torrent_flags::auto_managed.
        # In order to add a magnet link that will just download the metadata, but no payload, set the torrent_flags::upload_mode flag.

        add_torrent_params.flags = (lt.torrent_flags.upload_mode) ^ lt.torrent_flags.auto_managed ^ lt.torrent_flags.paused
        # add_torrent_params.flags = (lt.torrent_flags.duplicate_is_error) ^ lt.torrent_flags.auto_managed ^ lt.torrent_flags.paused

        torrent_handle = ses.add_torrent(add_torrent_params)
        torrent_handle.resume()

        hashes_processed_wdate.append({"h": torrent_handle, "removed": False, "added_on": datetime.now()})

        # torrent_handle.add_tracker(["udp://open.stealth.si:80/announce"])
        # torrent_handle.add_tracker("udp://explodie.org:6969/announce")
        logger.info(f"AH  [ {torrent_handle.info_hash()} ] Torrents in session {len(ses.get_torrents())}")

        # logger.debug(f"TH [ {torrent_handle} ]")

    hashes_to_process.clear()


def clean_up(ses, d_now, hashes_processed_wdate):
    for ha_wdate in hashes_processed_wdate:
        # print(ha_wdate)
        if not ha_wdate or ha_wdate["removed"]:
            continue

        # if not ha_wdate or ha_wdate["h"] is None or ha_wdate["h"].info_hash() is None or "0000000000000000000000000000000000000000" == ha_wdate["h"].info_hash():
        if not ha_wdate or ha_wdate["h"] is None:
            ha_wdate["removed"] = True
            logger.warning(f"* Invalid Hash in array *")
            continue

        delta1 = d_now - ha_wdate["added_on"]

        if delta1.seconds > (60 * 3):
            logger.info(f"RMW [ {ha_wdate["h"].info_hash()} ]")

            try:
                ha_wdate["removed"] = True
                ses.remove_torrent(ha_wdate["h"], 1)
            except Exception as ex:
                logger.error(f"remove_torrent {ex}")

    hashes_processed_wdate_re = list()

    # # copy the ones to keep, so to reduce the data structure size
    for ha_wdate in hashes_processed_wdate:
        if ha_wdate and ha_wdate["removed"] == False:
            hashes_processed_wdate_re.append(ha_wdate)

    hashes_processed_wdate.clear()
    for z in hashes_processed_wdate_re:
        hashes_processed_wdate.append(z)

    logger.info(f"CL  [ {len(hashes_processed_wdate)} ]")

    # https://www.rasterbar.com/products/libtorrent/single-page-ref.html#torrent-handle
    #        for torz in torzs:
    #            logger.debug(f"TORZ [ {torz} ] S [ {torz.status().state} ] H [ {torz.status().has_metadata} ]")


def print_session(ses):
    ths = ses.get_torrents()
    with open(SESSION_F, "w", encoding="utf-8") as file:

        file.write(f"THS >>> {len(ths)}\n\n")
        for th in ths:
            file.write(f"TH  [ {th.info_hash()} ] TN [ {th.status().name} ]\n")


def main():
    # https://www.libtorrent.org/reference-Settings.html#settings_pack
    ses = lt.session(
        {
            "active_downloads": 1000,
            "active_limit": 1000,
            "dht_max_dht_items": 1000,
            "download_rate_limit": 64 * 1024,
            "upload_rate_limit": 64 * 1024,
            "enable_dht": True,
            "enable_upnp": True,
            "enable_natpmp": True,
            "connections_limit": 600,
            "dht_bootstrap_nodes": "dht.libtorrent.org:25401,router.bittorrent.com:6881,router.utorrent.com:6881,dht.transmissionbt.com:6881,dht.aelitis.com:6881",
            "outgoing_interfaces": os.getenv("X_VPN_LOCAL_BIND_IP"),
            "listen_interfaces": os.getenv("X_VPN_LOCAL_BIND_IP") + ":36133",
            # https://www.libtorrent.org/reference-Alerts.html#alert_category_t
            "alert_mask": lt.alert.category_t.all_categories,
            # "alert_mask": lt.alert.category_t.dht_operation_notification | lt.alert.category_t.dht_notification | lt.alert.category_t.dht_log_notification,
            # "alert_mask": lt.alert.category_t.dht_operation_notification,
        }
    )

    logger.info(f"S [ {ses} ]")

    hashes_to_process = set()
    hashes_processed_wdate = list()

    while not terminate:
        process_alerts(ses=ses, hashes_to_process=hashes_to_process)

        de_queue(ses=ses, hashes_to_process=hashes_to_process, hashes_processed_wdate=hashes_processed_wdate)

        d_now = datetime.now()

        if d_now.second == 27 and d_now.minute % 3 == 0:
            print_session(ses=ses)

        clean_up(ses=ses, d_now=d_now, hashes_processed_wdate=hashes_processed_wdate)

        time.sleep(1)


if __name__ == "__main__":
    main()


# https://www.rasterbar.com/products/libtorrent/single-page-ref.html

# struct alert
# {
#    time_point timestamp () const;
#    virtual int type () const noexcept = 0;
#    virtual char const* what () const noexcept = 0;
#    virtual std::string message () const = 0;
#    virtual alert_category_t category () const noexcept = 0;

#    static constexpr alert_category_t error_notification  = 0_bit;
#    static constexpr alert_category_t peer_notification  = 1_bit;
#    static constexpr alert_category_t port_mapping_notification  = 2_bit;
#    static constexpr alert_category_t storage_notification  = 3_bit;
#    static constexpr alert_category_t tracker_notification  = 4_bit;
#    static constexpr alert_category_t connect_notification  = 5_bit;
#    static constexpr alert_category_t status_notification  = 6_bit;
#    static constexpr alert_category_t ip_block_notification  = 8_bit;
#    static constexpr alert_category_t performance_warning  = 9_bit;
#    static constexpr alert_category_t dht_notification  = 10_bit;
#    static constexpr alert_category_t session_log_notification  = 13_bit;
#    static constexpr alert_category_t torrent_log_notification  = 14_bit;
#    static constexpr alert_category_t peer_log_notification  = 15_bit;
#    static constexpr alert_category_t incoming_request_notification  = 16_bit;
#    static constexpr alert_category_t dht_log_notification  = 17_bit;
#    static constexpr alert_category_t dht_operation_notification  = 18_bit;
#    static constexpr alert_category_t port_mapping_log_notification  = 19_bit;
#    static constexpr alert_category_t picker_log_notification  = 20_bit;
#    static constexpr alert_category_t file_progress_notification  = 21_bit;
#    static constexpr alert_category_t piece_progress_notification  = 22_bit;
#    static constexpr alert_category_t upload_notification  = 23_bit;
#    static constexpr alert_category_t block_progress_notification  = 24_bit;
#    static constexpr alert_category_t all_categories  = alert_category_t::all();
# };
