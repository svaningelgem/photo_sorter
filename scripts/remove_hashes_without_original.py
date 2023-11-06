import sys
from pathlib import Path

from tqdm import tqdm

for folder in sys.argv[1:]:
    folder = Path(folder)
    if not folder.exists():
        print(f"{folder} doesn't exist anymore!")
        continue

    print(f"Loading files in {folder}:")
    mylist = {p.resolve().absolute() for p in folder.rglob('*.*') if p.is_file()}

    for file in (bar := tqdm(sorted(mylist))):
        bar.set_description(str(file))

        # Cleanup hash files without an original one
        if file.suffix.lower() == '.hash':
            original_file = Path(str(file)[:-5])
            if original_file not in mylist and not original_file.exists():  # First check against the list in memory. It'll be faster than going to the filesystem every time.
                print(file)
                # file.unlink()
            continue

    print("")
