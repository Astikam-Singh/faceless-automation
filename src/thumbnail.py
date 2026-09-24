"""
Thumbnail generator for Ancient Mindset Lab videos
"""
import os
import yaml
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip
from src.config_loader import load_config

class ThumbnailGenerator:
    """
    Generates custom thumbnails for YouTube videos with brand styling.
    """
    
    def __init__(self):
        self.config = load_config()
        
        self.width = self.config['niche'].get('thumbnail_width', 1280)
        self.height = self.config['niche'].get('thumbnail_height', 720)
        self.brand_name = self.config['niche']['brand_name']
        self.logo_path = self.config['assets'].get('logo_path', '')
        
        # Brand colors
        self.colors = {
            'background': '#101010',      # Deep black-charcoal
            'accent': '#FFD700',          # Bright Gold
            'text': '#FFFFFF',            # White
            'highlight': '#FF4500'        # Trendy "YouTube" Orange-Red
        }
    
    def generate_from_video(self, video_path, title, output_path=None):
        """
        Generate high-CTR thumbnail with trendy styling.
        """
        if not os.path.exists(video_path):
            print(f"âŒ Video file not found: {video_path}")
            return None
        
        if output_path is None:
            base = os.path.splitext(video_path)[0]
            output_path = f"{base}_thumbnail.jpg"
        
        try:
            clip = VideoFileClip(video_path)
            # Take a dramatic high-contrast frame
            timestamp = min(clip.duration * 0.5, 10) 
            frame = clip.get_frame(timestamp)
            clip.close()
            
            # Convert numpy array to PIL Image
            img = Image.fromarray(frame.astype('uint8')).convert('RGB')
            
            # Crop to fill high-quality aspect ratio
            img = self._crop_to_aspect(img, self.width/self.height)
            img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            
            # Apply dark tint for text contrast
            tint = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 150))
            img = Image.alpha_composite(img.convert('RGBA'), tint).convert('RGB')
            
            draw = ImageDraw.Draw(img)
            
            # Draw a thick border for "pop"
            draw.rectangle([20, 20, self.width-20, self.height-20], outline=self.colors['accent'], width=15)
            
            # Add catchy text with high-contrast styling
            self._add_trendy_text(draw, title)
            
            # Add CTA Arrow
            self._add_cta_arrow(draw)
            
            # Add logo if available
            if self.logo_path and os.path.exists(self.logo_path):
                self._add_logo(img)
            
            img.save(output_path, 'JPEG', quality=95)
            print(f"âœ… Trendy thumbnail generated: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"âŒ Failed to generate thumbnail: {e}")
            return None

    def _crop_to_aspect(self, img, target_ratio):
        """Crop image to fit target aspect ratio."""
        img_ratio = img.width / img.height
        if img_ratio > target_ratio:
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) / 2
            img = img.crop((left, 0, left + self.width, self.height))
        else:
            new_width = self.width
            new_height = int(new_width / target_ratio)
            top = (img.height - new_height) / 2
            img = img.crop((0, top, self.width, top + self.height))
        return img
    
    def _add_trendy_text(self, draw, text):
        """Add high-contrast, trendy text with dynamic wrapping."""
        try:
            # Use a slightly smaller font size for long titles so they fit better
            font = ImageFont.truetype("arialbd.ttf", 70)
        except:
            font = ImageFont.load_default()
        
        # Word wrap using the utility function
        # Max width is width minus margins
        max_text_width = self.width - 200
        wrapped_lines = self._wrap_text(draw, text.upper(), font, max_text_width)
        
        # Calculate start position to center text vertically
        line_height = 80
        total_height = len(wrapped_lines) * line_height
        y_offset = (self.height - total_height) // 2
        
        for line in wrapped_lines:
            # Calculate width to center horizontally
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_offset = (self.width - text_width) // 2
            
            # Outline
            for offset in [-4, 4]:
                draw.text((x_offset+offset, y_offset+offset), line, font=font, fill='black')
                
            # Main Text
            draw.text((x_offset, y_offset), line, font=font, fill=self.colors['accent'])
            y_offset += line_height
            
    def _add_cta_arrow(self, draw):
        """Add a simple trendy arrow visual cue."""
        x, y = self.width - 250, self.height - 250
        # Draw arrow shape
        draw.polygon([(x, y), (x+100, y+100), (x, y+200), (x+50, y+100)], fill=self.colors['highlight'])
        
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
        print(f"âœ… Static thumbnail generated: {output_path}")
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
        """Wrap text into multiple lines."""
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
