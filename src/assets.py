import os
import requests
import yaml

class AssetFetcher:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
        
        self.pexels_key = os.getenv("PEXELS_API_KEY", self.config.get("pexels_api_key", ""))

    def fetch_video(self, query: str, output_path: str = "output/clip.mp4"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if not self.pexels_key or self.pexels_key == "YOUR_PEXELS_API_KEY":
            # Fallback placeholder or sample video if no key provided
            print(f"Warning: Pexels API key not set. Using placeholder path for '{query}'.")
            return None

        headers = {"Authorization": self.pexels_key}
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=landscape&per_page=1"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            videos = data.get("videos", [])
            if videos:
                video_files = videos[0].get("video_files", [])
                
                # Try to get best landscape file (width >= 1280)
                best_file = None
                # Sort by width descending to get the highest resolution available
                sorted_files = sorted(video_files, key=lambda x: x.get("width", 0), reverse=True)
                
                for vf in sorted_files:
                    if vf.get("width", 0) >= 1280:
                        best_file = vf
                        break
                
                if not best_file and sorted_files:
                    best_file = sorted_files[0]
                
                if best_file:
                    download_url = best_file["link"]
                    v_data = requests.get(download_url)
                    with open(output_path, "wb") as f:
                        f.write(v_data.content)
                    return output_path
        return None

if __name__ == "__main__":
    fetcher = AssetFetcher()
    fetcher.fetch_video("dark moody cinematic stoicism")
