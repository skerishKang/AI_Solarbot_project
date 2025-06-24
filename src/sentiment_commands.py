"""
감정 분석 전용 텔레그램 명령어들 (5단계 4차 업그레이드)
"""

import re
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from intelligent_content_analyzer import IntelligentContentAnalyzer
from web_search_ide import fetch_content_with_fallback

logger = logging.getLogger(__name__)

def safe_markdown(text: str) -> str:
    """텔레그램 마크다운을 안전하게 처리"""
    text = text.replace('\\', '\\\\')
    text = text.replace('_', '\\_')
    text = text.replace('[', '\\[')
    text = text.replace(']', '\\]')
    text = re.sub(r'\*{3,}', '**', text)
    return text

async def sentiment_only_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """콘텐츠의 기본 감정 분석만 수행"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if not context.args:
        await update.message.reply_text(
            "❌ 사용법: /sentiment_only <URL>\n"
            "예시: /sentiment_only https://example.com\n\n"
            "😊 이 명령어는 콘텐츠의 기본 감정 분석만 수행합니다."
        )
        return
    
    url = context.args[0]
    
    try:
        progress_msg = await update.message.reply_text("🔄 감정 분석을 시작합니다...")
        
        # 콘텐츠 가져오기
        content = await fetch_content_with_fallback(url)
        
        if content:
            await progress_msg.edit_text("😊 감정 분석 중...")
            
            # 감정 분석 수행
            analyzer = IntelligentContentAnalyzer()
            result = await analyzer.analyze_content(content, content_type='웹페이지')
            
            if result and hasattr(result, 'sentiment_score'):
                message = "😊 **콘텐츠 감정 분석 결과**\n\n"
                
                # URL 정보
                message += f"🔗 **분석 URL:** {url}\n\n"
                
                # 전체 감정 점수
                sentiment_emoji = "😊" if result.sentiment_score > 0.2 else "😐" if result.sentiment_score > -0.2 else "😞"
                message += f"🎭 **감정 점수:** {result.sentiment_score:.2f} {sentiment_emoji}\n"
                message += f"📊 **감정 라벨:** {result.sentiment_label}\n\n"
                
                # 세분화된 감정 분석
                if hasattr(result, 'detailed_emotions'):
                    message += f"🎨 **세분화된 감정 분석:**\n"
                    
                    emotion_emojis = {
                        'joy': '😄', 'trust': '🤝', 'fear': '😨', 'surprise': '😲',
                        'sadness': '😢', 'disgust': '🤢', 'anger': '😡', 'anticipation': '🤔'
                    }
                    
                    emotion_names = {
                        'joy': '기쁨', 'trust': '신뢰', 'fear': '두려움', 'surprise': '놀라움',
                        'sadness': '슬픔', 'disgust': '혐오', 'anger': '분노', 'anticipation': '기대'
                    }
                    
                    sorted_emotions = sorted(result.detailed_emotions.items(), 
                                           key=lambda x: x[1], reverse=True)[:5]
                    
                    for emotion, score in sorted_emotions:
                        emoji = emotion_emojis.get(emotion, '😐')
                        name = emotion_names.get(emotion, emotion.title())
                        message += f"{emoji} **{name}:** {score:.2f}\n"
                    
                    message += "\n"
                
                # 감정 강도와 신뢰도
                if hasattr(result, 'emotion_intensity'):
                    message += f"⚡ **감정 강도:** {result.emotion_intensity:.2f}/1.0\n"
                if hasattr(result, 'emotion_confidence'):
                    message += f"🎯 **분석 신뢰도:** {result.emotion_confidence:.2f}/1.0\n"
                if hasattr(result, 'dominant_emotion'):
                    message += f"🏆 **주요 감정:** {result.dominant_emotion}\n\n"
                
                message += f"🕐 **분석 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                await progress_msg.edit_text(safe_markdown(message), parse_mode='Markdown')
            else:
                await progress_msg.edit_text("❌ 감정 분석에 실패했습니다.")
        else:
            await progress_msg.edit_text("❌ 감정 분석 실패: 콘텐츠를 가져올 수 없습니다.")
            
    except Exception as e:
        logger.error(f"감정 분석 오류: {e}")
        await update.message.reply_text(f"❌ 감정 분석 중 오류 발생: {str(e)}")

async def emotion_detail_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """콘텐츠의 상세 감정 분석 및 해석"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if not context.args:
        await update.message.reply_text(
            "❌ 사용법: /emotion_detail <URL>\n"
            "예시: /emotion_detail https://example.com\n\n"
            "🎭 이 명령어는 상세한 감정 분석과 해석을 제공합니다."
        )
        return
    
    url = context.args[0]
    
    try:
        progress_msg = await update.message.reply_text("🔄 상세 감정 분석을 시작합니다...")
        
        # 콘텐츠 가져오기
        content = await fetch_content_with_fallback(url)
        
        if content:
            await progress_msg.edit_text("🎭 심층 감정 분석 중...")
            
            # 감정 분석 수행
            analyzer = IntelligentContentAnalyzer()
            result = await analyzer.analyze_content(content, content_type='웹페이지')
            
            if result and hasattr(result, 'sentiment_score'):
                message = "🎭 **상세 감정 분석 결과**\n\n"
                
                # URL 정보
                message += f"🔗 **분석 URL:** {url}\n\n"
                
                # 전체 감정 분석
                sentiment_emoji = "😊" if result.sentiment_score > 0.2 else "😐" if result.sentiment_score > -0.2 else "😞"
                message += f"🎯 **전체 감정 점수:** {result.sentiment_score:.3f} {sentiment_emoji}\n"
                message += f"📊 **감정 라벨:** {result.sentiment_label}\n\n"
                
                # 모든 세분화된 감정 분석
                if hasattr(result, 'detailed_emotions'):
                    message += f"🎨 **8가지 세분화된 감정 분석:**\n"
                    
                    emotion_emojis = {
                        'joy': '😄', 'trust': '🤝', 'fear': '😨', 'surprise': '😲',
                        'sadness': '😢', 'disgust': '🤢', 'anger': '😡', 'anticipation': '🤔'
                    }
                    
                    emotion_names = {
                        'joy': '기쁨', 'trust': '신뢰', 'fear': '두려움', 'surprise': '놀라움',
                        'sadness': '슬픔', 'disgust': '혐오', 'anger': '분노', 'anticipation': '기대'
                    }
                    
                    for emotion, score in result.detailed_emotions.items():
                        emoji = emotion_emojis.get(emotion, '😐')
                        name = emotion_names.get(emotion, emotion.title())
                        bar = "▰" * int(score * 10) + "▱" * (10 - int(score * 10))
                        message += f"{emoji} **{name}:** {score:.3f} {bar}\n"
                    
                    message += "\n"
                
                # 감정 분포 분석
                if hasattr(result, 'emotion_distribution'):
                    message += f"📊 **감정 분포 분석:**\n"
                    positive_emotions = ['joy', 'trust', 'surprise', 'anticipation']
                    negative_emotions = ['sadness', 'disgust', 'anger', 'fear']
                    
                    positive_sum = sum(result.detailed_emotions.get(e, 0) for e in positive_emotions)
                    negative_sum = sum(result.detailed_emotions.get(e, 0) for e in negative_emotions)
                    
                    message += f"😊 **긍정적 감정:** {positive_sum:.2f} ({positive_sum*100:.1f}%)\n"
                    message += f"😞 **부정적 감정:** {negative_sum:.2f} ({negative_sum*100:.1f}%)\n\n"
                
                # 감정 강도와 신뢰도
                if hasattr(result, 'emotion_intensity'):
                    intensity_bar = "▰" * int(result.emotion_intensity * 10) + "▱" * (10 - int(result.emotion_intensity * 10))
                    message += f"⚡ **감정 강도:** {result.emotion_intensity:.3f} {intensity_bar}\n"
                
                if hasattr(result, 'emotion_confidence'):
                    confidence_bar = "▰" * int(result.emotion_confidence * 10) + "▱" * (10 - int(result.emotion_confidence * 10))
                    message += f"🎯 **분석 신뢰도:** {result.emotion_confidence:.3f} {confidence_bar}\n"
                
                if hasattr(result, 'dominant_emotion'):
                    message += f"🏆 **주요 감정:** {result.dominant_emotion}\n"
                
                if hasattr(result, 'contextual_sentiment'):
                    message += f"🌍 **맥락적 감정:** {result.contextual_sentiment}\n\n"
                
                # 감정 해석
                message += f"💭 **감정 해석:**\n"
                if result.sentiment_score > 0.5:
                    message += "이 콘텐츠는 매우 긍정적인 감정을 담고 있습니다. 독자에게 희망과 기쁨을 전달할 가능성이 높습니다.\n"
                elif result.sentiment_score > 0.2:
                    message += "이 콘텐츠는 전반적으로 긍정적인 감정을 담고 있습니다. 독자에게 좋은 인상을 줄 것으로 예상됩니다.\n"
                elif result.sentiment_score > -0.2:
                    message += "이 콘텐츠는 중립적인 감정을 담고 있습니다. 객관적이고 균형잡힌 정보를 제공합니다.\n"
                elif result.sentiment_score > -0.5:
                    message += "이 콘텐츠는 다소 부정적인 감정을 담고 있습니다. 비판적이거나 우려스러운 내용을 포함할 수 있습니다.\n"
                else:
                    message += "이 콘텐츠는 매우 부정적인 감정을 담고 있습니다. 독자에게 불쾌감이나 우울감을 줄 수 있습니다.\n"
                
                message += f"\n🕐 **분석 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                await progress_msg.edit_text(safe_markdown(message), parse_mode='Markdown')
            else:
                await progress_msg.edit_text("❌ 상세 감정 분석에 실패했습니다.")
        else:
            await progress_msg.edit_text("❌ 감정 분석 실패: 콘텐츠를 가져올 수 없습니다.")
            
    except Exception as e:
        logger.error(f"상세 감정 분석 오류: {e}")
        await update.message.reply_text(f"❌ 상세 감정 분석 중 오류 발생: {str(e)}")

async def sentiment_batch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """여러 콘텐츠의 일괄 감정 분석 (최대 5개)"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if not context.args:
        await update.message.reply_text(
            "❌ 사용법: /sentiment_batch <URL1> <URL2> ...\n"
            "예시: /sentiment_batch https://example1.com https://example2.com\n\n"
            "📊 최대 5개 URL의 감정을 일괄 분석합니다."
        )
        return
    
    urls = context.args[:5]  # 최대 5개로 제한
    
    try:
        progress_msg = await update.message.reply_text(f"🔄 {len(urls)}개 콘텐츠의 일괄 감정 분석을 시작합니다...")
        
        results = []
        
        for i, url in enumerate(urls):
            await progress_msg.edit_text(f"😊 감정 분석 중... ({i+1}/{len(urls)})")
            
            # 콘텐츠 가져오기
            content = await fetch_content_with_fallback(url)
            
            if content:
                # 감정 분석 수행
                analyzer = IntelligentContentAnalyzer()
                result = await analyzer.analyze_content(content, content_type='웹페이지')
                
                if result and hasattr(result, 'sentiment_score'):
                    results.append((url, result))
                else:
                    results.append((url, None))
            else:
                results.append((url, None))
        
        # 결과 정리
        message = "📊 **일괄 감정 분석 결과**\n\n"
        
        successful_results = [r for r in results if r[1] is not None]
        
        if successful_results:
            # 전체 통계
            avg_sentiment = sum(r[1].sentiment_score for r in successful_results) / len(successful_results)
            sentiment_emoji = "😊" if avg_sentiment > 0.2 else "😐" if avg_sentiment > -0.2 else "😞"
            
            message += f"📈 **전체 평균 감정:** {avg_sentiment:.3f} {sentiment_emoji}\n"
            message += f"✅ **성공:** {len(successful_results)}개\n"
            message += f"❌ **실패:** {len(results) - len(successful_results)}개\n\n"
            
            # 개별 결과
            message += f"📋 **개별 분석 결과:**\n"
            
            for i, (url, result) in enumerate(results):
                message += f"\n**{i+1}. {url[:50]}...**\n"
                
                if result:
                    sentiment_emoji = "😊" if result.sentiment_score > 0.2 else "😐" if result.sentiment_score > -0.2 else "😞"
                    message += f"   🎭 감정: {result.sentiment_score:.2f} {sentiment_emoji} ({result.sentiment_label})\n"
                    
                    if hasattr(result, 'dominant_emotion'):
                        message += f"   🏆 주요 감정: {result.dominant_emotion}\n"
                else:
                    message += f"   ❌ 분석 실패\n"
            
            # 감정 비교
            if len(successful_results) > 1:
                message += f"\n🔍 **감정 비교 분석:**\n"
                most_positive = max(successful_results, key=lambda x: x[1].sentiment_score)
                most_negative = min(successful_results, key=lambda x: x[1].sentiment_score)
                
                message += f"😊 **가장 긍정적:** {most_positive[0][:40]}... ({most_positive[1].sentiment_score:.2f})\n"
                message += f"😞 **가장 부정적:** {most_negative[0][:40]}... ({most_negative[1].sentiment_score:.2f})\n"
        else:
            message += "❌ 모든 콘텐츠의 감정 분석에 실패했습니다."
        
        message += f"\n🕐 **분석 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await progress_msg.edit_text(safe_markdown(message), parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"일괄 감정 분석 오류: {e}")
        await update.message.reply_text(f"❌ 일괄 감정 분석 중 오류 발생: {str(e)}")

async def sentiment_compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """두 콘텐츠의 감정 비교 분석"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ 사용법: /sentiment_compare <URL1> <URL2>\n"
            "예시: /sentiment_compare https://example1.com https://example2.com\n\n"
            "⚖️ 두 콘텐츠의 감정을 비교 분석합니다."
        )
        return
    
    url1, url2 = context.args[0], context.args[1]
    
    try:
        progress_msg = await update.message.reply_text("🔄 두 콘텐츠의 감정 비교 분석을 시작합니다...")
        
        # 콘텐츠 가져오기
        content1 = await fetch_content_with_fallback(url1)
        content2 = await fetch_content_with_fallback(url2)
        
        if content1 and content2:
            await progress_msg.edit_text("⚖️ 감정 비교 분석 중...")
            
            # 감정 분석 수행
            analyzer = IntelligentContentAnalyzer()
            result1 = await analyzer.analyze_content(content1, content_type='웹페이지')
            result2 = await analyzer.analyze_content(content2, content_type='웹페이지')
            
            if result1 and result2 and hasattr(result1, 'sentiment_score') and hasattr(result2, 'sentiment_score'):
                message = "⚖️ **감정 비교 분석 결과**\n\n"
                
                # URL 정보
                message += f"1️⃣ **첫 번째 콘텐츠:** {url1[:50]}...\n"
                message += f"2️⃣ **두 번째 콘텐츠:** {url2[:50]}...\n\n"
                
                # 전체 감정 점수 비교
                sentiment1_emoji = "😊" if result1.sentiment_score > 0.2 else "😐" if result1.sentiment_score > -0.2 else "😞"
                sentiment2_emoji = "😊" if result2.sentiment_score > 0.2 else "😐" if result2.sentiment_score > -0.2 else "😞"
                
                message += f"🎭 **전체 감정 점수:**\n"
                message += f"1️⃣ {result1.sentiment_score:.3f} {sentiment1_emoji} ({result1.sentiment_label})\n"
                message += f"2️⃣ {result2.sentiment_score:.3f} {sentiment2_emoji} ({result2.sentiment_label})\n"
                
                sentiment_diff = result1.sentiment_score - result2.sentiment_score
                if abs(sentiment_diff) > 0.1:
                    winner = "첫 번째" if sentiment_diff > 0 else "두 번째"
                    message += f"🏆 **더 긍정적:** {winner} 콘텐츠 (차이: {abs(sentiment_diff):.3f})\n\n"
                else:
                    message += f"⚖️ **감정 수준:** 비슷함 (차이: {abs(sentiment_diff):.3f})\n\n"
                
                # 세분화된 감정 비교
                if hasattr(result1, 'detailed_emotions') and hasattr(result2, 'detailed_emotions'):
                    message += f"🎨 **세분화된 감정 비교:**\n"
                    
                    emotion_emojis = {
                        'joy': '😄', 'trust': '🤝', 'fear': '😨', 'surprise': '😲',
                        'sadness': '😢', 'disgust': '🤢', 'anger': '😡', 'anticipation': '🤔'
                    }
                    
                    emotion_names = {
                        'joy': '기쁨', 'trust': '신뢰', 'fear': '두려움', 'surprise': '놀라움',
                        'sadness': '슬픔', 'disgust': '혐오', 'anger': '분노', 'anticipation': '기대'
                    }
                    
                    all_emotions = set(result1.detailed_emotions.keys()) | set(result2.detailed_emotions.keys())
                    
                    for emotion in sorted(all_emotions):
                        score1 = result1.detailed_emotions.get(emotion, 0)
                        score2 = result2.detailed_emotions.get(emotion, 0)
                        emoji = emotion_emojis.get(emotion, '😐')
                        name = emotion_names.get(emotion, emotion.title())
                        
                        diff = score1 - score2
                        if abs(diff) > 0.05:
                            winner = "1️⃣" if diff > 0 else "2️⃣"
                            message += f"{emoji} **{name}:** {winner} 더 강함 ({score1:.2f} vs {score2:.2f})\n"
                        else:
                            message += f"{emoji} **{name}:** 비슷함 ({score1:.2f} vs {score2:.2f})\n"
                    
                    message += "\n"
                
                # 감정 강도 비교
                if hasattr(result1, 'emotion_intensity') and hasattr(result2, 'emotion_intensity'):
                    message += f"⚡ **감정 강도 비교:**\n"
                    message += f"1️⃣ {result1.emotion_intensity:.3f}\n"
                    message += f"2️⃣ {result2.emotion_intensity:.3f}\n"
                    
                    intensity_diff = result1.emotion_intensity - result2.emotion_intensity
                    if abs(intensity_diff) > 0.1:
                        winner = "첫 번째" if intensity_diff > 0 else "두 번째"
                        message += f"🔥 **더 강한 감정:** {winner} 콘텐츠\n\n"
                    else:
                        message += f"⚖️ **감정 강도:** 비슷함\n\n"
                
                # 종합 비교 결과
                message += f"🎯 **종합 비교 결과:**\n"
                if abs(sentiment_diff) < 0.1:
                    message += "두 콘텐츠의 감정적 톤이 매우 유사합니다."
                elif sentiment_diff > 0.3:
                    message += "첫 번째 콘텐츠가 훨씬 더 긍정적입니다."
                elif sentiment_diff > 0.1:
                    message += "첫 번째 콘텐츠가 더 긍정적입니다."
                elif sentiment_diff < -0.3:
                    message += "두 번째 콘텐츠가 훨씬 더 긍정적입니다."
                elif sentiment_diff < -0.1:
                    message += "두 번째 콘텐츠가 더 긍정적입니다."
                
                message += f"\n\n🕐 **분석 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                await progress_msg.edit_text(safe_markdown(message), parse_mode='Markdown')
            else:
                await progress_msg.edit_text("❌ 감정 비교 분석에 실패했습니다.")
        else:
            missing = []
            if not content1: missing.append("첫 번째")
            if not content2: missing.append("두 번째")
            await progress_msg.edit_text(f"❌ {', '.join(missing)} 콘텐츠를 가져올 수 없습니다.")
            
    except Exception as e:
        logger.error(f"감정 비교 분석 오류: {e}")
        await update.message.reply_text(f"❌ 감정 비교 분석 중 오류 발생: {str(e)}") 