/**
 * 전체 파이프라인 스크립트
 * 
 * 채널 지정 → 주제 생성 → 대본 생성 → TTS 생성 → (Remotion 렌더링)
 */

import * as fs from 'fs';
import * as path from 'path';
import { loadChannelConfig, getTodayCategory, listChannels } from './config-loader';
import { generateTopicSuggestions, generateScript, saveScript } from './generate-script';
import { generateTTS } from './generate-tts';
import { ChannelConfig, Script } from '../src/types/config';
import * as dotenv from 'dotenv';

dotenv.config({ path: path.join(__dirname, '../../../.env') });

interface PipelineOptions {
  channel: string;
  topic?: string;
  style?: string;
  skipTTS?: boolean;
  skipRender?: boolean;
}

/**
 * 단일 채널 파이프라인 실행
 */
export async function runPipeline(options: PipelineOptions): Promise<void> {
  const { channel, skipTTS, skipRender } = options;
  let { topic, style } = options;
  
  console.log('═'.repeat(60));
  console.log(`🎬 언어 학습 영상 자동화 파이프라인`);
  console.log('═'.repeat(60));
  
  // 1. 채널 설정 로드
  console.log(`\n📺 [1/5] 채널 설정 로드: ${channel}`);
  const config = loadChannelConfig(channel);
  console.log(`   ✅ ${config.meta.name} (${config.meta.targetLanguage} → ${config.meta.nativeLanguage})`);
  
  const category = getTodayCategory(config);
  console.log(`   📌 오늘의 카테고리: ${category}`);
  
  // 2. 주제/스타일 생성 (없으면)
  if (!topic || !style) {
    console.log(`\n🎲 [2/5] 주제+스타일 생성 중...`);
    const suggestions = await generateTopicSuggestions(config, category, 1);
    topic = topic || suggestions[0].topic;
    style = style || suggestions[0].style;
    console.log(`   📌 주제: ${topic}`);
    console.log(`   📌 스타일: ${style}`);
  } else {
    console.log(`\n🎲 [2/5] 주제+스타일 (지정됨)`);
    console.log(`   📌 주제: ${topic}`);
    console.log(`   📌 스타일: ${style}`);
  }
  
  // 3. 대본 생성
  console.log(`\n📝 [3/5] 대본 생성 중...`);
  const script = await generateScript(config, topic, style, category);
  const scriptPath = saveScript(script);
  
  // 4. TTS 생성
  if (!skipTTS) {
    console.log(`\n🎤 [4/5] TTS 생성 중...`);
    await generateTTS(config, script);
  } else {
    console.log(`\n🎤 [4/5] TTS 생성 (건너뜀)`);
  }
  
  // 5. Remotion 렌더링
  if (!skipRender) {
    console.log(`\n🎬 [5/5] Remotion 렌더링`);
    console.log(`   ⚠️ 렌더링은 구현 예정 (Phase 2)`);
    // TODO: execSync(`npx remotion render ...`);
  } else {
    console.log(`\n🎬 [5/5] Remotion 렌더링 (건너뜀)`);
  }
  
  // 완료
  console.log('\n' + '═'.repeat(60));
  console.log('✅ 파이프라인 완료!');
  console.log('═'.repeat(60));
  console.log(`📂 출력 폴더: output/${config.channelId}/${script.date}/`);
  console.log('═'.repeat(60));
}

/**
 * 모든 채널 일괄 실행
 */
export async function runAllPipelines(): Promise<void> {
  const channels = listChannels();
  
  console.log(`🌐 전체 ${channels.length}개 채널 파이프라인 실행`);
  
  for (const channel of channels) {
    try {
      await runPipeline({ channel, skipRender: true });
    } catch (error) {
      console.error(`❌ ${channel} 채널 실패:`, error);
    }
  }
}

// CLI
async function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('--help') || args.length === 0) {
    console.log(`
언어 학습 영상 자동화 파이프라인

사용법:
  npm run pipeline -- --channel english
  npm run pipeline -- --channel japanese --topic "여행 이야기"
  npm run pipeline:all

옵션:
  --channel     채널 이름 (필수)
  --topic       주제 (선택, 없으면 AI 생성)
  --style       스타일 (선택, 없으면 AI 생성)
  --skip-tts    TTS 생성 건너뛰기
  --skip-render 렌더링 건너뛰기

사용 가능한 채널:
  ${listChannels().join(', ')}
    `);
    process.exit(0);
  }
  
  const options: PipelineOptions = {
    channel: 'english',
  };
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--channel' && args[i + 1]) {
      options.channel = args[i + 1];
      i++;
    } else if (args[i] === '--topic' && args[i + 1]) {
      options.topic = args[i + 1];
      i++;
    } else if (args[i] === '--style' && args[i + 1]) {
      options.style = args[i + 1];
      i++;
    } else if (args[i] === '--skip-tts') {
      options.skipTTS = true;
    } else if (args[i] === '--skip-render') {
      options.skipRender = true;
    }
  }
  
  try {
    await runPipeline(options);
  } catch (error) {
    console.error('❌ 파이프라인 오류:', error);
    process.exit(1);
  }
}

main();
