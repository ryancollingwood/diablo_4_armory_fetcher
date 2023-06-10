import os
import requests
import json
from pathlib import Path
from typing import Dict, List, Union
import logging
import logging.handlers

def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger_file_handler = logging.handlers.RotatingFileHandler(
        "status.log",
        maxBytes=1024 * 1024,
        backupCount=1,
        encoding="utf8",
    )
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger_file_handler.setFormatter(formatter)
    logger.addHandler(logger_file_handler)

    return logger

class Fetcher(object):
    def __init__(self) -> None:
        self.base_url = "https://d4armory.io/api"
        self.logger: logging.Logger = setup_logger()
        self.account_ids: List[str] = self.get_account_ids()
        self.data_path: Path = self.get_data_path()

    def get_environ_value(self, key: str, default_value = None) -> str:
        self.logger.debug(f"getting env var: {key}")
        try:
            return os.environ[key]
        except KeyError:
            self.logger.debug(f"couldn't get env var {key} - using default: {default_value}")
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
        try:
            accounts_ids = self.get_environ_value("ACCOUNT_ID")
            return accounts_ids.split(",")
        except Exception as e:
            self.logger.exception(e)
            raise e
        
    def get_data_path(self):
        try:
            data_path: Path = Path(self.get_environ_value("DATA_PATH", "data"))
            data_path.mkdir(exist_ok=True)
            return data_path
        except Exception as e:
            self.logger.exception(e)
            raise e   

    def process_char(self, char_data: Dict, account_path: Path):
        try:
            char_id = char_data["id"]
            self.logger.info(f"fetcing character id: {char_id}")
            account_id: str = account_path.name
            
            char_details_data = self.get_json(f'{self.base_url}/{account_id}/{char_id}')
            (account_path / f"{char_id}.json").write_text(self.dumps_json(char_details_data))
        except Exception as e:
            self.logger.exception(e)
            raise e

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

        account_path = self.data_path / account_id
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
    fetcher = Fetcher()
    fetcher.execute()
