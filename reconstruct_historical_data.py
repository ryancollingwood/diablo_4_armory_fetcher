import argparse
import json
from pathlib import Path
from git import Repo


def write_jsonl_changes(output_path, file_stem, revlist):
    # produce jsonlines output see: https://jsonlines.org/
    output_file = output_path / f"{file_stem}.jsonl"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf8") as outfile:
        for commit, filecontents in revlist:
            change_timestamp = int(commit.committed_datetime.timestamp())
            char_data = json.loads(filecontents.decode("utf8"))
            data = {"_timestamp": change_timestamp, "_hexsha": commit.hexsha, "data": char_data}
            outfile.write(f"{json.dumps(data, ensure_ascii=False, indent=None)}\n")

def write_individual_changes(output_path, file_stem, file_suffix, revlist):
    for commit, filecontents in revlist:
        change_timestamp = int(commit.committed_datetime.timestamp())
        output_file = output_path / f"{file_stem}/{change_timestamp}{file_suffix}"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        output_file.write_text(filecontents.decode("utf8"))      

if __name__ == "__main__":
    repo = Repo()

    parser = argparse.ArgumentParser("Diablo 4 Armory Fetcher - Data Builder")
    parser.add_argument("input_dir", help="Directory to source the files - default `data`", type=str, default="data", nargs='?')
    parser.add_argument("output_dir", help="Directory to place rebuilt files", type=str, default="data_history", nargs='?')
    parser.add_argument("jsonl", help="Write to json line format, if False indivdual files for indivdual changes will be written", type=bool, default=True, nargs='?')
    parser.add_argument("glob", help="Glob pattern to get files to retrieve history - relative to input_dir - default `'*/*.json'`", type=str, default="*/*.json", nargs='?')
    

    args, unknown = parser.parse_known_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    jsonl = args.jsonl
    glob_pattern = args.glob

    for json_file in Path(input_dir).glob(glob_pattern):
        file_name = json_file.name
        if file_name == "_.json":
            continue

        file_stem = json_file.stem
        file_suffix = json_file.suffix

        file_ext = json_file.suffix
        output_path = Path(output_dir) / json_file.parents[0].name
        
        revlist = (
            (commit, (commit.tree / str(json_file.as_posix())).data_stream.read())
            for commit in repo.iter_commits(paths=str(json_file))
        )

        if jsonl:
            write_jsonl_changes(output_path, file_stem, revlist)
        else:
            write_individual_changes(output_path, file_stem, file_suffix, revlist)
