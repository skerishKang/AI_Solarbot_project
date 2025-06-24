"""
AI 통합 분석 전용 텔레그램 명령어 모듈
향상된 AI 기반 콘텐츠 분석 명령어 제공
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from .enhanced_ai_analyzer import EnhancedAIAnalyzer

logger = logging.getLogger(__name__)

class AIIntegrationCommands:
    """AI 통합 분석 명령어 클래스"""
    
    def __init__(self, content_analyzer, ai_handler):
        """초기화"""
        self.content_analyzer = content_analyzer
        self.ai_handler = ai_handler
        self.ai_analyzer = EnhancedAIAnalyzer(content_analyzer, ai_handler)
    
    async def ai_analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /ai_analyze - AI 향상 콘텐츠 분석
        사용법: /ai_analyze <URL>
        """
        try:
            user_id = update.effective_user.id
            message_text = update.message.text.strip()
            
            # URL 추출
            parts = message_text.split(maxsplit=1)
            if len(parts) < 2:
                await update.message.reply_text(
                    "❌ **사용법 오류**\\n\\n"
                    "`/ai_analyze <URL>`\\n\\n"
                    "**예시:**\\n"
                    "`/ai_analyze https://example.com/article`\\n\\n"
                    "🤖 **AI 향상 분석 특징:**\\n"
                    "• Rule\\-based \\+ AI 융합 분석\\n"
                    "• 고급 감정 분석 \\(8개 세분화된 감정\\)\\n"
                    "• 6차원 품질 평가\\n"
                    "• 개선 제안사항 제공\\n"
                    "• 맥락적 감정 분석",
                    parse_mode='MarkdownV2'
                )
                return
            
            url = parts[1].strip()
            
            # 진행 상황 메시지
            progress_msg = await update.message.reply_text(
                "🤖 **AI 향상 분석 시작**\\n\\n"
                f"📋 URL: `{self._escape_markdown(url)}`\\n"
                "⚡ Rule\\-based 분석 중\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            # AI 향상 분석 수행
            result = await self.ai_analyzer.analyze_with_ai_enhancement(url, use_ai=True)
            
            if not result:
                await progress_msg.edit_text(
                    "❌ **분석 실패**\\n\\n"
                    f"URL: `{self._escape_markdown(url)}`\\n"
                    "분석을 수행할 수 없습니다\\. URL을 확인해주세요\\.",
                    parse_mode='MarkdownV2'
                )
                return
            
            # 분석 결과 포맷팅
            response = self._format_ai_analysis_result(result)
            
            await progress_msg.edit_text(response, parse_mode='MarkdownV2')
            
        except Exception as e:
            logger.error(f"AI 분석 명령어 오류: {e}")
            await update.message.reply_text(
                f"❌ **오류 발생**\\n\\n"
                f"오류 내용: `{self._escape_markdown(str(e))}`",
                parse_mode='MarkdownV2'
            )
    
    async def ai_compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /ai_compare - Rule-based vs AI 분석 비교
        사용법: /ai_compare <URL>
        """
        try:
            user_id = update.effective_user.id
            message_text = update.message.text.strip()
            
            # URL 추출
            parts = message_text.split(maxsplit=1)
            if len(parts) < 2:
                await update.message.reply_text(
                    "❌ **사용법 오류**\\n\\n"
                    "`/ai_compare <URL>`\\n\\n"
                    "**예시:**\\n"
                    "`/ai_compare https://example.com/article`\\n\\n"
                    "📊 **비교 분석 내용:**\\n"
                    "• Rule\\-based vs AI 분석 성능\\n"
                    "• 처리 시간 비교\\n"
                    "• 품질 점수 차이\\n"
                    "• AI 향상 효과 측정",
                    parse_mode='MarkdownV2'
                )
                return
            
            url = parts[1].strip()
            
            # 진행 상황 메시지
            progress_msg = await update.message.reply_text(
                "📊 **분석 방법 비교 시작**\\n\\n"
                f"📋 URL: `{self._escape_markdown(url)}`\\n"
                "🔄 Rule\\-based 분석 중\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            # 비교 분석 수행
            comparison = await self.ai_analyzer.compare_analysis_methods(url)
            
            if 'error' in comparison:
                await progress_msg.edit_text(
                    "❌ **비교 분석 실패**\\n\\n"
                    f"URL: `{self._escape_markdown(url)}`\\n"
                    f"오류: `{self._escape_markdown(comparison['error'])}`",
                    parse_mode='MarkdownV2'
                )
                return
            
            # 업데이트: AI 분석 진행 중
            await progress_msg.edit_text(
                "📊 **분석 방법 비교 진행**\\n\\n"
                f"📋 URL: `{self._escape_markdown(url)}`\\n"
                "✅ Rule\\-based 완료\\n"
                "🤖 AI 향상 분석 중\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            # 비교 결과 포맷팅
            response = self._format_comparison_result(comparison)
            
            await progress_msg.edit_text(response, parse_mode='MarkdownV2')
            
        except Exception as e:
            logger.error(f"AI 비교 명령어 오류: {e}")
            await update.message.reply_text(
                f"❌ **오류 발생**\\n\\n"
                f"오류 내용: `{self._escape_markdown(str(e))}`",
                parse_mode='MarkdownV2'
            )
    
    async def ai_batch_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /ai_batch - AI 향상 일괄 분석
        사용법: /ai_batch <URL1> <URL2> <URL3> (최대 3개)
        """
        try:
            user_id = update.effective_user.id
            message_text = update.message.text.strip()
            
            # URL들 추출
            parts = message_text.split()[1:]  # 첫 번째는 명령어이므로 제외
            
            if len(parts) == 0:
                await update.message.reply_text(
                    "❌ **사용법 오류**\\n\\n"
                    "`/ai_batch <URL1> <URL2> <URL3>`\\n\\n"
                    "**예시:**\\n"
                    "`/ai_batch https://site1.com https://site2.com`\\n\\n"
                    "📝 **제한사항:**\\n"
                    "• 최대 3개 URL\\n"
                    "• AI 향상 분석 적용\\n"
                    "• 병렬 처리로 빠른 분석",
                    parse_mode='MarkdownV2'
                )
                return
            
            if len(parts) > 3:
                await update.message.reply_text(
                    "❌ **URL 개수 초과**\\n\\n"
                    "최대 3개의 URL만 처리할 수 있습니다\\.",
                    parse_mode='MarkdownV2'
                )
                return
            
            urls = [url.strip() for url in parts]
            
            # 진행 상황 메시지
            progress_msg = await update.message.reply_text(
                f"🔄 **AI 일괄 분석 시작**\\n\\n"
                f"📊 총 {len(urls)}개 URL 분석\\n"
                "⚡ 병렬 처리 중\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            # AI 일괄 분석 수행
            batch_result = await self.ai_analyzer.batch_analyze_with_ai(urls, max_concurrent=3)
            
            if 'error' in batch_result:
                await progress_msg.edit_text(
                    "❌ **일괄 분석 실패**\\n\\n"
                    f"오류: `{self._escape_markdown(batch_result['error'])}`",
                    parse_mode='MarkdownV2'
                )
                return
            
            # 일괄 분석 결과 포맷팅
            response = self._format_batch_result(batch_result, urls)
            
            await progress_msg.edit_text(response, parse_mode='MarkdownV2')
            
        except Exception as e:
            logger.error(f"AI 일괄 분석 명령어 오류: {e}")
            await update.message.reply_text(
                f"❌ **오류 발생**\\n\\n"
                f"오류 내용: `{self._escape_markdown(str(e))}`",
                parse_mode='MarkdownV2'
            )
    
    async def ai_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /ai_stats - AI 분석 통계 조회
        """
        try:
            # AI 분석 통계 조회
            stats = self.ai_analyzer.get_ai_stats()
            
            if 'error' in stats:
                await update.message.reply_text(
                    f"❌ **통계 조회 실패**\\n\\n"
                    f"오류: `{self._escape_markdown(stats['error'])}`",
                    parse_mode='MarkdownV2'
                )
                return
            
            # 통계 포맷팅
            response = self._format_stats_result(stats)
            
            await update.message.reply_text(response, parse_mode='MarkdownV2')
            
        except Exception as e:
            logger.error(f"AI 통계 명령어 오류: {e}")
            await update.message.reply_text(
                f"❌ **오류 발생**\\n\\n"
                f"오류 내용: `{self._escape_markdown(str(e))}`",
                parse_mode='MarkdownV2'
            )
    
    def _format_ai_analysis_result(self, result) -> str:
        """AI 분석 결과 포맷팅"""
        try:
            title = result.get('title', 'Unknown')
            content_type = result.get('content_type', 'unknown')
            quality_score = result.get('quality_score', 0)
            sentiment_score = result.get('sentiment_score', 0)
            ai_model = result.get('ai_model_used', 'unknown')
            detailed_emotions = result.get('detailed_emotions', {})
            quality_dimensions = result.get('quality_dimensions', {})
            improvement_suggestions = result.get('improvement_suggestions', [])
            
            response = f"🤖 **AI 향상 분석 결과**\\n\\n"
            
            # 기본 정보
            title_suffix = '...' if len(title) > 50 else ''
            response += f"📄 **제목:** {self._escape_markdown(title[:50])}{title_suffix}\\n"
            response += f"🏷️ **타입:** {self._escape_markdown(content_type)}\\n"
            response += f"🎯 **품질 점수:** {quality_score:.1f}/100\\n"
            response += f"💭 **감정 점수:** {sentiment_score:+.2f}\\n\\n"
            
            # AI 모델 정보
            if ai_model != 'unknown':
                response += f"🧠 **AI 모델:** {self._escape_markdown(ai_model)}\\n\\n"
            
            # 세분화된 감정 분석 (상위 3개)
            if detailed_emotions:
                sorted_emotions = sorted(detailed_emotions.items(), key=lambda x: x[1], reverse=True)[:3]
                response += "🎭 **주요 감정 분석:**\\n"
                for emotion, score in sorted_emotions:
                    emotion_emoji = self._get_emotion_emoji(emotion)
                    response += f"{emotion_emoji} {self._escape_markdown(emotion.title())}: {score:.2f}\\n"
                response += "\\n"
            
            # 품질 차원 분석 (상위 3개)
            if quality_dimensions:
                sorted_dimensions = sorted(quality_dimensions.items(), key=lambda x: x[1], reverse=True)[:3]
                response += "📊 **품질 차원 분석:**\\n"
                for dimension, score in sorted_dimensions:
                    dimension_emoji = self._get_dimension_emoji(dimension)
                    response += f"{dimension_emoji} {self._escape_markdown(dimension.title())}: {score:.1f}/100\\n"
                response += "\\n"
            
            # 개선 제안사항 (상위 2개)
            if improvement_suggestions:
                response += "💡 **AI 개선 제안:**\\n"
                for i, suggestion in enumerate(improvement_suggestions[:2], 1):
                    suggestion_suffix = '...' if len(suggestion) > 80 else ''
                    response += f"{i}\\. {self._escape_markdown(suggestion[:80])}{suggestion_suffix}\\n"
                response += "\\n"
            
            response += f"⏰ **분석 시간:** {datetime.now().strftime('%H:%M:%S')}"
            
            return response
            
        except Exception as e:
            logger.error(f"AI 분석 결과 포맷팅 오류: {e}")
            return f"❌ **결과 포맷팅 오류**\\n\\n오류: `{self._escape_markdown(str(e))}`"
    
    def _format_comparison_result(self, comparison: Dict[str, Any]) -> str:
        """비교 분석 결과 포맷팅"""
        try:
            rule_based = comparison.get('rule_based', {})
            ai_enhanced = comparison.get('ai_enhanced', {})
            improvements = comparison.get('improvements', {})
            
            response = f"📊 **분석 방법 비교 결과**\\n\\n"
            
            # URL 정보
            url = comparison.get('url', 'Unknown')
            url_suffix = '...' if len(url) > 50 else ''
            response += f"📋 **URL:** `{self._escape_markdown(url[:50])}{url_suffix}`\\n\\n"
            
            # 성능 비교
            response += "⚡ **성능 비교:**\\n"
            rule_time = rule_based.get('processing_time', 0)
            ai_time = ai_enhanced.get('processing_time', 0)
            response += f"🔧 Rule\\-based: {rule_time:.2f}초\\n"
            response += f"🤖 AI 향상: {ai_time:.2f}초\\n\\n"
            
            # 품질 점수 비교
            response += "🎯 **품질 점수 비교:**\\n"
            rule_quality = rule_based.get('quality_score', 0)
            ai_quality = ai_enhanced.get('quality_score', 0)
            quality_diff = improvements.get('quality_score_diff', 0)
            
            response += f"🔧 Rule\\-based: {rule_quality:.1f}/100\\n"
            response += f"🤖 AI 향상: {ai_quality:.1f}/100\\n"
            
            if quality_diff > 0:
                response += f"📈 **개선:** \\+{quality_diff:.1f}점\\n\\n"
            elif quality_diff < 0:
                response += f"📉 **차이:** {quality_diff:.1f}점\\n\\n"
            else:
                response += f"➡️ **동일:** 차이 없음\\n\\n"
            
            # AI 향상 특징
            response += "🚀 **AI 향상 특징:**\\n"
            if improvements.get('additional_emotions'):
                response += "✅ 세분화된 감정 분석\\n"
            if improvements.get('quality_dimensions'):
                response += "✅ 6차원 품질 평가\\n"
            if improvements.get('improvement_suggestions'):
                response += "✅ 개선 제안사항\\n"
            if improvements.get('contextual_sentiment'):
                response += "✅ 맥락적 감정 분석\\n"
            
            improvement_level = improvements.get('improvement_level', 'low')
            level_emoji = '🔥' if improvement_level == 'high' else '⚡' if improvement_level == 'medium' else '💡'
            response += f"\\n{level_emoji} **향상 수준:** {self._escape_markdown(improvement_level.upper())}\\n"
            
            response += f"\\n⏰ **분석 시간:** {datetime.now().strftime('%H:%M:%S')}"
            
            return response
            
        except Exception as e:
            logger.error(f"비교 결과 포맷팅 오류: {e}")
            return f"❌ **결과 포맷팅 오류**\\n\\n오류: `{self._escape_markdown(str(e))}`"
    
    def _format_batch_result(self, batch_result: Dict[str, Any], urls: List[str]) -> str:
        """일괄 분석 결과 포맷팅"""
        try:
            total = batch_result.get('total_analyzed', 0)
            success = batch_result.get('success_count', 0)
            failed = batch_result.get('failed_count', 0)
            processing_time = batch_result.get('processing_time', 0)
            
            response = f"🔄 **AI 일괄 분석 완료**\\n\\n"
            
            # 기본 통계
            response += f"📊 **분석 통계:**\\n"
            response += f"📝 총 분석: {total}개\\n"
            response += f"✅ 성공: {success}개\\n"
            response += f"❌ 실패: {failed}개\\n"
            response += f"⏱️ 처리 시간: {processing_time:.2f}초\\n\\n"
            
            # 품질 통계
            avg_quality = batch_result.get('average_quality_score', 0)
            avg_sentiment = batch_result.get('average_sentiment_score', 0)
            
            response += f"🎯 **품질 통계:**\\n"
            response += f"📈 평균 품질: {avg_quality:.1f}/100\\n"
            response += f"💭 평균 감정: {avg_sentiment:+.2f}\\n\\n"
            
            # AI 향상 통계
            ai_stats = batch_result.get('ai_enhancement_stats', {})
            if ai_stats:
                ai_rate = ai_stats.get('ai_enhancement_rate', 0)
                emotions_count = ai_stats.get('detailed_emotions_count', 0)
                dimensions_count = ai_stats.get('quality_dimensions_count', 0)
                
                response += f"🤖 **AI 향상 통계:**\\n"
                response += f"🧠 AI 적용률: {ai_rate:.1f}%\\n"
                response += f"🎭 감정 분석: {emotions_count}개\\n"
                response += f"📊 품질 차원: {dimensions_count}개\\n\\n"
            
            # 성능 통계
            perf_stats = batch_result.get('performance_stats', {})
            if perf_stats:
                avg_time = perf_stats.get('avg_time_per_analysis', 0)
                analyses_per_sec = perf_stats.get('analyses_per_second', 0)
                
                response += f"⚡ **성능 통계:**\\n"
                response += f"⏱️ 평균 분석 시간: {avg_time:.2f}초\\n"
                response += f"🚀 초당 분석: {analyses_per_sec:.2f}개\\n\\n"
            
            # URL 목록 (최대 3개)
            response += f"📋 **분석된 URL:**\\n"
            for i, url in enumerate(urls[:3], 1):
                status = "✅" if i <= success else "❌"
                url_display = url[:40]
                url_suffix = '...' if len(url) > 40 else ''
                response += f"{status} {i}\\. `{self._escape_markdown(url_display)}{url_suffix}`\\n"
            
            response += f"\\n⏰ **완료 시간:** {datetime.now().strftime('%H:%M:%S')}"
            
            return response
            
        except Exception as e:
            logger.error(f"일괄 결과 포맷팅 오류: {e}")
            return f"❌ **결과 포맷팅 오류**\\n\\n오류: `{self._escape_markdown(str(e))}`"
    
    def _format_stats_result(self, stats: Dict[str, Any]) -> str:
        """통계 결과 포맷팅"""
        try:
            analysis_stats = stats.get('analysis_stats', {})
            cache_stats = stats.get('cache_stats', {})
            
            response = f"📈 **AI 분석 통계**\\n\\n"
            
            # 분석 통계
            total_analyses = analysis_stats.get('total_ai_analyses', 0)
            successful = analysis_stats.get('successful_ai_analyses', 0)
            failed = analysis_stats.get('failed_ai_analyses', 0)
            avg_response_time = analysis_stats.get('avg_response_time', 0)
            
            response += f"🔬 **분석 통계:**\\n"
            response += f"📊 총 분석: {total_analyses}회\\n"
            response += f"✅ 성공: {successful}회\\n"
            response += f"❌ 실패: {failed}회\\n"
            
            if total_analyses > 0:
                success_rate = (successful / total_analyses) * 100
                response += f"📈 성공률: {success_rate:.1f}%\\n"
            
            response += f"⏱️ 평균 응답 시간: {avg_response_time:.2f}초\\n\\n"
            
            # 캐시 통계
            cache_size = cache_stats.get('cache_size', 0)
            cache_hits = cache_stats.get('cache_hit_potential', 0)
            expired_entries = cache_stats.get('expired_entries', 0)
            
            response += f"💾 **캐시 통계:**\\n"
            response += f"📦 캐시 크기: {cache_size}개\\n"
            response += f"🎯 유효 항목: {cache_hits}개\\n"
            response += f"⏰ 만료 항목: {expired_entries}개\\n\\n"
            
            # 시스템 상태
            engine_status = stats.get('ai_engine_status', 'unknown')
            status_emoji = "🟢" if engine_status == 'active' else "🔴"
            
            response += f"🔧 **시스템 상태:**\\n"
            response += f"{status_emoji} AI 엔진: {self._escape_markdown(engine_status.upper())}\\n"
            
            last_updated = stats.get('last_updated', 'Unknown')
            response += f"🕐 마지막 업데이트: {self._escape_markdown(last_updated.split('T')[1][:8])}"
            
            return response
            
        except Exception as e:
            logger.error(f"통계 포맷팅 오류: {e}")
            return f"❌ **통계 포맷팅 오류**\\n\\n오류: `{self._escape_markdown(str(e))}`"
    
    def _get_emotion_emoji(self, emotion: str) -> str:
        """감정에 따른 이모지 반환"""
        emotion_emojis = {
            'joy': '😊', 'anger': '😠', 'sadness': '😢', 'fear': '😨',
            'surprise': '😲', 'disgust': '🤢', 'trust': '🤝', 'anticipation': '🤔'
        }
        return emotion_emojis.get(emotion.lower(), '😐')
    
    def _get_dimension_emoji(self, dimension: str) -> str:
        """품질 차원에 따른 이모지 반환"""
        dimension_emojis = {
            'reliability': '🔒', 'usefulness': '💡', 'accuracy': '🎯',
            'completeness': '📝', 'readability': '📖', 'originality': '✨'
        }
        return dimension_emojis.get(dimension.lower(), '📊')
    
    def _escape_markdown(self, text: str) -> str:
        """MarkdownV2 특수 문자 이스케이프"""
        if not text:
            return ""
        
        # MarkdownV2에서 이스케이프해야 할 문자들
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        escaped_text = str(text)
        for char in escape_chars:
            escaped_text = escaped_text.replace(char, f'\\{char}')
        
        return escaped_text 