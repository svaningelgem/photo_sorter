from pathlib import Path
from collections import defaultdict
import shutil


original_file = 'hashes.txt'
count = 20
clean_part = 0


def load_file(filename: str) -> dict[str, set]:
    print("Loading", filename)
    shutil.copy(filename, filename + '~')

    data = defaultdict(set)

    lines = Path(filename).read_text(encoding="utf8").splitlines()

    with open(filename, 'w', encoding="utf8") as fp:
        for line in lines:
            if not line:
                continue

            hash_, filename = line.split(' ', 1)
            if not Path(filename).exists():  # Already gone
                continue

            print(hash_, filename, file=fp)  # Cleanup!
            data[hash_].add(Path(filename))

    return data


def foto_in_sorted(value) -> int:
    total_size = 0

    foto_in_sorted = [file for file in value if 'ToBeSorted' in file.parts]
    foto_not_in_sorted = [file for file in value if 'ToBeSorted' not in file.parts]

    if foto_in_sorted and foto_not_in_sorted:
        for file in foto_in_sorted:
            total_size += file.stat().st_size
            file.unlink()
            Path(str(file)+'.hash').unlink(missing_ok=True)

        return total_size
    return 0


def process_data(data):
    print(f"Processing {len(data)} different files")

    total_size = 0
    still_to_process = count

    for key in list(data):
        value = data[key]
        if len(value) == 1:
            del data[key]
            continue

        if clean_part:
            total_size += foto_in_sorted(value)
            continue

        total_size += list(value)[0].stat().st_size * (len(value) - 1)

        print("-"*80)
        for v in value:
            print("rm", f'"{v}"')

        still_to_process -= 1
        if still_to_process < 0:
            break

    print("Duplicates:", len(data))
    print(f"Wasted size: {total_size:_}")


if __name__ == '__main__':
    process_data(load_file(original_file))
