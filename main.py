import os
import argparse
import requests
import json
from time import sleep
from pathlib import Path
from typing import Dict, List, Union, Any
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
        self.base_url = "https://d4armory.io/api/armory"
        self.config_valid = False
        self.logger = None

        self.account_ids: List[str] = account_ids
        if self.account_ids is None:
            self.account_ids = self.get_account_ids()

        if self.account_ids is None:
            print("No account ids to fetch, pass in value or set environment variable: ACCOUNT_ID")            
            return
        
        self.profile_queue_attempts = int(self.get_environ_value("PROFILE_QUEUE_ATTEMPTS", "3"))
        self.profile_queue_sleep = float(self.get_environ_value("PROFILE_QUEUE_ATTEMPTS", "5"))
        
        self.logger: logging.Logger = setup_logger("fetch_data")
        self.data_path: Path = self.get_data_path()

        self.config_valid = True

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
        self.logger.debug(f"fetching json: {url}")
        try:
            r = requests.get(url)

            if r.status_code == 200:
                return r.json()
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"connection error when accessing: {url}")
            raise e
        except Exception as e:
            self.logger.exception(e)
            raise e
    
    def get_account_ids(self):
        logger = self.logger
        try:
            accounts_ids = self.get_environ_value("ACCOUNT_ID")
            if accounts_ids is None or not accounts_ids:
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

    def process_char(self, char_data: Dict, account_path: Path, attempt_num: int = 0):
        try:
            char_id = char_data.get("id", None)
            char_name = char_data.get("name", None)

            if not char_id or not char_name:
                self.logger.error(f"Didn't get character id or name from response - char_id: {char_id} - char_name: {char_name}")
                return

            self.logger.info(f"fetching character id: {char_name} - {char_id}")
            account_id: str = account_path.name

            output_path: Path = (account_path / f"{char_name}.json")
            char_details_data: Dict[str, Any] = self.get_json(f'{self.base_url}/{account_id}/{char_id}')

            if attempt_num < self.profile_queue_attempts:
                queue: int = char_details_data.get("queue", -1)
                if queue > 0:
                    self.logger.info(f"queue position {queue} - sleeping for {self.profile_queue_attempts} seconds")
                    sleep(self.profile_queue_attempts)
                    self.process_char(char_data, account_path, attempt_num + 1)
                    return

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
    if fetcher.config_valid:        
        fetcher.execute()
