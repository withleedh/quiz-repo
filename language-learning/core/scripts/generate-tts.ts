/**
 * 다국어 TTS 생성 스크립트
 * 
 * 채널 설정에 따라 적절한 TTS 프로바이더 선택
 * - OpenAI TTS: 영어, 다국어 지원
 * - Google Cloud TTS: 일본어, 중국어 등 아시아 언어
 */

import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';
import { ChannelConfig, Script, Sentence } from '../src/types/config';
import { loadChannelConfig } from './config-loader';
import * as dotenv from 'dotenv';

dotenv.config({ path: path.join(__dirname, '../../../.env') });

interface TTSResult {
  sentenceId: number;
  speaker: "M" | "F";
  singlePath: string;
  repeatedPath: string;
}

/**
 * OpenAI TTS로 오디오 생성
 */
async function generateWithOpenAI(
  text: string,
  voice: string,
  outputPath: string
): Promise<void> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error('OPENAI_API_KEY가 설정되지 않았습니다');
  
  const response = await fetch('https://api.openai.com/v1/audio/speech', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'tts-1',
      input: text,
      voice: voice,
      response_format: 'mp3',
    }),
  });
  
  if (!response.ok) {
    throw new Error(`OpenAI TTS 오류: ${response.statusText}`);
  }
  
  const buffer = Buffer.from(await response.arrayBuffer());
  fs.writeFileSync(outputPath, buffer);
}

/**
 * Google Cloud TTS로 오디오 생성 (일본어/중국어 등)
 */
async function generateWithGoogle(
  text: string,
  voiceName: string,
  languageCode: string,
  outputPath: string
): Promise<void> {
  // Google Cloud TTS는 gcloud CLI 또는 SDK 필요
  // 여기서는 간단히 gtts 사용 (품질은 낮지만 무료)
  const escapedText = text.replace(/"/g, '\\"').replace(/'/g, "\\'");
  
  try {
    execSync(
      `python3 -c "from gtts import gTTS; tts = gTTS('${escapedText}', lang='${languageCode.split('-')[0]}'); tts.save('${outputPath}')"`,
      { stdio: 'pipe' }
    );
  } catch (error) {
    console.warn(`   ⚠️ gTTS 실패, edge-tts 시도 중...`);
    // edge-tts 대안
    execSync(
      `edge-tts --voice "${voiceName}" --text "${escapedText}" --write-media "${outputPath}"`,
      { stdio: 'pipe' }
    );
  }
}

/**
 * FFmpeg로 오디오 반복 합성
 */
function repeatAudio(inputPath: string, outputPath: string, count: number): void {
  // 동일 오디오를 count번 이어붙이기
  const listFile = inputPath.replace('.mp3', '_list.txt');
  const listContent = Array(count).fill(`file '${inputPath}'`).join('\n');
  fs.writeFileSync(listFile, listContent);
  
  execSync(
    `ffmpeg -y -f concat -safe 0 -i "${listFile}" -c copy "${outputPath}" 2>/dev/null`,
    { stdio: 'pipe' }
  );
  
  fs.unlinkSync(listFile);
}

/**
 * Edge TTS로 오디오 생성 (무료, 다국어, 성별 구분 가능)
 */
async function generateWithEdge(
  text: string,
  voiceName: string,
  outputPath: string
): Promise<void> {
  const escapedText = text.replace(/"/g, '\\"').replace(/'/g, "\\'");
  
  try {
    // Mac/Linux의 경우 edge-tts CLI 사용
    execSync(
      `edge-tts --voice "${voiceName}" --text "${escapedText}" --write-media "${outputPath}"`,
      { stdio: 'pipe' }
    );
  } catch (error) {
    throw new Error(`Edge TTS 실패: ${error}`);
  }
}

/**
 * 대본의 모든 문장에 대해 TTS 생성
 */
export async function generateTTS(
  config: ChannelConfig,
  script: Script,
  outputDir?: string
): Promise<TTSResult[]> {
  const dir = outputDir || path.join(
    __dirname, '../../../output', config.channelId, script.date, 'audio'
  );
  fs.mkdirSync(dir, { recursive: true });
  
  const { provider, maleVoice, femaleVoice, targetLanguageCode } = config.tts;
  const { repeatCount } = config.content;
  
  console.log(`🎤 TTS 생성 시작 (${script.sentences.length}개 문장)`);
  console.log(`   📁 출력: ${dir}`);
  console.log(`   🔊 프로바이더: ${provider}`);
  
  const results: TTSResult[] = [];
  
  for (const sentence of script.sentences) {
    const voice = sentence.speaker === 'M' ? maleVoice : femaleVoice;
    const paddedId = String(sentence.id).padStart(2, '0');
    const singlePath = path.join(dir, `sentence_${paddedId}_single.mp3`);
    const repeatedPath = path.join(dir, `sentence_${paddedId}_x${repeatCount}.mp3`);
    
    console.log(`   [${paddedId}] ${sentence.speaker}: "${sentence.target.substring(0, 30)}..."`);
    
    try {
      // 1. 단일 오디오 생성
      if (provider === 'openai') {
        await generateWithOpenAI(sentence.target, voice, singlePath);
      } else if (provider === 'edge-tts') {
        await generateWithEdge(sentence.target, voice, singlePath);
      } else {
        await generateWithGoogle(sentence.target, voice, targetLanguageCode, singlePath);
      }
      
      // 2. 반복 오디오 생성
      repeatAudio(singlePath, repeatedPath, repeatCount);
      
      results.push({
        sentenceId: sentence.id,
        speaker: sentence.speaker,
        singlePath,
        repeatedPath,
      });
      
    } catch (error) {
      console.error(`   ❌ 문장 ${sentence.id} TTS 실패:`, error);
    }
  }
  
  // 전체 대본 오디오 합성 (Step 1, 2, 4용)
  const fullScriptPath = path.join(dir, 'full_script.mp3');
  const singlePaths = results.map(r => r.singlePath);
  
  if (singlePaths.length > 0) {
    const listFile = path.join(dir, 'full_list.txt');
    const listContent = singlePaths.map(p => `file '${p}'`).join('\n');
    fs.writeFileSync(listFile, listContent);
    
    execSync(
      `ffmpeg -y -f concat -safe 0 -i "${listFile}" -c copy "${fullScriptPath}" 2>/dev/null`,
      { stdio: 'pipe' }
    );
    fs.unlinkSync(listFile);
    
    console.log(`   ✅ 전체 대본 오디오: ${fullScriptPath}`);
  }
  
  console.log(`✅ TTS 생성 완료! (${results.length}/${script.sentences.length})`);
  
  return results;
}

// CLI 실행
async function main() {
  const args = process.argv.slice(2);
  let channelName = 'english';
  let scriptPath = '';
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--channel' && args[i + 1]) {
      channelName = args[i + 1];
      i++;
    } else if (args[i] === '--script' && args[i + 1]) {
      scriptPath = args[i + 1];
      i++;
    }
  }
  
  if (!scriptPath) {
    console.error('사용법: npm run generate:tts -- --channel english --script output/english/2026-01-08/script.json');
    process.exit(1);
  }
  
  try {
    const config = loadChannelConfig(channelName);
    const script: Script = JSON.parse(fs.readFileSync(scriptPath, 'utf-8'));
    
    await generateTTS(config, script);
    
  } catch (error) {
    console.error('❌ 오류:', error);
    process.exit(1);
  }
}

// 직접 실행될 때만 main 호출
if (require.main === module) {
  main();
}
