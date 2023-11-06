from pathlib import Path

from tqdm import tqdm

from common import calculate_hash

with open('hashes.txt', 'a', encoding='utf8') as fp:
    folders = [
    ]

    for folder in folders:
        folder = Path(folder)
        if not folder.exists():
            print(f"{folder} doesn't exist anymore!")
            continue

        mylist = {p.resolve().absolute() for p in folder.rglob('*.*') if p.is_file()}
        for file in (bar := tqdm(sorted(mylist))):
            # Cleanup hash files without an original one
            if file.suffix.lower() == '.hash':
                continue

            bar.set_description(str(file))

            try:
                hash_ = calculate_hash(file)
                print(hash_, file, file=fp)
            except FileNotFoundError:
                continue

        print("")
