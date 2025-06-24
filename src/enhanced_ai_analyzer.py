"""
향상된 AI 콘텐츠 분석기
기존 IntelligentContentAnalyzer와 통합하여 AI 기반 분석 제공
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# 현재 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from ai_integration_engine import AIIntegrationEngine

logger = logging.getLogger(__name__)

class EnhancedAIAnalyzer:
    """향상된 AI 분석기 - 기존 시스템과 통합"""
    
    def __init__(self, content_analyzer, ai_handler):
        """초기화"""
        self.content_analyzer = content_analyzer
        self.ai_handler = ai_handler
        self.ai_engine = AIIntegrationEngine(ai_handler)
        
        # 성능 통계
        self.stats = {
            'total_ai_analyses': 0,
            'successful_ai_analyses': 0,
            'failed_ai_analyses': 0,
            'cache_hits': 0,
            'avg_response_time': 0.0
        }
    
    async def analyze_with_ai_enhancement(self, url: str, use_ai: bool = True) -> Optional[Dict[str, Any]]:
        """AI 향상 분석 수행"""
        try:
            start_time = datetime.now()
            
            # 1. 기본 Rule-based 분석 수행
            basic_result = await self.content_analyzer.analyze_web_content(url, use_ai=False)
            
            if not basic_result:
                return None
            
            # 2. AI 향상 분석 수행 (선택적)
            if use_ai and self.ai_handler:
                ai_results = await self._perform_ai_enhancement(basic_result)
                
                # 3. Rule-based와 AI 결과 융합
                enhanced_result = self.ai_engine.merge_rule_based_and_ai_results(
                    basic_result.__dict__, ai_results
                )
                
                # 4. 결과를 ContentAnalysisResult 객체로 변환
                enhanced_result = self._dict_to_analysis_result(enhanced_result)
                
                # 통계 업데이트
                self.stats['successful_ai_analyses'] += 1
                
            else:
                enhanced_result = basic_result
            
            # 성능 통계 업데이트
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_stats(processing_time)
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"AI 향상 분석 오류: {e}")
            self.stats['failed_ai_analyses'] += 1
            return basic_result if 'basic_result' in locals() else None
    
    async def _perform_ai_enhancement(self, basic_result) -> Dict[str, Any]:
        """AI 향상 분석 수행"""
        try:
            self.stats['total_ai_analyses'] += 1
            
            # AI 포괄적 분석 수행
            ai_results = await self.ai_engine.perform_comprehensive_ai_analysis(
                title=basic_result.title,
                content=basic_result.summary + " " + " ".join(basic_result.key_points),
                url=basic_result.url,
                content_type=basic_result.content_type
            )
            
            return ai_results
            
        except Exception as e:
            logger.error(f"AI 향상 분석 내부 오류: {e}")
            return {}
    
    def _dict_to_analysis_result(self, result_dict: Dict[str, Any]):
        """딕셔너리를 ContentAnalysisResult 객체로 변환"""
        try:
            from intelligent_content_analyzer import ContentAnalysisResult
            
            # 기본 필드들
            basic_fields = {
                'url': result_dict.get('url', ''),
                'title': result_dict.get('title', ''),
                'content_type': result_dict.get('content_type', 'unknown'),
                'summary': result_dict.get('summary', ''),
                'key_points': result_dict.get('key_points', []),
                'sentiment_score': result_dict.get('sentiment_score', 0.0),
                'sentiment_label': result_dict.get('sentiment_label', 'neutral'),
                'quality_score': result_dict.get('quality_score', 0.0),
                'topics': result_dict.get('topics', []),
                'language': result_dict.get('language', 'unknown'),
                'reading_time': result_dict.get('reading_time', 0),
                'complexity_level': result_dict.get('complexity_level', 'unknown'),
                'analysis_timestamp': result_dict.get('analysis_timestamp', datetime.now().isoformat()),
                'ai_model_used': result_dict.get('ai_model_used', 'unknown'),
                'word_count': result_dict.get('word_count', 0),
                'image_count': result_dict.get('image_count', 0),
                'link_count': result_dict.get('link_count', 0),
                'error_message': result_dict.get('error_message', ''),
                
                # 고급 감정 분석 필드
                'detailed_emotions': result_dict.get('detailed_emotions', {}),
                'emotion_intensity': result_dict.get('emotion_intensity', 0.0),
                'emotion_confidence': result_dict.get('emotion_confidence', 0.0),
                'dominant_emotion': result_dict.get('dominant_emotion', ''),
                'emotion_distribution': result_dict.get('emotion_distribution', {}),
                'contextual_sentiment': result_dict.get('contextual_sentiment', ''),
                
                # 고급 품질 평가 필드
                'quality_dimensions': result_dict.get('quality_dimensions', {}),
                'quality_report': result_dict.get('quality_report', ''),
                'improvement_suggestions': result_dict.get('improvement_suggestions', []),
                'content_reliability': result_dict.get('content_reliability', 0.0),
                'content_usefulness': result_dict.get('content_usefulness', 0.0),
                'content_accuracy': result_dict.get('content_accuracy', 0.0)
            }
            
            return ContentAnalysisResult(**basic_fields)
            
        except Exception as e:
            logger.error(f"객체 변환 오류: {e}")
            return result_dict
    
    def _update_performance_stats(self, processing_time: float):
        """성능 통계 업데이트"""
        try:
            total_analyses = self.stats['successful_ai_analyses'] + self.stats['failed_ai_analyses']
            if total_analyses > 0:
                # 이동 평균으로 평균 응답 시간 계산
                current_avg = self.stats['avg_response_time']
                self.stats['avg_response_time'] = (
                    (current_avg * (total_analyses - 1) + processing_time) / total_analyses
                )
        except Exception as e:
            logger.error(f"성능 통계 업데이트 오류: {e}")
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """AI 분석 통계 반환"""
        try:
            cache_stats = self.ai_engine.get_cache_stats()
            
            return {
                'analysis_stats': self.stats.copy(),
                'cache_stats': cache_stats,
                'ai_engine_status': 'active' if self.ai_engine else 'inactive',
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"AI 통계 조회 오류: {e}")
            return {'error': str(e)}
    
    def clear_ai_cache(self):
        """AI 캐시 초기화"""
        try:
            self.ai_engine.clear_cache()
            logger.info("AI 캐시가 초기화되었습니다.")
        except Exception as e:
            logger.error(f"AI 캐시 초기화 오류: {e}")
    
    def reset_stats(self):
        """통계 초기화"""
        self.stats = {
            'total_ai_analyses': 0,
            'successful_ai_analyses': 0,
            'failed_ai_analyses': 0,
            'cache_hits': 0,
            'avg_response_time': 0.0
        } 