"""
VOICEVOX TTS 모듈
- 텍스트 파일을 입력받아 TTS 음성과 SRT 자막을 생성
"""

import sys
import os

# Windows 콘솔 인코딩 문제 해결
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import requests
import re
import wave
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum


# =====================
# 설정 클래스
# =====================
class SplitMode(str, Enum):
    """문장 분리 모드"""
    PUNCTUATION = "punctuation"  # 。！？ 기준
    LINE = "line"                # 줄바꿈 기준


@dataclass
class TTSConfig:
    """TTS 생성 설정"""
    voicevox_url: str = "http://127.0.0.1:50021"
    speaker_id: int = 2  # 기본: 四国めたん ノーマル
    speed_scale: float = 1.0
    pitch_scale: float = 0.0
    intonation_scale: float = 1.0
    volume_scale: float = 1.0
    split_mode: SplitMode = SplitMode.PUNCTUATION  # 문장 분리 모드


# =====================
# 유틸리티 함수
# =====================
def split_by_punctuation(text: str) -> list[str]:
    """일본어 문장 분리 (。！？ 기준)"""
    return [s for s in re.split(r'(?<=[。！？])', text) if s.strip()]


def split_by_line(text: str) -> list[str]:
    """줄바꿈 기준 분리 (긴 문장 수동 분리 가능)"""
    return [line.strip() for line in text.splitlines() if line.strip()]


def split_sentences(text: str, mode: SplitMode) -> list[str]:
    """텍스트를 지정된 모드로 분리"""
    if mode == SplitMode.LINE:
        return split_by_line(text)
    return split_by_punctuation(text)


def sec_to_srt(t: float) -> str:
    """초를 SRT 타임스탬프 형식으로 변환"""
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def calc_duration(query: dict) -> float:
    """audio_query에서 음성 길이 계산"""
    t = query["prePhonemeLength"]
    for ap in query["accent_phrases"]:
        for m in ap["moras"]:
            t += (m.get("consonant_length") or 0)
            t += (m.get("vowel_length") or 0)
        if ap.get("pause_mora"):
            t += (ap["pause_mora"].get("vowel_length") or 0)
    t += query["postPhonemeLength"]
    return max(t, 1.0)


# =====================
# 메인 TTS 클래스
# =====================
class VoicevoxTTS:
    """VOICEVOX TTS 생성기"""
    
    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
    
    def _audio_query(self, text: str) -> dict:
        """텍스트에 대한 audio_query 생성"""
        resp = requests.post(
            f"{self.config.voicevox_url}/audio_query",
            params={"text": text, "speaker": self.config.speaker_id}
        )
        resp.raise_for_status()
        query = resp.json()
        
        # 설정 적용
        query["speedScale"] = self.config.speed_scale
        query["pitchScale"] = self.config.pitch_scale
        query["intonationScale"] = self.config.intonation_scale
        query["volumeScale"] = self.config.volume_scale
        
        return query
    
    def _synthesize(self, query: dict) -> bytes:
        """audio_query로부터 음성 합성"""
        import time
        time.sleep(0.1)  # VOICEVOX 엔진 안정화를 위한 지연
        
        resp = requests.post(
            f"{self.config.voicevox_url}/synthesis",
            params={"speaker": self.config.speaker_id},
            json=query,
            timeout=60
        )
        resp.raise_for_status()
        return resp.content
    
    def _concat_wav_files(self, wav_files: list[Path], output_path: Path) -> None:
        """여러 WAV 파일을 하나로 결합"""
        with wave.open(str(wav_files[0]), "rb") as w0:
            params = w0.getparams()
        
        with wave.open(str(output_path), "wb") as out:
            out.setparams(params)
            for wav_file in wav_files:
                with wave.open(str(wav_file), "rb") as w:
                    out.writeframes(w.readframes(w.getnframes()))
    
    def generate(
        self,
        script_path: str | Path,
        output_wav: Optional[str | Path] = None,
        output_srt: Optional[str | Path] = None,
        keep_temp_files: bool = False
    ) -> dict:
        """
        TTS 음성과 SRT 자막 생성
        
        Args:
            script_path: 대본 텍스트 파일 경로
            output_wav: 출력 WAV 파일 경로 (기본: {script_name}.wav)
            output_srt: 출력 SRT 파일 경로 (기본: {script_name}.srt)
            keep_temp_files: 임시 파일 유지 여부
        
        Returns:
            dict: 생성 결과 정보
        """
        script_path = Path(script_path)
        
        # 기본 출력 경로 설정
        base_name = script_path.stem
        output_dir = script_path.parent
        
        if output_wav is None:
            output_wav = output_dir / f"{base_name}.wav"
        else:
            output_wav = Path(output_wav)
        
        if output_srt is None:
            output_srt = output_dir / f"{base_name}.srt"
        else:
            output_srt = Path(output_srt)
        
        # 대본 읽기 및 문장 분리
        text = script_path.read_text(encoding="utf-8")
        sentences = split_sentences(text, self.config.split_mode)
        
        mode_name = "줄바꿈" if self.config.split_mode == SplitMode.LINE else "문장부호(。！？)"
        print(f"📌 분리 모드: {mode_name}")
        
        print(f"📝 문장 수: {len(sentences)}")
        
        wav_files: list[Path] = []
        srt_entries: list[str] = []
        current_time = 0.0
        
        for i, sentence in enumerate(sentences, 1):
            print(f"  [{i}/{len(sentences)}] 생성 중: {sentence[:30]}...")
            
            # audio_query 생성
            query = self._audio_query(sentence)
            duration = calc_duration(query)
            
            start = current_time
            end = current_time + duration
            
            # 음성 합성
            voice_data = self._synthesize(query)
            
            # 임시 WAV 저장
            tmp_wav = output_dir / f"_tmp_{i}.wav"
            tmp_wav.write_bytes(voice_data)
            wav_files.append(tmp_wav)
            
            # SRT 엔트리 추가
            srt_entries.append(
                f"{i}\n"
                f"{sec_to_srt(start)} --> {sec_to_srt(end)}\n"
                f"{sentence.strip()}\n"
            )
            
            current_time = end
        
        # WAV 파일 결합
        self._concat_wav_files(wav_files, output_wav)
        
        # 임시 파일 삭제
        if not keep_temp_files:
            for wav_file in wav_files:
                wav_file.unlink()
        
        # SRT 파일 저장
        output_srt.write_text("\n".join(srt_entries), encoding="utf-8")
        
        result = {
            "wav_path": str(output_wav),
            "srt_path": str(output_srt),
            "sentences": len(sentences),
            "total_duration": current_time
        }
        
        print(f"\n✅ 생성 완료!")
        print(f"  🔊 음성: {output_wav}")
        print(f"  📄 자막: {output_srt}")
        print(f"  ⏱️ 총 길이: {sec_to_srt(current_time)}")
        
        return result


# =====================
# CLI 인터페이스
# =====================
def main():
    parser = argparse.ArgumentParser(
        description="VOICEVOX TTS 생성기 - 텍스트 파일에서 음성과 자막 생성"
    )
    parser.add_argument(
        "script",
        type=str,
        help="대본 텍스트 파일 경로"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="출력 파일 이름 (확장자 제외). 기본값: 입력 파일명"
    )
    parser.add_argument(
        "--speaker",
        type=int,
        default=2,
        help="VOICEVOX 화자 ID (기본: 2, 四国めたん ノーマル)"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="말하기 속도 (기본: 1.0)"
    )
    parser.add_argument(
        "--pitch",
        type=float,
        default=0.0,
        help="피치 조절 (기본: 0.0)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:50021",
        help="VOICEVOX 엔진 URL (기본: http://127.0.0.1:50021)"
    )
    parser.add_argument(
        "--split",
        type=str,
        choices=["punctuation", "line"],
        default="punctuation",
        help="문장 분리 모드: punctuation(。！？ 기준) / line(줄바꿈 기준) (기본: punctuation)"
    )
    
    args = parser.parse_args()
    
    # 분리 모드 설정
    split_mode = SplitMode.LINE if args.split == "line" else SplitMode.PUNCTUATION
    
    # 설정 생성
    config = TTSConfig(
        voicevox_url=args.url,
        speaker_id=args.speaker,
        speed_scale=args.speed,
        pitch_scale=args.pitch,
        split_mode=split_mode
    )
    
    # TTS 생성
    tts = VoicevoxTTS(config)
    
    script_path = Path(args.script)
    output_wav = None
    output_srt = None
    
    if args.output:
        output_dir = script_path.parent
        output_wav = output_dir / f"{args.output}.wav"
        output_srt = output_dir / f"{args.output}.srt"
    
    tts.generate(
        script_path=script_path,
        output_wav=output_wav,
        output_srt=output_srt
    )


# =====================
if __name__ == "__main__":
    main()
