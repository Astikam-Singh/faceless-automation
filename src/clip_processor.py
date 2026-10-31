import os
import subprocess

import imageio_ffmpeg
import yaml

class ClipProcessor:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
        self.long_w, self.long_h = self.config['niche']['resolution_longform']
        self.short_w, self.short_h = self.config['niche']['resolution_shortform']

    def process_clip(self, clip_path, clip_idx, is_longform=True):
        """Processes clip (crop/resize) and saves as intermediate file."""
        output_dir = "output/processed"
        os.makedirs(output_dir, exist_ok=True)
        
        target_w = self.long_w if is_longform else self.short_w
        target_h = self.long_h if is_longform else self.short_h
        suffix = "long" if is_longform else "short"
        source_name = os.path.splitext(os.path.basename(clip_path))[0]
        output_path = os.path.join(output_dir, f"{source_name}_{clip_idx}_{suffix}.mp4")
        
        if os.path.exists(output_path):
            return output_path
            
        fps = self.config['niche']['fps']
        scale_and_crop = (
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h},fps={fps}"
        )
        subprocess.run(
            [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-y",
                "-loglevel", "error",
                "-i", clip_path,
                "-t", "6",
                "-vf", scale_and_crop,
                "-an",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                output_path,
            ],
            check=True,
        )
        return output_path
