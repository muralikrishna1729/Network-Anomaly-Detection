import os
import urllib.request

from src import config


def download():
	os.makedirs(config.DATA_DIR, exist_ok=True)
	for path, url in (
		(config.TRAIN_PATH, config.TRAIN_URL),
		(config.TEST_PATH, config.TEST_URL),
	):
		if os.path.exists(path):
			print(f"[skip] {os.path.basename(path)} already exists")
			continue
		print(f"[download] {os.path.basename(path)}")
		urllib.request.urlretrieve(url, path)
		print(f"[done] saved to {path}")


if __name__ == "__main__":
	download()
