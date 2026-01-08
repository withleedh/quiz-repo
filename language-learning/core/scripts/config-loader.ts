/**
 * 채널 설정 로더
 * 
 * channels/ 폴더의 JSON 파일을 읽어 ChannelConfig 객체로 반환
 */

import * as fs from 'fs';
import * as path from 'path';
import { ChannelConfig } from '../src/types/config';

const CHANNELS_DIR = path.join(__dirname, '../../channels');

/**
 * 특정 채널 설정 로드
 */
export function loadChannelConfig(channelName: string): ChannelConfig {
  const configPath = path.join(CHANNELS_DIR, `${channelName}.json`);
  
  if (!fs.existsSync(configPath)) {
    throw new Error(`채널 설정 파일을 찾을 수 없습니다: ${configPath}`);
  }
  
  const configJson = fs.readFileSync(configPath, 'utf-8');
  const config = JSON.parse(configJson) as ChannelConfig;
  
  // 기본값 설정 (config가 없는 필드에만 적용)
  config.content = {
    ...{
      sentenceCount: 12,
      repeatCount: 10,
      difficulty: 'intermediate' as const,
    },
    ...config.content,
  };
  
  config.layout = {
    ...{
      step3ImageRatio: 0.4,
      subtitlePosition: 'center' as const,
      speakerIndicator: 'left' as const,
    },
    ...config.layout,
  };
  
  return config;
}

/**
 * 사용 가능한 모든 채널 목록 가져오기
 */
export function listChannels(): string[] {
  if (!fs.existsSync(CHANNELS_DIR)) {
    return [];
  }
  
  return fs.readdirSync(CHANNELS_DIR)
    .filter(file => file.endsWith('.json'))
    .map(file => file.replace('.json', ''));
}

/**
 * 모든 채널 설정 로드
 */
export function loadAllChannelConfigs(): Map<string, ChannelConfig> {
  const configs = new Map<string, ChannelConfig>();
  const channels = listChannels();
  
  for (const channel of channels) {
    try {
      configs.set(channel, loadChannelConfig(channel));
    } catch (error) {
      console.warn(`채널 로드 실패: ${channel}`, error);
    }
  }
  
  return configs;
}

/**
 * 오늘의 카테고리 가져오기
 */
export function getTodayCategory(config: ChannelConfig): string {
  const today = new Date();
  const dayOfWeek = today.getDay(); // 0=일, 1=월, ...
  
  const category = config.categories?.find(c => c.dayOfWeek === dayOfWeek);
  
  return category?.name || '일상 이야기';
}

/**
 * 채널 검증
 */
export function validateChannelConfig(config: ChannelConfig): string[] {
  const errors: string[] = [];
  
  if (!config.channelId) errors.push('channelId가 필요합니다');
  if (!config.meta?.targetLanguage) errors.push('meta.targetLanguage가 필요합니다');
  if (!config.meta?.nativeLanguage) errors.push('meta.nativeLanguage가 필요합니다');
  if (!config.tts?.maleVoice) errors.push('tts.maleVoice가 필요합니다');
  if (!config.tts?.femaleVoice) errors.push('tts.femaleVoice가 필요합니다');
  
  return errors;
}
