import os
import yaml
from moviepy.editor import AudioFileClip, ColorClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips, vfx

class VideoRenderer:
    def __init__(self, config_path="config.yaml", is_longform=False):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
        
        # Select resolution based on format
        res_key = 'resolution_longform' if is_longform else 'resolution_shortform'
        self.width, self.height = self.config['niche'][res_key]
        self.is_longform = is_longform

    def render(self, audio_path: str, script_segments: list, output_path: str = "output/final_video.mp4"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        brand_name = self.config['niche'].get('brand_name', 'Ancient Mindset Lab')

        clips = []
        seg_duration = duration / max(1, len(script_segments))
        
        for i, _ in enumerate(script_segments):
            clip_path = f"output/clip_{i}.mp4"
            if os.path.exists(clip_path):
                try:
                    c = VideoFileClip(clip_path)
                    print(f"Loaded clip {clip_path}: {c.w}x{c.h}, duration={c.duration:.2f}s")
                    
                    if c.w == 0 or c.h == 0:
                        raise ValueError(f"Clip {clip_path} has zero dimensions.")
                    
                    # Ensure clip is long enough
                    if c.duration < seg_duration:
                        c = c.fx(vfx.loop, duration=seg_duration)
                    else:
                        c = c.subclip(0, seg_duration)
                    
                    # Set fps
                    c = c.set_fps(self.config['niche']['fps'])
                    
                    # Fix visuals: Resize to fill frame (16:9 landscape)
                    target_ratio = self.width / self.height
                    clip_ratio = c.w / c.h
                    
                    if clip_ratio > target_ratio:
                        c = c.resize(height=self.height)
                        x_center = c.w / 2
                        c = c.crop(x1=x_center - self.width/2, y1=0, x2=x_center + self.width/2, y2=self.height)
                    else:
                        c = c.resize(width=self.width)
                        y_center = c.h / 2
                        c = c.crop(x1=0, y1=y_center - self.height/2, x2=self.width, y2=y_center + self.height/2)
                    
                    # Resize to exact target dimensions
                    c = c.resize(newsize=(self.width, self.height))
                    clips.append(c)
                except Exception as e:
                    print(f"Failed to load clip {clip_path}: {e}")
                    clips.append(ColorClip(size=(self.width, self.height), color=(20, 20, 20), duration=seg_duration))
            else:
                clips.append(ColorClip(size=(self.width, self.height), color=(20, 20, 20), duration=seg_duration))

        final_visuals = concatenate_videoclips(clips, method="compose") if clips else ColorClip(size=(self.width, self.height), color=(20, 20, 20), duration=duration)
        
        overlay_elements = [final_visuals]

        # 1. Add Watermark (Logo or Text)
        logo_path = self.config['assets'].get('logo_path')
        if os.path.exists(logo_path):
            from moviepy.editor import ImageClip
            watermark = ImageClip(logo_path).set_duration(duration).set_opacity(self.config['assets']['watermark_opacity']).resize(width=self.width*0.1)
            watermark = watermark.set_position(("right", "top"))
            overlay_elements.append(watermark)
        else:
            # Fallback text watermark if no logo
            from moviepy.config import change_settings
            try:
                txt_watermark = TextClip(brand_name, fontsize=30, color='white', font='Arial-Bold').set_duration(duration).set_opacity(0.3).set_position(("right", "top"))
                overlay_elements.append(txt_watermark)
            except:
                print("Skipping text watermark (ImageMagick missing)")

        # 2. Add Subscribe Animation at the end
        anim_path = self.config['assets'].get('subscribe_anim_path')
        if os.path.exists(anim_path):
            sub_anim = VideoFileClip(anim_path).resize(width=self.width*0.3).set_position(("center", "bottom")).set_start(duration - 5)
            overlay_elements.append(sub_anim)

        video = CompositeVideoClip(overlay_elements).set_audio(audio_clip)
        
        # Windows-specific fix for temp file permission errors
        temp_audio = os.path.join(os.path.dirname(output_path), "temp_audio_render.m4a")
        
        video.write_videofile(
            output_path,
            fps=self.config['niche']['fps'],
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=temp_audio,
            remove_temp=True
        )
        
        # Cleanup
        for c in clips: c.close()
        audio_clip.close()
        return output_path

if __name__ == "__main__":
    renderer = VideoRenderer()
    print("VideoRenderer initialized.")
