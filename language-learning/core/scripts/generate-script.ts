/**
 * AI 대본 생성 스크립트
 * 
 * Gemini API를 사용하여 채널 설정에 맞는 2인 대화 대본 생성
 */

import * as fs from 'fs';
import * as path from 'path';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { ChannelConfig, Script, Sentence, WordMeaning } from '../src/types/config';
import { loadChannelConfig, getTodayCategory } from './config-loader';
import * as dotenv from 'dotenv';

dotenv.config({ path: path.join(__dirname, '../../../.env') });

/**
 * 대본 생성 프롬프트 템플릿
 */
function buildPrompt(
  config: ChannelConfig,
  topic: string,
  style: string,
  category: string
): string {
  const { targetLanguage, nativeLanguage } = config.meta;
  const { sentenceCount } = config.content;
  
  return `# 역할
너는 ${targetLanguage} 학습 대화 콘텐츠 작가야.

# 기본 규칙 (필수 준수)
1. 화자: 남성(M)과 여성(F) 두 명의 대화
2. 턴 수: ${sentenceCount}~${sentenceCount + 4}턴 (총 ${sentenceCount * 2}~${(sentenceCount + 4) * 2}문장)
3. 문장 길이: 8~15단어
4. 난이도: ${config.content.difficulty}
5. 학습 언어: ${targetLanguage}
6. 해석 언어: ${nativeLanguage}

# 오늘의 카테고리
${category}

# 오늘의 주제
${topic}

# 오늘의 스타일 (자유롭게 적용)
${style}

# 출력 형식 (JSON만 출력, 다른 텍스트 없이)
{
  "title": {
    "target": "${targetLanguage}로 된 제목",
    "native": "${nativeLanguage}로 된 제목"
  },
  "sentences": [
    {
      "id": 1,
      "speaker": "M",
      "target": "${targetLanguage} 문장",
      "native": "${nativeLanguage} 해석",
      "words": [
        {"word": "핵심단어1", "meaning": "${nativeLanguage} 뜻"},
        {"word": "핵심단어2", "meaning": "${nativeLanguage} 뜻"}
      ]
    },
    {
      "id": 2,
      "speaker": "F",
      "target": "${targetLanguage} 문장",
      "native": "${nativeLanguage} 해석",
      "words": [
        {"word": "핵심단어", "meaning": "${nativeLanguage} 뜻"}
      ]
    }
  ]
}

중요: 
- 각 문장에서 2~4개의 핵심 단어/표현을 선정하여 words 배열에 포함
- JSON만 출력하세요. 마크다운이나 다른 텍스트 없이.`;
}

/**
 * 주제 + 스타일 제안 생성
 */
export async function generateTopicSuggestions(
  config: ChannelConfig,
  category: string,
  count: number = 3
): Promise<Array<{ topic: string; style: string }>> {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error('GEMINI_API_KEY가 설정되지 않았습니다');
  
  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });
  
  const { targetLanguage, nativeLanguage } = config.meta;
  
  const prompt = `# 역할
너는 ${targetLanguage} 학습 콘텐츠 기획자야.

# 목표
"${category}" 카테고리에 맞는 대화 주제와 스타일을 ${count}개 제안해.

# 조건
- 학습 언어: ${targetLanguage}
- 학습자 모국어: ${nativeLanguage}
- 주제는 일상적이고 공감 가능한 것
- 스타일은 분위기, 감정 흐름, 톤을 설명

# 출력 형식 (JSON만)
[
  {
    "topic": "${nativeLanguage}로 된 주제 설명",
    "style": "분위기→감정변화, 톤 설명"
  }
]`;

  const result = await model.generateContent(prompt);
  const text = result.response.text();
  
  // JSON 파싱
  let jsonStr = text.trim();
  const match = jsonStr.match(/\[[\s\S]*\]/);
  if (match) jsonStr = match[0];
  
  return JSON.parse(jsonStr);
}

/**
 * 대본 생성
 */
export async function generateScript(
  config: ChannelConfig,
  topic: string,
  style: string,
  category?: string
): Promise<Script> {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error('GEMINI_API_KEY가 설정되지 않았습니다');
  
  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });
  
  const cat = category || getTodayCategory(config);
  const prompt = buildPrompt(config, topic, style, cat);
  
  console.log(`🎭 대본 생성 중... (${config.meta.targetLanguage})`);
  console.log(`   📌 주제: ${topic}`);
  console.log(`   📌 스타일: ${style}`);
  
  const result = await model.generateContent(prompt);
  const text = result.response.text();
  
  // JSON 파싱
  let jsonStr = text.trim();
  const jsonMatch = jsonStr.match(/\{[\s\S]*\}/);
  if (jsonMatch) jsonStr = jsonMatch[0];
  
  const parsed = JSON.parse(jsonStr);
  
  const script: Script = {
    channelId: config.channelId,
    date: new Date().toISOString().split('T')[0],
    category: cat,
    metadata: {
      topic,
      style,
      title: parsed.title,
    },
    sentences: parsed.sentences,
  };
  
  console.log(`   ✅ 생성 완료! (${script.sentences.length}개 문장)`);
  
  return script;
}

/**
 * 대본 저장
 */
export function saveScript(script: Script, outputDir?: string): string {
  const dir = outputDir || path.join(
    __dirname, '../../../output', script.channelId, script.date
  );
  fs.mkdirSync(dir, { recursive: true });
  
  const filePath = path.join(dir, 'script.json');
  fs.writeFileSync(filePath, JSON.stringify(script, null, 2), 'utf-8');
  
  console.log(`   💾 저장: ${filePath}`);
  return filePath;
}

// CLI 실행
async function main() {
  const args = process.argv.slice(2);
  let channelName = 'english';
  let topic = '';
  let style = '';
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--channel' && args[i + 1]) {
      channelName = args[i + 1];
      i++;
    } else if (args[i] === '--topic' && args[i + 1]) {
      topic = args[i + 1];
      i++;
    } else if (args[i] === '--style' && args[i + 1]) {
      style = args[i + 1];
      i++;
    }
  }
  
  try {
    const config = loadChannelConfig(channelName);
    
    // 주제/스타일이 없으면 AI 생성
    if (!topic || !style) {
      console.log('🎲 주제+스타일 생성 중...');
      const suggestions = await generateTopicSuggestions(
        config, getTodayCategory(config), 1
      );
      topic = topic || suggestions[0].topic;
      style = style || suggestions[0].style;
    }
    
    const script = await generateScript(config, topic, style);
    saveScript(script);
    
  } catch (error) {
    console.error('❌ 오류:', error);
    process.exit(1);
  }
}

// 직접 실행될 때만 main 호출
if (require.main === module) {
  main();
}
