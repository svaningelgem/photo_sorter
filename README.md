# Photo_sorter
## Purpose
I needed an easy way to sort all my pictures. But I don't want duplicates, and I want to keep all of them organized in a logical way.
What way is better than on the actual date that this picture is taken?

When ran, the script will store pictures under a `YYYY-mm` directory. Images will be called `IMG_<YYYYmmdd>_<HHMMSS>.<suffix>`. Whereas movies will have the `MOV_` prefix.

The location where these `YYYY-mm` directories are stored is under the directories which were provided on the commandline.


## Installation
```bash
mamba env create -f environment.yml
```

## Usage
```bash
mamba activate photo_sorter
python scripts/reorder.py <directory_1> [<directory_2>, ...]
```

## Cleanup
The script will generate a `.hash` file for every file it checks. This is to improve performance and can be safely removed. If you want to remove these, simply execute this:
```bash
find <directory> -type f -name \*.hash -print0 | xargs -0 rm
```
Other files that might go are `desktop.ini` and `Thumbs.db`:
```bash
find <directory> -type f \( -name desktop.ini -o -name Thumbs.db \) -print0 | xargs -0 rm
```
