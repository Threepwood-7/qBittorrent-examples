import csv
import ipaddress
import re

allow_countries = re.compile(
    "(ad|ar|at|au|be|bg|br|by|ca|ch|cl|co|cy|cz|de|dk|ee|es|eu|fi|fo|fr|gb|gi|gr|hk|hr|hu|ie|il|im|is|it|jp|kr|kw|kz|li|lt|lu|lv|mc|md|me|mk|mt|mx|nl|no|nz|pa|pe|pl|pt|py|qa|ro|rs|ru|se|si|sk|sm|tw|ua|uk|us|uy|uz|va|za)",
    re.IGNORECASE,
)


def read_and_format_csv(file_path, output_path):
    with open(file_path, newline="", encoding="ascii") as csvfile, open(output_path, mode="w", encoding="ascii") as outfile:
        reader = csv.reader(csvfile)
        rows = [row for row in reader if len(row) >= 5 and ":" not in ",".join(row)]

        # Sort IP addresses
        rows.sort(key=lambda x: (ipaddress.ip_address(x[0]), ipaddress.ip_address(x[1])))

        for row in rows:
            field1 = row[0].ljust(16)
            field2 = row[1].ljust(16)
            field4 = row[4].lower()
            field5 = row[5]

            if not allow_countries.match(field4):
                outfile.write(f"{field1}- {field2}, 000 , {field4} {field5}\n")


file_path = "GeoIP-legacy.csv"  # download it from https://mailfud.org/geoip-legacy/GeoIP-legacy.csv.gz
output_path = "ipfilter.dat"

read_and_format_csv(file_path, output_path)
