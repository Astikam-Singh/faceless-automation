import os
from moviepy.editor import VideoFileClip, vfx
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
        output_path = os.path.join(output_dir, f"clip_{clip_idx}_{suffix}.mp4")
        
        if os.path.exists(output_path):
            return output_path
            
        clip = VideoFileClip(clip_path)
        
        # Crop/Resize logic
        target_ratio = target_w / target_h
        clip_ratio = clip.w / clip.h
        
        if clip_ratio > target_ratio:
            clip = clip.resize(height=target_h)
            x_center = clip.w / 2
            clip = clip.crop(x1=x_center - target_w/2, y1=0, x2=x_center + target_w/2, y2=target_h)
        else:
            clip = clip.resize(width=target_w)
            y_center = clip.h / 2
            clip = clip.crop(x1=0, y1=y_center - target_h/2, x2=target_w, y2=y_center + target_h/2)
            
        clip = clip.resize(newsize=(target_w, target_h))
        clip.write_videofile(output_path, codec='libx264', audio=False, logger=None)
        clip.close()
        return output_path
