"""
advanced_web_commands.py - 고급 웹 자동화 명령어들
Selenium WebDriver 기반의 고급 웹 자동화 기능 제공
"""

from telegram import Update
from telegram.ext import ContextTypes
from web_search_ide import web_search_ide
import logging

logger = logging.getLogger(__name__)

async def auto_visit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """고급 자동화 사이트 방문"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text(
            "🤖 **고급 자동화 사이트 방문**\n\n"
            "사용법: `/auto_visit [URL] [작업옵션]`\n\n"
            "**작업 옵션:**\n"
            "• `screenshot` - 스크린샷 캡처\n"
            "• `extract` - 콘텐츠 추출\n"
            "• `info` - 페이지 정보 수집\n\n"
            "**예시:**\n"
            "`/auto_visit https://github.com screenshot`\n"
            "`/auto_visit https://stackoverflow.com extract`",
            parse_mode='Markdown'
        )
        return
    
    url = context.args[0]
    
    # 작업 옵션 파싱
    automation_tasks = []
    if len(context.args) > 1:
        options = context.args[1:]
        
        for option in options:
            if option == "screenshot":
                automation_tasks.append({"type": "screenshot"})
            elif option == "extract":
                automation_tasks.append({
                    "type": "extract_content",
                    "selectors": ["h1", "h2", "h3", "p", "code", "pre"]
                })
            elif option == "info":
                # 페이지 정보는 기본적으로 수집됨
                pass
    
    await update.message.reply_text(f"🤖 고급 자동화로 사이트 방문 중: {url}")
    
    try:
        result = web_search_ide.advanced_site_visit(user_id, url, automation_tasks)
        
        if result.get("success"):
            response = f"✅ **고급 사이트 방문 완료**\n\n"
            response += f"🔗 **URL:** {result['url']}\n"
            
            # 페이지 정보
            page_info = result.get("page_info", {})
            if page_info.get("success"):
                response += f"📄 **제목:** {page_info.get('title', '없음')}\n"
                response += f"⏱️ **로딩 시간:** {page_info.get('load_time_ms', 'N/A')}ms\n"
            
            # 자동화 작업 결과
            automation_results = result.get("automation_results", [])
            if automation_results:
                response += f"\n🔧 **수행된 작업:**\n"
                for task_result in automation_results:
                    task_type = task_result["task"]
                    task_data = task_result["result"]
                    
                    if task_type == "screenshot" and task_data.get("success"):
                        response += f"📸 스크린샷 캡처 완료 ({task_data.get('size', 0)} bytes)\n"
                    elif task_type == "extract_content" and task_data.get("success"):
                        extracted = task_data.get("extracted_content", {})
                        total_elements = sum(len(v) if isinstance(v, list) else 0 for v in extracted.values())
                        response += f"📄 콘텐츠 추출 완료 ({total_elements}개 요소)\n"
            
            response += f"\n⏰ **완료 시간:** {result.get('timestamp', 'N/A')}"
            
        else:
            response = f"❌ **사이트 방문 실패**\n\n{result.get('error', '알 수 없는 오류')}"
        
    except Exception as e:
        logger.error(f"Auto visit command error: {e}")
        response = f"❌ **오류 발생:** {str(e)}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def screenshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """웹페이지 스크린샷 캡처"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text(
            "📸 **웹페이지 스크린샷 캡처**\n\n"
            "사용법: `/screenshot [URL]`\n\n"
            "**예시:**\n"
            "`/screenshot https://github.com`\n"
            "`/screenshot` (현재 열린 페이지)",
            parse_mode='Markdown'
        )
        return
    
    url = context.args[0] if context.args else None
    
    await update.message.reply_text(f"📸 스크린샷 캡처 중...")
    
    try:
        result = web_search_ide.capture_page_screenshot(user_id, url)
        
        if result.get("success"):
            response = f"✅ **스크린샷 캡처 완료**\n\n"
            response += f"📄 **파일명:** {result.get('filename', 'unknown')}\n"
            response += f"📊 **크기:** {result.get('size', 0)} bytes\n"
            response += f"⏰ **시간:** {result.get('timestamp', 'N/A')}"
            
            # 스크린샷 데이터가 있으면 표시 (실제로는 파일로 저장하거나 다른 방식으로 처리)
            if result.get("data"):
                response += f"\n\n📋 **Base64 데이터 길이:** {len(result['data'])} 문자"
            
        else:
            response = f"❌ **스크린샷 캡처 실패**\n\n{result.get('error', '알 수 없는 오류')}"
        
    except Exception as e:
        logger.error(f"Screenshot command error: {e}")
        response = f"❌ **오류 발생:** {str(e)}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def click_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """웹 요소 클릭"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text(
            "🖱️ **웹 요소 클릭**\n\n"
            "사용법: `/click [CSS셀렉터]`\n\n"
            "**CSS 셀렉터 예시:**\n"
            "• `button` - 첫 번째 버튼\n"
            "• `#submit-btn` - ID가 submit-btn인 요소\n"
            "• `.nav-link` - nav-link 클래스 요소\n"
            "• `a[href='/login']` - /login으로 가는 링크\n\n"
            "**예시:**\n"
            "`/click button.primary`\n"
            "`/click #search-button`",
            parse_mode='Markdown'
        )
        return
    
    selector = ' '.join(context.args)
    
    await update.message.reply_text(f"🖱️ 요소 클릭 중: `{selector}`", parse_mode='Markdown')
    
    try:
        result = web_search_ide.interact_with_page(user_id, selector, "click")
        
        if result.get("success"):
            response = f"✅ **요소 클릭 완료**\n\n"
            response += f"🎯 **셀렉터:** `{selector}`\n"
            response += f"✨ **결과:** {result.get('message', '클릭 완료')}"
            
        else:
            response = f"❌ **요소 클릭 실패**\n\n{result.get('error', '알 수 없는 오류')}"
        
    except Exception as e:
        logger.error(f"Click command error: {e}")
        response = f"❌ **오류 발생:** {str(e)}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def type_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """웹 요소에 텍스트 입력"""
    user_id = str(update.effective_user.id)
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "⌨️ **웹 요소에 텍스트 입력**\n\n"
            "사용법: `/type [CSS셀렉터] [텍스트]`\n\n"
            "**예시:**\n"
            "`/type input[name='search'] python tutorial`\n"
            "`/type #username myuser123`\n"
            "`/type .search-box machine learning`",
            parse_mode='Markdown'
        )
        return
    
    selector = context.args[0]
    text = ' '.join(context.args[1:])
    
    await update.message.reply_text(f"⌨️ 텍스트 입력 중: `{selector}`", parse_mode='Markdown')
    
    try:
        result = web_search_ide.interact_with_page(user_id, selector, "input", text)
        
        if result.get("success"):
            response = f"✅ **텍스트 입력 완료**\n\n"
            response += f"🎯 **셀렉터:** `{selector}`\n"
            response += f"📝 **입력 텍스트:** `{text}`\n"
            response += f"✨ **결과:** {result.get('message', '입력 완료')}"
            
        else:
            response = f"❌ **텍스트 입력 실패**\n\n{result.get('error', '알 수 없는 오류')}"
        
    except Exception as e:
        logger.error(f"Type command error: {e}")
        response = f"❌ **오류 발생:** {str(e)}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def extract_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """동적 콘텐츠 추출"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text(
            "📄 **동적 콘텐츠 추출**\n\n"
            "사용법: `/extract [CSS셀렉터1] [CSS셀렉터2] ...`\n\n"
            "**일반적인 셀렉터:**\n"
            "• `h1, h2, h3` - 제목들\n"
            "• `p` - 문단\n"
            "• `code, pre` - 코드 블록\n"
            "• `a` - 링크\n"
            "• `.class-name` - 특정 클래스\n"
            "• `#id-name` - 특정 ID\n\n"
            "**예시:**\n"
            "`/extract h1 h2 p`\n"
            "`/extract .code-snippet pre`\n"
            "`/extract a[href*='github']`",
            parse_mode='Markdown'
        )
        return
    
    selectors = context.args
    
    await update.message.reply_text(f"📄 콘텐츠 추출 중: {len(selectors)}개 셀렉터")
    
    try:
        result = web_search_ide.extract_dynamic_page_content(user_id, selectors)
        
        if result.get("success"):
            extracted_content = result.get("extracted_content", {})
            
            response = f"✅ **동적 콘텐츠 추출 완료**\n\n"
            
            total_elements = 0
            for selector, elements in extracted_content.items():
                if isinstance(elements, list):
                    element_count = len(elements)
                    total_elements += element_count
                    response += f"🎯 **{selector}:** {element_count}개 요소\n"
                    
                    # 첫 번째 요소의 텍스트 미리보기 (50자 제한)
                    if elements and isinstance(elements[0], dict):
                        preview_text = elements[0].get('text', '')[:50]
                        if preview_text:
                            response += f"   📝 미리보기: {preview_text}...\n"
                elif isinstance(elements, dict) and 'error' in elements:
                    response += f"❌ **{selector}:** {elements['error']}\n"
                
                response += "\n"
            
            response += f"📊 **총 추출된 요소:** {total_elements}개"
            
        else:
            response = f"❌ **콘텐츠 추출 실패**\n\n{result.get('error', '알 수 없는 오류')}"
        
    except Exception as e:
        logger.error(f"Extract command error: {e}")
        response = f"❌ **오류 발생:** {str(e)}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def js_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """페이지에서 JavaScript 실행"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text(
            "🚀 **JavaScript 실행**\n\n"
            "사용법: `/js [JavaScript코드]`\n\n"
            "**예시:**\n"
            "`/js document.title`\n"
            "`/js window.location.href`\n"
            "`/js document.querySelectorAll('h1').length`\n"
            "`/js return document.body.innerHTML.length`\n\n"
            "⚠️ **주의:** 페이지를 변경하는 코드는 신중히 사용하세요.",
            parse_mode='Markdown'
        )
        return
    
    script = ' '.join(context.args)
    
    await update.message.reply_text(f"🚀 JavaScript 실행 중...")
    
    try:
        result = web_search_ide.execute_page_javascript(user_id, script)
        
        if result.get("success"):
            js_result = result.get("result")
            
            response = f"✅ **JavaScript 실행 완료**\n\n"
            response += f"📜 **코드:** `{script}`\n"
            response += f"📤 **결과:** `{js_result}`\n"
            response += f"✨ **메시지:** {result.get('message', '실행 완료')}"
            
        else:
            response = f"❌ **JavaScript 실행 실패**\n\n{result.get('error', '알 수 없는 오류')}"
        
    except Exception as e:
        logger.error(f"JS command error: {e}")
        response = f"❌ **오류 발생:** {str(e)}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def close_browser_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """브라우저 종료"""
    await update.message.reply_text("🔒 브라우저 종료 중...")
    
    try:
        result = web_search_ide.close_browser()
        
        if result.get("success"):
            response = f"✅ **브라우저 종료 완료**\n\n{result.get('message', '브라우저가 정상적으로 종료되었습니다.')}"
        else:
            response = f"❌ **브라우저 종료 실패**\n\n{result.get('error', '알 수 없는 오류')}"
        
    except Exception as e:
        logger.error(f"Close browser command error: {e}")
        response = f"❌ **오류 발생:** {str(e)}"
    
    await update.message.reply_text(response, parse_mode='Markdown') 