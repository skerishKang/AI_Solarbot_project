"""
AI 통합 명령어 모듈

AI 기반 감정 분석과 품질 평가를 위한 텔레그램 명령어들을 제공합니다.
기존 rule-based 분석과 AI 분석을 융합하여 더 정교한 결과를 제공합니다.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.enhanced_ai_analyzer import EnhancedAIAnalyzer
from core.ai_integration_engine import AIIntegrationEngine
from utils.url_validator import URLValidator
from utils.content_extractor import ContentExtractor
from config.settings import OFFLINE_MODE

logger = logging.getLogger(__name__)

class AIIntegrationCommands:
    """AI 통합 명령어 클래스"""
    
    def __init__(self, ai_handler=None):
        """
        AI 통합 명령어 초기화
        
        Args:
            ai_handler: AI 핸들러 인스턴스
        """
        self.ai_handler = ai_handler
        self.enhanced_analyzer = EnhancedAIAnalyzer(ai_handler) if not OFFLINE_MODE else None
        self.ai_engine = AIIntegrationEngine(ai_handler) if not OFFLINE_MODE else None
        self.url_validator = URLValidator()
        self.content_extractor = ContentExtractor()
        
        # 명령어 설명
        self.commands_info = {
            'ai_sentiment': {
                'description': '🤖 AI 기반 고급 감정 분석',
                'usage': '/ai_sentiment <URL>',
                'example': '/ai_sentiment https://example.com/article'
            },
            'ai_quality': {
                'description': '🎯 AI 기반 고급 품질 평가',
                'usage': '/ai_quality <URL>',
                'example': '/ai_quality https://example.com/content'
            },
            'ai_comprehensive': {
                'description': '🔍 AI 기반 종합 분석 (감정+품질)',
                'usage': '/ai_comprehensive <URL>',
                'example': '/ai_comprehensive https://example.com/page'
            },
            'ai_compare': {
                'description': '⚖️ AI 기반 콘텐츠 비교 분석',
                'usage': '/ai_compare <URL1> <URL2>',
                'example': '/ai_compare https://site1.com https://site2.com'
            }
        }
    
    async def ai_sentiment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        AI 기반 고급 감정 분석 명령어
        
        Args:
            update: 텔레그램 업데이트 객체
            context: 명령어 컨텍스트
        """
        try:
            if OFFLINE_MODE:
                await update.message.reply_text(
                    "❌ AI 기반 분석은 OFFLINE_MODE에서 사용할 수 없습니다.\n"
                    "기본 감정 분석은 /sentiment_only 명령어를 사용해주세요."
                )
                return
            
            # URL 추출 및 검증
            if not context.args:
                await self._send_usage_info(update, 'ai_sentiment')
                return
            
            url = context.args[0]
            if not self.url_validator.is_valid_url(url):
                await update.message.reply_text("❌ 올바른 URL을 입력해주세요.")
                return
            
            # 진행 상황 메시지
            progress_msg = await update.message.reply_text(
                "🤖 AI 기반 감정 분석을 시작합니다...\n"
                "⏳ 콘텐츠를 추출하고 있습니다..."
            )
            
            # 콘텐츠 추출
            content_data = await self._extract_content_safely(url)
            if not content_data:
                await progress_msg.edit_text("❌ 콘텐츠 추출에 실패했습니다.")
                return
            
            await progress_msg.edit_text(
                "🤖 AI 기반 감정 분석을 시작합니다...\n"
                "🧠 AI가 감정을 분석하고 있습니다..."
            )
            
            # AI 기반 감정 분석 수행
            ai_result = await self.ai_engine.perform_ai_sentiment_analysis(
                content_data['content'],
                content_data.get('metadata', {})
            )
            
            # 결과 포맷팅
            result_text = self._format_ai_sentiment_result(ai_result, url, content_data)
            
            await progress_msg.edit_text(result_text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"AI 감정 분석 명령어 오류: {str(e)}")
            await update.message.reply_text(
                f"❌ AI 감정 분석 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def ai_quality_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        AI 기반 고급 품질 평가 명령어
        
        Args:
            update: 텔레그램 업데이트 객체
            context: 명령어 컨텍스트
        """
        try:
            if OFFLINE_MODE:
                await update.message.reply_text(
                    "❌ AI 기반 분석은 OFFLINE_MODE에서 사용할 수 없습니다.\n"
                    "기본 품질 평가는 /quality_only 명령어를 사용해주세요."
                )
                return
            
            # URL 추출 및 검증
            if not context.args:
                await self._send_usage_info(update, 'ai_quality')
                return
            
            url = context.args[0]
            if not self.url_validator.is_valid_url(url):
                await update.message.reply_text("❌ 올바른 URL을 입력해주세요.")
                return
            
            # 진행 상황 메시지
            progress_msg = await update.message.reply_text(
                "🎯 AI 기반 품질 평가를 시작합니다...\n"
                "⏳ 콘텐츠를 추출하고 있습니다..."
            )
            
            # 콘텐츠 추출
            content_data = await self._extract_content_safely(url)
            if not content_data:
                await progress_msg.edit_text("❌ 콘텐츠 추출에 실패했습니다.")
                return
            
            await progress_msg.edit_text(
                "🎯 AI 기반 품질 평가를 시작합니다...\n"
                "📊 AI가 품질을 평가하고 있습니다..."
            )
            
            # AI 기반 품질 평가 수행
            ai_result = await self.ai_engine.perform_ai_quality_analysis(
                content_data['content'],
                content_data.get('metadata', {})
            )
            
            # 결과 포맷팅
            result_text = self._format_ai_quality_result(ai_result, url, content_data)
            
            await progress_msg.edit_text(result_text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"AI 품질 평가 명령어 오류: {str(e)}")
            await update.message.reply_text(
                f"❌ AI 품질 평가 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def ai_comprehensive_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        AI 기반 종합 분석 명령어 (감정+품질)
        
        Args:
            update: 텔레그램 업데이트 객체
            context: 명령어 컨텍스트
        """
        try:
            if OFFLINE_MODE:
                await update.message.reply_text(
                    "❌ AI 기반 분석은 OFFLINE_MODE에서 사용할 수 없습니다.\n"
                    "기본 분석 명령어들을 사용해주세요."
                )
                return
            
            # URL 추출 및 검증
            if not context.args:
                await self._send_usage_info(update, 'ai_comprehensive')
                return
            
            url = context.args[0]
            if not self.url_validator.is_valid_url(url):
                await update.message.reply_text("❌ 올바른 URL을 입력해주세요.")
                return
            
            # 진행 상황 메시지
            progress_msg = await update.message.reply_text(
                "🔍 AI 기반 종합 분석을 시작합니다...\n"
                "⏳ 콘텐츠를 추출하고 있습니다..."
            )
            
            # 콘텐츠 추출
            content_data = await self._extract_content_safely(url)
            if not content_data:
                await progress_msg.edit_text("❌ 콘텐츠 추출에 실패했습니다.")
                return
            
            await progress_msg.edit_text(
                "🔍 AI 기반 종합 분석을 시작합니다...\n"
                "🧠 AI가 종합 분석을 수행하고 있습니다..."
            )
            
            # AI 기반 종합 분석 수행
            comprehensive_result = await self.ai_engine.perform_comprehensive_ai_analysis(
                content_data['content'],
                content_data.get('metadata', {})
            )
            
            # 결과 포맷팅
            result_text = self._format_comprehensive_result(comprehensive_result, url, content_data)
            
            await progress_msg.edit_text(result_text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"AI 종합 분석 명령어 오류: {str(e)}")
            await update.message.reply_text(
                f"❌ AI 종합 분석 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def ai_compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        AI 기반 콘텐츠 비교 분석 명령어
        
        Args:
            update: 텔레그램 업데이트 객체
            context: 명령어 컨텍스트
        """
        try:
            if OFFLINE_MODE:
                await update.message.reply_text(
                    "❌ AI 기반 분석은 OFFLINE_MODE에서 사용할 수 없습니다."
                )
                return
            
            # URL 추출 및 검증
            if len(context.args) < 2:
                await self._send_usage_info(update, 'ai_compare')
                return
            
            url1, url2 = context.args[0], context.args[1]
            
            if not self.url_validator.is_valid_url(url1) or not self.url_validator.is_valid_url(url2):
                await update.message.reply_text("❌ 두 개의 올바른 URL을 입력해주세요.")
                return
            
            # 진행 상황 메시지
            progress_msg = await update.message.reply_text(
                "⚖️ AI 기반 콘텐츠 비교 분석을 시작합니다...\n"
                "⏳ 첫 번째 콘텐츠를 추출하고 있습니다..."
            )
            
            # 첫 번째 콘텐츠 추출
            content1 = await self._extract_content_safely(url1)
            if not content1:
                await progress_msg.edit_text("❌ 첫 번째 콘텐츠 추출에 실패했습니다.")
                return
            
            await progress_msg.edit_text(
                "⚖️ AI 기반 콘텐츠 비교 분석을 시작합니다...\n"
                "⏳ 두 번째 콘텐츠를 추출하고 있습니다..."
            )
            
            # 두 번째 콘텐츠 추출
            content2 = await self._extract_content_safely(url2)
            if not content2:
                await progress_msg.edit_text("❌ 두 번째 콘텐츠 추출에 실패했습니다.")
                return
            
            await progress_msg.edit_text(
                "⚖️ AI 기반 콘텐츠 비교 분석을 시작합니다...\n"
                "🧠 AI가 비교 분석을 수행하고 있습니다..."
            )
            
            # 각 콘텐츠에 대한 AI 분석 수행
            analysis1 = await self.ai_engine.perform_comprehensive_ai_analysis(
                content1['content'], content1.get('metadata', {})
            )
            analysis2 = await self.ai_engine.perform_comprehensive_ai_analysis(
                content2['content'], content2.get('metadata', {})
            )
            
            # 비교 결과 포맷팅
            result_text = self._format_comparison_result(
                analysis1, analysis2, url1, url2, content1, content2
            )
            
            await progress_msg.edit_text(result_text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"AI 비교 분석 명령어 오류: {str(e)}")
            await update.message.reply_text(
                f"❌ AI 비교 분석 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def _extract_content_safely(self, url: str) -> Optional[Dict[str, Any]]:
        """안전한 콘텐츠 추출"""
        try:
            content_data = await asyncio.to_thread(
                self.content_extractor.extract_content, url
            )
            
            if not content_data or not content_data.get('content'):
                return None
                
            return content_data
            
        except Exception as e:
            logger.error(f"콘텐츠 추출 오류 ({url}): {str(e)}")
            return None
    
    def _format_ai_sentiment_result(self, ai_result: Dict[str, Any], url: str, content_data: Dict[str, Any]) -> str:
        """AI 감정 분석 결과 포맷팅"""
        sentiment = ai_result.get('sentiment', {})
        emotions = ai_result.get('emotions', {})
        insights = ai_result.get('insights', [])
        
        # 감정 이모지 매핑
        emotion_emojis = {
            'joy': '😊', 'sadness': '😢', 'anger': '😠', 'fear': '😨',
            'surprise': '😲', 'disgust': '🤢', 'trust': '🤗', 'anticipation': '🤔'
        }
        
        result = f"🤖 <b>AI 기반 고급 감정 분석 결과</b>\n\n"
        result += f"📄 <b>URL:</b> {url}\n"
        result += f"📝 <b>제목:</b> {content_data.get('metadata', {}).get('title', 'N/A')}\n\n"
        
        # 전체 감정 점수
        if sentiment:
            polarity = sentiment.get('polarity', 0)
            confidence = sentiment.get('confidence', 0)
            
            if polarity > 0.1:
                sentiment_emoji = "😊"
                sentiment_text = "긍정적"
            elif polarity < -0.1:
                sentiment_emoji = "😔"
                sentiment_text = "부정적"
            else:
                sentiment_emoji = "😐"
                sentiment_text = "중립적"
            
            result += f"🎯 <b>전체 감정:</b> {sentiment_emoji} {sentiment_text}\n"
            result += f"📊 <b>감정 강도:</b> {polarity:.2f} (신뢰도: {confidence:.1%})\n\n"
        
        # 세부 감정 분석
        if emotions:
            result += "🎭 <b>세부 감정 분석:</b>\n"
            sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
            
            for emotion, score in sorted_emotions[:5]:  # 상위 5개만 표시
                emoji = emotion_emojis.get(emotion, '🔸')
                result += f"  {emoji} {emotion.title()}: {score:.1%}\n"
            result += "\n"
        
        # AI 인사이트
        if insights:
            result += "💡 <b>AI 인사이트:</b>\n"
            for insight in insights[:3]:  # 상위 3개만 표시
                result += f"  • {insight}\n"
            result += "\n"
        
        # 분석 메타데이터
        result += f"⏰ <b>분석 시간:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"🔧 <b>분석 엔진:</b> AI 기반 고급 감정 분석"
        
        return result
    
    def _format_ai_quality_result(self, ai_result: Dict[str, Any], url: str, content_data: Dict[str, Any]) -> str:
        """AI 품질 평가 결과 포맷팅"""
        quality = ai_result.get('quality', {})
        dimensions = ai_result.get('dimensions', {})
        recommendations = ai_result.get('recommendations', [])
        
        result = f"🎯 <b>AI 기반 고급 품질 평가 결과</b>\n\n"
        result += f"📄 <b>URL:</b> {url}\n"
        result += f"📝 <b>제목:</b> {content_data.get('metadata', {}).get('title', 'N/A')}\n\n"
        
        # 전체 품질 점수
        if quality:
            overall_score = quality.get('overall_score', 0)
            grade = quality.get('grade', 'N/A')
            confidence = quality.get('confidence', 0)
            
            # 등급별 이모지
            grade_emojis = {
                'A+': '🏆', 'A': '🥇', 'B+': '🥈', 'B': '🥉',
                'C+': '📈', 'C': '📊', 'D+': '📉', 'D': '⚠️', 'F': '❌'
            }
            
            emoji = grade_emojis.get(grade, '📊')
            result += f"🏅 <b>전체 품질:</b> {emoji} {grade} ({overall_score:.1f}/100)\n"
            result += f"📊 <b>신뢰도:</b> {confidence:.1%}\n\n"
        
        # 품질 차원별 분석
        if dimensions:
            result += "📋 <b>품질 차원별 분석:</b>\n"
            dimension_names = {
                'credibility': '신뢰도',
                'usefulness': '유용성', 
                'accuracy': '정확성',
                'completeness': '완성도',
                'readability': '가독성',
                'originality': '독창성'
            }
            
            for dim, score in dimensions.items():
                name = dimension_names.get(dim, dim.title())
                result += f"  📌 {name}: {score:.1f}/100\n"
            result += "\n"
        
        # AI 추천사항
        if recommendations:
            result += "💡 <b>AI 개선 추천사항:</b>\n"
            for rec in recommendations[:4]:  # 상위 4개만 표시
                result += f"  • {rec}\n"
            result += "\n"
        
        # 분석 메타데이터
        result += f"⏰ <b>분석 시간:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"🔧 <b>분석 엔진:</b> AI 기반 고급 품질 평가"
        
        return result
    
    def _format_comprehensive_result(self, comprehensive_result: Dict[str, Any], url: str, content_data: Dict[str, Any]) -> str:
        """AI 종합 분석 결과 포맷팅"""
        sentiment = comprehensive_result.get('sentiment', {})
        quality = comprehensive_result.get('quality', {})
        insights = comprehensive_result.get('insights', [])
        
        result = f"🔍 <b>AI 기반 종합 분석 결과</b>\n\n"
        result += f"📄 <b>URL:</b> {url}\n"
        result += f"📝 <b>제목:</b> {content_data.get('metadata', {}).get('title', 'N/A')}\n\n"
        
        # 감정 분석 요약
        if sentiment:
            polarity = sentiment.get('polarity', 0)
            if polarity > 0.1:
                sentiment_emoji = "😊"
                sentiment_text = "긍정적"
            elif polarity < -0.1:
                sentiment_emoji = "😔" 
                sentiment_text = "부정적"
            else:
                sentiment_emoji = "😐"
                sentiment_text = "중립적"
            
            result += f"🎭 <b>감정 분석:</b> {sentiment_emoji} {sentiment_text} ({polarity:.2f})\n"
        
        # 품질 평가 요약
        if quality:
            grade = quality.get('grade', 'N/A')
            score = quality.get('overall_score', 0)
            
            grade_emojis = {
                'A+': '🏆', 'A': '🥇', 'B+': '🥈', 'B': '🥉',
                'C+': '📈', 'C': '📊', 'D+': '📉', 'D': '⚠️', 'F': '❌'
            }
            emoji = grade_emojis.get(grade, '📊')
            
            result += f"🏅 <b>품질 평가:</b> {emoji} {grade} ({score:.1f}/100)\n\n"
        
        # 종합 인사이트
        if insights:
            result += "💡 <b>종합 인사이트:</b>\n"
            for insight in insights[:5]:  # 상위 5개만 표시
                result += f"  • {insight}\n"
            result += "\n"
        
        # 분석 메타데이터
        result += f"⏰ <b>분석 시간:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"🔧 <b>분석 엔진:</b> AI 기반 종합 분석 (감정+품질)"
        
        return result
    
    def _format_comparison_result(self, analysis1: Dict[str, Any], analysis2: Dict[str, Any], 
                                url1: str, url2: str, content1: Dict[str, Any], content2: Dict[str, Any]) -> str:
        """AI 비교 분석 결과 포맷팅"""
        result = f"⚖️ <b>AI 기반 콘텐츠 비교 분석</b>\n\n"
        
        # URL 및 제목 정보
        result += f"📄 <b>콘텐츠 1:</b> {content1.get('metadata', {}).get('title', 'N/A')}\n"
        result += f"🔗 {url1}\n\n"
        result += f"📄 <b>콘텐츠 2:</b> {content2.get('metadata', {}).get('title', 'N/A')}\n"
        result += f"🔗 {url2}\n\n"
        
        # 감정 비교
        sentiment1 = analysis1.get('sentiment', {})
        sentiment2 = analysis2.get('sentiment', {})
        
        if sentiment1 and sentiment2:
            pol1 = sentiment1.get('polarity', 0)
            pol2 = sentiment2.get('polarity', 0)
            
            result += "🎭 <b>감정 비교:</b>\n"
            result += f"  📊 콘텐츠 1: {pol1:.2f} {'😊' if pol1 > 0.1 else '😔' if pol1 < -0.1 else '😐'}\n"
            result += f"  📊 콘텐츠 2: {pol2:.2f} {'😊' if pol2 > 0.1 else '😔' if pol2 < -0.1 else '😐'}\n"
            
            if abs(pol1 - pol2) > 0.2:
                winner = "콘텐츠 1" if pol1 > pol2 else "콘텐츠 2"
                result += f"  🏆 더 긍정적: {winner}\n"
            result += "\n"
        
        # 품질 비교
        quality1 = analysis1.get('quality', {})
        quality2 = analysis2.get('quality', {})
        
        if quality1 and quality2:
            score1 = quality1.get('overall_score', 0)
            score2 = quality2.get('overall_score', 0)
            grade1 = quality1.get('grade', 'N/A')
            grade2 = quality2.get('grade', 'N/A')
            
            result += "🏅 <b>품질 비교:</b>\n"
            result += f"  📊 콘텐츠 1: {grade1} ({score1:.1f}/100)\n"
            result += f"  📊 콘텐츠 2: {grade2} ({score2:.1f}/100)\n"
            
            if abs(score1 - score2) > 5:
                winner = "콘텐츠 1" if score1 > score2 else "콘텐츠 2"
                result += f"  🏆 더 높은 품질: {winner}\n"
            result += "\n"
        
        # 종합 결론
        result += "🎯 <b>종합 결론:</b>\n"
        
        # 감정과 품질을 종합한 결론
        total1 = (sentiment1.get('polarity', 0) * 50 + 50) + quality1.get('overall_score', 0)
        total2 = (sentiment2.get('polarity', 0) * 50 + 50) + quality2.get('overall_score', 0)
        
        if abs(total1 - total2) < 10:
            result += "  📊 두 콘텐츠의 전반적 품질이 비슷합니다.\n"
        else:
            winner = "콘텐츠 1" if total1 > total2 else "콘텐츠 2"
            result += f"  🏆 전반적으로 {winner}이 더 우수합니다.\n"
        
        result += f"\n⏰ <b>분석 시간:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"🔧 <b>분석 엔진:</b> AI 기반 비교 분석"
        
        return result
    
    async def ai_quality_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """AI 기반 고급 품질 평가 명령어"""
        try:
            if OFFLINE_MODE:
                await update.message.reply_text(
                    "❌ AI 기반 분석은 OFFLINE_MODE에서 사용할 수 없습니다.\n"
                    "기본 품질 평가는 /quality_only 명령어를 사용해주세요."
                )
                return
            
            if not context.args:
                await self._send_usage_info(update, 'ai_quality')
                return
            
            url = context.args[0]
            if not self.url_validator.is_valid_url(url):
                await update.message.reply_text("❌ 올바른 URL을 입력해주세요.")
                return
            
            progress_msg = await update.message.reply_text(
                "🎯 AI 기반 품질 평가를 시작합니다...\n⏳ 콘텐츠를 추출하고 있습니다..."
            )
            
            content_data = await self._extract_content_safely(url)
            if not content_data:
                await progress_msg.edit_text("❌ 콘텐츠 추출에 실패했습니다.")
                return
            
            await progress_msg.edit_text(
                "🎯 AI 기반 품질 평가를 시작합니다...\n📊 AI가 품질을 평가하고 있습니다..."
            )
            
            ai_result = await self.ai_engine.perform_ai_quality_analysis(
                content_data['content'], content_data.get('metadata', {})
            )
            
            result_text = self._format_ai_quality_result(ai_result, url, content_data)
            await progress_msg.edit_text(result_text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"AI 품질 평가 명령어 오류: {str(e)}")
            await update.message.reply_text(f"❌ AI 품질 평가 중 오류가 발생했습니다: {str(e)}")
    
    def _format_ai_quality_result(self, ai_result: Dict[str, Any], url: str, content_data: Dict[str, Any]) -> str:
        """AI 품질 평가 결과 포맷팅"""
        quality = ai_result.get('quality', {})
        dimensions = ai_result.get('dimensions', {})
        recommendations = ai_result.get('recommendations', [])
        
        result = f"🎯 <b>AI 기반 고급 품질 평가 결과</b>\n\n"
        result += f"📄 <b>URL:</b> {url}\n"
        result += f"📝 <b>제목:</b> {content_data.get('metadata', {}).get('title', 'N/A')}\n\n"
        
        if quality:
            overall_score = quality.get('overall_score', 0)
            grade = quality.get('grade', 'N/A')
            confidence = quality.get('confidence', 0)
            
            grade_emojis = {
                'A+': '🏆', 'A': '🥇', 'B+': '🥈', 'B': '🥉',
                'C+': '📈', 'C': '📊', 'D+': '📉', 'D': '⚠️', 'F': '❌'
            }
            
            emoji = grade_emojis.get(grade, '📊')
            result += f"🏅 <b>전체 품질:</b> {emoji} {grade} ({overall_score:.1f}/100)\n"
            result += f"📊 <b>신뢰도:</b> {confidence:.1%}\n\n"
        
        if dimensions:
            result += "📋 <b>품질 차원별 분석:</b>\n"
            dimension_names = {
                'credibility': '신뢰도', 'usefulness': '유용성', 'accuracy': '정확성',
                'completeness': '완성도', 'readability': '가독성', 'originality': '독창성'
            }
            
            for dim, score in dimensions.items():
                name = dimension_names.get(dim, dim.title())
                result += f"  📌 {name}: {score:.1f}/100\n"
            result += "\n"
        
        if recommendations:
            result += "💡 <b>AI 개선 추천사항:</b>\n"
            for rec in recommendations[:4]:
                result += f"  • {rec}\n"
            result += "\n"
        
        result += f"⏰ <b>분석 시간:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"🔧 <b>분석 엔진:</b> AI 기반 고급 품질 평가"
        
        return result
    
    async def ai_comprehensive_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """AI 기반 종합 분석 명령어 (감정+품질)"""
        try:
            if OFFLINE_MODE:
                await update.message.reply_text(
                    "❌ AI 기반 분석은 OFFLINE_MODE에서 사용할 수 없습니다.\n기본 분석 명령어들을 사용해주세요."
                )
                return
            
            if not context.args:
                await self._send_usage_info(update, 'ai_comprehensive')
                return
            
            url = context.args[0]
            if not self.url_validator.is_valid_url(url):
                await update.message.reply_text("❌ 올바른 URL을 입력해주세요.")
                return
            
            progress_msg = await update.message.reply_text(
                "🔍 AI 기반 종합 분석을 시작합니다...\n⏳ 콘텐츠를 추출하고 있습니다..."
            )
            
            content_data = await self._extract_content_safely(url)
            if not content_data:
                await progress_msg.edit_text("❌ 콘텐츠 추출에 실패했습니다.")
                return
            
            await progress_msg.edit_text(
                "🔍 AI 기반 종합 분석을 시작합니다...\n🧠 AI가 종합 분석을 수행하고 있습니다..."
            )
            
            comprehensive_result = await self.ai_engine.perform_comprehensive_ai_analysis(
                content_data['content'], content_data.get('metadata', {})
            )
            
            result_text = self._format_comprehensive_result(comprehensive_result, url, content_data)
            await progress_msg.edit_text(result_text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"AI 종합 분석 명령어 오류: {str(e)}")
            await update.message.reply_text(f"❌ AI 종합 분석 중 오류가 발생했습니다: {str(e)}")
    
    def _format_comprehensive_result(self, comprehensive_result: Dict[str, Any], url: str, content_data: Dict[str, Any]) -> str:
        """AI 종합 분석 결과 포맷팅"""
        sentiment = comprehensive_result.get('sentiment', {})
        quality = comprehensive_result.get('quality', {})
        insights = comprehensive_result.get('insights', [])
        
        result = f"🔍 <b>AI 기반 종합 분석 결과</b>\n\n"
        result += f"📄 <b>URL:</b> {url}\n"
        result += f"📝 <b>제목:</b> {content_data.get('metadata', {}).get('title', 'N/A')}\n\n"
        
        if sentiment:
            polarity = sentiment.get('polarity', 0)
            if polarity > 0.1:
                sentiment_emoji = "😊"
                sentiment_text = "긍정적"
            elif polarity < -0.1:
                sentiment_emoji = "😔" 
                sentiment_text = "부정적"
            else:
                sentiment_emoji = "😐"
                sentiment_text = "중립적"
            
            result += f"🎭 <b>감정 분석:</b> {sentiment_emoji} {sentiment_text} ({polarity:.2f})\n"
        
        if quality:
            grade = quality.get('grade', 'N/A')
            score = quality.get('overall_score', 0)
            
            grade_emojis = {
                'A+': '🏆', 'A': '🥇', 'B+': '🥈', 'B': '🥉',
                'C+': '📈', 'C': '📊', 'D+': '📉', 'D': '⚠️', 'F': '❌'
            }
            emoji = grade_emojis.get(grade, '📊')
            
            result += f"🏅 <b>품질 평가:</b> {emoji} {grade} ({score:.1f}/100)\n\n"
        
        if insights:
            result += "💡 <b>종합 인사이트:</b>\n"
            for insight in insights[:5]:
                result += f"  • {insight}\n"
            result += "\n"
        
        result += f"⏰ <b>분석 시간:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"🔧 <b>분석 엔진:</b> AI 기반 종합 분석 (감정+품질)"
        
        return result
    
    async def ai_compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """AI 기반 콘텐츠 비교 분석 명령어"""
        try:
            if OFFLINE_MODE:
                await update.message.reply_text("❌ AI 기반 분석은 OFFLINE_MODE에서 사용할 수 없습니다.")
                return
            
            if len(context.args) < 2:
                await self._send_usage_info(update, 'ai_compare')
                return
            
            url1, url2 = context.args[0], context.args[1]
            
            if not self.url_validator.is_valid_url(url1) or not self.url_validator.is_valid_url(url2):
                await update.message.reply_text("❌ 두 개의 올바른 URL을 입력해주세요.")
                return
            
            progress_msg = await update.message.reply_text(
                "⚖️ AI 기반 콘텐츠 비교 분석을 시작합니다...\n⏳ 첫 번째 콘텐츠를 추출하고 있습니다..."
            )
            
            content1 = await self._extract_content_safely(url1)
            if not content1:
                await progress_msg.edit_text("❌ 첫 번째 콘텐츠 추출에 실패했습니다.")
                return
            
            await progress_msg.edit_text(
                "⚖️ AI 기반 콘텐츠 비교 분석을 시작합니다...\n⏳ 두 번째 콘텐츠를 추출하고 있습니다..."
            )
            
            content2 = await self._extract_content_safely(url2)
            if not content2:
                await progress_msg.edit_text("❌ 두 번째 콘텐츠 추출에 실패했습니다.")
                return
            
            await progress_msg.edit_text(
                "⚖️ AI 기반 콘텐츠 비교 분석을 시작합니다...\n🧠 AI가 비교 분석을 수행하고 있습니다..."
            )
            
            analysis1 = await self.ai_engine.perform_comprehensive_ai_analysis(
                content1['content'], content1.get('metadata', {})
            )
            analysis2 = await self.ai_engine.perform_comprehensive_ai_analysis(
                content2['content'], content2.get('metadata', {})
            )
            
            result_text = self._format_comparison_result(
                analysis1, analysis2, url1, url2, content1, content2
            )
            
            await progress_msg.edit_text(result_text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"AI 비교 분석 명령어 오류: {str(e)}")
            await update.message.reply_text(f"❌ AI 비교 분석 중 오류가 발생했습니다: {str(e)}")
    
    def _format_comparison_result(self, analysis1: Dict[str, Any], analysis2: Dict[str, Any], 
                                url1: str, url2: str, content1: Dict[str, Any], content2: Dict[str, Any]) -> str:
        """AI 비교 분석 결과 포맷팅"""
        result = f"⚖️ <b>AI 기반 콘텐츠 비교 분석</b>\n\n"
        
        result += f"📄 <b>콘텐츠 1:</b> {content1.get('metadata', {}).get('title', 'N/A')}\n"
        result += f"🔗 {url1}\n\n"
        result += f"📄 <b>콘텐츠 2:</b> {content2.get('metadata', {}).get('title', 'N/A')}\n"
        result += f"🔗 {url2}\n\n"
        
        sentiment1 = analysis1.get('sentiment', {})
        sentiment2 = analysis2.get('sentiment', {})
        
        if sentiment1 and sentiment2:
            pol1 = sentiment1.get('polarity', 0)
            pol2 = sentiment2.get('polarity', 0)
            
            result += "🎭 <b>감정 비교:</b>\n"
            result += f"  📊 콘텐츠 1: {pol1:.2f} {'😊' if pol1 > 0.1 else '😔' if pol1 < -0.1 else '😐'}\n"
            result += f"  📊 콘텐츠 2: {pol2:.2f} {'😊' if pol2 > 0.1 else '😔' if pol2 < -0.1 else '😐'}\n"
            
            if abs(pol1 - pol2) > 0.2:
                winner = "콘텐츠 1" if pol1 > pol2 else "콘텐츠 2"
                result += f"  🏆 더 긍정적: {winner}\n"
            result += "\n"
        
        quality1 = analysis1.get('quality', {})
        quality2 = analysis2.get('quality', {})
        
        if quality1 and quality2:
            score1 = quality1.get('overall_score', 0)
            score2 = quality2.get('overall_score', 0)
            grade1 = quality1.get('grade', 'N/A')
            grade2 = quality2.get('grade', 'N/A')
            
            result += "🏅 <b>품질 비교:</b>\n"
            result += f"  📊 콘텐츠 1: {grade1} ({score1:.1f}/100)\n"
            result += f"  📊 콘텐츠 2: {grade2} ({score2:.1f}/100)\n"
            
            if abs(score1 - score2) > 5:
                winner = "콘텐츠 1" if score1 > score2 else "콘텐츠 2"
                result += f"  🏆 더 높은 품질: {winner}\n"
            result += "\n"
        
        result += "🎯 <b>종합 결론:</b>\n"
        
        total1 = (sentiment1.get('polarity', 0) * 50 + 50) + quality1.get('overall_score', 0)
        total2 = (sentiment2.get('polarity', 0) * 50 + 50) + quality2.get('overall_score', 0)
        
        if abs(total1 - total2) < 10:
            result += "  📊 두 콘텐츠의 전반적 품질이 비슷합니다.\n"
        else:
            winner = "콘텐츠 1" if total1 > total2 else "콘텐츠 2"
            result += f"  🏆 전반적으로 {winner}이 더 우수합니다.\n"
        
        result += f"\n⏰ <b>분석 시간:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"🔧 <b>분석 엔진:</b> AI 기반 비교 분석"
        
        return result
    
    async def _send_usage_info(self, update: Update, command: str) -> None:
        """명령어 사용법 정보 전송"""
        if command in self.commands_info:
            info = self.commands_info[command]
            message = f"ℹ️ <b>{info['description']}</b>\n\n"
            message += f"📝 <b>사용법:</b> <code>{info['usage']}</code>\n"
            message += f"💡 <b>예시:</b> <code>{info['example']}</code>"
            
            await update.message.reply_text(message, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ 알 수 없는 명령어입니다.")
    
    def get_commands_help(self) -> str:
        """모든 AI 통합 명령어의 도움말 반환"""
        help_text = "🤖 <b>AI 통합 명령어 목록</b>\n\n"
        
        for cmd, info in self.commands_info.items():
            help_text += f"🔸 <code>/{cmd}</code>\n"
            help_text += f"   {info['description']}\n"
            help_text += f"   사용법: <code>{info['usage']}</code>\n\n"
        
        help_text += "💡 <b>참고:</b> AI 기반 명령어는 OFFLINE_MODE에서 사용할 수 없습니다."
        
        return help_text 