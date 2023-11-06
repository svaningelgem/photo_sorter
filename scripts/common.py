from hashlib import md5, sha512
from pathlib import Path
from typing import Optional


class HashFileError(FileNotFoundError):
    ...


def calculate_hash(file_path) -> Optional[str]:
    if str(file_path).endswith('.hash'):
        raise HashFileError

    hash_file = Path(str(file_path) + '.hash')
    try:
        return hash_file.read_text()
    except FileNotFoundError:
        ...

    hash_md5 = md5()
    hash_sha512 = sha512()
    with open(file_path, 'rb') as file:
        # Read the file in chunks to avoid memory issues with large files
        for chunk in iter(lambda: file.read(4096), b''):
            hash_md5.update(chunk)
            hash_sha512.update(chunk)

    final = hash_md5.hexdigest() + '_' + hash_sha512.hexdigest()
    hash_file.write_text(final)
    return final


def is_same_file(source: Path, target: Path) -> bool:
    assert source.exists()
    assert target.exists()

    if source.stat().st_size != target.stat().st_size:
        return False  # Filesize is already different, don't bother with calculating hashes!

    source_hash = calculate_hash(source)
    target_hash = calculate_hash(target)

    return source_hash == target_hash
