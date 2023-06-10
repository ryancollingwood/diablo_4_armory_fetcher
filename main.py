import os
import argparse
import requests
import json
from pathlib import Path
from typing import Dict, List, Union
import logging
import logging.handlers

def setup_logger(filename: str):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger_file_handler = logging.handlers.RotatingFileHandler(
        f"{filename}.log",
        maxBytes=1024 * 1024,
        backupCount=1,
        encoding="utf8",
    )
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger_file_handler.setFormatter(formatter)
    logger.addHandler(logger_file_handler)

    # std out logger
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger

class Fetcher(object):
    def __init__(self, account_ids: List[str] = None) -> None:
        self.base_url = "https://d4armory.io/api"
        self.logger = None

        self.account_ids: List[str] = account_ids
        if self.account_ids is None:
            self.account_ids = self.get_account_ids()

        if self.account_ids is None:
            raise ValueError("No account ids to fetch, pass in value or set environment variable: ACCOUNT_ID")
        
        self.logger: logging.Logger = setup_logger("fetch_data")
        self.data_path: Path = self.get_data_path()

    def get_environ_value(self, key: str, default_value = None) -> str:
        logger = self.logger
        if logger is not None:
            logger.debug(f"getting env var: {key}")
        try:
            return os.environ[key]
        except KeyError:
            if logger is not None:
                logger.debug(f"couldn't get env var {key} - using default: {default_value}")
            return default_value
        
    def dumps_json(self, obj) -> str:
        try:
            return json.dumps(obj, ensure_ascii=True)
        except Exception as e:
            self.logger.exception(e)
            raise e

    def get_json(self, url: str) -> Union[List,Dict]:
        self.logger.info(f"fetching json: {url}")
        try:
            r = requests.get(url)

            if r.status_code == 200:
                return r.json()
        except Exception as e:
            self.logger.exception(e)
            raise e
    
    def get_account_ids(self):
        logger = self.logger
        try:
            accounts_ids = self.get_environ_value("ACCOUNT_ID")
            if accounts_ids is None:
                return None
            return accounts_ids.split(",")
        except Exception as e:
            if logger is not None:
                logger.exception(e)
            raise e
        
    def get_data_path(self):
        try:
            data_path: Path = Path(self.get_environ_value("DATA_PATH", "data"))
            data_path.mkdir(exist_ok=True)
            return data_path
        except Exception as e:
            self.logger.exception(e)
            raise e
        
    def char_last_login(self, char_data_path :Path):
        try:
            exisiting_data: Dict = json.loads(char_data_path.read_text())
            last_login = exisiting_data.get("lastLogin")
            self.logger.info(f"last login: {last_login}")
            return last_login
        except Exception as e:
            self.logger.exception(e)
            return None

    def process_char(self, char_data: Dict, account_path: Path):
        try:
            char_id = char_data["id"]
            char_name = char_data["name"]

            self.logger.info(f"fetcing character id: {char_name} - {char_id}")
            account_id: str = account_path.name

            output_path: Path = (account_path / f"{char_name}.json")
            char_details_data = self.get_json(f'{self.base_url}/{account_id}/{char_id}')
            write_data = True

            write_data = self.has_logged_since_last_check(output_path, char_details_data)
            self.logger.info(f"has logged in since last check: {write_data}")

            if write_data:
                output_path.write_text(self.dumps_json(char_details_data))

        except Exception as e:
            self.logger.exception(e)
            raise e

    def has_logged_since_last_check(self, output_path, char_details_data):
        result = True

        if output_path.exists():
            last_login = self.char_last_login(output_path)
            current_login = char_details_data.get("lastLogin")

            if (last_login and current_login):
                if (last_login != current_login):
                    result = True
                    output_path.write_text(self.dumps_json(char_details_data))
                else:
                    self.logger.warning("character hasn't logged in since last fetch")
                    result = False
            else:
                result = True

        return result

    def process_all_chars(self, all_chars_data: Dict, account_path: Path):
        try:
            character_data = all_chars_data.get("characters")
            if character_data is None:
                return
                    
            for char_data in character_data:
                try:
                    self.process_char(char_data, account_path)
                except Exception as e:
                    # try next char
                    continue

        except Exception as e:
            self.logger.exception(e)
            raise e

    def process_account(self, account_id: str):
        self.logger.info(f"processing account: {account_id}")

        data = self.get_json(f'{self.base_url}/{account_id}')

        account_path = self.data_path / str(account_id)
        account_path.mkdir(exist_ok=True)

        (account_path / f"_.json").write_text(self.dumps_json(data))

        self.process_all_chars(data, account_path)

        self.logger.info(f"completed processing account: {account_id}")

    def execute(self):
        self.logger.info("START EXECUTE")

        for account_id in self.account_ids:
            self.process_account(account_id)
        
        self.logger.info("COMPLETE EXECUTE")



if __name__ == "__main__":
    parser = argparse.ArgumentParser("Diablo 4 Armory Fetcher")
    parser.add_argument("account_id", help="Account ID to fetch", type=str, default=None, nargs='?')
    args, unknown = parser.parse_known_args()

    account_ids = None
    if args.account_id:
        account_ids = [args.account_id]

    fetcher = Fetcher(account_ids = account_ids)
    fetcher.execute()
