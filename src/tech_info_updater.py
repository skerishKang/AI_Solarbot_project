"""
최신 기술 정보 자동 업데이트 시스템
GitHub API, NPM API, PyPI API를 연동하여 최신 기술 정보를 자동으로 업데이트
"""

import os
import json
import asyncio
import aiohttp
import feedparser
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from cachetools import TTLCache
from loguru import logger
import xmltodict

@dataclass
class TechNews:
    """기술 뉴스 데이터 클래스"""
    title: str
    url: str
    description: str
    published: str
    source: str
    tags: List[str]
    score: float = 0.0

@dataclass
class PackageInfo:
    """패키지 정보 데이터 클래스"""
    name: str
    version: str
    description: str
    homepage: str
    repository: str
    downloads: int
    last_updated: str
    ecosystem: str  # npm, pypi, github

class TechInfoUpdater:
    """최신 기술 정보 자동 업데이트 시스템"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.stack_exchange_key = os.getenv('STACK_EXCHANGE_KEY')
        
        # 캐시 설정 (1시간 TTL)
        self.cache = TTLCache(maxsize=1000, ttl=3600)
        
        # RSS 피드 URL들
        self.rss_feeds = {
            'dev.to': 'https://dev.to/feed',
            'medium_tech': 'https://medium.com/feed/topic/technology',
            'hackernews': 'https://hnrss.org/frontpage',
            'github_blog': 'https://github.blog/feed/',
            'stackoverflow_blog': 'https://stackoverflow.blog/feed/',
            'python_org': 'https://www.python.org/jobs/feed/rss/',
            'nodejs_blog': 'https://nodejs.org/en/feed/blog.xml'
        }
        
        # API 엔드포인트
        self.api_endpoints = {
            'github_trending': 'https://api.github.com/search/repositories',
            'npm_registry': 'https://registry.npmjs.org',
            'pypi_api': 'https://pypi.org/pypi',
            'stack_exchange': 'https://api.stackexchange.com/2.3'
        }
        
        logger.info("TechInfoUpdater 초기화 완료")

    async def get_github_trending(self, language: str = '', time_range: str = 'daily') -> List[Dict]:
        """GitHub 트렌딩 리포지토리 정보 수집"""
        try:
            cache_key = f"github_trending_{language}_{time_range}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # 날짜 계산
            if time_range == 'daily':
                since_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            elif time_range == 'weekly':
                since_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            else:
                since_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # 검색 쿼리 구성
            query = f"created:>{since_date}"
            if language:
                query += f" language:{language}"
            
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': 30
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_endpoints['github_trending'],
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        repositories = []
                        
                        for repo in data.get('items', []):
                            repo_info = {
                                'name': repo['full_name'],
                                'description': repo.get('description', ''),
                                'url': repo['html_url'],
                                'stars': repo['stargazers_count'],
                                'forks': repo['forks_count'],
                                'language': repo.get('language', ''),
                                'created_at': repo['created_at'],
                                'updated_at': repo['updated_at'],
                                'topics': repo.get('topics', [])
                            }
                            repositories.append(repo_info)
                        
                        self.cache[cache_key] = repositories
                        logger.info(f"GitHub 트렌딩 {len(repositories)}개 리포지토리 수집 완료")
                        return repositories
                    else:
                        logger.error(f"GitHub API 오류: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"GitHub 트렌딩 수집 오류: {e}")
            return []

    async def get_npm_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """NPM 패키지 정보 수집"""
        try:
            cache_key = f"npm_{package_name}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            async with aiohttp.ClientSession() as session:
                # NPM 레지스트리에서 패키지 정보 가져오기
                async with session.get(f"{self.api_endpoints['npm_registry']}/{package_name}") as response:
                    if response.status == 200:
                        data = await response.json()
                        latest_version = data['dist-tags']['latest']
                        latest_info = data['versions'][latest_version]
                        
                        # 다운로드 통계 가져오기
                        downloads = 0
                        try:
                            async with session.get(f"https://api.npmjs.org/downloads/point/last-month/{package_name}") as dl_response:
                                if dl_response.status == 200:
                                    dl_data = await dl_response.json()
                                    downloads = dl_data.get('downloads', 0)
                        except:
                            pass
                        
                        package_info = PackageInfo(
                            name=package_name,
                            version=latest_version,
                            description=latest_info.get('description', ''),
                            homepage=latest_info.get('homepage', ''),
                            repository=latest_info.get('repository', {}).get('url', ''),
                            downloads=downloads,
                            last_updated=data['time'][latest_version],
                            ecosystem='npm'
                        )
                        
                        self.cache[cache_key] = package_info
                        return package_info
                    else:
                        logger.error(f"NPM API 오류: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"NPM 패키지 정보 수집 오류: {e}")
            return None

    async def get_pypi_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """PyPI 패키지 정보 수집"""
        try:
            cache_key = f"pypi_{package_name}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_endpoints['pypi_api']}/{package_name}/json") as response:
                    if response.status == 200:
                        data = await response.json()
                        info = data['info']
                        
                        package_info = PackageInfo(
                            name=package_name,
                            version=info['version'],
                            description=info.get('summary', ''),
                            homepage=info.get('home_page', ''),
                            repository=info.get('project_urls', {}).get('Repository', ''),
                            downloads=0,  # PyPI는 별도 API 필요
                            last_updated=data['releases'][info['version']][0]['upload_time'] if data['releases'][info['version']] else '',
                            ecosystem='pypi'
                        )
                        
                        self.cache[cache_key] = package_info
                        return package_info
                    else:
                        logger.error(f"PyPI API 오류: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"PyPI 패키지 정보 수집 오류: {e}")
            return None

    def parse_rss_feeds(self) -> List[TechNews]:
        """RSS 피드에서 기술 뉴스 수집"""
        try:
            cache_key = "rss_feeds"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            all_news = []
            
            for source, url in self.rss_feeds.items():
                try:
                    feed = feedparser.parse(url)
                    
                    for entry in feed.entries[:10]:  # 최신 10개만
                        # 태그 추출
                        tags = []
                        if hasattr(entry, 'tags'):
                            tags = [tag.term for tag in entry.tags]
                        
                        # 점수 계산 (간단한 키워드 기반)
                        score = self._calculate_relevance_score(entry.title + ' ' + entry.get('summary', ''))
                        
                        news = TechNews(
                            title=entry.title,
                            url=entry.link,
                            description=entry.get('summary', '')[:200],
                            published=entry.get('published', ''),
                            source=source,
                            tags=tags,
                            score=score
                        )
                        all_news.append(news)
                        
                except Exception as e:
                    logger.error(f"RSS 피드 파싱 오류 ({source}): {e}")
                    continue
            
            # 점수순으로 정렬
            all_news.sort(key=lambda x: x.score, reverse=True)
            
            self.cache[cache_key] = all_news[:50]  # 상위 50개만 캐시
            logger.info(f"RSS 피드에서 {len(all_news)} 개 뉴스 수집 완료")
            return all_news[:50]
            
        except Exception as e:
            logger.error(f"RSS 피드 수집 오류: {e}")
            return []

    async def get_stackoverflow_questions(self, tags: List[str], sort: str = 'activity') -> List[Dict]:
        """Stack Overflow 최신 질문 수집"""
        try:
            cache_key = f"stackoverflow_{'-'.join(tags)}_{sort}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            params = {
                'order': 'desc',
                'sort': sort,
                'tagged': ';'.join(tags),
                'site': 'stackoverflow',
                'pagesize': 20
            }
            
            if self.stack_exchange_key:
                params['key'] = self.stack_exchange_key
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_endpoints['stack_exchange']}/questions",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        questions = []
                        
                        for question in data.get('items', []):
                            question_info = {
                                'title': question['title'],
                                'url': question['link'],
                                'score': question['score'],
                                'view_count': question['view_count'],
                                'answer_count': question['answer_count'],
                                'tags': question['tags'],
                                'creation_date': datetime.fromtimestamp(question['creation_date']).isoformat(),
                                'is_answered': question.get('is_answered', False)
                            }
                            questions.append(question_info)
                        
                        self.cache[cache_key] = questions
                        logger.info(f"Stack Overflow {len(questions)}개 질문 수집 완료")
                        return questions
                    else:
                        logger.error(f"Stack Exchange API 오류: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Stack Overflow 질문 수집 오류: {e}")
            return []

    def _calculate_relevance_score(self, text: str) -> float:
        """텍스트의 기술 관련성 점수 계산"""
        tech_keywords = [
            'python', 'javascript', 'react', 'node', 'ai', 'machine learning',
            'deep learning', 'api', 'database', 'cloud', 'docker', 'kubernetes',
            'programming', 'development', 'software', 'web', 'mobile', 'data',
            'algorithm', 'framework', 'library', 'github', 'open source'
        ]
        
        text_lower = text.lower()
        score = 0.0
        
        for keyword in tech_keywords:
            if keyword in text_lower:
                score += 1.0
        
        return score

    async def get_tech_summary(self, category: str = 'all') -> Dict[str, Any]:
        """기술 정보 종합 요약"""
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'category': category,
                'github_trending': [],
                'tech_news': [],
                'stackoverflow_questions': [],
                'popular_packages': {
                    'npm': [],
                    'pypi': []
                }
            }
            
            # 병렬로 데이터 수집
            tasks = []
            
            if category in ['all', 'github']:
                tasks.append(self.get_github_trending('python'))
                tasks.append(self.get_github_trending('javascript'))
            
            if category in ['all', 'news']:
                tasks.append(asyncio.create_task(asyncio.to_thread(self.parse_rss_feeds)))
            
            if category in ['all', 'stackoverflow']:
                tasks.append(self.get_stackoverflow_questions(['python', 'javascript']))
            
            # 인기 패키지 정보
            popular_npm = ['react', 'vue', 'express', 'lodash', 'axios']
            popular_pypi = ['requests', 'numpy', 'pandas', 'django', 'flask']
            
            if category in ['all', 'packages']:
                for pkg in popular_npm[:3]:  # 상위 3개만
                    tasks.append(self.get_npm_package_info(pkg))
                for pkg in popular_pypi[:3]:  # 상위 3개만
                    tasks.append(self.get_pypi_package_info(pkg))
            
            # 모든 작업 실행
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 정리
            result_index = 0
            
            if category in ['all', 'github']:
                summary['github_trending'].extend(results[result_index] if not isinstance(results[result_index], Exception) else [])
                result_index += 1
                summary['github_trending'].extend(results[result_index] if not isinstance(results[result_index], Exception) else [])
                result_index += 1
            
            if category in ['all', 'news']:
                tech_news = results[result_index] if not isinstance(results[result_index], Exception) else []
                summary['tech_news'] = [asdict(news) for news in tech_news[:20]]
                result_index += 1
            
            if category in ['all', 'stackoverflow']:
                summary['stackoverflow_questions'] = results[result_index] if not isinstance(results[result_index], Exception) else []
                result_index += 1
            
            if category in ['all', 'packages']:
                # NPM 패키지
                for i in range(3):
                    if result_index < len(results) and not isinstance(results[result_index], Exception):
                        pkg_info = results[result_index]
                        if pkg_info:
                            summary['popular_packages']['npm'].append(asdict(pkg_info))
                    result_index += 1
                
                # PyPI 패키지
                for i in range(3):
                    if result_index < len(results) and not isinstance(results[result_index], Exception):
                        pkg_info = results[result_index]
                        if pkg_info:
                            summary['popular_packages']['pypi'].append(asdict(pkg_info))
                    result_index += 1
            
            logger.info(f"기술 정보 요약 완료 (카테고리: {category})")
            return summary
            
        except Exception as e:
            logger.error(f"기술 정보 요약 오류: {e}")
            return {'error': str(e)}

    def format_tech_summary_message(self, summary: Dict[str, Any]) -> str:
        """기술 정보 요약을 텔레그램 메시지 형식으로 포맷"""
        try:
            message = "🚀 **최신 기술 정보 요약**\n\n"
            
            # GitHub 트렌딩
            if summary.get('github_trending'):
                message += "📈 **GitHub 트렌딩**\n"
                for repo in summary['github_trending'][:5]:
                    message += f"⭐ [{repo['name']}]({repo['url']}) - {repo['stars']}⭐\n"
                    if repo['description']:
                        message += f"   {repo['description'][:100]}...\n"
                message += "\n"
            
            # 기술 뉴스
            if summary.get('tech_news'):
                message += "📰 **최신 기술 뉴스**\n"
                for news in summary['tech_news'][:5]:
                    message += f"🔗 [{news['title'][:50]}...]({news['url']})\n"
                    message += f"   📅 {news['source']} | 점수: {news['score']}\n"
                message += "\n"
            
            # Stack Overflow 질문
            if summary.get('stackoverflow_questions'):
                message += "❓ **Stack Overflow 인기 질문**\n"
                for q in summary['stackoverflow_questions'][:3]:
                    message += f"🤔 [{q['title'][:60]}...]({q['url']})\n"
                    message += f"   👍 {q['score']} | 👀 {q['view_count']} | 💬 {q['answer_count']}\n"
                message += "\n"
            
            # 인기 패키지
            packages = summary.get('popular_packages', {})
            if packages.get('npm') or packages.get('pypi'):
                message += "📦 **인기 패키지**\n"
                
                if packages.get('npm'):
                    message += "🟨 **NPM:**\n"
                    for pkg in packages['npm'][:3]:
                        message += f"   📦 {pkg['name']} v{pkg['version']}\n"
                
                if packages.get('pypi'):
                    message += "🐍 **PyPI:**\n"
                    for pkg in packages['pypi'][:3]:
                        message += f"   📦 {pkg['name']} v{pkg['version']}\n"
            
            message += f"\n🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return message
            
        except Exception as e:
            logger.error(f"메시지 포맷 오류: {e}")
            return f"❌ 기술 정보 요약 생성 중 오류가 발생했습니다: {str(e)}"

# 전역 인스턴스
tech_updater = TechInfoUpdater() 