/**
 * Remotion Root
 * 
 * 컴포지션 등록 파일
 */

import React from 'react';
import { Composition } from 'remotion';
import { z } from 'zod';
import { ListeningVideo, calculateTotalDuration } from './compositions/ListeningVideo';
import { AudioListeningVideo, calculateAudioVideoDuration } from './compositions/AudioListeningVideo';
import { Step3Section, Step3SectionProps } from './compositions/Step3Section';
import { IntroSection, IntroSectionProps } from './compositions/IntroSection';

// 샘플 데이터 (미리보기용)
const sampleScript = {
  channelId: 'english_for_korean',
  date: '2026-01-08',
  category: '안내 상황',
  metadata: {
    topic: '공항에서 수하물 분실 신고하기',
    style: '걱정스러움→ 침착함',
    title: { target: 'Reporting Lost Luggage', native: '수하물 분실 신고' },
  },
  sentences: [
    { id: 1, speaker: 'M' as const, target: "Hello, I'm calling to report lost luggage from my recent flight.", native: '안녕하세요, 최근 비행에서 잃어버린 수하물을 신고하려고 전화했습니다.', words: [{ word: 'report', meaning: '신고하다' }, { word: 'lost luggage', meaning: '분실된 수하물' }] },
    { id: 2, speaker: 'F' as const, target: "I'm sorry to hear that. Can I get your flight number and name?", native: '정말 안타깝네요. 항공편 번호와 성함을 알 수 있을까요?', words: [{ word: 'flight number', meaning: '항공편 번호' }] },
    { id: 3, speaker: 'M' as const, target: "Yes, it's flight KE123, and my name is Michael Johnson.", native: '네, KE123편이고, 제 이름은 마이클 존슨입니다.', words: [{ word: 'flight', meaning: '항공편' }] },
    { id: 4, speaker: 'F' as const, target: "Thank you, Mr. Johnson. What does the luggage look like?", native: '감사합니다, 존슨 씨. 수하물은 어떻게 생겼나요?', words: [{ word: 'luggage', meaning: '수하물' }] },
    { id: 5, speaker: 'M' as const, target: "It's a large, black suitcase with a red tag on the handle.", native: '손잡이에 빨간색 태그가 달린 크고 검은색 여행 가방입니다.', words: [{ word: 'suitcase', meaning: '여행 가방' }, { word: 'tag', meaning: '태그' }] },
    { id: 6, speaker: 'F' as const, target: "Okay. And what are the contents of the suitcase, generally?", native: '알겠습니다. 일반적으로 여행 가방의 내용물은 무엇인가요?', words: [{ word: 'contents', meaning: '내용물' }] },
    { id: 7, speaker: 'M' as const, target: "Mostly clothes and some personal items; nothing too valuable, I think.", native: '주로 옷과 몇 가지 개인 소지품입니다. 아주 귀중한 물건은 없는 것 같아요.', words: [{ word: 'personal items', meaning: '개인 소지품' }] },
    { id: 8, speaker: 'F' as const, target: "Alright. We will start a search for your luggage immediately, sir.", native: '알겠습니다. 즉시 수하물 검색을 시작하겠습니다.', words: [{ word: 'immediately', meaning: '즉시' }] },
    { id: 9, speaker: 'M' as const, target: "How long does it usually take to find lost luggage like this?", native: '이런 식으로 분실된 수하물을 찾는 데 보통 얼마나 걸리나요?', words: [{ word: 'usually', meaning: '보통' }] },
    { id: 10, speaker: 'F' as const, target: "It varies, but we usually locate most bags within 24 to 72 hours.", native: '다르지만, 보통 24시간에서 72시간 이내에 대부분의 가방을 찾습니다.', words: [{ word: 'locate', meaning: '찾아내다' }] },
    { id: 11, speaker: 'M' as const, target: "Okay, that’s good to know. What happens if you can't find it?", native: '알겠습니다, 알고 있어서 다행입니다. 찾을 수 없으면 어떻게 되나요?', words: [{ word: 'happens', meaning: '일어나다' }] },
    { id: 12, speaker: 'F' as const, target: "If we can't locate your bag, you'll be compensated based on its contents.", native: '만약 가방을 찾을 수 없다면, 내용물에 따라 보상을 받게 됩니다.', words: [{ word: 'compensated', meaning: '보상받다' }] },
    { id: 13, speaker: 'M' as const, target: "I understand. Can you provide me with a reference number for this report?", native: '알겠습니다. 이 보고서에 대한 참조 번호를 알려주시겠어요?', words: [{ word: 'reference number', meaning: '참조 번호' }] },
    { id: 14, speaker: 'F' as const, target: "Certainly. Your reference number is LST789. We'll keep you updated.", native: '물론입니다. 참조 번호는 LST789입니다. 계속 업데이트해 드리겠습니다.', words: [{ word: 'updated', meaning: '업데이트' }] },
    { id: 15, speaker: 'M' as const, target: "Thank you so much for your help. I really appreciate it.", native: '도와주셔서 정말 감사합니다. 정말 감사합니다.', words: [{ word: 'appreciate', meaning: '감사하다' }] },
    { id: 16, speaker: 'F' as const, target: "You're welcome, Mr. Johnson. We'll do our best to find your luggage.", native: '천만에요, 존슨 씨. 수하물을 찾기 위해 최선을 다하겠습니다.', words: [{ word: 'do our best', meaning: '최선을 다하다' }] },
  ],
};

// 실제 오디오 파일 길이 (초) - ffprobe로 측정 (edge-tts)
const audioDurations = [
  5.016, 5.328, 5.304, 4.992, 4.848, 5.016, 4.896, 5.328,
  4.104, 5.928, 5.592, 6.648, 5.808, 8.136, 4.968, 7.080
];

const sampleConfig = {
  channelId: 'english_for_korean',
  meta: { name: '귀가 뚫리는 영어', targetLanguage: 'English', nativeLanguage: 'Korean' },
  theme: { logo: '', introSound: '', backgroundStyle: 'illustration' as const, primaryColor: '#87CEEB', secondaryColor: '#FF69B4' },
  colors: { maleText: '#87CEEB', femaleText: '#FF69B4', nativeText: '#FFFFFF', wordMeaning: '#888888', background: '#000000' },
  layout: { step3ImageRatio: 0.4, subtitlePosition: 'center' as const, speakerIndicator: 'left' as const },
  tts: { provider: 'google' as const, maleVoice: 'en-US-Standard-D', femaleVoice: 'en-US-Standard-F', targetLanguageCode: 'en-US' },
  content: { sentenceCount: 12, repeatCount: 10, difficulty: 'intermediate' as const },
  schedule: { publishTime: '06:00', timezone: 'Asia/Seoul' },
};

const defaultSteps = [
  { step: 1, title: '자막 없이 듣기', description: '자막 없이 전체 내용을 들어보세요' },
  { step: 2, title: '자막 보며 듣기', description: '자막과 함께 들으며 내용을 파악하세요' },
  { step: 3, title: '문장별 반복 듣기', description: '문장을 10번씩 반복해서 익히세요' },
  { step: 4, title: '다시 자막 없이 듣기', description: '얼마나 잘 들리는지 확인하세요' },
];

// Wrapper components
const ListeningVideoWrapper: React.FC<Record<string, unknown>> = () => (
  <ListeningVideo script={sampleScript} config={sampleConfig} />
);

const AudioListeningVideoWrapper: React.FC<Record<string, unknown>> = () => (
  <AudioListeningVideo 
    script={sampleScript} 
    config={sampleConfig}
    audioBasePath="audio"  // public/audio 폴더 참조
    audioDurations={audioDurations}
  />
);

const Step3PreviewWrapper: React.FC<Record<string, unknown>> = () => (
  <Step3Section
    sentence={sampleScript.sentences[0]}
    colors={sampleConfig.colors}
    repeatIndex={1}
    totalRepeats={10}
  />
);

const IntroPreviewWrapper: React.FC<Record<string, unknown>> = () => (
  <IntroSection channelName={sampleConfig.meta.name} steps={defaultSteps} />
);

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* 오디오 포함 전체 영상 */}
      <Composition
        id="AudioListeningVideo"
        component={AudioListeningVideoWrapper}
        durationInFrames={calculateAudioVideoDuration(
          sampleScript.sentences.length, 
          sampleConfig.content.repeatCount,
          audioDurations
        )}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 전체 영상 (오디오 없음) */}
      <Composition
        id="ListeningVideo"
        component={ListeningVideoWrapper}
        durationInFrames={calculateTotalDuration(sampleScript.sentences.length, sampleConfig.content.repeatCount)}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* Step3 개별 테스트 */}
      <Composition
        id="Step3Preview"
        component={Step3PreviewWrapper}
        durationInFrames={90}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 인트로 테스트 */}
      <Composition
        id="IntroPreview"
        component={IntroPreviewWrapper}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
