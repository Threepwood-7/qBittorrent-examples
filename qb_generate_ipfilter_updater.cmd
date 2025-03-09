@ECHO OFF

CD /D %TMP%

ECHO SCRIPT  DIR IS [ %~dp0 ]
ECHO WORKING DIR IS [ %CD% ]

DEL /F /Q GeoIP-legacy.csv GeoIP-legacy.csv.gz

WGET.exe https://mailfud.org/geoip-legacy/GeoIP-legacy.csv.gz

IF %ERRORLEVEL% EQU 0 (
  IF EXIST GeoIP-legacy.csv.gz (

    7Z.exe e GeoIP-legacy.csv.gz

    findstr /V ":" "GeoIP-legacy.csv" > GeoIPCountryWhois.csv

    START "" /D %CD% /MIN /WAIT %~dp0qb_generate_ipfilter.py

    IF EXIST ipfilter.dat (
        COPY /Y ipfilter.dat %APPDATA%\qBittorrent\qb_ipfilter.dat
    )
  )
)

DEL /F /Q GeoIP-legacy.csv GeoIP-legacy.csv.gz
