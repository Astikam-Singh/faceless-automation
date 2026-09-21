"""
Thumbnail generator for Ancient Mindset Lab videos
"""
import os
import yaml
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip

class ThumbnailGenerator:
    """
    Generates custom thumbnails for YouTube videos with brand styling.
    """
    
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
        
        self.width = self.config['niche'].get('thumbnail_width', 1280)
        self.height = self.config['niche'].get('thumbnail_height', 720)
        self.brand_name = self.config['niche']['brand_name']
        self.logo_path = self.config['assets'].get('logo_path', '')
        
        # Brand colors
        self.colors = {
            'background': '#1A1A1A',  # Dark charcoal
            'accent': '#C9A227',      # Antique gold
            'text': '#FFFFFF',        # White
            'secondary': '#4A5568'    # Slate gray
        }
    
    def generate_from_video(self, video_path, title, output_path=None):
        """
        Generate thumbnail from video frame with custom styling.
        """
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return None
        
        if output_path is None:
            base = os.path.splitext(video_path)[0]
            output_path = f"{base}_thumbnail.jpg"
        
        # Extract frame from video (first 5 seconds or middle)
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            
            # Get frame at 10% of duration (avoid black intro)
            timestamp = min(duration * 0.1, 5)
            frame = clip.get_frame(timestamp)
            clip.close()
            
            # Convert numpy array to PIL Image
            img = Image.fromarray(frame.astype('uint8'))
            
            # Resize and crop to fill thumbnail dimensions
            target_ratio = self.width / self.height
            img_ratio = img.width / img.height
            
            if img_ratio > target_ratio:
                # Clip is wider than target: resize height to match target
                new_height = self.height
                new_width = int(new_height * img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                left = (new_width - self.width) / 2
                img = img.crop((left, 0, left + self.width, self.height))
            else:
                # Clip is taller than target: resize width to match target
                new_width = self.width
                new_height = int(new_width / img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                top = (new_height - self.height) / 2
                img = img.crop((0, top, self.width, top + self.height))
            
            # Add dark gradient overlay at bottom for text readability
            for y in range(self.height - 200, self.height):
                alpha = int(180 * (y - (self.height - 200)) / 200)
                # Create a transparent overlay for this row
                overlay_row = Image.new('RGBA', (self.width, 1), (0, 0, 0, alpha))
                # Paste the overlay row onto the image
                img = img.convert('RGBA')
                img.paste(overlay_row, (0, y), overlay_row)
            
            img = img.convert('RGB')
            
            # Create draw object
            draw = ImageDraw.Draw(img)
            
            # Add title text
            self._add_text(draw, title, y_offset=50)
            
            # Add brand name
            self._add_text(draw, self.brand_name, y_offset=120, font_size=24, color=self.colors['accent'])
            
            # Add logo if available
            if self.logo_path and os.path.exists(self.logo_path):
                self._add_logo(img)
            
            # Save thumbnail
            img.save(output_path, 'JPEG', quality=95)
            print(f"✅ Thumbnail generated: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Failed to generate thumbnail: {e}")
            return None
    
    def generate_static(self, title, subtitle=None, output_path=None):
        """
        Generate static thumbnail without video frame.
        """
        if output_path is None:
            output_path = "output/static_thumbnail.jpg"
        
        # Create base image with gradient background
        img = Image.new('RGB', (self.width, self.height), self.colors['background'])
        draw = ImageDraw.Draw(img)
        
        # Draw subtle pattern
        for i in range(0, max(self.width, self.height), 40):
            draw.line([(i, 0), (i - self.height, self.height)], fill=self.colors['secondary'], width=1)
        
        # Add title
        self._add_text(draw, title, y_offset=250, font_size=48, bold=True)
        
        # Add subtitle if provided
        if subtitle:
            self._add_text(draw, subtitle, y_offset=350, font_size=28, color=self.colors['accent'])
        
        # Add brand name
        self._add_text(draw, self.brand_name, y_offset=450, font_size=20, color=self.colors['secondary'])
        
        # Add logo if available
        if self.logo_path and os.path.exists(self.logo_path):
            self._add_logo(img)
        
        # Save
        img.save(output_path, 'JPEG', quality=95)
        print(f"✅ Static thumbnail generated: {output_path}")
        return output_path
    
    def _add_text(self, draw, text, y_offset, font_size=32, color=None, bold=False):
        """Add text to thumbnail with proper wrapping."""
        if color is None:
            color = self.colors['text']
        
        # Try to load a font
        try:
            font_path = self._find_font(bold)
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
        
        # Word wrap text
        lines = self._wrap_text(draw, text, font, self.width - 100)
        
        # Draw each line
        y = y_offset
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, font=font, fill=color)
            y += font_size + 10
    
    def _add_logo(self, img):
        """Add logo watermark to thumbnail."""
        try:
            logo = Image.open(self.logo_path).convert('RGBA')
            logo = logo.resize((100, 100), Image.Resampling.LANCZOS)
            
            # Add slight transparency
            logo.putalpha(180)
            
            # Position at bottom right
            pos = (self.width - 120, self.height - 120)
            
            # Composite logo onto image
            img_rgba = img.convert('RGBA')
            img_rgba.paste(logo, pos, logo)
            
            return img_rgba.convert('RGB')
        except:
            return img
    
    def _wrap_text(self, draw, text, font, max_width):
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _find_font(self, bold=False):
        """Find a suitable font file."""
        font_paths = [
            'C:/Windows/Fonts/ARIALBD.TTF',   # Arial Bold
            'C:/Windows/Fonts/arial.ttf',      # Arial Regular
            'C:/Windows/Fonts/tahoma.ttf',
            'C:/Windows/Fonts/calibri.ttf',
        ]
        
        for path in font_paths:
            if bold and 'BD' in path:
                if os.path.exists(path):
                    return path
            elif not bold and 'BD' not in path:
                if os.path.exists(path):
                    return path
        
        return None

if __name__ == "__main__":
    gen = ThumbnailGenerator()
    
    # Test with existing video
    test_video = "output/final_video.mp4"
    if os.path.exists(test_video):
        thumb = gen.generate_from_video(test_video, "The Stoic Hack to Emotional Immunity")
        print(f"Thumbnail: {thumb}")
    else:
        # Generate static thumbnail
        thumb = gen.generate_static("Ancient Wisdom", "Stoic Philosophy & Mindset")
        print(f"Static thumbnail: {thumb}")
