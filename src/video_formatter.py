import os
import yaml
from moviepy.editor import VideoFileClip, concatenate_videoclips, ColorClip

class VideoFormatter:
    """
    Handles multi-format video generation:
    - Long-form (10-12 minutes) for YouTube
    - Short-form (45-60 seconds) for Instagram Reels & YouTube Shorts
    """
    
from src.config_loader import load_config
from moviepy.editor import VideoFileClip, concatenate_videoclips, ColorClip

class VideoFormatter:
    """
    Handles multi-format video generation:
    - Long-form (10-12 minutes) for YouTube
    - Short-form (45-60 seconds) for Instagram Reels & YouTube Shorts
    """
    
    def __init__(self, is_longform=False):
        self.config = load_config()
        
        # Select resolution based on format
        res_key = 'resolution_longform' if is_longform else 'resolution_shortform'
        self.width, self.height = self.config['niche'][res_key]
        self.is_longform = is_longform
    
    def create_longform_video(self, base_video_path, num_repeats=5, output_path="output/longform_youtube.mp4"):
        """
        Create long-form video (10-12 mins) by repeating and extending the base video.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Load base video
        base_clip = VideoFileClip(base_video_path)
        base_duration = base_clip.duration
        target_duration = 10 * 60  # 10 minutes
        
        print(f"DEBUG: Base video duration is {base_duration}s")
        
        # Calculate repeats needed
        num_repeats = int(target_duration / base_duration) + 1
        
        print(f"Creating long-form video: {base_duration:.1f}s × {num_repeats} = {base_duration * num_repeats:.1f}s")
        
        # Create long-form by concatenating repeated clips
        clips = [base_clip for _ in range(num_repeats)]
        print(f"DEBUG: Number of clips concatenated: {len(clips)}")
        longform = concatenate_videoclips(clips)
        print(f"DEBUG: Concatenated video duration: {longform.duration}s")
        
        # Trim to exact target duration
        longform = longform.subclip(0, target_duration)
        print(f"DEBUG: Final long-form video duration: {longform.duration}s")
        
        # Write output
        print(f"Rendering long-form video ({target_duration/60:.1f} mins)...")
        longform.write_videofile(
            output_path,
            fps=self.config['niche']['fps'],
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        base_clip.close()
        longform.close()
        
        return output_path
    
    def create_shortform_video(self, base_video_path, max_duration=60, output_path="output/shortform_reels.mp4"):
        """
        Create short-form video (45-60 seconds) by trimming or extending the base video.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Load base video
        base_clip = VideoFileClip(base_video_path)
        base_duration = base_clip.duration
        
        if base_duration >= max_duration:
            # Trim to max duration
            shortform = base_clip.subclip(0, max_duration)
            print(f"Trimming to {max_duration}s for short-form")
        else:
            # Extend by looping
            num_repeats = int(max_duration / base_duration) + 1
            clips = [base_clip for _ in range(num_repeats)]
            shortform = concatenate_videoclips(clips).subclip(0, max_duration)
            print(f"Extending to {max_duration}s for short-form")
        
        # Write output
        print(f"Rendering short-form video ({max_duration}s)...")
        shortform.write_videofile(
            output_path,
            fps=self.config['niche']['fps'],
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        base_clip.close()
        shortform.close()
        
        return output_path

if __name__ == "__main__":
    formatter = VideoFormatter(is_longform=True)
    
    # Example: Create both formats from base video
    base_video = "output/final_video.mp4"
    if os.path.exists(base_video):
        longform = formatter.create_longform_video(base_video)
        print(f"\n✅ Long-form video: {longform}")
        
        shortform = formatter.create_shortform_video(base_video)
        print(f"✅ Short-form video: {shortform}")
