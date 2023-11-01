from pathlib import Path

from tqdm import tqdm

from common import calculate_hash

with open('hashes.txt', 'a') as fp:
    mylist = sorted(p for p in Path('/home/papa_fotos/photos').rglob('*.*') if p.is_file())
    for file in (bar := tqdm(mylist)):
        bar.set_description(str(file))

        hash_ = calculate_hash(file)
        if hash_:
            print(hash_, file, file=fp)
