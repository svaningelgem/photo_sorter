from pathlib import Path
from collections import defaultdict
import shutil


original_file = '/home/papa_fotos/photos/hashes.txt'
shutil.copy(original_file, original_file + '~')

data = defaultdict(set)

lines = Path(original_file).read_text().splitlines()

with open(original_file, 'w') as fp:
    for line in lines:
        if not line:
            continue

        hash_, filename = line.split(' ', 1)
        if not Path(filename).exists():  # Already gone
            continue

        print(hash_, filename, file=fp)  # Cleanup!
        data[hash_].add(filename)


total_size = 0

count = 20
clean_part = 0

for key in list(data):
    value = data[key]
    if len(value) == 1:
        del data[key]
        continue

    total_size += Path(list(value)[0]).stat().st_size * (len(value) - 1)

    if clean_part:
        p1 = next((Path(path) for path in value for part in Path(path).parts if 'afdrukking' in part), None)
        p2 = next((Path(path) for path in value for part in Path(path).parts if 'Wenen' in part), None)
        # p2 = next((Path(path) for path in value if str(Path(path).parent.parent) == '/home/papa_fotos/photos/Backup iPhone/DCIM'), None)

        if p1 and p2:
            p1.unlink()
    else:
        print("-"*80)
        for v in value:
            print("rm", f'"{v}"')

        count -= 1
        if count < 0:
            break

print("Duplicates:", len(data))
print(f"Wasted size: {total_size:_}")
