#!/usr/bin/python3
import argparse
import string
import sys
import traceback

import requests
import logging
import json
from datetime import datetime, timezone

API_URL = "https://api.mullvad.net/public/accounts/v1"


class MullvadAccount:
    def __init__(self, url: string, args: argparse.Namespace):
        self.url = url
        self.account = args.account
        self.warning = args.warning
        self.critical = args.critical
        log = logging.getLogger("urllib3")
        stream = logging.StreamHandler()
        if args.verbose:
            log.setLevel(logging.DEBUG)
            stream.setLevel(logging.DEBUG)
        log.addHandler(stream)
        self.log = log

    def fetch_mullvad_account_information(self, account: int) -> dict:
        response = requests.get(self.url + f"/{account}/")
        status_code = response.status_code
        try:
            data = response.json()
            self.log.debug(json.dumps(data, indent=4))
        except Exception:
            print(
                f"UNKNOWN - Mullvad API did not respond with valid JSON (Returned code HTTP {status_code})"
            )
            sys.exit(3)
        if status_code == 404:
            print("CRITICAL - Code 404: Mullvad account not found")
            sys.exit(2)
        elif status_code != 200:
            print(f"UNKNOWN - Mullvad API HTTP ERROR {status_code}")
            sys.exit(3)
        return data

    def check_expiration_date(self, now: datetime) -> None:
        try:
            data = self.fetch_mullvad_account_information(self.account)

            if "expiry" not in data:
                raise Exception("Expiry date missing in API return")

            isotime = data["expiry"]
            date_of_expiration = datetime.fromisoformat(isotime)
            delta = date_of_expiration - now
            day_string = "day" if delta.days == 1 else "days"
            print_info = (
                "Mullvad VPN account expiration in "
                + str(delta.days)
                + " "
                + day_string
                + " ("
                + date_of_expiration.strftime("%Y-%m-%d %H:%M:%S %Z")
                + ")"
                + "|days_till_exp="
                + str(delta.days)
                + f";{self.warning};{self.critical}"
            )

            if delta.days <= self.critical:
                print("CRITICAL -", print_info)
                sys.exit(2)
            elif delta.days <= self.warning:
                print("WARNING -", print_info)
                sys.exit(1)
            elif delta.days > self.warning:
                print("OK -", print_info)
                sys.exit(0)
            else:
                print("UNKNOWN -", print_info)
                sys.exit(3)
        except Exception as e:
            self.log.debug(traceback.format_exc())
            print("UNKNOWN - Error Occurred: ", e)
            sys.exit(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mullvad account expiration date checker"
    )
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "--account",
        "-a",
        type=int,
        metavar="<YOUR_ACCOUNT_NUMBER>",
        help="Mullvad account-number to check (int)",
        required=True,
    )
    parser.add_argument(
        "--warning", "-w", type=int, metavar="<DAYS>", help="warning days", default=14
    )
    parser.add_argument(
        "--critical", "-c", type=int, metavar="<DAYS>", help="critical days", default=7
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parseargs = parser.parse_args()

    check = MullvadAccount(API_URL, parseargs)
    check.check_expiration_date(datetime.now(timezone.utc))
