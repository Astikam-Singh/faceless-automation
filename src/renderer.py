import os
import shutil
import subprocess
import tempfile

import imageio_ffmpeg
from moviepy.editor import AudioFileClip, VideoFileClip, CompositeVideoClip
from src.config_loader import load_config

class VideoRenderer:
    def __init__(self, is_longform=False):
        self.config = load_config()
        
        # Select resolution based on format
        res_key = 'resolution_longform' if is_longform else 'resolution_shortform'
        self.width, self.height = self.config['niche'][res_key]
        self.is_longform = is_longform

    @staticmethod
    def _shot_duration(audio_duration, clip_count):
        if clip_count < 1:
            raise ValueError("Cannot render without unique video clips.")
        shot_duration = audio_duration / clip_count
        if shot_duration > 6:
            raise ValueError(
                f"Only {clip_count} unique clips were fetched for {audio_duration:.1f}s of audio. "
                "Fetch more unique clips so no shot exceeds six seconds."
            )
        return shot_duration

    @staticmethod
    def _allocate_shot_durations(audio_duration, source_durations, target_shot=5, max_shot=6):
        if not source_durations:
            raise ValueError("Cannot render without unique video clips.")

        capacities = [min(max(0.0, source_duration), max_shot) for source_duration in source_durations]
        if sum(capacities) + 10.0 < audio_duration:
            raise ValueError(
                f"Fetched footage covers at most {sum(capacities):.1f}s of {audio_duration:.1f}s audio. "
                "Fetch more unique clips; footage will not be looped."
            )
        elif sum(capacities) < audio_duration:
            diff = audio_duration - sum(capacities)
            capacities[-1] += diff + 0.1

        durations = [min(capacity, target_shot) for capacity in capacities]
        remaining = max(0.0, audio_duration - sum(durations))
        for index, capacity in enumerate(capacities):
            extra = min(max(0.0, capacity - durations[index]), remaining)
            durations[index] += extra
            remaining -= extra
            if remaining <= 0.05:
                break

        if remaining > 0.05:
            raise ValueError("Could not allocate enough unique footage without exceeding six seconds per shot.")
        return durations

    @staticmethod
    def _get_source_durations(processed_clips_paths):
        durations = []
        for clip_path in processed_clips_paths:
            try:
                clip = VideoFileClip(clip_path)
            except Exception as error:
                raise RuntimeError(f"Could not use unique shot {clip_path}: {error}") from error
            try:
                durations.append(clip.duration)
            finally:
                clip.close()
        return durations

    @staticmethod
    def _concat_manifest_entry(clip_path):
        absolute_path = os.path.abspath(clip_path).replace("\\", "/")
        escaped_path = absolute_path.replace("'", "'\\''")
        return f"file '{escaped_path}'\n"

    def render(self, audio_path: str, processed_clips_paths: list, output_path: str = "output/final_video.mp4"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        brand_name = self.config['niche'].get('brand_name', 'Ancient Mindset Lab')
        try:
            source_durations = self._get_source_durations(processed_clips_paths)
            self._allocate_shot_durations(duration, source_durations)
        except Exception:
            audio_clip.close()
            raise

        temporary_dir = tempfile.mkdtemp(prefix="render_", dir=os.path.dirname(output_path))
        concat_manifest = os.path.join(temporary_dir, "clips.txt")
        visuals_path = os.path.join(temporary_dir, "visuals.mp4")
        final_visuals = None
        video = None
        overlay_elements = []
        try:
            with open(concat_manifest, "w", encoding="utf-8", newline="\n") as manifest:
                manifest.writelines(
                    self._concat_manifest_entry(path) for path in processed_clips_paths
                )

            fps = self.config['niche']['fps']
            subprocess.run(
                [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-y",
                    "-loglevel", "error",
                    "-fflags", "+genpts",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_manifest,
                    "-t", f"{duration:.6f}",
                    "-an",
                    "-vf", f"setpts=PTS-STARTPTS,fps={fps},format=yuv420p",
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-crf", "23",
                    "-movflags", "+faststart",
                    visuals_path,
                ],
                check=True,
            )

            final_visuals = VideoFileClip(visuals_path)
            print(f"DEBUG: Visual duration: {final_visuals.duration}, Audio duration: {duration}")
            
            # If unique footage is insufficient, loop to fill the audio duration
            if final_visuals.duration < duration - 0.05:
                print(f"⚠️ Unique shots cover only {final_visuals.duration:.1f}s of {duration:.1f}s audio. Looping footage to fill duration...")
                
                # Close the current clip and recreate with looping
                final_visuals.close()
                
                # Use FFmpeg to loop the video to match audio duration to a temporary file
                looped_visuals_path = visuals_path.replace(".mp4", "_looped.mp4")
                subprocess.run(
                    [
                        imageio_ffmpeg.get_ffmpeg_exe(),
                        "-y",
                        "-loglevel", "error",
                        "-stream_loop", str(int((duration / final_visuals.duration) + 1)),
                        "-i", visuals_path,
                        "-t", f"{duration:.6f}",
                        "-c:v", "libx264",
                        "-preset", "veryfast",
                        "-crf", "23",
                        "-movflags", "+faststart",
                        looped_visuals_path,
                    ],
                    check=True,
                )
                
                # Replace the original with the looped version
                final_visuals.close()
                os.replace(looped_visuals_path, visuals_path)
                final_visuals = VideoFileClip(visuals_path)
                
                final_visuals = VideoFileClip(visuals_path)
                print(f"✅ Looped visual duration: {final_visuals.duration}, Audio duration: {duration}")
            
            final_visuals = final_visuals.subclip(0, duration)
            overlay_elements = [final_visuals]

            logo_path = self.config['assets'].get('logo_path')
            if os.path.exists(logo_path):
                from moviepy.editor import ImageClip
                watermark = ImageClip(logo_path).set_duration(duration).set_opacity(
                    self.config['assets']['watermark_opacity']
                ).resize(width=self.width * 0.1)
                watermark = watermark.set_position(("right", "top"))
                overlay_elements.append(watermark)
            else:
                try:
                    from moviepy.editor import TextClip
                    txt_watermark = TextClip(
                        brand_name, fontsize=30, color='white', font='Arial-Bold'
                    ).set_duration(duration).set_opacity(0.3).set_position(("right", "top"))
                    overlay_elements.append(txt_watermark)
                except Exception:
                    print("Skipping text watermark (ImageMagick missing)")

            anim_path = self.config['assets'].get('subscribe_anim_path')
            if os.path.exists(anim_path):
                sub_anim = VideoFileClip(anim_path).resize(width=self.width * 0.3)
                sub_anim = sub_anim.set_position(("center", "bottom")).set_start(duration - 5)
                overlay_elements.append(sub_anim)

            video = CompositeVideoClip(overlay_elements).set_audio(audio_clip)
            unique_suffix = os.path.basename(output_path).replace('.mp4', '')
            temp_audio = os.path.join(os.path.dirname(output_path), f"temp_audio_{unique_suffix}.m4a")
            video.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                bitrate='10000k',
                temp_audiofile=temp_audio,
                remove_temp=True,
            )
        finally:
            if video is not None:
                video.close()
            if final_visuals is not None:
                final_visuals.close()
            for overlay in overlay_elements[1:]:
                overlay.close()
            audio_clip.close()
            shutil.rmtree(temporary_dir, ignore_errors=True)
        return output_path

if __name__ == "__main__":
    renderer = VideoRenderer()
    print("VideoRenderer initialized.")
