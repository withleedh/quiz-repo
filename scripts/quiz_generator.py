#!/usr/bin/env python3
"""
퀴즈 영상 생성기 v3
- TTS 나레이션 지원
- 효과음 지원 (시작, 팝업)
- 설정 가능한 페이드인 시간
- JSON 설정 파일 연동
"""

import sys

# Windows 콘솔 인코딩 문제 해결
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import os
import random
import math
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy import (
    ImageClip, AudioFileClip, CompositeAudioClip, 
    concatenate_audioclips, CompositeVideoClip
)

# 같은 폴더의 api.py import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ==================== 설정 ====================
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# 기본 경로
BASE_DIR = Path(__file__).parent.parent
SOUNDS_DIR = BASE_DIR / "resources" / "sounds"
DEFAULT_INTRO_SOUND = SOUNDS_DIR / "intro_sound.wav"
DEFAULT_POPUP_SOUND = SOUNDS_DIR / "popup_sound.wav"

FONT_PATHS = [
    # macOS
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    # Windows (일본어 지원 폰트)
    "C:/Windows/Fonts/YuGothB.ttc",      # Yu Gothic Bold
    "C:/Windows/Fonts/YuGothR.ttc",      # Yu Gothic Regular
    "C:/Windows/Fonts/meiryo.ttc",       # Meiryo
    "C:/Windows/Fonts/msgothic.ttc",     # MS Gothic
    "C:/Windows/Fonts/msmincho.ttc",     # MS Mincho
    "C:/Windows/Fonts/malgun.ttf",       # Malgun Gothic (한글)
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def get_font(size=60):
    for font_path in FONT_PATHS:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    return ImageFont.load_default()


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def remove_white_background(image, threshold=240):
    """이미지의 흰색/밝은 배경을 투명하게 처리"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    data = np.array(image)
    r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
    white_mask = (r > threshold) & (g > threshold) & (b > threshold)
    data[:, :, 3] = np.where(white_mask, 0, a)
    
    return Image.fromarray(data)


class SparkleParticle:
    def __init__(self, width, height):
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.size = random.randint(2, 6)
        self.alpha = random.randint(100, 255)
        self.speed_x = random.uniform(-0.5, 0.5)
        self.speed_y = random.uniform(-0.3, 0.3)
        self.twinkle_speed = random.uniform(0.05, 0.15)
        self.twinkle_phase = random.uniform(0, 2 * math.pi)
        self.width = width
        self.height = height
    
    def update(self, frame):
        self.x += self.speed_x
        self.y += self.speed_y
        if self.x < 0: self.x = self.width
        if self.x > self.width: self.x = 0
        if self.y < 0: self.y = self.height
        if self.y > self.height: self.y = 0
        self.alpha = int(128 + 127 * math.sin(frame * self.twinkle_speed + self.twinkle_phase))
    
    def draw(self, draw, color):
        r, g, b = hex_to_rgb(color) if isinstance(color, str) else color[:3]
        x, y, s = int(self.x), int(self.y), self.size
        draw.ellipse([x-s, y-s, x+s, y+s], fill=(r, g, b, self.alpha))
        draw.line([x-s*2, y, x+s*2, y], fill=(r, g, b, self.alpha), width=1)
        draw.line([x, y-s*2, x, y+s*2], fill=(r, g, b, self.alpha), width=1)


class QuizVideoGenerator:
    """퀴즈 영상 생성기"""
    
    def __init__(self, config: dict):
        self.config = config
        self.image = None
        
        # 이미지 로드
        image_path = config.get("image_path")
        if image_path and os.path.exists(image_path):
            self.image = Image.open(image_path).convert('RGBA')
        
        # 반짝이 파티클
        self.sparkles = [SparkleParticle(VIDEO_WIDTH, VIDEO_HEIGHT) 
                        for _ in range(config.get("sparkle_count", 50))]
        
        # 타이밍 설정 (기본값: 0.2초)
        self.button_fade_start = config.get("button_fade_start", 0.5)
        self.button_fade_duration = config.get("button_fade_duration", 0.2)
        self.badge_fade_start = config.get("badge_fade_start", 2.0)
        self.badge_fade_duration = config.get("badge_fade_duration", 0.2)
    
    def draw_background(self, img):
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, VIDEO_WIDTH, 350], 
                      fill=hex_to_rgb(self.config.get("bg_top_color", "#C2B299")))
        draw.rectangle([0, 350, VIDEO_WIDTH, 1450], 
                      fill=hex_to_rgb(self.config.get("bg_middle_color", "#FFE4E1")))
        draw.rectangle([0, 1450, VIDEO_WIDTH, VIDEO_HEIGHT], 
                      fill=hex_to_rgb(self.config.get("bg_bottom_color", "#C2B299")))
    
    def draw_title(self, img):
        draw = ImageDraw.Draw(img)
        font = get_font(self.config.get("title_font_size", 70))
        
        title_text = self.config.get("title_text", "")
        max_width = VIDEO_WIDTH - 80  # 좌우 여백 40px씩
        
        # 텍스트 자동 줄바꿈 처리
        lines = []
        for paragraph in title_text.split('\n'):
            if not paragraph.strip():
                continue
            
            # 텍스트 너비 확인
            bbox = draw.textbbox((0, 0), paragraph, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                lines.append(paragraph)
            else:
                # 텍스트가 너무 길면 중간에서 분할
                chars = list(paragraph)
                current_line = ""
                
                for char in chars:
                    test_line = current_line + char
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    if bbox[2] - bbox[0] <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = char
                
                if current_line:
                    lines.append(current_line)
        
        colors = [self.config.get("title_color1", "#FFC800"), 
                 self.config.get("title_color2", "#FF6496")]
        
        y = self.config.get("title_y", 120)
        outline_width = self.config.get("title_outline_width", 3)
        outline_color = hex_to_rgb(self.config.get("title_outline_color", "#323232"))
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (VIDEO_WIDTH - text_width) // 2
            
            color = hex_to_rgb(colors[i % len(colors)])
            
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), line, font=font, fill=outline_color)
            
            draw.text((x, y), line, font=font, fill=color)
            y += self.config.get("title_font_size", 70) + 20
    
    def draw_center_image(self, img):
        if not self.image:
            return
        
        center_img = self.image.copy()
        
        if self.config.get("image_remove_bg", True):
            threshold = self.config.get("image_bg_threshold", 240)
            center_img = remove_white_background(center_img, threshold)
        
        max_w = self.config.get("image_max_width", 900)
        max_h = self.config.get("image_max_height", 850)
        ratio = min(max_w / center_img.width, max_h / center_img.height)
        new_size = (int(center_img.width * ratio), int(center_img.height * ratio))
        center_img = center_img.resize(new_size, Image.Resampling.LANCZOS)
        
        x = (VIDEO_WIDTH - center_img.width) // 2
        y = self.config.get("image_y", 450)
        
        img.paste(center_img, (x, y), center_img)
    
    def draw_buttons(self, img, opacity=1.0):
        if opacity <= 0:
            return
        
        draw = ImageDraw.Draw(img, 'RGBA')
        font = get_font(self.config.get("button_font_size", 50))
        
        buttons = self.config.get("buttons", [])
        if not buttons:
            return
        
        btn_w = self.config.get("button_width", 280)
        btn_h = self.config.get("button_height", 80)
        spacing = self.config.get("button_spacing", 30)
        
        total_width = len(buttons) * btn_w + (len(buttons) - 1) * spacing
        start_x = (VIDEO_WIDTH - total_width) // 2
        y = self.config.get("button_y", 1550)
        
        btn_color = hex_to_rgb(self.config.get("button_color", "#FFE600"))
        border_color = hex_to_rgb(self.config.get("button_border_color", "#323232"))
        text_color = hex_to_rgb(self.config.get("button_text_color", "#000000"))
        
        alpha = int(255 * opacity)
        
        for i, text in enumerate(buttons):
            x = start_x + i * (btn_w + spacing)
            
            draw.rounded_rectangle(
                [x, y, x + btn_w, y + btn_h],
                radius=15,
                fill=(*btn_color, alpha),
                outline=(*border_color, alpha),
                width=3
            )
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = x + (btn_w - text_width) // 2
            text_y = y + (btn_h - text_height) // 2 - 5
            
            draw.text((text_x, text_y), text, font=font, fill=(*text_color, alpha))
    
    def draw_badges(self, img, opacity=1.0):
        if opacity <= 0:
            return
        
        draw = ImageDraw.Draw(img, 'RGBA')
        font = get_font(self.config.get("badge_font_size", 40))
        
        buttons = self.config.get("buttons", [])
        if not buttons:
            return
        
        btn_w = self.config.get("button_width", 280)
        spacing = self.config.get("button_spacing", 30)
        badge_size = self.config.get("badge_size", 50)
        
        total_width = len(buttons) * btn_w + (len(buttons) - 1) * spacing
        start_x = (VIDEO_WIDTH - total_width) // 2
        y = self.config.get("button_y", 1550) + self.config.get("badge_offset_y", -60)
        
        badge_color = hex_to_rgb(self.config.get("badge_color", "#64B4FF"))
        text_color = hex_to_rgb(self.config.get("badge_text_color", "#FFFFFF"))
        
        alpha = int(255 * opacity)
        
        for i in range(len(buttons)):
            x = start_x + i * (btn_w + spacing)
            badge_x = x + (btn_w - badge_size) // 2
            badge_y = y
            
            draw.ellipse(
                [badge_x, badge_y, badge_x + badge_size, badge_y + badge_size],
                fill=(*badge_color, alpha),
                outline=(255, 255, 255, alpha),
                width=3
            )
            
            num_text = str(i + 1)
            bbox = draw.textbbox((0, 0), num_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = badge_x + (badge_size - text_width) // 2
            text_y = badge_y + (badge_size - text_height) // 2 - 3
            
            draw.text((text_x, text_y), num_text, font=font, fill=(*text_color, alpha))
    
    def draw_sparkles(self, img, frame):
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        sparkle_color = self.config.get("sparkle_color", "#FFFFC8")
        
        for sparkle in self.sparkles:
            sparkle.update(frame)
            sparkle.draw(draw, sparkle_color)
        
        return Image.alpha_composite(img, overlay)
    
    def make_frame(self, t):
        frame_num = int(t * FPS)
        
        img = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (255, 255, 255, 255))
        
        self.draw_background(img)
        self.draw_title(img)
        self.draw_center_image(img)
        
        # 버튼 페이드인
        button_opacity = 0.0
        if t >= self.button_fade_start:
            button_opacity = min(1.0, (t - self.button_fade_start) / self.button_fade_duration)
        self.draw_buttons(img, button_opacity)
        
        # 숫자 페이드인
        badge_opacity = 0.0
        if t >= self.badge_fade_start:
            badge_opacity = min(1.0, (t - self.badge_fade_start) / self.badge_fade_duration)
        self.draw_badges(img, badge_opacity)
        
        # 반짝이
        img = self.draw_sparkles(img, frame_num)
        
        # RGB 변환
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        
        return np.array(img)
    
    def generate(self, output_path: str, duration: float = 5.0, 
                 narration_audio: str = None, 
                 intro_sound: str = None, 
                 popup_sound: str = None):
        """
        영상 생성
        
        Args:
            output_path: 출력 파일 경로
            duration: 영상 길이 (초)
            narration_audio: 나레이션 오디오 파일 경로
            intro_sound: 시작 효과음 경로
            popup_sound: 숫자 팝업 효과음 경로
        """
        print(f"🎬 퀴즈 영상 생성 시작...")
        
        # 비디오 클립 생성
        clip = ImageClip(self.make_frame(0), duration=duration)
        clip = clip.with_fps(FPS)
        clip = clip.transform(lambda get_frame, t: self.make_frame(t))
        
        # 오디오 트랙 생성
        audio_clips = []
        
        # 시작 효과음 (없거나 파일이 없으면 기본값 사용)
        actual_intro = intro_sound
        if not actual_intro or not os.path.exists(actual_intro):
            actual_intro = str(DEFAULT_INTRO_SOUND)
        
        if os.path.exists(actual_intro):
            print(f"  🔊 시작 효과음 추가: {actual_intro}")
            intro_audio = AudioFileClip(actual_intro).with_start(0)
            audio_clips.append(intro_audio)
        else:
            print(f"  ⚠️ 시작 효과음 없음: {actual_intro}")
        
        # 숫자 팝업 효과음 (없거나 파일이 없으면 기본값 사용)
        actual_popup = popup_sound
        if not actual_popup or not os.path.exists(actual_popup):
            actual_popup = str(DEFAULT_POPUP_SOUND)
        
        if os.path.exists(actual_popup):
            print(f"  🔊 팝업 효과음 추가: {actual_popup}")
            popup_audio = AudioFileClip(actual_popup).with_start(self.badge_fade_start)
            audio_clips.append(popup_audio)
        else:
            print(f"  ⚠️ 팝업 효과음 없음: {actual_popup}")
        
        # 나레이션
        if narration_audio and os.path.exists(narration_audio):
            print(f"  🎤 나레이션 추가: {narration_audio}")
            
            narration = AudioFileClip(narration_audio).with_start(0.3)
            audio_clips.append(narration)
            
            # 나레이션 길이에 맞게 영상 길이 조정
            total_duration = max(duration, narration.duration + 1.0)
            clip = clip.with_duration(total_duration)
        
        # 오디오 합성
        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            clip = clip.with_audio(final_audio)
        
        # 영상 출력
        clip.write_videofile(
            output_path,
            fps=FPS,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            threads=4
        )
        
        print(f"✅ 영상 생성 완료: {output_path}")
        return output_path


def generate_narration_tts(narration_text: str, speaker_id: int = 2, 
                          speed: float = 1.0, output_dir: str = None) -> str:
    """
    나레이션 TTS 생성
    
    Args:
        narration_text: 나레이션 텍스트
        speaker_id: VOICEVOX 화자 ID
        speed: 말하기 속도
        output_dir: 출력 디렉토리
    
    Returns:
        생성된 WAV 파일 경로
    """
    try:
        from api import VoicevoxTTS, TTSConfig, SplitMode
        
        output_dir = output_dir or tempfile.gettempdir()
        
        # 임시 텍스트 파일 생성
        temp_script = Path(output_dir) / "narration_temp.txt"
        temp_script.write_text(narration_text, encoding="utf-8")
        
        # TTS 설정
        config = TTSConfig(
            speaker_id=speaker_id,
            speed_scale=speed,
            split_mode=SplitMode.LINE
        )
        
        tts = VoicevoxTTS(config)
        
        output_wav = Path(output_dir) / "narration.wav"
        
        result = tts.generate(
            script_path=temp_script,
            output_wav=output_wav,
            output_srt=Path(output_dir) / "narration.srt"
        )
        
        # 임시 파일 삭제
        temp_script.unlink(missing_ok=True)
        
        return result["wav_path"]
        
    except Exception as e:
        print(f"⚠️ TTS 생성 실패: {e}")
        return None


def generate_from_json(json_path: str, image_path: str, output_path: str):
    """
    JSON 설정 파일과 이미지로 영상 생성
    
    Args:
        json_path: 퀴즈 JSON 설정 파일 경로
        image_path: 이미지 파일 경로
        output_path: 출력 영상 파일 경로
    """
    # JSON 로드
    with open(json_path, 'r', encoding='utf-8') as f:
        quiz_config = json.load(f)
    
    # 설정 파일 형식 확인 (에디터 설정 vs 퀴즈 JSON)
    if "ui_elements" in quiz_config:
        # 퀴즈 JSON 형식 → 에디터 설정으로 변환
        ui = quiz_config.get("ui_elements", {})
        
        config = {
            "bg_top_color": "#C2B299",
            "bg_middle_color": "#C2B299",
            "bg_bottom_color": "#C2B299",
            "title_text": ui.get("top_title", ""),
            "title_y": 250,
            "title_font_size": 90,
            "title_color1": "#FFC800",
            "title_color2": "#FF6496",
            "title_outline_color": "#323232",
            "title_outline_width": 5,
            "image_path": image_path,
            "image_y": 500,
            "image_max_width": 900,
            "image_max_height": 800,
            "image_remove_bg": True,
            "image_bg_threshold": 240,
            "buttons": ui.get("selection_buttons", []),
            "button_y": 1400,
            "button_width": 220,
            "button_height": 120,
            "button_spacing": 20,
            "button_color": "#FFE600",
            "button_border_color": "#c1b299",
            "button_font_size": 45,
            "button_text_color": "#000000",
            "badge_color": "#619cf4",
            "badge_size": 78,
            "badge_offset_y": -85,
            "badge_font_size": 60,
            "badge_text_color": "#f5ffe2",
            "sparkle_count": 50,
            "sparkle_color": "#FFFFC8",
            # 타이밍
            "button_fade_start": 0.5,
            "button_fade_duration": 0.2,
            "badge_fade_start": 2.0,
            "badge_fade_duration": 0.2,
        }
        
        # 나레이션
        narration_text = ui.get("narration_script", "")
        
        # TTS 설정
        tts_config = quiz_config.get("tts_config", {})
        speaker_id = tts_config.get("speaker_id", 2)
        speed = tts_config.get("speed", 1.0)
        
        # 효과음 설정
        sound_config = quiz_config.get("sound_config", {})
        intro_sound = sound_config.get("intro_sound", str(DEFAULT_INTRO_SOUND))
        popup_sound = sound_config.get("popup_sound", str(DEFAULT_POPUP_SOUND))
        
    else:
        # 에디터 설정 형식
        config = quiz_config.copy()
        config["image_path"] = image_path
        
        narration_text = config.pop("narration_script", "")
        speaker_id = config.pop("tts_speaker_id", 2)
        speed = config.pop("tts_speed", 1.0)
        intro_sound = config.pop("intro_sound", str(DEFAULT_INTRO_SOUND))
        popup_sound = config.pop("popup_sound", str(DEFAULT_POPUP_SOUND))
    
    # 나레이션 TTS 생성
    narration_audio = None
    if narration_text:
        print(f"🎤 나레이션 TTS 생성 중...")
        narration_audio = generate_narration_tts(
            narration_text, 
            speaker_id=speaker_id,
            speed=speed,
            output_dir=str(Path(output_path).parent)
        )
    
    # 영상 생성
    generator = QuizVideoGenerator(config)
    generator.generate(
        output_path=output_path,
        duration=5.0,
        narration_audio=narration_audio,
        intro_sound=intro_sound,
        popup_sound=popup_sound
    )


def generate_from_editor_config(config: dict, output_path: str, duration: float = 5.0):
    """GUI 에디터 설정으로 영상 생성 (기존 호환)"""
    
    narration_text = config.pop("narration_script", "")
    speaker_id = config.pop("tts_speaker_id", 2)
    speed = config.pop("tts_speed", 1.0)
    intro_sound = config.pop("intro_sound", str(DEFAULT_INTRO_SOUND))
    popup_sound = config.pop("popup_sound", str(DEFAULT_POPUP_SOUND))
    
    # 나레이션 TTS 생성
    narration_audio = None
    if narration_text:
        print(f"🎤 나레이션 TTS 생성 중...")
        narration_audio = generate_narration_tts(
            narration_text, 
            speaker_id=speaker_id,
            speed=speed,
            output_dir=str(Path(output_path).parent)
        )
    
    generator = QuizVideoGenerator(config)
    generator.generate(
        output_path=output_path,
        duration=duration,
        narration_audio=narration_audio,
        intro_sound=intro_sound,
        popup_sound=popup_sound
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="퀴즈 영상 생성기 v3")
    parser.add_argument("--config", "-c", required=True, help="설정 JSON 파일")
    parser.add_argument("--image", "-i", help="이미지 파일 (설정에 없는 경우)")
    parser.add_argument("--output", "-o", default="output.mp4", help="출력 파일")
    parser.add_argument("--duration", "-d", type=float, default=5.0, help="영상 길이")
    
    args = parser.parse_args()
    
    with open(args.config, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 이미지 경로 결정
    image_path = args.image or config.get("image_path", "")
    
    if not image_path or not os.path.exists(image_path):
        print("❌ 이미지 파일을 지정해주세요.")
        sys.exit(1)
    
    generate_from_json(args.config, image_path, args.output)

