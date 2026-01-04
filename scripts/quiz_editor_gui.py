#!/usr/bin/env python3
"""
퀴즈 영상 GUI 에디터 v4
드래그앤드롭 + 실시간 미리보기 + 숫자 직접 입력 + TTS/효과음 설정
"""

import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageTk
import numpy as np

# ==================== 설정 ====================
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
PREVIEW_SCALE = 0.45

# 기본 경로
BASE_DIR = Path(__file__).parent.parent
SOUNDS_DIR = BASE_DIR / "resources" / "sounds"
DEFAULT_INTRO_SOUND = str(SOUNDS_DIR / "intro_sound.wav")
DEFAULT_POPUP_SOUND = str(SOUNDS_DIR / "popup_sound.wav")

# VOICEVOX 화자 목록
VOICEVOX_SPEAKERS = {
    0: "四国めたん (あまあま)",
    2: "四国めたん (ノーマル)",
    4: "四国めたん (セクシー)",
    6: "四国めたん (ツンツン)",
    1: "ずんだもん (あまあま)",
    3: "ずんだもん (ノーマル)",
    5: "ずんだもん (セクシー)",
    7: "ずんだもん (ツンツン)",
    8: "春日部つむぎ",
    9: "波音リツ",
    10: "雨晴はう",
    11: "玄野武宏",
    12: "白上虎太郎",
    13: "青山龍星",
    14: "冥鳴ひまり",
}

FONT_PATHS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
]


def get_font(size=60):
    for font_path in FONT_PATHS:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    return ImageFont.load_default()


def remove_white_background(image, threshold=240):
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    data = np.array(image)
    r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
    white_mask = (r > threshold) & (g > threshold) & (b > threshold)
    data[:, :, 3] = np.where(white_mask, 0, a)
    
    return Image.fromarray(data)


class EditableValue(ttk.Frame):
    """클릭해서 편집 가능한 값 위젯"""
    
    def __init__(self, parent, initial_value, callback, min_val=0, max_val=2000, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.callback = callback
        self.min_val = min_val
        self.max_val = max_val
        self.editing = False
        
        # 라벨 (기본 상태)
        self.label = ttk.Label(self, text=str(int(initial_value)), width=6, 
                               cursor="hand2", font=("Arial", 10, "bold"))
        self.label.pack()
        self.label.bind("<Button-1>", self.start_edit)
        
        # 엔트리 (편집 상태)
        self.entry_var = tk.StringVar(value=str(int(initial_value)))
        self.entry = ttk.Entry(self, textvariable=self.entry_var, width=6, 
                               font=("Arial", 10), justify="center")
        self.entry.bind("<Return>", self.finish_edit)
        self.entry.bind("<Escape>", self.cancel_edit)
        self.entry.bind("<FocusOut>", self.finish_edit)
    
    def start_edit(self, event=None):
        """편집 모드 시작"""
        if self.editing:
            return
        self.editing = True
        self.label.pack_forget()
        self.entry.pack()
        self.entry.select_range(0, tk.END)
        self.entry.focus_set()
    
    def finish_edit(self, event=None):
        """편집 완료"""
        if not self.editing:
            return
        
        try:
            value = int(float(self.entry_var.get()))
            value = max(self.min_val, min(self.max_val, value))
            self.label.config(text=str(value))
            self.callback(value)
        except ValueError:
            pass
        
        self.editing = False
        self.entry.pack_forget()
        self.label.pack()
    
    def cancel_edit(self, event=None):
        """편집 취소"""
        self.editing = False
        self.entry.pack_forget()
        self.label.pack()
    
    def set_value(self, value):
        """값 설정"""
        self.label.config(text=str(int(value)))
        self.entry_var.set(str(int(value)))


class SmoothSlider(ttk.Frame):
    """부드러운 슬라이더 + 클릭 편집 가능한 값"""
    
    def __init__(self, parent, label, initial_value, from_, to, callback, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.callback = callback
        self.from_ = from_
        self.to = to
        
        # 라벨
        ttk.Label(self, text=label, width=15).pack(side=tk.LEFT)
        
        # 슬라이더
        self.var = tk.DoubleVar(value=initial_value)
        self.slider = ttk.Scale(self, from_=from_, to=to, variable=self.var, 
                               orient=tk.HORIZONTAL, command=self._on_change)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 편집 가능한 값
        self.value_widget = EditableValue(
            self, initial_value, self._on_entry_change, 
            min_val=from_, max_val=to
        )
        self.value_widget.pack(side=tk.LEFT)
    
    def _on_change(self, value):
        """슬라이더 변경"""
        int_val = int(float(value))
        self.value_widget.set_value(int_val)
        self.callback(int_val)
    
    def _on_entry_change(self, value):
        """직접 입력 변경"""
        self.var.set(value)
        self.callback(value)
    
    def set_value(self, value):
        """외부에서 값 설정"""
        self.var.set(value)
        self.value_widget.set_value(value)
    
    def get_value(self):
        """현재 값 반환"""
        return int(self.var.get())


class QuizEditorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("퀴즈 영상 에디터 v3")
        self.root.geometry("1500x950")
        
        # 기본 설정값
        self.config = {
            "bg_top_color": "#C2B299",
            "bg_middle_color": "#C2B299",
            "bg_bottom_color": "#C2B299",
            
            "title_text": "認知症が始まった人は\n違って見える絵",
            "title_y": 250,
            "title_font_size": 90,
            "title_color1": "#FFC800",
            "title_color2": "#FF6496",
            "title_outline_color": "#323232",
            "title_outline_width": 5,
            
            "image_path": "",
            "image_y": 500,
            "image_max_width": 900,
            "image_max_height": 800,
            "image_remove_bg": True,
            "image_bg_threshold": 240,
            
            "buttons": ["5個以下", "6〜7個", "8〜9個", "10個以上"],
            "button_y": 1400,
            "button_width": 220,
            "button_height": 120,
            "button_spacing": 20,
            "button_color": "#FFE600",
            "button_border_color": "#c1b299",
            "button_font_size": 45,
            "button_text_color": "#000000",
            "button_auto_size": True,
            
            "badge_color": "#619cf4",
            "badge_size": 78,
            "badge_offset_y": -85,
            "badge_font_size": 60,
            "badge_text_color": "#f5ffe2",
            
            "sparkle_count": 50,
            "sparkle_color": "#FFFFC8",
            
            # TTS 설정
            "narration_script": "",
            "tts_speaker_id": 2,
            "tts_speed": 1.0,
            
            # 효과음 설정
            "intro_sound": DEFAULT_INTRO_SOUND,
            "popup_sound": DEFAULT_POPUP_SOUND,
            
            # 타이밍 설정
            "button_fade_start": 0.5,
            "button_fade_duration": 0.2,
            "badge_fade_start": 2.0,
            "badge_fade_duration": 0.2,
        }
        
        self.image = None
        self.preview_image = None
        
        # 드래그 상태 (부드러운 이동)
        self.dragging = None
        self.drag_start_pos = None
        self.drag_start_value = None
        self.drag_smooth_factor = 0.3  # 부드러움 계수
        
        # 슬라이더 위젯 참조
        self.sliders = {}
        
        self.button_presets = {
            3: {"width": 280, "spacing": 30, "font_size": 50},
            4: {"width": 220, "spacing": 20, "font_size": 45},
        }
        
        self.setup_ui()
        self.update_preview()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 왼쪽: 설정 패널
        left_frame = ttk.Frame(main_frame, width=550)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        canvas = tk.Canvas(left_frame)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        self.settings_frame = ttk.Frame(canvas)
        
        self.settings_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.settings_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 마우스 휠 스크롤
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self.create_image_section()
        self.create_background_section()
        self.create_title_section()
        self.create_button_section()
        self.create_badge_section()
        self.create_tts_section()
        self.create_sound_section()
        self.create_timing_section()
        self.create_export_section()
        
        # 오른쪽: 미리보기
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        header_frame = ttk.Frame(right_frame)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(header_frame, text="🖼️ 미리보기", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="| 드래그: 위치 조정 | 숫자 클릭: 직접 입력", 
                 font=("Arial", 10), foreground="gray").pack(side=tk.LEFT, padx=10)
        
        preview_w = int(VIDEO_WIDTH * PREVIEW_SCALE)
        preview_h = int(VIDEO_HEIGHT * PREVIEW_SCALE)
        
        self.preview_canvas = tk.Canvas(right_frame, width=preview_w, height=preview_h, 
                                        bg="gray", cursor="hand2")
        self.preview_canvas.pack(pady=10)
        
        # 드래그 이벤트
        self.preview_canvas.bind("<Button-1>", self.on_canvas_click)
        self.preview_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
    
    def create_section_header(self, text):
        frame = ttk.Frame(self.settings_frame)
        frame.pack(fill=tk.X, pady=(15, 5))
        ttk.Label(frame, text=text, font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Separator(frame, orient="horizontal").pack(fill=tk.X, pady=2)
        return frame
    
    def create_slider(self, parent, label, key, from_, to):
        """부드러운 슬라이더 생성"""
        slider = SmoothSlider(
            parent, label, self.config[key], from_, to,
            callback=lambda v: self.on_slider_change(key, v)
        )
        slider.pack(fill=tk.X, pady=2)
        self.sliders[key] = slider
        return slider
    
    def create_color_picker(self, parent, label, key):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text=label, width=15).pack(side=tk.LEFT)
        
        color_btn = tk.Button(frame, bg=self.config[key], width=8,
                             command=lambda: self.pick_color(key, color_btn))
        color_btn.pack(side=tk.LEFT, padx=5)
        
        hex_label = ttk.Label(frame, text=self.config[key])
        hex_label.pack(side=tk.LEFT)
        
        setattr(self, f"{key}_btn", color_btn)
        setattr(self, f"{key}_hex", hex_label)
    
    def create_image_section(self):
        self.create_section_header("📷 이미지 설정")
        
        img_frame = ttk.Frame(self.settings_frame)
        img_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(img_frame, text="이미지 선택", command=self.select_image).pack(side=tk.LEFT)
        self.image_path_label = ttk.Label(img_frame, text="선택된 이미지 없음")
        self.image_path_label.pack(side=tk.LEFT, padx=10)
        
        self.create_slider(self.settings_frame, "이미지 Y 위치", "image_y", 300, 800)
        self.create_slider(self.settings_frame, "최대 너비", "image_max_width", 400, 1000)
        self.create_slider(self.settings_frame, "최대 높이", "image_max_height", 400, 1000)
        
        bg_frame = ttk.Frame(self.settings_frame)
        bg_frame.pack(fill=tk.X, pady=5)
        
        self.remove_bg_var = tk.BooleanVar(value=self.config["image_remove_bg"])
        ttk.Checkbutton(bg_frame, text="흰색 배경 제거", variable=self.remove_bg_var,
                       command=self.on_checkbox_change).pack(side=tk.LEFT)
        
        self.create_slider(self.settings_frame, "배경 임계값", "image_bg_threshold", 180, 255)
    
    def create_background_section(self):
        self.create_section_header("🎨 배경 색상")
        self.create_color_picker(self.settings_frame, "상단 배경", "bg_top_color")
        self.create_color_picker(self.settings_frame, "중앙 배경", "bg_middle_color")
        self.create_color_picker(self.settings_frame, "하단 배경", "bg_bottom_color")
    
    def create_title_section(self):
        self.create_section_header("📝 상단 타이틀")
        
        text_frame = ttk.Frame(self.settings_frame)
        text_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(text_frame, text="타이틀 텍스트:").pack(anchor="w")
        self.title_text = tk.Text(text_frame, height=3, width=40)
        self.title_text.insert("1.0", self.config["title_text"])
        self.title_text.pack(fill=tk.X)
        self.title_text.bind("<KeyRelease>", self.on_text_change)
        
        self.create_slider(self.settings_frame, "Y 위치", "title_y", 100, 400)
        self.create_slider(self.settings_frame, "폰트 크기", "title_font_size", 40, 120)
        
        self.create_color_picker(self.settings_frame, "첫 줄 색상", "title_color1")
        self.create_color_picker(self.settings_frame, "둘째 줄 색상", "title_color2")
        self.create_color_picker(self.settings_frame, "테두리 색상", "title_outline_color")
        self.create_slider(self.settings_frame, "테두리 두께", "title_outline_width", 0, 10)
    
    def create_button_section(self):
        self.create_section_header("🔘 하단 버튼 (3~4개)")
        
        preset_frame = ttk.Frame(self.settings_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(preset_frame, text="버튼 개수:").pack(side=tk.LEFT)
        self.button_count_var = tk.IntVar(value=len(self.config["buttons"]))
        
        for count in [3, 4]:
            ttk.Radiobutton(preset_frame, text=f"{count}개", variable=self.button_count_var,
                           value=count, command=self.on_button_count_change).pack(side=tk.LEFT, padx=10)
        
        btn_frame = ttk.Frame(self.settings_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(btn_frame, text="버튼 텍스트 (쉼표 구분):").pack(anchor="w")
        self.button_text = ttk.Entry(btn_frame, width=50)
        self.button_text.insert(0, ",".join(self.config["buttons"]))
        self.button_text.pack(fill=tk.X)
        self.button_text.bind("<KeyRelease>", self.on_button_text_change)
        
        auto_frame = ttk.Frame(self.settings_frame)
        auto_frame.pack(fill=tk.X, pady=3)
        
        self.auto_size_var = tk.BooleanVar(value=self.config["button_auto_size"])
        ttk.Checkbutton(auto_frame, text="버튼 자동 크기 조절", variable=self.auto_size_var,
                       command=self.on_auto_size_change).pack(side=tk.LEFT)
        
        self.create_slider(self.settings_frame, "Y 위치", "button_y", 1200, 1750)
        self.create_slider(self.settings_frame, "버튼 너비", "button_width", 150, 300)
        self.create_slider(self.settings_frame, "버튼 높이", "button_height", 50, 120)
        self.create_slider(self.settings_frame, "버튼 간격", "button_spacing", 5, 50)
        self.create_slider(self.settings_frame, "폰트 크기", "button_font_size", 25, 70)
        
        self.create_color_picker(self.settings_frame, "버튼 색상", "button_color")
        self.create_color_picker(self.settings_frame, "테두리 색상", "button_border_color")
        self.create_color_picker(self.settings_frame, "텍스트 색상", "button_text_color")
    
    def create_badge_section(self):
        self.create_section_header("🔢 숫자 뱃지")
        
        self.create_slider(self.settings_frame, "뱃지 크기", "badge_size", 30, 80)
        self.create_slider(self.settings_frame, "Y 오프셋", "badge_offset_y", -100, 0)
        self.create_slider(self.settings_frame, "폰트 크기", "badge_font_size", 20, 60)
        
        self.create_color_picker(self.settings_frame, "뱃지 색상", "badge_color")
        self.create_color_picker(self.settings_frame, "텍스트 색상", "badge_text_color")
    
    def create_tts_section(self):
        self.create_section_header("🎤 나레이션 TTS")
        
        # 나레이션 텍스트
        ttk.Label(self.settings_frame, text="나레이션 스크립트:").pack(anchor="w")
        self.narration_text = tk.Text(self.settings_frame, height=3, width=40)
        self.narration_text.insert("1.0", self.config.get("narration_script", ""))
        self.narration_text.pack(fill=tk.X, pady=2)
        self.narration_text.bind("<KeyRelease>", self.on_narration_change)
        
        # 화자 선택
        speaker_frame = ttk.Frame(self.settings_frame)
        speaker_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(speaker_frame, text="화자:", width=15).pack(side=tk.LEFT)
        self.speaker_var = tk.StringVar()
        self.speaker_combo = ttk.Combobox(speaker_frame, textvariable=self.speaker_var, 
                                         state="readonly", width=25)
        self.speaker_combo['values'] = [f"{k}: {v}" for k, v in VOICEVOX_SPEAKERS.items()]
        self.speaker_combo.current(list(VOICEVOX_SPEAKERS.keys()).index(self.config["tts_speaker_id"]))
        self.speaker_combo.pack(side=tk.LEFT, padx=5)
        self.speaker_combo.bind("<<ComboboxSelected>>", self.on_speaker_change)
        
        # 속도
        self.create_slider(self.settings_frame, "말하기 속도 (%)", "tts_speed", 50, 200)
    
    def create_sound_section(self):
        self.create_section_header("🔊 효과음")
        
        # 시작 효과음
        intro_frame = ttk.Frame(self.settings_frame)
        intro_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(intro_frame, text="시작 효과음:", width=15).pack(side=tk.LEFT)
        ttk.Button(intro_frame, text="선택", command=self.select_intro_sound).pack(side=tk.LEFT)
        self.intro_sound_label = ttk.Label(intro_frame, text=os.path.basename(self.config["intro_sound"]))
        self.intro_sound_label.pack(side=tk.LEFT, padx=5)
        
        # 숫자 팝업 효과음
        popup_frame = ttk.Frame(self.settings_frame)
        popup_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(popup_frame, text="팝업 효과음:", width=15).pack(side=tk.LEFT)
        ttk.Button(popup_frame, text="선택", command=self.select_popup_sound).pack(side=tk.LEFT)
        self.popup_sound_label = ttk.Label(popup_frame, text=os.path.basename(self.config["popup_sound"]))
        self.popup_sound_label.pack(side=tk.LEFT, padx=5)
    
    def create_timing_section(self):
        self.create_section_header("⏱️ 타이밍 설정")
        
        # 버튼 페이드인 시작
        self.create_slider(self.settings_frame, "버튼 시작 (초x10)", "button_fade_start", 0, 30)
        self.create_slider(self.settings_frame, "버튼 지속 (초x10)", "button_fade_duration", 1, 10)
        
        # 숫자 페이드인 시작
        self.create_slider(self.settings_frame, "숫자 시작 (초x10)", "badge_fade_start", 0, 50)
        self.create_slider(self.settings_frame, "숫자 지속 (초x10)", "badge_fade_duration", 1, 10)
    
    def create_export_section(self):
        self.create_section_header("💾 저장 및 내보내기")
        
        btn_frame = ttk.Frame(self.settings_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="📥 설정 저장", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📤 설정 불러오기", command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🎬 영상 생성", command=self.export_video).pack(side=tk.LEFT, padx=5)
    
    # ==================== 드래그앤드롭 (부드러운 이동) ====================
    def get_element_at(self, x, y):
        real_x = x / PREVIEW_SCALE
        real_y = y / PREVIEW_SCALE
        
        # 타이틀 영역
        title_y = self.config["title_y"]
        title_h = self.config["title_font_size"] * 2.5
        if title_y - 20 <= real_y <= title_y + title_h + 20:
            return "title", "title_y", title_y
        
        # 이미지 영역
        if self.image:
            img_y = self.config["image_y"]
            img_h = self.config["image_max_height"]
            if img_y - 20 <= real_y <= img_y + img_h + 20:
                return "image", "image_y", img_y
        
        # 버튼 영역
        btn_y = self.config["button_y"]
        btn_h = self.config["button_height"]
        if btn_y - 100 <= real_y <= btn_y + btn_h + 20:
            return "buttons", "button_y", btn_y
        
        return None, None, None
    
    def on_canvas_click(self, event):
        element, key, value = self.get_element_at(event.x, event.y)
        if element:
            self.dragging = element
            self.drag_key = key
            self.drag_start_pos = event.y
            self.drag_start_value = value
            self.preview_canvas.config(cursor="fleur")
    
    def on_canvas_drag(self, event):
        if not self.dragging:
            return
        
        # 부드러운 이동 계산
        dy_pixels = event.y - self.drag_start_pos
        dy_real = dy_pixels / PREVIEW_SCALE
        
        # 새 값 계산 (부드럽게)
        target_value = self.drag_start_value + dy_real
        current_value = self.config[self.drag_key]
        
        # 선형 보간으로 부드럽게
        smooth_value = current_value + (target_value - current_value) * self.drag_smooth_factor
        
        # 범위 제한
        if self.drag_key == "title_y":
            smooth_value = max(100, min(400, smooth_value))
        elif self.drag_key == "image_y":
            smooth_value = max(300, min(800, smooth_value))
        elif self.drag_key == "button_y":
            smooth_value = max(1200, min(1750, smooth_value))
        
        self.config[self.drag_key] = int(smooth_value)
        
        # 슬라이더 업데이트
        if self.drag_key in self.sliders:
            self.sliders[self.drag_key].set_value(int(smooth_value))
        
        self.update_preview()
    
    def on_canvas_release(self, event):
        self.dragging = None
        self.drag_key = None
        self.drag_start_pos = None
        self.drag_start_value = None
        self.preview_canvas.config(cursor="hand2")
    
    # ==================== 이벤트 핸들러 ====================
    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if path:
            self.config["image_path"] = path
            self.image_path_label.config(text=os.path.basename(path))
            self.load_image()
            self.update_preview()
    
    def load_image(self):
        if self.config["image_path"] and os.path.exists(self.config["image_path"]):
            self.image = Image.open(self.config["image_path"]).convert('RGBA')
    
    def on_slider_change(self, key, value):
        self.config[key] = int(value)
        self.update_preview()
    
    def on_checkbox_change(self):
        self.config["image_remove_bg"] = self.remove_bg_var.get()
        self.update_preview()
    
    def on_auto_size_change(self):
        self.config["button_auto_size"] = self.auto_size_var.get()
        if self.config["button_auto_size"]:
            self.apply_button_preset()
        self.update_preview()
    
    def on_button_count_change(self):
        count = self.button_count_var.get()
        current_buttons = self.config["buttons"]
        
        if count == 3 and len(current_buttons) > 3:
            self.config["buttons"] = current_buttons[:3]
        elif count == 4 and len(current_buttons) < 4:
            self.config["buttons"] = current_buttons + ["10個以上"]
        
        self.button_text.delete(0, tk.END)
        self.button_text.insert(0, ",".join(self.config["buttons"]))
        
        if self.config["button_auto_size"]:
            self.apply_button_preset()
        
        self.update_preview()
    
    def apply_button_preset(self):
        count = len(self.config["buttons"])
        if count in self.button_presets:
            preset = self.button_presets[count]
            self.config["button_width"] = preset["width"]
            self.config["button_spacing"] = preset["spacing"]
            self.config["button_font_size"] = preset["font_size"]
            
            for key in ["button_width", "button_spacing", "button_font_size"]:
                if key in self.sliders:
                    self.sliders[key].set_value(self.config[key])
    
    def on_text_change(self, event=None):
        self.config["title_text"] = self.title_text.get("1.0", tk.END).strip()
        self.update_preview()
    
    def on_button_text_change(self, event=None):
        text = self.button_text.get().strip()
        self.config["buttons"] = [b.strip() for b in text.split(",") if b.strip()]
        self.button_count_var.set(len(self.config["buttons"]))
        
        if self.config["button_auto_size"]:
            self.apply_button_preset()
        
        self.update_preview()
    
    def pick_color(self, key, button):
        color = colorchooser.askcolor(color=self.config[key])
        if color[1]:
            self.config[key] = color[1]
            button.config(bg=color[1])
            hex_label = getattr(self, f"{key}_hex", None)
            if hex_label:
                hex_label.config(text=color[1])
            self.update_preview()
    
    def on_narration_change(self, event=None):
        self.config["narration_script"] = self.narration_text.get("1.0", tk.END).strip()
    
    def on_speaker_change(self, event=None):
        selected = self.speaker_var.get()
        speaker_id = int(selected.split(":")[0])
        self.config["tts_speaker_id"] = speaker_id
    
    def select_intro_sound(self):
        path = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3 *.ogg")])
        if path:
            self.config["intro_sound"] = path
            self.intro_sound_label.config(text=os.path.basename(path))
    
    def select_popup_sound(self):
        path = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3 *.ogg")])
        if path:
            self.config["popup_sound"] = path
            self.popup_sound_label.config(text=os.path.basename(path))
    
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # ==================== 렌더링 ====================
    def render_preview(self):
        img = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        draw.rectangle([0, 0, VIDEO_WIDTH, 350], fill=self.hex_to_rgb(self.config["bg_top_color"]))
        draw.rectangle([0, 350, VIDEO_WIDTH, 1450], fill=self.hex_to_rgb(self.config["bg_middle_color"]))
        draw.rectangle([0, 1450, VIDEO_WIDTH, VIDEO_HEIGHT], fill=self.hex_to_rgb(self.config["bg_bottom_color"]))
        
        self.draw_title(img)
        if self.image:
            self.draw_center_image(img)
        self.draw_buttons(img)
        self.draw_badges(img)
        
        return img
    
    def draw_title(self, img):
        draw = ImageDraw.Draw(img)
        font = get_font(self.config["title_font_size"])
        
        lines = self.config["title_text"].split('\n')
        colors = [self.config["title_color1"], self.config["title_color2"]]
        
        y = self.config["title_y"]
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (VIDEO_WIDTH - text_width) // 2
            
            color = self.hex_to_rgb(colors[i % len(colors)])
            outline_color = self.hex_to_rgb(self.config["title_outline_color"])
            outline_width = self.config["title_outline_width"]
            
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), line, font=font, fill=outline_color)
            
            draw.text((x, y), line, font=font, fill=color)
            y += self.config["title_font_size"] + 20
    
    def draw_center_image(self, img):
        center_img = self.image.copy()
        
        if self.config["image_remove_bg"]:
            center_img = remove_white_background(center_img, self.config["image_bg_threshold"])
        
        max_w = self.config["image_max_width"]
        max_h = self.config["image_max_height"]
        ratio = min(max_w / center_img.width, max_h / center_img.height)
        new_size = (int(center_img.width * ratio), int(center_img.height * ratio))
        center_img = center_img.resize(new_size, Image.Resampling.LANCZOS)
        
        x = (VIDEO_WIDTH - center_img.width) // 2
        y = self.config["image_y"]
        
        img.paste(center_img, (x, y), center_img)
    
    def draw_buttons(self, img):
        draw = ImageDraw.Draw(img, 'RGBA')
        font = get_font(self.config["button_font_size"])
        
        buttons = self.config["buttons"]
        if not buttons:
            return
        
        num_buttons = len(buttons)
        btn_w = self.config["button_width"]
        btn_h = self.config["button_height"]
        spacing = self.config["button_spacing"]
        
        total_width = num_buttons * btn_w + (num_buttons - 1) * spacing
        start_x = (VIDEO_WIDTH - total_width) // 2
        y = self.config["button_y"]
        
        btn_color = self.hex_to_rgb(self.config["button_color"])
        border_color = self.hex_to_rgb(self.config["button_border_color"])
        text_color = self.hex_to_rgb(self.config["button_text_color"])
        
        for i, text in enumerate(buttons):
            x = start_x + i * (btn_w + spacing)
            
            draw.rounded_rectangle([x, y, x + btn_w, y + btn_h], radius=15,
                                  fill=btn_color, outline=border_color, width=3)
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = x + (btn_w - text_width) // 2
            text_y = y + (btn_h - text_height) // 2 - 5
            
            draw.text((text_x, text_y), text, font=font, fill=text_color)
    
    def draw_badges(self, img):
        draw = ImageDraw.Draw(img, 'RGBA')
        font = get_font(self.config["badge_font_size"])
        
        buttons = self.config["buttons"]
        if not buttons:
            return
        
        num_buttons = len(buttons)
        btn_w = self.config["button_width"]
        spacing = self.config["button_spacing"]
        badge_size = self.config["badge_size"]
        
        total_width = num_buttons * btn_w + (num_buttons - 1) * spacing
        start_x = (VIDEO_WIDTH - total_width) // 2
        y = self.config["button_y"] + self.config["badge_offset_y"]
        
        badge_color = self.hex_to_rgb(self.config["badge_color"])
        text_color = self.hex_to_rgb(self.config["badge_text_color"])
        
        for i in range(num_buttons):
            x = start_x + i * (btn_w + spacing)
            badge_x = x + (btn_w - badge_size) // 2
            badge_y = y
            
            draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size],
                        fill=badge_color, outline=(255, 255, 255), width=3)
            
            num_text = str(i + 1)
            bbox = draw.textbbox((0, 0), num_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = badge_x + (badge_size - text_width) // 2
            text_y = badge_y + (badge_size - text_height) // 2 - 3
            
            draw.text((text_x, text_y), num_text, font=font, fill=text_color)
    
    def update_preview(self):
        try:
            preview = self.render_preview()
            preview_size = (int(VIDEO_WIDTH * PREVIEW_SCALE), int(VIDEO_HEIGHT * PREVIEW_SCALE))
            preview = preview.resize(preview_size, Image.Resampling.LANCZOS)
            
            self.preview_image = ImageTk.PhotoImage(preview)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, anchor="nw", image=self.preview_image)
        except Exception as e:
            print(f"Preview error: {e}")
    
    # ==================== 저장/불러오기 ====================
    def save_config(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("저장 완료", f"설정이 저장되었습니다:\n{path}")
    
    def load_config(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                self.config.update(loaded)
            
            self.title_text.delete("1.0", tk.END)
            self.title_text.insert("1.0", self.config["title_text"])
            self.button_text.delete(0, tk.END)
            self.button_text.insert(0, ",".join(self.config["buttons"]))
            self.button_count_var.set(len(self.config["buttons"]))
            
            if self.config["image_path"]:
                self.image_path_label.config(text=os.path.basename(self.config["image_path"]))
                self.load_image()
            
            # 나레이션 업데이트
            if hasattr(self, 'narration_text'):
                self.narration_text.delete("1.0", tk.END)
                self.narration_text.insert("1.0", self.config.get("narration_script", ""))
            
            # 화자 업데이트
            if hasattr(self, 'speaker_combo'):
                speaker_id = self.config.get("tts_speaker_id", 2)
                if speaker_id in VOICEVOX_SPEAKERS:
                    idx = list(VOICEVOX_SPEAKERS.keys()).index(speaker_id)
                    self.speaker_combo.current(idx)
            
            # 효과음 레이블 업데이트
            if hasattr(self, 'intro_sound_label'):
                self.intro_sound_label.config(text=os.path.basename(self.config.get("intro_sound", "")))
            if hasattr(self, 'popup_sound_label'):
                self.popup_sound_label.config(text=os.path.basename(self.config.get("popup_sound", "")))
            
            # 모든 슬라이더 업데이트
            for key, slider in self.sliders.items():
                if key in self.config:
                    slider.set_value(self.config[key])
            
            self.update_preview()
            messagebox.showinfo("불러오기 완료", "설정을 불러왔습니다.")
    
    def export_video(self):
        if not self.config["image_path"]:
            messagebox.showerror("오류", "이미지를 먼저 선택해주세요.")
            return
        
        output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
        if not output_path:
            return
        
        messagebox.showinfo("안내", "영상 생성을 시작합니다.\n완료되면 알림이 표시됩니다.")
        
        try:
            # 타이밍 값을 실제 초 단위로 변환 (슬라이더는 x10 단위)
            export_config = self.config.copy()
            export_config["button_fade_start"] = self.config.get("button_fade_start", 5) / 10.0
            export_config["button_fade_duration"] = self.config.get("button_fade_duration", 2) / 10.0
            export_config["badge_fade_start"] = self.config.get("badge_fade_start", 20) / 10.0
            export_config["badge_fade_duration"] = self.config.get("badge_fade_duration", 2) / 10.0
            export_config["tts_speed"] = self.config.get("tts_speed", 100) / 100.0
            
            from quiz_generator import generate_from_editor_config
            generate_from_editor_config(export_config, output_path)
            messagebox.showinfo("완료", f"영상이 생성되었습니다:\n{output_path}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("오류", f"영상 생성 중 오류 발생:\n{e}")


def main():
    root = tk.Tk()
    app = QuizEditorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
