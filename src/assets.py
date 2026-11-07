import json
import math
import os
import random
import time

import requests

from src.config_loader import load_config


class AssetFetcher:
    def __init__(self, history_path=None):
        self.config = load_config()
        self.pexels_key = os.getenv("PEXELS_API_KEY", self.config.get("pexels_api_key", ""))
        self.history_path = history_path or os.path.join("output", "used_pexels_videos.json")
        os.makedirs(os.path.dirname(os.path.abspath(self.history_path)), exist_ok=True)

    def _reserve_asset_id(self, asset_id):
        lock_path = f"{self.history_path}.lock"
        with open(lock_path, "a+b") as lock_file:
            if os.fstat(lock_file.fileno()).st_size == 0:
                lock_file.write(b"0")
                lock_file.flush()
            lock_file.seek(0)

            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

            try:
                try:
                    with open(self.history_path, "r", encoding="utf-8") as history_file:
                        used_ids = set(json.load(history_file))
                except (FileNotFoundError, json.JSONDecodeError):
                    used_ids = set()

                asset_id = str(asset_id)
                if asset_id in used_ids:
                    return False

                used_ids.add(asset_id)
                temp_path = f"{self.history_path}.{os.getpid()}.tmp"
                with open(temp_path, "w", encoding="utf-8") as history_file:
                    json.dump(sorted(used_ids), history_file)
                os.replace(temp_path, self.history_path)
                return True
            finally:
                lock_file.seek(0)
                if os.name == "nt":
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _select_video_file(video_files, orientation):
        dimension = "height" if orientation == "portrait" else "width"
        candidates = [item for item in video_files if item.get("link")]
        if not candidates:
            return None

        target_dimension = 1920
        sufficient = [
            item for item in candidates
            if item.get(dimension, 0) >= target_dimension
        ]
        if sufficient:
            return min(sufficient, key=lambda item: item.get(dimension, 0))
        return max(candidates, key=lambda item: item.get(dimension, 0))

    def fetch_video(self, query: str, output_path: str = "output/clip.mp4", orientation="landscape"):
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if not self.pexels_key or self.pexels_key == "YOUR_PEXELS_API_KEY":
            print(f"Warning: Pexels API key not set. Cannot fetch a unique shot for '{query}'.")
            return None

        fallback_queries = [
            query,
            " ".join([w for w in query.split() if len(w) > 3][:3]) if len(query.split()) > 2 else "",
            "stoic philosophy",
            "ancient marble bust",
            "dark cinematic background"
        ]
        fallback_queries = [q for q in dict.fromkeys(fallback_queries) if q]

        headers = {"Authorization": self.pexels_key}
        url = "https://api.pexels.com/videos/search"
        
        videos = []
        for q in fallback_queries:
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    params={"query": q, "orientation": orientation, "per_page": 80},
                    timeout=30,
                )
                if response.status_code == 200:
                    videos = response.json().get("videos", [])
                    if videos:
                        break
            except requests.RequestException:
                continue

        if not videos:
            print(f"Pexels search failed for all fallbacks of '{query}'.")
            return None

        random.shuffle(videos)
        for video in videos:
            asset_id = video.get("id")
            video_files = video.get("video_files", [])
            if asset_id is None or not video_files:
                continue

            best_file = self._select_video_file(video_files, orientation)
            if not best_file or not best_file.get("link"):
                continue
            if not self._reserve_asset_id(asset_id):
                continue

            download_url = best_file["link"]
            print(f"   Downloading unique Pexels video {asset_id}: {download_url[:50]}...")
            for attempt in range(3):
                try:
                    with requests.get(download_url, stream=True, timeout=60) as download:
                        download.raise_for_status()
                        with open(output_path, "wb") as output_file:
                            for chunk in download.iter_content(chunk_size=8192):
                                if chunk:
                                    output_file.write(chunk)
                    print(f"   Saved unique shot: {output_path}")
                    return output_path
                except requests.RequestException as error:
                    print(f"   Download attempt {attempt + 1} failed: {error}")
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    if attempt < 2:
                        time.sleep(2)

        print(f"No unused Pexels videos found for '{query}'.")
        return None

    def fetch_video_shots(self, segments, duration, output_prefix, orientation="landscape", shot_seconds=5):
        shot_count = max(1, math.ceil(duration / shot_seconds))
        queries = [
            segment.get("visual_prompt") or segment.get("text", "cinematic stoic philosophy")
            for segment in segments
            if isinstance(segment, dict)
        ]
        if not queries:
            queries = ["cinematic stoic philosophy"]

        paths = []
        for index in range(shot_count):
            query = queries[index % len(queries)]
            path = self.fetch_video(
                query,
                f"{output_prefix}_shot_{index:03d}.mp4",
                orientation=orientation,
            )
            if path:
                paths.append(path)
        return paths


if __name__ == "__main__":
    fetcher = AssetFetcher()
    fetcher.fetch_video("dark moody cinematic stoicism")