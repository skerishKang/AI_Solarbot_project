"""
AI 기반 콘텐츠 분석 통합 모듈
intelligent_content_analyzer와 ai_handler를 연결하여 고급 AI 분석 제공
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
import asyncio
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class AIContentIntegration:
    """AI 기반 콘텐츠 분석 통합 클래스"""
    
    def __init__(self, ai_handler):
        """
        AI 핸들러와 연동하여 초기화
        
        Args:
            ai_handler: AIHandler 인스턴스
        """
        self.ai_handler = ai_handler
        self.cache = {}  # AI 응답 캐싱
        self.cache_expiry = 3600  # 1시간 캐시 유효시간
        
        # 성능 최적화를 위한 설정
        self.max_content_length = 2000  # AI 분석용 최대 콘텐츠 길이
        self.batch_size = 3  # 배치 처리 크기
        self.request_delay = 1  # API 요청 간 지연 시간 (초)
        
    async def perform_ai_sentiment_analysis(self, text: str, content_type: str) -> Dict[str, Any]:
        """
        AI 기반 감정 분석 수행
        
        Args:
            text: 분석할 텍스트
            content_type: 콘텐츠 타입
            
        Returns:
            감정 분석 결과 딕셔너리
        """
        try:
            # 캐시 확인
            cache_key = f"sentiment_{hash(text[:500])}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 텍스트 길이 제한
            analyzed_text = text[:self.max_content_length]
            if len(text) > self.max_content_length:
                analyzed_text += "..."
            
            # AI 감정 분석 프롬프트 (개선된 버전)
            prompt = self._create_sentiment_analysis_prompt(analyzed_text, content_type)
            
            # AI 응답 요청
            ai_response, model_used = await self.ai_handler.chat_with_ai(prompt, "SentimentAnalyzer")
            
            if ai_response and ai_response.strip():
                parsed_result = self._parse_sentiment_response(ai_response)
                parsed_result['ai_model_used'] = model_used
                parsed_result['analysis_timestamp'] = datetime.now().isoformat()
                
                # 캐시에 저장
                self._save_to_cache(cache_key, parsed_result)
                
                return parsed_result
            
            return self._get_default_sentiment_result()
            
        except Exception as e:
            logger.error(f"AI 감정 분석 오류: {e}")
            return self._get_default_sentiment_result()
    
    async def perform_ai_quality_analysis(self, title: str, content: str, url: str, content_type: str) -> Dict[str, Any]:
        """
        AI 기반 품질 분석 수행
        
        Args:
            title: 콘텐츠 제목
            content: 콘텐츠 내용
            url: 콘텐츠 URL
            content_type: 콘텐츠 타입
            
        Returns:
            품질 분석 결과 딕셔너리
        """
        try:
            # 캐시 확인
            cache_key = f"quality_{hash(title + content[:500])}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 콘텐츠 길이 제한
            analyzed_content = content[:self.max_content_length]
            if len(content) > self.max_content_length:
                analyzed_content += "..."
            
            # AI 품질 분석 프롬프트
            prompt = self._create_quality_analysis_prompt(title, analyzed_content, url, content_type)
            
            # AI 응답 요청
            ai_response, model_used = await self.ai_handler.chat_with_ai(prompt, "QualityAnalyzer")
            
            if ai_response and ai_response.strip():
                parsed_result = self._parse_quality_response(ai_response)
                parsed_result['ai_model_used'] = model_used
                parsed_result['analysis_timestamp'] = datetime.now().isoformat()
                
                # 캐시에 저장
                self._save_to_cache(cache_key, parsed_result)
                
                return parsed_result
            
            return self._get_default_quality_result()
            
        except Exception as e:
            logger.error(f"AI 품질 분석 오류: {e}")
            return self._get_default_quality_result()
    
    async def perform_comprehensive_ai_analysis(self, title: str, content: str, url: str, content_type: str) -> Dict[str, Any]:
        """
        포괄적 AI 분석 수행 (감정 + 품질 통합)
        
        Args:
            title: 콘텐츠 제목
            content: 콘텐츠 내용
            url: 콘텐츠 URL
            content_type: 콘텐츠 타입
            
        Returns:
            통합 분석 결과 딕셔너리
        """
        try:
            # 병렬로 감정 분석과 품질 분석 수행
            sentiment_task = self.perform_ai_sentiment_analysis(content, content_type)
            quality_task = self.perform_ai_quality_analysis(title, content, url, content_type)
            
            sentiment_result, quality_result = await asyncio.gather(
                sentiment_task, quality_task, return_exceptions=True
            )
            
            # 결과 통합
            integrated_result = {}
            
            if isinstance(sentiment_result, dict):
                integrated_result.update(sentiment_result)
            
            if isinstance(quality_result, dict):
                integrated_result.update(quality_result)
            
            # 통합 점수 계산
            integrated_result['ai_comprehensive_score'] = self._calculate_comprehensive_score(
                sentiment_result, quality_result
            )
            
            return integrated_result
            
        except Exception as e:
            logger.error(f"포괄적 AI 분석 오류: {e}")
            return {}
    
    async def perform_batch_ai_analysis(self, content_list: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        배치 AI 분석 수행
        
        Args:
            content_list: 분석할 콘텐츠 리스트 [{"title": "", "content": "", "url": "", "type": ""}]
            
        Returns:
            분석 결과 리스트
        """
        try:
            results = []
            
            # 배치 크기만큼 나누어 처리
            for i in range(0, len(content_list), self.batch_size):
                batch = content_list[i:i + self.batch_size]
                
                # 배치 내 병렬 처리
                batch_tasks = []
                for content_info in batch:
                    task = self.perform_comprehensive_ai_analysis(
                        content_info.get('title', ''),
                        content_info.get('content', ''),
                        content_info.get('url', ''),
                        content_info.get('type', 'unknown')
                    )
                    batch_tasks.append(task)
                
                # 배치 결과 수집
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, dict):
                        results.append(result)
                    else:
                        results.append({'error': str(result)})
                
                # API 요청 간 지연
                if i + self.batch_size < len(content_list):
                    await asyncio.sleep(self.request_delay)
            
            return results
            
        except Exception as e:
            logger.error(f"배치 AI 분석 오류: {e}")
            return []
    
    def merge_rule_based_and_ai_results(self, rule_based: Dict[str, Any], ai_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rule-based와 AI 결과 융합
        
        Args:
            rule_based: Rule-based 분석 결과
            ai_results: AI 분석 결과
            
        Returns:
            융합된 분석 결과
        """
        try:
            merged = rule_based.copy()
            
            if not ai_results:
                return merged
            
            # 감정 분석 결과 융합
            self._merge_sentiment_results(merged, ai_results)
            
            # 품질 분석 결과 융합
            self._merge_quality_results(merged, ai_results)
            
            # AI 모델 정보 추가
            if 'ai_model_used' in ai_results:
                merged['ai_model_used'] = ai_results['ai_model_used']
            
            return merged
            
        except Exception as e:
            logger.error(f"결과 융합 오류: {e}")
            return rule_based
    
    def _create_sentiment_analysis_prompt(self, text: str, content_type: str) -> str:
        """감정 분석 프롬프트 생성"""
        return f"""다음 텍스트의 감정을 정밀하게 분석해주세요.

텍스트: "{text}"
콘텐츠 타입: {content_type}

다음 JSON 형식으로 정확히 응답해주세요:
{{
    "dominant_emotion": "joy|anger|sadness|fear|surprise|disgust|trust|anticipation|neutral",
    "intensity": 0.8,
    "confidence": 0.9,
    "detailed_emotions": {{
        "joy": 0.2,
        "anger": 0.1,
        "sadness": 0.0,
        "fear": 0.0,
        "surprise": 0.1,
        "disgust": 0.0,
        "trust": 0.3,
        "anticipation": 0.3
    }},
    "contextual_features": "direct|sarcastic|ironic|emphatic|neutral",
    "sentiment_summary": "감정 분석 요약 설명"
}}

분석 기준:
- 한국어 맥락과 문화적 뉘앙스 고려
- 반어법, 아이러니, 강조 표현 감지
- 콘텐츠 타입별 특성 반영 ({content_type})
- 정확한 수치 제공 (소수점 1자리)
- 모든 감정 점수의 합은 1.0이 되도록 조정"""
    
    def _create_quality_analysis_prompt(self, title: str, content: str, url: str, content_type: str) -> str:
        """품질 분석 프롬프트 생성"""
        return f"""다음 콘텐츠의 품질을 6개 차원으로 정밀 평가해주세요.

제목: "{title}"
URL: {url}
콘텐츠 타입: {content_type}
콘텐츠: "{content}"

다음 JSON 형식으로 정확히 응답해주세요:
{{
    "overall_quality": 85,
    "quality_grade": "A+|A|A-|B+|B|B-|C+|C|C-|D+|D|D-|F",
    "dimensions": {{
        "reliability": 90,
        "usefulness": 85,
        "accuracy": 80,
        "completeness": 75,
        "readability": 88,
        "originality": 70
    }},
    "language_quality": {{
        "grammar_score": 90,
        "vocabulary_diversity": 85,
        "sentence_variety": 80
    }},
    "improvement_suggestions": [
        "구체적인 개선 제안 1",
        "구체적인 개선 제안 2",
        "구체적인 개선 제안 3"
    ],
    "quality_summary": "품질 평가 요약 및 주요 특징"
}}

평가 기준:
- 신뢰도: 출처의 신뢰성, 사실 확인 가능성 (0-100)
- 유용성: 독자에게 실질적 도움 정도 (0-100)
- 정확성: 정보의 정확성, 오류 여부 (0-100)
- 완성도: 내용의 완전성, 빠진 정보 여부 (0-100)
- 가독성: 읽기 쉬움, 구조화 정도 (0-100)
- 독창성: 새로운 관점, 차별화된 내용 (0-100)

콘텐츠 타입 특성 고려: {content_type}"""
    
    def _parse_sentiment_response(self, response: str) -> Dict[str, Any]:
        """AI 감정 분석 응답 파싱"""
        try:
            # JSON 부분 추출 시도
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                try:
                    parsed_json = json.loads(json_str)
                    
                    result = {
                        'ai_dominant_emotion': parsed_json.get('dominant_emotion', 'neutral'),
                        'ai_intensity': float(parsed_json.get('intensity', 0.5)),
                        'ai_confidence': float(parsed_json.get('confidence', 0.5)),
                        'ai_distribution': parsed_json.get('detailed_emotions', {}),
                        'ai_context': parsed_json.get('contextual_features', 'neutral'),
                        'ai_sentiment_summary': parsed_json.get('sentiment_summary', '')
                    }
                    
                    # 값 검증 및 정규화
                    result['ai_intensity'] = max(0.0, min(1.0, result['ai_intensity']))
                    result['ai_confidence'] = max(0.0, min(1.0, result['ai_confidence']))
                    
                    # 감정 분포 정규화
                    if result['ai_distribution']:
                        total_score = sum(result['ai_distribution'].values())
                        if total_score > 0:
                            for emotion in result['ai_distribution']:
                                result['ai_distribution'][emotion] = result['ai_distribution'][emotion] / total_score
                    
                    return result
                    
                except json.JSONDecodeError:
                    pass
            
            # JSON 파싱 실패 시 기본값 반환
            return self._get_default_sentiment_result()
            
        except Exception as e:
            logger.error(f"감정 분석 응답 파싱 오류: {e}")
            return self._get_default_sentiment_result()
    
    def _parse_quality_response(self, response: str) -> Dict[str, Any]:
        """AI 품질 분석 응답 파싱"""
        try:
            # JSON 부분 추출 시도
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                try:
                    parsed_json = json.loads(json_str)
                    
                    result = {
                        'ai_overall_quality': float(parsed_json.get('overall_quality', 50.0)),
                        'ai_quality_grade': parsed_json.get('quality_grade', 'C'),
                        'ai_quality_dimensions': parsed_json.get('dimensions', {}),
                        'ai_language_quality': parsed_json.get('language_quality', {}),
                        'ai_improvement_suggestions': parsed_json.get('improvement_suggestions', []),
                        'ai_quality_summary': parsed_json.get('quality_summary', '')
                    }
                    
                    # 값 검증 및 정규화
                    result['ai_overall_quality'] = max(0.0, min(100.0, result['ai_overall_quality']))
                    
                    # 차원별 점수 정규화
                    for dimension, score in result['ai_quality_dimensions'].items():
                        result['ai_quality_dimensions'][dimension] = max(0.0, min(100.0, float(score)))
                    
                    # 언어 품질 점수 정규화
                    for aspect, score in result['ai_language_quality'].items():
                        result['ai_language_quality'][aspect] = max(0.0, min(100.0, float(score)))
                    
                    return result
                    
                except json.JSONDecodeError:
                    pass
            
            # JSON 파싱 실패 시 기본값 반환
            return self._get_default_quality_result()
            
        except Exception as e:
            logger.error(f"품질 분석 응답 파싱 오류: {e}")
            return self._get_default_quality_result()
    
    def _merge_sentiment_results(self, merged: Dict[str, Any], ai_results: Dict[str, Any]):
        """감정 분석 결과 융합"""
        if 'ai_dominant_emotion' in ai_results:
            merged['dominant_emotion'] = ai_results['ai_dominant_emotion']
            merged['emotion_intensity'] = ai_results.get('ai_intensity', merged.get('emotion_intensity', 0.5))
            merged['emotion_confidence'] = ai_results.get('ai_confidence', merged.get('emotion_confidence', 0.5))
            
            # AI와 Rule-based 감정 분포 융합 (AI 우선)
            if 'ai_distribution' in ai_results and ai_results['ai_distribution']:
                merged['detailed_emotions'] = ai_results['ai_distribution']
            
            merged['contextual_sentiment'] = ai_results.get('ai_context', merged.get('contextual_sentiment', 'neutral'))
    
    def _merge_quality_results(self, merged: Dict[str, Any], ai_results: Dict[str, Any]):
        """품질 분석 결과 융합"""
        if 'ai_overall_quality' in ai_results:
            rule_quality = merged.get('quality_score', 50.0)
            ai_quality = ai_results['ai_overall_quality']
            
            # AI와 Rule-based 품질 점수 융합 (가중 평균: AI 60%, Rule-based 40%)
            merged['quality_score'] = ai_quality * 0.6 + rule_quality * 0.4
            
            # AI 품질 차원 결과 우선 사용
            if 'ai_quality_dimensions' in ai_results and ai_results['ai_quality_dimensions']:
                merged['quality_dimensions'] = ai_results['ai_quality_dimensions']
            
            # AI 개선 제안 추가
            if 'ai_improvement_suggestions' in ai_results:
                existing_suggestions = merged.get('improvement_suggestions', [])
                ai_suggestions = ai_results['ai_improvement_suggestions']
                
                # 중복 제거하며 병합 (최대 5개)
                all_suggestions = existing_suggestions + ai_suggestions
                merged['improvement_suggestions'] = list(dict.fromkeys(all_suggestions))[:5]
            
            # AI 품질 요약 사용
            if 'ai_quality_summary' in ai_results:
                merged['quality_report'] = ai_results['ai_quality_summary']
            
            # 언어 품질 결과 융합
            if 'ai_language_quality' in ai_results and ai_results['ai_language_quality']:
                merged['language_quality'] = ai_results['ai_language_quality']
    
    def _calculate_comprehensive_score(self, sentiment_result: Dict[str, Any], quality_result: Dict[str, Any]) -> float:
        """포괄적 분석 점수 계산"""
        try:
            sentiment_score = 50.0
            quality_score = 50.0
            
            if isinstance(sentiment_result, dict):
                # 감정 강도와 신뢰도를 종합하여 점수 계산
                intensity = sentiment_result.get('ai_intensity', 0.5)
                confidence = sentiment_result.get('ai_confidence', 0.5)
                sentiment_score = (intensity * confidence) * 100
            
            if isinstance(quality_result, dict):
                quality_score = quality_result.get('ai_overall_quality', 50.0)
            
            # 감정 점수 30%, 품질 점수 70% 가중 평균
            comprehensive_score = sentiment_score * 0.3 + quality_score * 0.7
            return round(comprehensive_score, 1)
            
        except Exception as e:
            logger.error(f"포괄적 점수 계산 오류: {e}")
            return 50.0
    
    def _get_default_sentiment_result(self) -> Dict[str, Any]:
        """기본 감정 분석 결과"""
        return {
            'ai_dominant_emotion': 'neutral',
            'ai_intensity': 0.5,
            'ai_confidence': 0.3,
            'ai_distribution': {
                'joy': 0.125, 'anger': 0.125, 'sadness': 0.125, 'fear': 0.125,
                'surprise': 0.125, 'disgust': 0.125, 'trust': 0.125, 'anticipation': 0.125
            },
            'ai_context': 'neutral',
            'ai_sentiment_summary': 'AI 분석을 수행할 수 없어 기본값을 사용했습니다.'
        }
    
    def _get_default_quality_result(self) -> Dict[str, Any]:
        """기본 품질 분석 결과"""
        return {
            'ai_overall_quality': 50.0,
            'ai_quality_grade': 'C',
            'ai_quality_dimensions': {
                'reliability': 50.0, 'usefulness': 50.0, 'accuracy': 50.0,
                'completeness': 50.0, 'readability': 50.0, 'originality': 50.0
            },
            'ai_language_quality': {
                'grammar_score': 50.0, 'vocabulary_diversity': 50.0, 'sentence_variety': 50.0
            },
            'ai_improvement_suggestions': ['AI 분석을 수행할 수 없어 구체적인 제안을 제공할 수 없습니다.'],
            'ai_quality_summary': 'AI 분석을 수행할 수 없어 기본값을 사용했습니다.'
        }
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 결과 가져오기"""
        try:
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_expiry:
                    return cached_data
                else:
                    del self.cache[cache_key]
            return None
        except Exception:
            return None
    
    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]):
        """캐시에 결과 저장"""
        try:
            self.cache[cache_key] = (result, time.time())
            
            # 캐시 크기 제한 (최대 100개)
            if len(self.cache) > 100:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
                
        except Exception as e:
            logger.error(f"캐시 저장 오류: {e}")
    
    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        return {
            'cache_size': len(self.cache),
            'cache_hit_potential': len([k for k, (_, t) in self.cache.items() if time.time() - t < self.cache_expiry]),
            'expired_entries': len([k for k, (_, t) in self.cache.items() if time.time() - t >= self.cache_expiry])
        } 