"""
팜솔라 AI_Solarbot - 지능형 웹 콘텐츠 분석 시스템
AI 기반 웹 콘텐츠 분석, 요약, 감정 분석, 품질 평가 기능 제공
"""

import os
import asyncio
import aiohttp
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from cachetools import TTLCache
from loguru import logger
from urllib.parse import urlparse, urljoin
import hashlib
from bs4 import BeautifulSoup
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

# 기존 시스템 모듈 import
from src.ai_handler import AIHandler
from src.web_search_ide import WebSearchIDE
from src.google_drive_handler import GoogleDriveHandler

@dataclass
class ContentAnalysisResult:
    """콘텐츠 분석 결과 데이터 클래스"""
    url: str
    title: str
    content_type: str  # news, blog, technical, academic, social, commercial, other
    summary: str
    key_points: List[str]
    sentiment_score: float  # -1.0 (매우 부정) ~ 1.0 (매우 긍정)
    sentiment_label: str  # positive, negative, neutral
    quality_score: float  # 0-100 점수
    topics: List[str]
    language: str
    reading_time: int  # 예상 읽기 시간 (분)
    complexity_level: str  # beginner, intermediate, advanced, expert
    analysis_timestamp: str
    ai_model_used: str
    word_count: int = 0
    image_count: int = 0
    link_count: int = 0
    error_message: str = ""
    
    # =================== 4단계 추가: 고급 감정 분석 필드 ===================
    detailed_emotions: Dict[str, float] = field(default_factory=dict)  # 세분화된 감정 점수
    emotion_intensity: float = 0.0  # 감정 강도 (0.0-1.0)
    emotion_confidence: float = 0.0  # 감정 분석 신뢰도 (0.0-1.0)
    dominant_emotion: str = ""  # 주요 감정
    emotion_distribution: Dict[str, float] = field(default_factory=dict)  # 감정 분포
    contextual_sentiment: str = ""  # 맥락적 감정 (사회적, 개인적 등)
    
    # =================== 4단계 추가: 고급 품질 평가 필드 ===================
    quality_dimensions: Dict[str, float] = field(default_factory=dict)  # 다차원 품질 점수
    quality_report: str = ""  # 품질 평가 리포트
    improvement_suggestions: List[str] = field(default_factory=list)  # 개선 제안사항
    content_reliability: float = 0.0  # 신뢰도 점수
    content_usefulness: float = 0.0  # 유용성 점수
    content_accuracy: float = 0.0  # 정확성 점수

@dataclass
class BatchAnalysisReport:
    """배치 분석 리포트 데이터 클래스"""
    total_analyzed: int
    success_count: int
    failed_count: int
    average_quality_score: float
    dominant_sentiment: str
    top_topics: List[Tuple[str, int]]  # (topic, count)
    content_type_distribution: Dict[str, int]
    analysis_summary: str
    processing_time: float
    report_timestamp: str

class IntelligentContentAnalyzer:
    """지능형 콘텐츠 분석 시스템"""
    
    def __init__(self):
        """초기화 - 기존 시스템과 연동"""
        try:
            # 기존 모듈 연동
            self.ai_handler = AIHandler()
            self.web_search = WebSearchIDE()
            self.drive_handler = GoogleDriveHandler()
            
            # 캐시 설정 (2시간 TTL)
            self.analysis_cache = TTLCache(maxsize=500, ttl=7200)
            self.batch_cache = TTLCache(maxsize=100, ttl=3600)
            
            # 분석 템플릿 설정 (확장된 콘텐츠 타입)
            self.content_types = {
                'news': ['뉴스', '기사', '보도', '언론', '신문', '속보', '취재'],
                'blog': ['블로그', '포스트', '개인', '일기', '후기', '리뷰', '경험'],
                'tech_doc': ['기술', '개발', '프로그래밍', 'API', '문서', '가이드', '레퍼런스'],
                'academic': ['논문', '연구', '학술', '저널', '학회', '실험', '분석'],
                'tutorial': ['튜토리얼', '따라하기', '단계', '방법', '배우기', '익히기', '설명'],
                'commercial': ['상품', '판매', '마케팅', '광고', '쇼핑', '구매', '할인'],
                'social': ['SNS', '소셜', '커뮤니티', '포럼', '댓글', '토론'],
                'general': ['일반', '기본', '정보', '내용', '글', '텍스트']
            }
            
            # 감정 분석 키워드
            self.sentiment_keywords = {
                'positive': ['좋은', '훌륭한', '완벽한', '성공', '만족', '추천', '최고', '우수한'],
                'negative': ['나쁜', '실망', '문제', '오류', '실패', '불만', '최악', '부족한'],
                'neutral': ['보통', '일반적인', '평범한', '표준', '기본']
            }
            
            # =================== 4단계 추가: 확장된 감정 분석 키워드 ===================
            # 세분화된 감정 카테고리 (Plutchik의 감정 모델 기반)
            self.detailed_emotion_keywords = {
                'joy': {  # 기쁨
                    'korean': ['기쁜', '행복한', '즐거운', '신나는', '유쾌한', '희망진진한', '환상적인', 
                              '놀라운', '멋진', '아름다운', '사랑스러운', '감동적인', '희망적인'],
                    'english': ['happy', 'joyful', 'excited', 'amazing', 'wonderful', 'fantastic', 
                               'delighted', 'cheerful', 'optimistic', 'thrilled'],
                    'weight': 1.0
                },
                'anger': {  # 분노
                    'korean': ['화나는', '짜증나는', '분노한', '열받는', '억울한', '불공평한', '악질적인',
                              '미친', '어이없는', '황당한', '답답한', '빡치는'],
                    'english': ['angry', 'furious', 'mad', 'irritated', 'frustrated', 'outraged',
                               'annoyed', 'infuriated', 'enraged'],
                    'weight': 1.2
                },
                'sadness': {  # 슬픔
                    'korean': ['슬픈', '우울한', '눈물나는', '안타까운', '쓸쓸한', '외로운', '허무한',
                              '절망적인', '비참한', '처참한', '마음아픈', '가슴아픈'],
                    'english': ['sad', 'depressed', 'melancholy', 'gloomy', 'sorrowful', 'tragic',
                               'heartbroken', 'miserable', 'dejected'],
                    'weight': 1.1
                },
                'fear': {  # 두려움
                    'korean': ['무서운', '두려운', '불안한', '걱정되는', '위험한', '겁나는', '떨리는',
                              '긴장되는', '조마조마한', '심각한', '위기적인'],
                    'english': ['scary', 'frightening', 'anxious', 'worried', 'nervous', 'terrifying',
                               'alarming', 'threatening', 'dangerous'],
                    'weight': 1.1
                },
                'surprise': {  # 놀람
                    'korean': ['놀라운', '깜짝', '예상외의', '뜻밖의', '신기한', '특이한', '이상한',
                              '충격적인', '반전', '의외의', '예측불가한'],
                    'english': ['surprising', 'shocking', 'unexpected', 'astonishing', 'amazing',
                               'incredible', 'unbelievable', 'stunning'],
                    'weight': 0.9
                },
                'disgust': {  # 혐오
                    'korean': ['역겨운', '징그러운', '더러운', '혐오스러운', '구역질나는', '끔찍한',
                              '지긋지긋한', '싫은', '불쾌한', '거부감드는'],
                    'english': ['disgusting', 'revolting', 'repulsive', 'gross', 'awful', 'terrible',
                               'horrible', 'nasty', 'offensive'],
                    'weight': 1.1
                },
                'trust': {  # 신뢰
                    'korean': ['믿을만한', '신뢰할만한', '확실한', '안전한', '든든한', '의지가되는',
                              '검증된', '보장된', '확신하는', '신용있는'],
                    'english': ['trustworthy', 'reliable', 'credible', 'dependable', 'secure',
                               'confident', 'certain', 'guaranteed'],
                    'weight': 1.0
                },
                'anticipation': {  # 기대
                    'korean': ['기대되는', '기다려지는', '설레는', '궁금한', '흥미로운', '관심있는',
                              '고대하는', '바라는', '희망하는', '예상하는'],
                    'english': ['anticipated', 'expected', 'exciting', 'interesting', 'hopeful',
                               'eager', 'looking forward', 'awaiting'],
                    'weight': 0.8
                }
            }
            
            # 감정 강도 지시어
            self.emotion_intensity_modifiers = {
                'high': ['매우', '정말', '진짜', '완전', '너무', '엄청', '극도로', '최고로', 'absolutely', 'extremely', 'incredibly', 'totally'],
                'medium': ['꽤', '상당히', '제법', '어느정도', 'quite', 'fairly', 'rather', 'somewhat'],
                'low': ['조금', '약간', '살짝', '다소', 'slightly', 'a bit', 'somewhat', 'little']
            }
            
            # 맥락적 감정 패턴
            self.contextual_patterns = {
                'sarcasm': [r'정말\s*좋네요', r'완전\s*대박이네요', r'역시\s*최고네요', r'참\s*잘했네요'],
                'irony': [r'그럼\s*그렇지', r'당연히\s*그렇겠죠', r'예상대로네요'],
                'emphasis': [r'!{2,}', r'[ㅋㅎ]{3,}', r'[ㅠㅜ]{2,}', r'[.]{3,}']
            }
            
            # 한국어 특화 감정 표현
            self.korean_emotion_expressions = {
                'positive_slang': ['대박', '쩔어', '굿', '짱', '킹왕짱', '개좋아', '레전드'],
                'negative_slang': ['별로', '노답', '헬', '망함', '쓰레기', '개별로', '최악'],
                'neutral_slang': ['그냥', '뭐', '별거없음', '평범', '무난']
            }
            
            # =================== 4단계 추가: 다차원 품질 평가 설정 ===================
            # 6개 품질 차원 정의
            self.quality_dimensions = {
                'reliability': {  # 신뢰도
                    'name': '신뢰도',
                    'description': '정보의 정확성과 출처의 신뢰성',
                    'weight': 1.2,
                    'indicators': {
                        'source_credibility': ['edu', 'gov', 'org', 'ac.kr', 'go.kr'],
                        'author_expertise': ['박사', '교수', '전문가', '연구원', 'PhD', 'Dr.'],
                        'citation_quality': ['참고문헌', '출처', '인용', 'reference', 'citation'],
                        'fact_checking': ['검증', '확인', '사실', '데이터', '통계']
                    }
                },
                'usefulness': {  # 유용성
                    'name': '유용성',
                    'description': '독자에게 실질적인 도움이 되는 정도',
                    'weight': 1.1,
                    'indicators': {
                        'practical_value': ['방법', '해결', '팁', '가이드', '단계', 'how-to', 'tutorial'],
                        'actionable_content': ['실행', '적용', '활용', '구현', '실제', 'action', 'implement'],
                        'problem_solving': ['문제', '해결책', '솔루션', '대안', 'solution', 'fix'],
                        'learning_value': ['배우기', '익히기', '이해', '학습', 'learn', 'understand']
                    }
                },
                'accuracy': {  # 정확성
                    'name': '정확성',
                    'description': '내용의 정확성과 오류 없음',
                    'weight': 1.3,
                    'indicators': {
                        'technical_precision': ['정확한', '정밀한', '엄밀한', 'accurate', 'precise'],
                        'error_indicators': ['오류', '틀린', '잘못된', '부정확한', 'error', 'wrong', 'incorrect'],
                        'verification_marks': ['검증됨', '확인됨', '테스트됨', 'verified', 'tested'],
                        'update_frequency': ['최신', '업데이트', '갱신', 'updated', 'latest', 'current']
                    }
                },
                'completeness': {  # 완성도
                    'name': '완성도',
                    'description': '내용의 완전성과 포괄성',
                    'weight': 1.0,
                    'indicators': {
                        'comprehensive_coverage': ['전체', '완전한', '포괄적', '종합적', 'comprehensive', 'complete'],
                        'detailed_explanation': ['자세한', '상세한', '구체적', 'detailed', 'specific'],
                        'example_provision': ['예제', '사례', '실례', 'example', 'case study'],
                        'step_by_step': ['단계별', '순서', '절차', 'step-by-step', 'procedure']
                    }
                },
                'readability': {  # 가독성
                    'name': '가독성',
                    'description': '읽기 쉽고 이해하기 쉬운 정도',
                    'weight': 0.9,
                    'indicators': {
                        'clear_structure': ['목차', '제목', '소제목', '구조', 'heading', 'structure'],
                        'simple_language': ['쉬운', '간단한', '명확한', 'simple', 'clear', 'easy'],
                        'visual_aids': ['그림', '도표', '차트', '이미지', 'image', 'chart', 'diagram'],
                        'formatting': ['목록', '번호', '강조', 'list', 'bullet', 'bold', 'highlight']
                    }
                },
                'originality': {  # 독창성
                    'name': '독창성',
                    'description': '독창적이고 새로운 관점의 제공',
                    'weight': 0.8,
                    'indicators': {
                        'unique_perspective': ['새로운', '독특한', '독창적', '혁신적', 'unique', 'innovative', 'novel'],
                        'personal_insight': ['개인적', '경험', '인사이트', '통찰', 'insight', 'experience'],
                        'creative_approach': ['창의적', '창조적', '참신한', 'creative', 'original'],
                        'thought_provoking': ['생각해볼', '고민', '성찰', 'thought-provoking', 'reflection']
                    }
                }
            }
            
            # 콘텐츠 타입별 품질 가중치
            self.content_type_quality_weights = {
                'news': {
                    'reliability': 1.5, 'accuracy': 1.4, 'usefulness': 1.0, 
                    'completeness': 1.1, 'readability': 1.0, 'originality': 0.7
                },
                'blog': {
                    'reliability': 0.9, 'accuracy': 1.0, 'usefulness': 1.2, 
                    'completeness': 0.9, 'readability': 1.3, 'originality': 1.4
                },
                'tech_doc': {
                    'reliability': 1.3, 'accuracy': 1.5, 'usefulness': 1.4, 
                    'completeness': 1.3, 'readability': 1.2, 'originality': 0.8
                },
                'academic': {
                    'reliability': 1.6, 'accuracy': 1.5, 'usefulness': 1.1, 
                    'completeness': 1.4, 'readability': 0.9, 'originality': 1.2
                },
                'tutorial': {
                    'reliability': 1.1, 'accuracy': 1.3, 'usefulness': 1.5, 
                    'completeness': 1.4, 'readability': 1.4, 'originality': 0.9
                },
                'commercial': {
                    'reliability': 0.8, 'accuracy': 1.0, 'usefulness': 1.3, 
                    'completeness': 1.0, 'readability': 1.2, 'originality': 1.1
                },
                'general': {
                    'reliability': 1.0, 'accuracy': 1.0, 'usefulness': 1.0, 
                    'completeness': 1.0, 'readability': 1.0, 'originality': 1.0
                }
            }
            
            # 언어 품질 평가 지표
            self.language_quality_indicators = {
                'grammar_errors': [
                    r'이/가\s+이/가',  # 조사 중복
                    r'을/를\s+을/를',  # 조사 중복
                    r'한다고\s+한다',  # 어미 중복
                    r'있다\s+있다',   # 동사 중복
                ],
                'spelling_errors': [
                    r'됬다',  # 됐다
                    r'않됨',  # 안됨
                    r'되여',  # 되어
                    r'어떻해',  # 어떻게
                ],
                'good_expressions': [
                    r'따라서', r'그러므로', r'결과적으로',  # 논리적 연결
                    r'예를\s*들어', r'구체적으로', r'실제로',  # 구체화
                    r'반면에', r'한편', r'그러나',  # 대조
                    r'첫째', r'둘째', r'마지막으로'  # 순서
                ]
            }
            
            # 복잡도 판단 기준
            self.complexity_indicators = {
                'beginner': ['기초', '입문', '초보', '시작', '처음'],
                'intermediate': ['중급', '일반', '실무', '활용'],
                'advanced': ['고급', '심화', '전문', '응용'],
                'expert': ['전문가', '마스터', '고수', '전문']
            }
            
            # 분석 통계
            self.analysis_stats = {
                'total_analyzed': 0,
                'successful_analyses': 0,
                'failed_analyses': 0,
                'average_processing_time': 0.0,
                'most_common_content_type': '',
                'average_quality_score': 0.0
            }
            
            logger.info("IntelligentContentAnalyzer 초기화 완료")
            
        except Exception as e:
            logger.error(f"IntelligentContentAnalyzer 초기화 실패: {e}")
            raise
    
    def _generate_cache_key(self, url: str, analysis_type: str = "full") -> str:
        """캐시 키 생성"""
        content = f"{url}_{analysis_type}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _detect_content_type(self, title: str, content: str, url: str, html_soup=None) -> str:
        """고급 콘텐츠 타입 감지 - web_search_ide.py 패턴 확장"""
        try:
            text = f"{title} {content}".lower()
            domain = urlparse(url).netloc.lower()
            
            # 1. 도메인 기반 정확한 분류 (web_search_ide 패턴 확장)
            domain_types = {
                # 뉴스 사이트
                'news': ['news', 'naver.com', 'daum.net', 'chosun.com', 'joongang.co.kr', 
                        'donga.com', 'hani.co.kr', 'ytn.co.kr', 'sbs.co.kr', 'kbs.co.kr'],
                
                # 기술 문서 및 개발
                'tech_doc': ['github.com', 'stackoverflow.com', 'dev.to', 'docs.python.org',
                           'developer.mozilla.org', 'reactjs.org', 'nodejs.org', 'django.com'],
                
                # 블로그 플랫폼
                'blog': ['medium.com', 'tistory.com', 'wordpress', 'blogger.com', 'velog.io',
                        'brunch.co.kr', 'steemit.com'],
                
                # 학술 및 연구
                'academic': ['arxiv.org', 'scholar.google', 'researchgate.net', 'ieee.org',
                           'acm.org', 'springer.com', 'sciencedirect.com'],
                
                # 튜토리얼 및 교육
                'tutorial': ['codecademy.com', 'freecodecamp.org', 'w3schools.com', 
                           'tutorialspoint.com', 'coursera.org', 'udemy.com'],
                
                # 상업적 사이트
                'commercial': ['amazon.com', 'ebay.com', 'coupang.com', '11st.co.kr',
                             'gmarket.co.kr', 'interpark.com']
            }
            
            # 도메인 매칭 검사
            for content_type, domains in domain_types.items():
                if any(domain_name in domain for domain_name in domains):
                    return content_type
            
            # 2. URL 경로 분석
            url_path = urlparse(url).path.lower()
            if any(path_indicator in url_path for path_indicator in ['/blog/', '/post/', '/article/']):
                return 'blog'
            elif any(path_indicator in url_path for path_indicator in ['/docs/', '/documentation/', '/api/']):
                return 'tech_doc'
            elif any(path_indicator in url_path for path_indicator in ['/tutorial/', '/guide/', '/how-to/']):
                return 'tutorial'
            elif any(path_indicator in url_path for path_indicator in ['/news/', '/press/', '/article/']):
                return 'news'
            
            # 3. 콘텐츠 구조 분석 (HTML 메타데이터 활용)
            if html_soup:
                # 메타 태그 분석
                meta_tags = html_soup.find_all('meta')
                for meta in meta_tags:
                    content_attr = meta.get('content', '').lower()
                    name_attr = meta.get('name', '').lower()
                    property_attr = meta.get('property', '').lower()
                    
                    if 'article' in property_attr or 'news' in content_attr:
                        return 'news'
                    elif 'blog' in content_attr or 'blog' in name_attr:
                        return 'blog'
                    elif 'documentation' in content_attr:
                        return 'tech_doc'
                
                # 스키마 마크업 분석
                schema_elements = html_soup.find_all(attrs={"itemtype": True})
                for element in schema_elements:
                    itemtype = element.get('itemtype', '').lower()
                    if 'newsarticle' in itemtype:
                        return 'news'
                    elif 'blogarticle' in itemtype:
                        return 'blog'
                    elif 'technicalarticle' in itemtype:
                        return 'tech_doc'
            
            # 4. 고급 키워드 기반 분석
            advanced_content_patterns = {
                'news': {
                    'keywords': ['기자', '뉴스', '보도', '취재', '언론', '신문', '방송', '속보'],
                    'patterns': [r'\d{4}년 \d{1,2}월 \d{1,2}일', r'기자\s*=', r'뉴스\s*\|'],
                    'weight': 2.0
                },
                'tech_doc': {
                    'keywords': ['API', '함수', '메서드', '클래스', '라이브러리', '프레임워크', 
                               '코드', '예제', 'import', 'function', 'class', 'def'],
                    'patterns': [r'```\w*\n', r'<code>', r'def\s+\w+\(', r'function\s+\w+'],
                    'weight': 2.5
                },
                'blog': {
                    'keywords': ['개인적으로', '생각해보니', '후기', '리뷰', '경험', '느낌', 
                               '추천', '개인', '일상', '블로그'],
                    'patterns': [r'안녕하세요', r'오늘은', r'개인적으로'],
                    'weight': 1.5
                },
                'academic': {
                    'keywords': ['논문', '연구', '학술', '저널', '학회', '참고문헌', '인용',
                               '실험', '분석', '결과', 'abstract', 'introduction', 'conclusion'],
                    'patterns': [r'\[\d+\]', r'et al\.', r'Abstract:', r'References:'],
                    'weight': 3.0
                },
                'tutorial': {
                    'keywords': ['단계', '따라하기', '튜토리얼', '가이드', '방법', '설명',
                               '처음', '시작', '배우기', '익히기'],
                    'patterns': [r'1\.\s', r'첫\s*번째', r'단계\s*\d+', r'Step\s*\d+'],
                    'weight': 2.0
                },
                'commercial': {
                    'keywords': ['구매', '판매', '가격', '할인', '배송', '상품', '주문',
                               '결제', '쇼핑', '마케팅'],
                    'patterns': [r'\d+원', r'\$\d+', r'할인\s*\d+%', r'무료\s*배송'],
                    'weight': 1.8
                }
            }
            
            # 각 타입별 점수 계산
            type_scores = {}
            for content_type, pattern_data in advanced_content_patterns.items():
                score = 0
                
                # 키워드 매칭
                keyword_matches = sum(1 for keyword in pattern_data['keywords'] if keyword in text)
                score += keyword_matches * pattern_data['weight']
                
                # 정규식 패턴 매칭
                pattern_matches = 0
                for pattern in pattern_data['patterns']:
                    if re.search(pattern, content, re.IGNORECASE):
                        pattern_matches += 1
                score += pattern_matches * pattern_data['weight'] * 1.5
                
                type_scores[content_type] = score
            
            # 5. 최종 결정
            if type_scores:
                max_score = max(type_scores.values())
                if max_score > 2.0:  # 임계값 설정
                    return max(type_scores, key=type_scores.get)
            
            # 6. 기본 키워드 기반 분류 (fallback)
            for content_type, keywords in self.content_types.items():
                score = sum(1 for keyword in keywords if keyword in text)
                if score >= 2:  # 최소 2개 키워드 매칭
                    return content_type
            
            return 'general'
            
        except Exception as e:
            logger.error(f"콘텐츠 타입 감지 오류: {e}")
            return 'general'
    
    def _calculate_sentiment_score(self, text: str) -> Tuple[float, str]:
        """감정 점수 계산"""
        try:
            text_lower = text.lower()
            
            positive_count = sum(1 for word in self.sentiment_keywords['positive'] if word in text_lower)
            negative_count = sum(1 for word in self.sentiment_keywords['negative'] if word in text_lower)
            neutral_count = sum(1 for word in self.sentiment_keywords['neutral'] if word in text_lower)
            
            total_sentiment_words = positive_count + negative_count + neutral_count
            
            if total_sentiment_words == 0:
                return 0.0, 'neutral'
            
            # 감정 점수 계산 (-1.0 ~ 1.0)
            sentiment_score = (positive_count - negative_count) / total_sentiment_words
            
            # 라벨 결정
            if sentiment_score > 0.2:
                label = 'positive'
            elif sentiment_score < -0.2:
                label = 'negative'
            else:
                label = 'neutral'
            
            return sentiment_score, label
            
        except Exception as e:
            logger.error(f"감정 점수 계산 오류: {e}")
            return 0.0, 'neutral'
    
    # =================== 4단계 추가: 고급 감정 분석 메서드 ===================
    
    def _calculate_advanced_sentiment_score(self, text: str) -> Dict[str, Any]:
        """고급 감정 분석 - 세분화된 감정 감지"""
        try:
            text_lower = text.lower()
            
            # 1. 세분화된 감정 점수 계산
            detailed_emotions = {}
            total_emotion_score = 0
            
            for emotion, keywords_data in self.detailed_emotion_keywords.items():
                emotion_score = 0
                
                # 한국어 키워드 매칭
                korean_matches = sum(1 for keyword in keywords_data['korean'] if keyword in text_lower)
                english_matches = sum(1 for keyword in keywords_data['english'] if keyword in text_lower)
                
                # 가중치 적용
                emotion_score = (korean_matches + english_matches) * keywords_data['weight']
                detailed_emotions[emotion] = emotion_score
                total_emotion_score += emotion_score
            
            # 2. 한국어 특화 슬랭 분석
            slang_bonus = 0
            for slang_type, slang_words in self.korean_emotion_expressions.items():
                matches = sum(1 for slang in slang_words if slang in text_lower)
                if matches > 0:
                    if 'positive' in slang_type:
                        detailed_emotions['joy'] = detailed_emotions.get('joy', 0) + matches * 1.5
                        slang_bonus += matches * 0.3
                    elif 'negative' in slang_type:
                        detailed_emotions['anger'] = detailed_emotions.get('anger', 0) + matches * 1.2
                        slang_bonus += matches * 0.2
            
            # 3. 감정 강도 분석
            intensity_score = self._calculate_emotion_intensity(text_lower)
            
            # 4. 맥락적 감정 분석
            contextual_info = self._analyze_contextual_sentiment(text)
            
            # 5. 정규화 및 주요 감정 결정
            if total_emotion_score > 0:
                # 감정 분포 정규화
                emotion_distribution = {
                    emotion: score / total_emotion_score 
                    for emotion, score in detailed_emotions.items() 
                    if score > 0
                }
                
                # 주요 감정 결정
                dominant_emotion = max(detailed_emotions, key=detailed_emotions.get) if detailed_emotions else 'neutral'
                
                # 감정 신뢰도 계산
                max_score = max(detailed_emotions.values()) if detailed_emotions else 0
                confidence = min(1.0, (max_score / total_emotion_score) * 2) if total_emotion_score > 0 else 0
                
            else:
                emotion_distribution = {}
                dominant_emotion = 'neutral'
                confidence = 0.5
            
            # 6. 기존 시스템과의 호환성을 위한 기본 감정 점수 계산
            basic_sentiment_score, basic_sentiment_label = self._calculate_sentiment_score(text)
            
            return {
                'detailed_emotions': detailed_emotions,
                'emotion_distribution': emotion_distribution,
                'dominant_emotion': dominant_emotion,
                'emotion_intensity': intensity_score,
                'emotion_confidence': confidence,
                'contextual_sentiment': contextual_info['type'],
                'basic_sentiment_score': basic_sentiment_score,
                'basic_sentiment_label': basic_sentiment_label,
                'slang_detected': slang_bonus > 0,
                'analysis_method': 'advanced_multilayer'
            }
            
        except Exception as e:
            logger.error(f"고급 감정 분석 오류: {e}")
            # 실패 시 기본 분석으로 fallback
            basic_score, basic_label = self._calculate_sentiment_score(text)
            return {
                'detailed_emotions': {},
                'emotion_distribution': {},
                'dominant_emotion': 'neutral',
                'emotion_intensity': 0.0,
                'emotion_confidence': 0.0,
                'contextual_sentiment': 'unknown',
                'basic_sentiment_score': basic_score,
                'basic_sentiment_label': basic_label,
                'slang_detected': False,
                'analysis_method': 'fallback_basic'
            }
    
    def _calculate_emotion_intensity(self, text: str) -> float:
        """감정 강도 계산"""
        try:
            intensity_score = 0.5  # 기본 강도
            
            # 강도 지시어 검사
            for intensity_level, modifiers in self.emotion_intensity_modifiers.items():
                matches = sum(1 for modifier in modifiers if modifier in text)
                if matches > 0:
                    if intensity_level == 'high':
                        intensity_score += matches * 0.3
                    elif intensity_level == 'medium':
                        intensity_score += matches * 0.15
                    elif intensity_level == 'low':
                        intensity_score -= matches * 0.1
            
            # 문장부호를 통한 강도 분석
            exclamation_count = text.count('!')
            question_count = text.count('?')
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
            
            intensity_score += min(0.2, exclamation_count * 0.05)  # 느낌표
            intensity_score += min(0.1, question_count * 0.03)     # 물음표
            intensity_score += min(0.15, caps_ratio * 0.5)         # 대문자 비율
            
            # 반복 문자 패턴 (ㅋㅋㅋ, ㅠㅠㅠ 등)
            repeated_patterns = len(re.findall(r'[ㅋㅎㅠㅜ]{3,}', text))
            intensity_score += min(0.2, repeated_patterns * 0.1)
            
            return min(1.0, max(0.0, intensity_score))
            
        except Exception as e:
            logger.error(f"감정 강도 계산 오류: {e}")
            return 0.5
    
    def _analyze_contextual_sentiment(self, text: str) -> Dict[str, Any]:
        """맥락적 감정 분석"""
        try:
            context_info = {
                'type': 'direct',
                'confidence': 1.0,
                'detected_patterns': []
            }
            
            # 반어법/비꼼 감지
            for pattern in self.contextual_patterns['sarcasm']:
                if re.search(pattern, text, re.IGNORECASE):
                    context_info['type'] = 'sarcastic'
                    context_info['confidence'] = 0.7
                    context_info['detected_patterns'].append('sarcasm')
                    break
            
            # 아이러니 감지
            for pattern in self.contextual_patterns['irony']:
                if re.search(pattern, text, re.IGNORECASE):
                    context_info['type'] = 'ironic'
                    context_info['confidence'] = 0.8
                    context_info['detected_patterns'].append('irony')
                    break
            
            # 강조 패턴 감지
            emphasis_count = 0
            for pattern in self.contextual_patterns['emphasis']:
                emphasis_count += len(re.findall(pattern, text))
            
            if emphasis_count > 0:
                context_info['detected_patterns'].append('emphasis')
                context_info['confidence'] = min(1.0, context_info['confidence'] + emphasis_count * 0.1)
            
            # 문장 구조 분석
            sentences = re.split(r'[.!?]', text)
            if len(sentences) > 3:
                context_info['structure'] = 'complex'
            elif len(sentences) > 1:
                context_info['structure'] = 'moderate'
            else:
                context_info['structure'] = 'simple'
            
            return context_info
            
        except Exception as e:
            logger.error(f"맥락적 감정 분석 오류: {e}")
            return {
                'type': 'unknown',
                'confidence': 0.5,
                'detected_patterns': [],
                'structure': 'unknown'
            }
    
    async def _perform_ai_sentiment_analysis(self, text: str, content_type: str) -> Dict[str, Any]:
        """AI 기반 감정 분석"""
        try:
            if not hasattr(self, 'ai_handler') or not self.ai_handler:
                return {}
            
            # AI 감정 분석 프롬프트
            prompt = f"""다음 텍스트의 감정을 정확히 분석해주세요.

텍스트: "{text[:500]}..."

다음 형식으로 응답해주세요:
1. 주요 감정: [joy/anger/sadness/fear/surprise/disgust/trust/anticipation/neutral 중 하나]
2. 감정 강도: [0.0-1.0 사이의 숫자]
3. 감정 신뢰도: [0.0-1.0 사이의 숫자]
4. 세부 감정 분포: [각 감정별 점수]
5. 맥락적 특징: [직접적/반어적/아이러니적/강조적]

콘텐츠 타입: {content_type}
언어: 한국어 중심 분석
"""
            
            ai_response = await self.ai_handler.get_ai_response(prompt)
            
            if ai_response and ai_response.strip():
                return self._parse_ai_sentiment_response(ai_response)
            
            return {}
            
        except Exception as e:
            logger.error(f"AI 감정 분석 오류: {e}")
            return {}
    
    def _parse_ai_sentiment_response(self, response: str) -> Dict[str, Any]:
        """AI 감정 분석 응답 파싱"""
        try:
            result = {
                'ai_dominant_emotion': 'neutral',
                'ai_intensity': 0.5,
                'ai_confidence': 0.5,
                'ai_distribution': {},
                'ai_context': 'direct'
            }
            
            lines = response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                if '주요 감정:' in line:
                    emotion = line.split(':')[1].strip()
                    if emotion in ['joy', 'anger', 'sadness', 'fear', 'surprise', 'disgust', 'trust', 'anticipation', 'neutral']:
                        result['ai_dominant_emotion'] = emotion
                
                elif '감정 강도:' in line:
                    try:
                        intensity = float(line.split(':')[1].strip())
                        result['ai_intensity'] = max(0.0, min(1.0, intensity))
                    except:
                        pass
                
                elif '감정 신뢰도:' in line:
                    try:
                        confidence = float(line.split(':')[1].strip())
                        result['ai_confidence'] = max(0.0, min(1.0, confidence))
                    except:
                        pass
                
                elif '맥락적 특징:' in line:
                    context = line.split(':')[1].strip()
                    if any(ctx in context for ctx in ['반어', '아이러니', '강조', '직접']):
                        result['ai_context'] = context
            
            return result
            
        except Exception as e:
            logger.error(f"AI 감정 분석 응답 파싱 오류: {e}")
            return {}
    
    def _calculate_quality_score(self, title: str, content: str, url: str) -> float:
        """품질 점수 계산 (0-100)"""
        try:
            score = 50.0  # 기본 점수
            
            # 제목 품질 (20점)
            if title and len(title.strip()) > 10:
                score += 10
            if title and len(title.strip()) > 20:
                score += 10
            
            # 콘텐츠 길이 (30점)
            content_length = len(content)
            if content_length > 500:
                score += 10
            if content_length > 1500:
                score += 10
            if content_length > 3000:
                score += 10
            
            # 구조화 정도 (20점)
            if '.' in content or '!' in content or '?' in content:
                score += 5
            if '\n' in content:  # 단락 구분
                score += 5
            if any(marker in content for marker in ['1.', '2.', '-', '*']):  # 목록 구조
                score += 10
            
            # URL 신뢰도 (30점)
            domain = urlparse(url).netloc.lower()
            if any(trusted in domain for trusted in ['edu', 'gov', 'org']):
                score += 15
            elif any(known in domain for known in ['naver', 'google', 'github', 'stackoverflow']):
                score += 10
            elif not any(suspicious in domain for suspicious in ['bit.ly', 'tinyurl']):
                score += 5
            
            # HTTPS 사용
            if url.startswith('https'):
                score += 5
            
            return min(100.0, max(0.0, score))
            
        except Exception as e:
            logger.error(f"품질 점수 계산 오류: {e}")
            return 50.0
    
    def _determine_complexity_level(self, content: str) -> str:
        """복잡도 레벨 결정"""
        try:
            text_lower = content.lower()
            
            # 각 레벨별 점수 계산
            level_scores = {}
            for level, keywords in self.complexity_indicators.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                level_scores[level] = score
            
            # 최고 점수 레벨 반환
            if max(level_scores.values()) == 0:
                # 키워드가 없으면 콘텐츠 길이로 판단
                content_length = len(content)
                if content_length < 1000:
                    return 'beginner'
                elif content_length < 3000:
                    return 'intermediate'
                elif content_length < 5000:
                    return 'advanced'
                else:
                    return 'expert'
            
            return max(level_scores, key=level_scores.get)
            
        except Exception as e:
            logger.error(f"복잡도 레벨 결정 오류: {e}")
            return 'intermediate'
    
    def _calculate_reading_time(self, content: str) -> int:
        """예상 읽기 시간 계산 (분)"""
        try:
            # 한국어 평균 읽기 속도: 분당 250자
            # 영어 평균 읽기 속도: 분당 200단어 (약 1000자)
            
            korean_chars = len(re.findall(r'[가-힣]', content))
            english_words = len(re.findall(r'[a-zA-Z]+', content))
            
            korean_time = korean_chars / 250
            english_time = english_words / 200
            
            total_time = korean_time + english_time
            return max(1, int(total_time))  # 최소 1분
            
        except Exception as e:
            logger.error(f"읽기 시간 계산 오류: {e}")
            return 1
    
    def _extract_topics(self, content: str, max_topics: int = 5) -> List[str]:
        """주요 토픽 추출"""
        try:
            # 간단한 키워드 추출 (추후 AI 기반으로 개선)
            text = content.lower()
            
            # 기술 관련 키워드
            tech_keywords = ['python', 'javascript', 'react', 'django', 'api', 'database', 
                           'ai', 'machine learning', 'deep learning', 'blockchain']
            
            # 비즈니스 키워드
            business_keywords = ['마케팅', '비즈니스', '경영', '전략', '투자', '창업']
            
            # 일반 키워드
            general_keywords = ['교육', '건강', '여행', '음식', '문화', '스포츠']
            
            all_keywords = tech_keywords + business_keywords + general_keywords
            
            found_topics = []
            for keyword in all_keywords:
                if keyword in text and len(found_topics) < max_topics:
                    found_topics.append(keyword)
            
            return found_topics
            
        except Exception as e:
            logger.error(f"토픽 추출 오류: {e}")
            return []
    
    def _detect_language(self, content: str) -> str:
        """언어 감지"""
        try:
            korean_chars = len(re.findall(r'[가-힣]', content))
            english_chars = len(re.findall(r'[a-zA-Z]', content))
            
            if korean_chars > english_chars:
                return 'korean'
            elif english_chars > korean_chars * 2:
                return 'english'
            else:
                return 'mixed'
                
        except Exception as e:
            logger.error(f"언어 감지 오류: {e}")
            return 'unknown'
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """분석 통계 반환"""
        return {
            "총_분석_수": self.analysis_stats['total_analyzed'],
            "성공_분석_수": self.analysis_stats['successful_analyses'],
            "실패_분석_수": self.analysis_stats['failed_analyses'],
            "평균_처리시간": f"{self.analysis_stats['average_processing_time']:.2f}초",
            "평균_품질점수": f"{self.analysis_stats['average_quality_score']:.1f}점",
            "캐시_적중률": f"{len(self.analysis_cache)}/{self.analysis_stats['total_analyzed'] or 1}",
            "시스템_상태": "정상 운영중"
        }
    
    def get_system_status(self) -> str:
        """시스템 상태 문자열 반환"""
        stats = self.get_analysis_stats()
        
        return f"""🔧 **시스템 상태**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **분석 통계**:
• 총 분석 수: {stats['총_분석_수']}건
• 성공률: {stats['성공_분석_수']}/{stats['총_분석_수']}건
• 평균 처리시간: {stats['평균_처리시간']}
• 평균 품질점수: {stats['평균_품질점수']}

💾 **캐시 상태**:
• 분석 캐시: {len(self.analysis_cache)}개 항목
• 배치 캐시: {len(self.batch_cache)}개 항목

🌐 **연동 모듈**:
• AI Handler: ✅ 연결됨
• Web Search IDE: ✅ 연결됨
• Google Drive: ✅ 연결됨

🔋 **시스템**: {stats['시스템_상태']}"""

    def clear_cache(self):
        """캐시 초기화"""
        self.analysis_cache.clear()
        self.batch_cache.clear()
        logger.info("분석 캐시 초기화 완료")

    # =================== 대화형 가이드 시스템 (3단계) ===================
    
    async def chat_analyze_content(self, user_message: str, context: Dict = None) -> str:
        """대화형 콘텐츠 분석 - ChatGPT 스타일"""
        try:
            # URL 자동 감지
            urls = self._extract_urls_from_message(user_message)
            
            if urls:
                # URL이 있으면 자동 분석 후 가이드 제공
                url = urls[0]
                analysis = await self.analyze_web_content(url, use_ai=True)
                
                if analysis and not analysis.error_message:
                    return self._generate_conversational_response(analysis, user_message)
                else:
                    return f"죄송합니다. '{url}' 분석 중 오류가 발생했습니다. URL을 다시 확인해주세요. 🔍"
            
            elif any(keyword in user_message.lower() for keyword in ['분석', '요약', '정보', '내용']):
                return self._generate_analysis_help_message()
            
            elif any(keyword in user_message.lower() for keyword in ['명령어', '기능', '도움말']):
                return self._generate_command_guide()
            
            else:
                return self._generate_general_help_message()
                
        except Exception as e:
            logger.error(f"대화형 분석 오류: {e}")
            return "죄송합니다. 처리 중 오류가 발생했습니다. 다시 시도해주세요. 😅"
    
    def _extract_urls_from_message(self, message: str) -> List[str]:
        """메시지에서 URL 추출"""
        url_pattern = r'https?://[^\\s<>\"\\{\\}\\|\\\\\\^`\\[\\]]+'
        return re.findall(url_pattern, message)
    
    def _generate_conversational_response(self, analysis: ContentAnalysisResult, user_message: str) -> str:
        """대화형 분석 응답 생성 - 기본 결과 + 전문 기능 안내"""
        
        # 감정 이모지 매핑
        sentiment_emoji = {
            'positive': '😊',
            'negative': '😔', 
            'neutral': '😐'
        }
        
        # 품질 등급 매핑
        if analysis.quality_score >= 80:
            quality_grade = "⭐ 매우 우수"
        elif analysis.quality_score >= 60:
            quality_grade = "👍 양호"
        else:
            quality_grade = "⚠️ 보통"
        
        # 기본 응답 생성
        response = f"""📱 **{analysis.title}** 분석 완료!

📊 **품질점수**: {analysis.quality_score:.1f}/100 ({quality_grade})
{sentiment_emoji.get(analysis.sentiment_label, '😐')} **감정**: {analysis.sentiment_label} ({analysis.sentiment_score:.1f}점)
⏱️ **읽기시간**: {analysis.reading_time}분
📝 **요약**: {analysis.summary[:150]}{'...' if len(analysis.summary) > 150 else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 **더 정확하고 전문적인 분석을 원하신다면**:

💎 `/analyze_url {analysis.url}` - 완전한 상세 분석 (구조화된 데이터)
🎯 `/sentiment_only {analysis.url}` - 감정분석만 정밀하게
📊 `/quality_check {analysis.url}` - 품질 평가 세부 항목
🔍 `/extract_topics {analysis.url}` - 주제 및 키워드 추출
📈 `/complexity_analysis {analysis.url}` - 복잡도 상세 분석

📚 **배치 분석**:
💼 `/batch_analyze url1,url2,url3` - 여러 URL 동시 분석
📋 `/compare_urls url1,url2` - 두 콘텐츠 비교 분석

🤖 **AI 심화 분석**:
🧠 `/ai_deep_analysis {analysis.url}` - AI 기반 심층 분석
📖 `/generate_summary {analysis.url}` - AI 맞춤형 요약 생성

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 **팁**: 명령어를 사용하면 더 정확하고 전문적인 분석 결과를 얻을 수 있어요!
"""
        
        # 사용자 메시지에 따른 추가 안내
        if '요약' in user_message:
            response += "\n\n🎯 **요약에 특화된 명령어**: `/generate_summary {analysis.url}`"
        elif '감정' in user_message:
            response += "\n\n🎯 **감정분석에 특화된 명령어**: `/sentiment_only {analysis.url}`"
        elif '품질' in user_message:
            response += "\n\n🎯 **품질분석에 특화된 명령어**: `/quality_check {analysis.url}`"
        
        return response
    
    def _generate_analysis_help_message(self) -> str:
        """분석 도움말 메시지 생성"""
        return """🔍 **웹 콘텐츠 분석 도움말**

📌 **사용법**:
1️⃣ **간단 분석**: URL을 포함한 메시지 전송
   예: "이 사이트 분석해줘 https://example.com"

2️⃣ **전문 분석**: 명령어 사용
   예: `/analyze_url https://example.com`

🎯 **지원하는 콘텐츠 타입**:
• 📰 뉴스 기사 (네이버뉴스, 조선일보 등)
• 💻 기술 블로그 (velog, 티스토리, Medium 등)
• 📚 공식 문서 (GitHub, Stack Overflow 등)
• 🛒 쇼핑몰 (네이버 스마트스토어, 쿠팡 등)
• 🎓 학술 자료 (논문, 연구보고서 등)

💡 **분석 항목**:
• 콘텐츠 요약 및 핵심 포인트
• 감정 분석 (긍정/부정/중립)
• 품질 점수 (신뢰도, 유용성)
• 읽기 시간 및 복잡도
• 주제 및 키워드 추출

URL을 알려주시면 바로 분석해드릴게요! 😊"""
    
    def _generate_command_guide(self) -> str:
        """명령어 가이드 생성"""
        return """🤖 **전문 분석 명령어 가이드**

🔥 **기본 분석 명령어**:
• `/analyze_url <URL>` - 완전한 웹 콘텐츠 분석
• `/quick_analysis <URL>` - 빠른 기본 분석
• `/sentiment_only <URL>` - 감정분석만 수행
• `/quality_check <URL>` - 품질 평가 상세 분석

📊 **고급 분석 명령어**:
• `/extract_topics <URL>` - 주제/키워드 추출
• `/complexity_analysis <URL>` - 복잡도 상세 분석
• `/structure_analysis <URL>` - HTML 구조 분석
• `/metadata_extract <URL>` - 메타데이터 추출

🚀 **배치 처리 명령어**:
• `/batch_analyze <URL1,URL2,URL3>` - 여러 URL 동시 분석
• `/compare_urls <URL1,URL2>` - 두 콘텐츠 비교
• `/batch_sentiment <URL1,URL2,URL3>` - 배치 감정분석

🧠 **AI 심화 분석 명령어**:
• `/ai_deep_analysis <URL>` - AI 기반 심층 분석
• `/generate_summary <URL>` - AI 맞춤형 요약
• `/extract_insights <URL>` - 인사이트 추출
• `/content_recommendations <URL>` - 관련 콘텐츠 추천

⚙️ **시스템 명령어**:
• `/analysis_stats` - 분석 통계 조회
• `/clear_cache` - 캐시 초기화
• `/system_status` - 시스템 상태 확인

💡 **사용 팁**:
- 명령어는 더 정확하고 구조화된 결과를 제공합니다
- 대화형으로 물어보시면 적절한 명령어를 추천해드려요
- 배치 명령어로 여러 콘텐츠를 효율적으로 분석할 수 있습니다"""
    
    def _generate_general_help_message(self) -> str:
        """일반 도움말 메시지 생성"""
        return """👋 **팜솔라 AI 콘텐츠 분석봇입니다!**

🌟 **할 수 있는 일**:
• 웹사이트 내용 분석 및 요약
• 감정 분석 (긍정/부정/중립)
• 콘텐츠 품질 평가
• 주제 및 키워드 추출
• 여러 사이트 비교 분석

💬 **사용법**:
1️⃣ **간단하게**: "이 사이트 분석해줘 https://example.com"
2️⃣ **전문적으로**: `/analyze_url https://example.com`

🔍 **더 많은 도움이 필요하시면**:
• "분석 도움말" - 분석 기능 상세 설명
• "명령어 가이드" - 전문 명령어 목록
• URL을 포함한 메시지 - 바로 분석 시작

무엇을 도와드릴까요? 😊"""

    # =================== 결과 포맷팅 메서드 ===================
    
    def format_analysis_result(self, analysis: ContentAnalysisResult, format_type: str = "detailed") -> str:
        """분석 결과 포맷팅"""
        try:
            if format_type == "simple":
                return self._format_simple_result(analysis)
            elif format_type == "detailed":
                return self._format_detailed_result(analysis)
            elif format_type == "json":
                return self._format_json_result(analysis)
            else:
                return self._format_detailed_result(analysis)
        except Exception as e:
            logger.error(f"결과 포맷팅 오류: {e}")
            return f"결과 포맷팅 중 오류 발생: {str(e)}"
    
    def _format_simple_result(self, analysis: ContentAnalysisResult) -> str:
        """간단한 결과 포맷"""
        return f"""📌 **{analysis.title}**
🏷️ 타입: {analysis.content_type} | 📊 품질: {analysis.quality_score:.1f}점
😊 감정: {analysis.sentiment_label} | ⏱️ 읽기시간: {analysis.reading_time}분
📝 요약: {analysis.summary}"""
    
    def _format_detailed_result(self, analysis: ContentAnalysisResult) -> str:
        """상세한 결과 포맷"""
        key_points_text = "\n".join([f"• {point}" for point in analysis.key_points])
        topics_text = " ".join([f"#{topic}" for topic in analysis.topics[:5]])
        
        return f"""📱 **{analysis.title}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 **URL**: {analysis.url}
🏷️ **콘텐츠 타입**: {analysis.content_type}
📊 **품질점수**: {analysis.quality_score:.1f}/100
😊 **감정분석**: {analysis.sentiment_label} ({analysis.sentiment_score:.1f}점)
🌐 **언어**: {analysis.language}
⏱️ **읽기시간**: {analysis.reading_time}분
📈 **복잡도**: {analysis.complexity_level}
📝 **단어수**: {analysis.word_count}개
🖼️ **이미지**: {analysis.image_count}개
🔗 **링크**: {analysis.link_count}개

📖 **AI 요약**:
{analysis.summary}

🔑 **핵심 포인트**:
{key_points_text}

🏷️ **주요 토픽**: {topics_text}

🤖 **분석 모델**: {analysis.ai_model_used}
⏰ **분석시간**: {analysis.analysis_timestamp}"""
    
    def _format_json_result(self, analysis: ContentAnalysisResult) -> str:
        """JSON 결과 포맷"""
        import json
        
        result_dict = {
            "url": analysis.url,
            "title": analysis.title,
            "content_type": analysis.content_type,
            "summary": analysis.summary,
            "key_points": analysis.key_points,
            "sentiment": {
                "score": analysis.sentiment_score,
                "label": analysis.sentiment_label
            },
            "quality_score": analysis.quality_score,
            "topics": analysis.topics,
            "language": analysis.language,
            "reading_time": analysis.reading_time,
            "complexity_level": analysis.complexity_level,
            "metrics": {
                "word_count": analysis.word_count,
                "image_count": analysis.image_count,
                "link_count": analysis.link_count
            },
            "metadata": {
                "ai_model_used": analysis.ai_model_used,
                "analysis_timestamp": analysis.analysis_timestamp
            }
        }
        
        return f"```json\n{json.dumps(result_dict, ensure_ascii=False, indent=2)}\n```"

    # =================== AI 분석 엔진 메서드 ===================
    
    async def _perform_ai_analysis(self, title: str, content: str, url: str, content_type: str) -> Dict[str, Any]:
        """AI 기반 콘텐츠 분석 수행"""
        try:
            # AI 핸들러 가져오기
            if hasattr(self, 'ai_handler') and self.ai_handler:
                prompt = self._get_analysis_prompt(title, content, url, content_type)
                ai_response = await self.ai_handler.chat_with_ai(prompt, "content_analyzer")
                return self._parse_ai_response(ai_response, content_type)
            else:
                logger.warning("AI 핸들러를 사용할 수 없어 기본 분석으로 대체")
                return self._get_fallback_analysis(title, content, content_type)
                
        except Exception as e:
            logger.error(f"AI 분석 오류: {e}")
            return self._get_fallback_analysis(title, content, content_type)
    
    def _get_analysis_prompt(self, title: str, content: str, url: str, content_type: str) -> str:
        """콘텐츠 타입별 AI 분석 프롬프트 생성"""
        base_prompt = f"""
다음 {content_type} 콘텐츠를 분석해주세요:

제목: {title}
URL: {url}
내용: {content[:3000]}...

분석 결과를 다음 JSON 형식으로 제공해주세요:
{{
    "summary": "3-4문장으로 핵심 내용 요약",
    "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
    "main_insights": "주요 인사이트",
    "target_audience": "대상 독자",
    "usefulness": "높음/보통/낮음",
    "credibility": "높음/보통/낮음"
}}
"""
        return base_prompt
    
    def _parse_ai_response(self, ai_response: str, content_type: str) -> Dict[str, Any]:
        """AI 응답 파싱"""
        try:
            import json
            import re
            
            # JSON 부분 추출
            json_match = re.search(r'{.*}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                return parsed_data
            
            # JSON이 아닌 경우 텍스트 파싱
            return self._parse_text_response(ai_response)
            
        except Exception as e:
            logger.error(f"AI 응답 파싱 오류: {e}")
            return {"summary": "AI 분석 결과를 파싱할 수 없습니다.", "key_points": []}
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """텍스트 응답 파싱"""
        try:
            lines = response.split('\n')
            parsed = {"summary": "", "key_points": []}
            
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if '요약' in line or 'summary' in line.lower():
                    current_section = 'summary'
                elif '핵심' in line or 'key' in line.lower():
                    current_section = 'key_points'
                elif current_section == 'summary' and not parsed['summary']:
                    parsed['summary'] = line
                elif current_section == 'key_points':
                    if line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                        parsed['key_points'].append(line.lstrip('-•*123. '))
            
            return parsed
            
        except Exception as e:
            logger.error(f"텍스트 응답 파싱 오류: {e}")
            return {"summary": "텍스트 파싱 오류", "key_points": []}
    
    def _get_fallback_analysis(self, title: str, content: str, content_type: str) -> Dict[str, Any]:
        """AI 분석 실패 시 대체 분석"""
        return {
            'summary': f"{title}에 대한 {content_type} 콘텐츠입니다. " + content[:200] + "...",
            'key_points': self._extract_topics(content, max_topics=3),
            'analysis_method': 'fallback',
            'confidence': 'low'
        }
    
    # =================== 누락된 분석 메서드들 ===================
    
    def _analyze_content_structure(self, html_content: str, url: str) -> Dict[str, Any]:
        """콘텐츠 구조 분석"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            structure_info = {
                'has_navigation': bool(soup.find(['nav', 'header'])),
                'has_sidebar': bool(soup.find(['aside', 'sidebar'])),
                'has_footer': bool(soup.find('footer')),
                'article_count': len(soup.find_all('article')),
                'heading_count': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
                'paragraph_count': len(soup.find_all('p')),
                'list_count': len(soup.find_all(['ul', 'ol'])),
                'image_count': len(soup.find_all('img')),
                'link_count': len(soup.find_all('a')),
                'code_block_count': len(soup.find_all(['pre', 'code'])),
                'table_count': len(soup.find_all('table'))
            }
            
            return structure_info
            
        except Exception as e:
            logger.error(f"콘텐츠 구조 분석 오류: {e}")
            return {}
    
    def _extract_metadata(self, html_content: str) -> Dict[str, str]:
        """HTML 메타데이터 추출"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            metadata = {}
            
            # 기본 메타 태그
            meta_tags = {
                'description': soup.find('meta', attrs={'name': 'description'}),
                'keywords': soup.find('meta', attrs={'name': 'keywords'}),
                'author': soup.find('meta', attrs={'name': 'author'}),
                'robots': soup.find('meta', attrs={'name': 'robots'}),
                'viewport': soup.find('meta', attrs={'name': 'viewport'})
            }
            
            for key, tag in meta_tags.items():
                if tag and tag.get('content'):
                    metadata[key] = tag.get('content')
            
            # Open Graph 태그
            og_tags = soup.find_all('meta', attrs={'property': lambda x: x and x.startswith('og:')})
            for tag in og_tags:
                property_name = tag.get('property', '').replace('og:', '')
                if property_name and tag.get('content'):
                    metadata[f'og_{property_name}'] = tag.get('content')
            
            # Twitter Card 태그
            twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
            for tag in twitter_tags:
                name = tag.get('name', '').replace('twitter:', '')
                if name and tag.get('content'):
                    metadata[f'twitter_{name}'] = tag.get('content')
            
            # JSON-LD 구조화 데이터
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict):
                        if '@type' in json_data:
                            metadata['schema_type'] = json_data['@type']
                        if 'headline' in json_data:
                            metadata['schema_headline'] = json_data['headline']
                        if 'datePublished' in json_data:
                            metadata['schema_date_published'] = json_data['datePublished']
                except:
                    continue
            
            return metadata
            
        except Exception as e:
            logger.error(f"메타데이터 추출 오류: {e}")
            return {}
    
    def _detect_content_language_advanced(self, content: str, metadata: Dict[str, str]) -> str:
        """고급 언어 감지 (메타데이터 포함)"""
        try:
            # 메타데이터에서 언어 정보 확인
            if 'og_locale' in metadata:
                locale = metadata['og_locale'].lower()
                if 'ko' in locale:
                    return 'korean'
                elif 'en' in locale:
                    return 'english'
            
            # HTML lang 속성 확인
            if 'lang' in metadata:
                lang = metadata['lang'].lower()
                if 'ko' in lang:
                    return 'korean'
                elif 'en' in lang:
                    return 'english'
            
            # 기존 텍스트 기반 분석
            return self._detect_language(content)
            
        except Exception as e:
            logger.error(f"고급 언어 감지 오류: {e}")
            return self._detect_language(content)
    
    def _calculate_content_metrics(self, content: str, structure_info: Dict[str, Any]) -> Dict[str, int]:
        """콘텐츠 메트릭 계산"""
        try:
            metrics = {
                'word_count': len(content.split()),
                'character_count': len(content),
                'sentence_count': len(re.findall(r'[.!?]+', content)),
                'paragraph_count': structure_info.get('paragraph_count', 0),
                'heading_count': structure_info.get('heading_count', 0),
                'image_count': structure_info.get('image_count', 0),
                'link_count': structure_info.get('link_count', 0),
                'code_block_count': structure_info.get('code_block_count', 0),
                'list_count': structure_info.get('list_count', 0),
                'table_count': structure_info.get('table_count', 0)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"콘텐츠 메트릭 계산 오류: {e}")
            return {
                'word_count': len(content.split()) if content else 0,
                'character_count': len(content) if content else 0,
                'sentence_count': 0,
                'paragraph_count': 0,
                'heading_count': 0,
                'image_count': 0,
                'link_count': 0,
                'code_block_count': 0,
                'list_count': 0,
                'table_count': 0
            }
    
    # =================== 메인 분석 메서드 ===================
    
    async def analyze_web_content(self, url: str, use_ai: bool = True) -> Optional[ContentAnalysisResult]:
        """웹 콘텐츠 종합 분석 - AI 엔진 통합"""
        start_time = datetime.now()
        
        try:
            # 캐시 확인
            cache_key = self._generate_cache_key(url, "full_analysis")
            if cache_key in self.analysis_cache:
                logger.info(f"캐시에서 분석 결과 반환: {url}")
                return self.analysis_cache[cache_key]
            
            # 웹 콘텐츠 가져오기
            content_data = await self._fetch_web_content(url)
            if not content_data:
                return self._create_error_result(url, "웹 콘텐츠를 가져올 수 없습니다")
            
            # 기본 정보 추출
            title = content_data.get('title', '')
            content = content_data.get('content', '')
            html_content = content_data.get('html', '')
            
            # 1. 콘텐츠 타입 감지 (2단계에서 구현한 고급 분류)
            soup = BeautifulSoup(html_content, 'html.parser') if html_content else None
            content_type = self._detect_content_type(title, content, url, soup)
            
            # 2. 구조 분석 및 메타데이터 추출
            structure_info = self._analyze_content_structure(html_content, url) if html_content else {}
            metadata = self._extract_metadata(html_content) if html_content else {}
            
            # 3. 기본 분석
            sentiment_score, sentiment_label = self._calculate_sentiment_score(content)
            quality_score = self._calculate_quality_score(title, content, url)
            complexity_level = self._determine_complexity_level(content)
            reading_time = self._calculate_reading_time(content)
            language = self._detect_content_language_advanced(content, metadata)
            topics = self._extract_topics(content)
            
            # =================== 4단계 추가: 고급 감정 분석 통합 ===================
            # 고급 감정 분석 수행
            advanced_sentiment = self._calculate_advanced_sentiment_score(content)
            
            # AI 기반 감정 분석 (선택적)
            ai_sentiment = {}
            if use_ai and content:
                ai_sentiment = await self._perform_ai_sentiment_analysis(content, content_type)
            
            # 감정 분석 결과 통합
            final_sentiment_score = advanced_sentiment.get('basic_sentiment_score', sentiment_score)
            final_sentiment_label = advanced_sentiment.get('basic_sentiment_label', sentiment_label)
            detailed_emotions = advanced_sentiment.get('detailed_emotions', {})
            emotion_intensity = advanced_sentiment.get('emotion_intensity', 0.0)
            emotion_confidence = advanced_sentiment.get('emotion_confidence', 0.0)
            dominant_emotion = advanced_sentiment.get('dominant_emotion', 'neutral')
            emotion_distribution = advanced_sentiment.get('emotion_distribution', {})
            contextual_sentiment = advanced_sentiment.get('contextual_sentiment', 'direct')
            
            # AI 감정 분석 결과가 있으면 신뢰도 가중평균으로 통합
            if ai_sentiment:
                ai_confidence = ai_sentiment.get('ai_confidence', 0.0)
                rule_confidence = emotion_confidence
                
                # 신뢰도 기반 가중평균
                if ai_confidence > 0.7 and rule_confidence > 0.0:
                    total_confidence = ai_confidence + rule_confidence
                    emotion_confidence = (ai_confidence * ai_confidence + rule_confidence * rule_confidence) / total_confidence
                    
                    # AI 결과가 더 신뢰도가 높으면 주요 감정 업데이트
                    if ai_confidence > rule_confidence:
                        dominant_emotion = ai_sentiment.get('ai_dominant_emotion', dominant_emotion)
                        emotion_intensity = (emotion_intensity + ai_sentiment.get('ai_intensity', 0.0)) / 2
            
            # 4. 콘텐츠 메트릭 계산
            metrics = self._calculate_content_metrics(content, structure_info)
            
            # 5. AI 기반 고급 분석 (3단계 신규 기능)
            ai_analysis = {}
            if use_ai and content:
                ai_analysis = await self._perform_ai_analysis(title, content, url, content_type)
            
            # 6. 분석 결과 통합
            analysis_result = ContentAnalysisResult(
                url=url,
                title=title,
                content_type=content_type,
                summary=ai_analysis.get('summary', content[:200] + "..."),
                key_points=ai_analysis.get('key_points', topics[:3]),
                sentiment_score=final_sentiment_score,
                sentiment_label=final_sentiment_label,
                quality_score=quality_score,
                topics=topics,
                language=language,
                reading_time=reading_time,
                complexity_level=complexity_level,
                analysis_timestamp=datetime.now().isoformat(),
                ai_model_used="gpt-4" if use_ai and ai_analysis else "rule-based",
                word_count=metrics.get('word_count', 0),
                image_count=metrics.get('image_count', 0),
                link_count=metrics.get('link_count', 0),
                error_message="",
                
                # =================== 4단계 추가: 고급 감정 분석 필드 ===================
                detailed_emotions=detailed_emotions,
                emotion_intensity=emotion_intensity,
                emotion_confidence=emotion_confidence,
                dominant_emotion=dominant_emotion,
                emotion_distribution=emotion_distribution,
                contextual_sentiment=contextual_sentiment,
                
                # =================== 4단계 추가: 고급 품질 평가 필드 (임시) ===================
                quality_dimensions={},  # 다음 작업에서 구현 예정
                quality_report="",
                improvement_suggestions=[],
                content_reliability=0.0,
                content_usefulness=0.0,
                content_accuracy=0.0
            )
            
            # 7. 캐시에 저장
            self.analysis_cache[cache_key] = analysis_result
            
            # 8. 통계 업데이트
            self._update_analysis_stats(analysis_result, start_time)
            
            logger.info(f"웹 콘텐츠 분석 완료: {url} (타입: {content_type}, 품질: {quality_score:.1f})")
            return analysis_result
            
        except Exception as e:
            logger.error(f"웹 콘텐츠 분석 오류: {e}")
            self.analysis_stats['failed_analyses'] += 1
            return self._create_error_result(url, f"분석 중 오류 발생: {str(e)}")
    
    async def _fetch_web_content(self, url: str) -> Optional[Dict[str, str]]:
        """웹 콘텐츠 가져오기 - web_search_ide 활용"""
        try:
            # web_search_ide의 visit_site 메서드 활용
            result = self.web_search.visit_site("content_analyzer", url, extract_code=False)
            
            if result.get('success'):
                return {
                    'title': result.get('title', ''),
                    'content': result.get('content_preview', ''),
                    'html': result.get('html_content', ''),  # 전체 HTML이 필요한 경우
                    'url': url
                }
            else:
                # 대안: 직접 HTTP 요청
                return await self._fetch_content_direct(url)
                
        except Exception as e:
            logger.error(f"웹 콘텐츠 가져오기 오류: {e}")
            return await self._fetch_content_direct(url)
    
    async def _fetch_content_direct(self, url: str) -> Optional[Dict[str, str]]:
        """직접 HTTP 요청으로 콘텐츠 가져오기"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # BeautifulSoup으로 파싱
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # 제목 추출
                        title_tag = soup.find('title')
                        title = title_tag.get_text().strip() if title_tag else "제목 없음"
                        
                        # 본문 텍스트 추출
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        text_content = soup.get_text()
                        clean_text = ' '.join(text_content.split())
                        
                        return {
                            'title': title,
                            'content': clean_text,
                            'html': html_content,
                            'url': url
                        }
                    else:
                        logger.warning(f"HTTP {response.status}: {url}")
                        return None
                        
        except Exception as e:
            logger.error(f"직접 콘텐츠 가져오기 오류: {e}")
            return None
    
    def _create_error_result(self, url: str, error_message: str) -> ContentAnalysisResult:
        """오류 결과 생성"""
        return ContentAnalysisResult(
            url=url,
            title="분석 실패",
            content_type="error",
            summary="",
            key_points=[],
            sentiment_score=0.0,
            sentiment_label="neutral",
            quality_score=0.0,
            topics=[],
            language="unknown",
            reading_time=0,
            complexity_level="unknown",
            analysis_timestamp=datetime.now().isoformat(),
            ai_model_used="none",
            word_count=0,
            image_count=0,
            link_count=0,
            error_message=error_message
        )
    
    def _update_analysis_stats(self, result: ContentAnalysisResult, start_time: datetime):
        """분석 통계 업데이트"""
        try:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.analysis_stats['total_analyzed'] += 1
            if not result.error_message:
                self.analysis_stats['successful_analyses'] += 1
            
            # 평균 처리 시간 업데이트
            current_avg = self.analysis_stats['average_processing_time']
            total = self.analysis_stats['total_analyzed']
            self.analysis_stats['average_processing_time'] = (current_avg * (total - 1) + processing_time) / total
            
            # 평균 품질 점수 업데이트
            if result.quality_score > 0:
                current_quality_avg = self.analysis_stats['average_quality_score']
                success_count = self.analysis_stats['successful_analyses']
                self.analysis_stats['average_quality_score'] = (current_quality_avg * (success_count - 1) + result.quality_score) / success_count
            
        except Exception as e:
            logger.error(f"통계 업데이트 오류: {e}")

    # =================== 배치 분석 메서드 ===================
    
    async def analyze_batch_urls(self, urls: List[str], max_concurrent: int = 5) -> BatchAnalysisReport:
        """배치 URL 분석"""
        start_time = datetime.now()
        
        try:
            # 캐시 확인
            urls_key = hashlib.md5(str(sorted(urls)).encode()).hexdigest()
            cache_key = f"batch_{urls_key}"
            
            if cache_key in self.batch_cache:
                logger.info("배치 분석 캐시 결과 반환")
                return self.batch_cache[cache_key]
            
            # 비동기 배치 분석
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def analyze_single_url(url):
                async with semaphore:
                    return await self.analyze_web_content(url)
            
            # 모든 URL 동시 분석
            tasks = [analyze_single_url(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 집계
            successful_results = []
            failed_count = 0
            
            for result in results:
                if isinstance(result, ContentAnalysisResult) and not result.error_message:
                    successful_results.append(result)
                else:
                    failed_count += 1
            
            # 리포트 생성
            report = self._generate_batch_report(successful_results, failed_count, len(urls), start_time)
            
            # 캐시 저장
            self.batch_cache[cache_key] = report
            
            logger.info(f"배치 분석 완료: {len(successful_results)}/{len(urls)} 성공")
            return report
            
        except Exception as e:
            logger.error(f"배치 분석 오류: {e}")
            return self._create_error_batch_report(len(urls), str(e))
    
    def _generate_batch_report(self, results: List[ContentAnalysisResult], failed_count: int, total_count: int, start_time: datetime) -> BatchAnalysisReport:
        """배치 분석 리포트 생성"""
        try:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if not results:
                return BatchAnalysisReport(
                    total_analyzed=total_count,
                    success_count=0,
                    failed_count=failed_count,
                    average_quality_score=0.0,
                    dominant_sentiment="neutral",
                    top_topics=[],
                    content_type_distribution={},
                    analysis_summary="분석된 콘텐츠가 없습니다.",
                    processing_time=processing_time,
                    report_timestamp=datetime.now().isoformat()
                )
            
            # 통계 계산
            avg_quality = sum(r.quality_score for r in results) / len(results)
            
            # 감정 분포
            sentiment_counts = {}
            for result in results:
                sentiment = result.sentiment_label
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)
            
            # 토픽 집계
            topic_counts = {}
            for result in results:
                for topic in result.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # 콘텐츠 타입 분포
            type_distribution = {}
            for result in results:
                content_type = result.content_type
                type_distribution[content_type] = type_distribution.get(content_type, 0) + 1
            
            # 요약 생성
            summary = f"총 {len(results)}개 콘텐츠 분석 완료. 평균 품질점수 {avg_quality:.1f}점, 주요 감정 {dominant_sentiment}"
            
            return BatchAnalysisReport(
                total_analyzed=total_count,
                success_count=len(results),
                failed_count=failed_count,
                average_quality_score=avg_quality,
                dominant_sentiment=dominant_sentiment,
                top_topics=top_topics,
                content_type_distribution=type_distribution,
                analysis_summary=summary,
                processing_time=processing_time,
                report_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"배치 리포트 생성 오류: {e}")
            return self._create_error_batch_report(total_count, str(e))
    
    def _create_error_batch_report(self, total_count: int, error_message: str) -> BatchAnalysisReport:
        """오류 배치 리포트 생성"""
        return BatchAnalysisReport(
            total_analyzed=total_count,
            success_count=0,
            failed_count=total_count,
            average_quality_score=0.0,
            dominant_sentiment="neutral",
            top_topics=[],
            content_type_distribution={},
            analysis_summary=f"배치 분석 실패: {error_message}",
            processing_time=0.0,
            report_timestamp=datetime.now().isoformat()
        )
    
    # =================== 4단계 추가: 정교한 품질 평가 시스템 ===================
    
    def _calculate_advanced_quality_score(self, title: str, content: str, url: str, 
                                        content_type: str, structure_info: Dict = None) -> Dict[str, Any]:
        """정교한 다차원 품질 평가"""
        try:
            # 콘텐츠 타입별 가중치 적용
            type_weights = self.content_type_quality_weights.get(content_type, 
                                                               self.content_type_quality_weights['general'])
            
            # 각 차원별 점수 계산
            dimension_scores = {}
            detailed_analysis = {}
            
            # 1. 신뢰도 (Reliability) 평가
            reliability_score, reliability_detail = self._evaluate_reliability(title, content, url, structure_info)
            dimension_scores['reliability'] = reliability_score * type_weights['reliability']
            detailed_analysis['reliability'] = reliability_detail
            
            # 2. 유용성 (Usefulness) 평가
            usefulness_score, usefulness_detail = self._evaluate_usefulness(title, content, content_type)
            dimension_scores['usefulness'] = usefulness_score * type_weights['usefulness']
            detailed_analysis['usefulness'] = usefulness_detail
            
            # 3. 정확성 (Accuracy) 평가
            accuracy_score, accuracy_detail = self._evaluate_accuracy(title, content, url)
            dimension_scores['accuracy'] = accuracy_score * type_weights['accuracy']
            detailed_analysis['accuracy'] = accuracy_detail
            
            # 4. 완성도 (Completeness) 평가
            completeness_score, completeness_detail = self._evaluate_completeness(title, content, structure_info)
            dimension_scores['completeness'] = completeness_score * type_weights['completeness']
            detailed_analysis['completeness'] = completeness_detail
            
            # 5. 가독성 (Readability) 평가
            readability_score, readability_detail = self._evaluate_readability(title, content, structure_info)
            dimension_scores['readability'] = readability_score * type_weights['readability']
            detailed_analysis['readability'] = readability_detail
            
            # 6. 독창성 (Originality) 평가
            originality_score, originality_detail = self._evaluate_originality(title, content, content_type)
            dimension_scores['originality'] = originality_score * type_weights['originality']
            detailed_analysis['originality'] = originality_detail
            
            # 언어 품질 평가
            language_quality = self._evaluate_language_quality(content)
            
            # 전체 품질 점수 계산 (가중평균)
            total_weight = sum(type_weights.values())
            overall_score = sum(dimension_scores.values()) / total_weight
            overall_score = min(100.0, max(0.0, overall_score))
            
            # 품질 등급 결정
            quality_grade = self._determine_quality_grade(overall_score)
            
            # 개선 제안사항 생성
            improvement_suggestions = self._generate_improvement_suggestions(
                dimension_scores, detailed_analysis, content_type
            )
            
            # 품질 리포트 생성
            quality_report = self._generate_quality_report(
                dimension_scores, detailed_analysis, language_quality, 
                quality_grade, content_type
            )
            
            return {
                'overall_score': overall_score,
                'quality_grade': quality_grade,
                'dimension_scores': dimension_scores,
                'detailed_analysis': detailed_analysis,
                'language_quality': language_quality,
                'improvement_suggestions': improvement_suggestions,
                'quality_report': quality_report,
                'content_type_weights': type_weights
            }
            
        except Exception as e:
            logger.error(f"고급 품질 평가 오류: {e}")
            return {
                'overall_score': 50.0,
                'quality_grade': 'C',
                'dimension_scores': {},
                'detailed_analysis': {},
                'language_quality': {},
                'improvement_suggestions': ['품질 평가 중 오류가 발생했습니다.'],
                'quality_report': '품질 평가를 완료할 수 없습니다.',
                'content_type_weights': {}
            }
    
    def _evaluate_reliability(self, title: str, content: str, url: str, structure_info: Dict = None) -> Tuple[float, Dict]:
        """신뢰도 평가"""
        try:
            score = 50.0  # 기본 점수
            details = {}
            
            domain = urlparse(url).netloc.lower()
            text_lower = f"{title} {content}".lower()
            
            # 출처 신뢰도 평가
            source_score = 0
            credible_domains = self.quality_dimensions['reliability']['indicators']['source_credibility']
            for domain_type in credible_domains:
                if domain_type in domain:
                    source_score += 20
                    break
            else:
                # 알려진 신뢰할 만한 사이트 체크
                if any(trusted in domain for trusted in ['naver', 'google', 'wikipedia', 'github']):
                    source_score += 10
            
            details['source_credibility'] = source_score
            score += source_score
            
            # 저자 전문성 평가
            expertise_score = 0
            expertise_indicators = self.quality_dimensions['reliability']['indicators']['author_expertise']
            expertise_matches = sum(1 for indicator in expertise_indicators if indicator in text_lower)
            expertise_score = min(15, expertise_matches * 5)
            
            details['author_expertise'] = expertise_score
            score += expertise_score
            
            # 인용 및 참고문헌 품질
            citation_score = 0
            citation_indicators = self.quality_dimensions['reliability']['indicators']['citation_quality']
            citation_matches = sum(1 for indicator in citation_indicators if indicator in text_lower)
            citation_score = min(10, citation_matches * 3)
            
            details['citation_quality'] = citation_score
            score += citation_score
            
            # 사실 확인 및 데이터 기반
            fact_score = 0
            fact_indicators = self.quality_dimensions['reliability']['indicators']['fact_checking']
            fact_matches = sum(1 for indicator in fact_indicators if indicator in text_lower)
            fact_score = min(10, fact_matches * 2)
            
            details['fact_checking'] = fact_score
            score += fact_score
            
            # HTTPS 사용 (보안)
            if url.startswith('https'):
                score += 5
                details['security'] = 5
            else:
                details['security'] = 0
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"신뢰도 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_usefulness(self, title: str, content: str, content_type: str) -> Tuple[float, Dict]:
        """유용성 평가"""
        try:
            score = 50.0
            details = {}
            text_lower = f"{title} {content}".lower()
            
            # 실용적 가치
            practical_score = 0
            practical_indicators = self.quality_dimensions['usefulness']['indicators']['practical_value']
            practical_matches = sum(1 for indicator in practical_indicators if indicator in text_lower)
            practical_score = min(25, practical_matches * 4)
            
            details['practical_value'] = practical_score
            score += practical_score
            
            # 실행 가능한 내용
            actionable_score = 0
            actionable_indicators = self.quality_dimensions['usefulness']['indicators']['actionable_content']
            actionable_matches = sum(1 for indicator in actionable_indicators if indicator in text_lower)
            actionable_score = min(20, actionable_matches * 3)
            
            details['actionable_content'] = actionable_score
            score += actionable_score
            
            # 문제 해결 능력
            problem_solving_score = 0
            problem_indicators = self.quality_dimensions['usefulness']['indicators']['problem_solving']
            problem_matches = sum(1 for indicator in problem_indicators if indicator in text_lower)
            problem_solving_score = min(15, problem_matches * 3)
            
            details['problem_solving'] = problem_solving_score
            score += problem_solving_score
            
            # 학습 가치
            learning_score = 0
            learning_indicators = self.quality_dimensions['usefulness']['indicators']['learning_value']
            learning_matches = sum(1 for indicator in learning_indicators if indicator in text_lower)
            learning_score = min(10, learning_matches * 2)
            
            details['learning_value'] = learning_score
            score += learning_score
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"유용성 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_accuracy(self, title: str, content: str, url: str) -> Tuple[float, Dict]:
        """정확성 평가"""
        try:
            score = 50.0
            details = {}
            text_lower = f"{title} {content}".lower()
            
            # 기술적 정밀성
            precision_score = 0
            precision_indicators = self.quality_dimensions['accuracy']['indicators']['technical_precision']
            precision_matches = sum(1 for indicator in precision_indicators if indicator in text_lower)
            precision_score = min(25, precision_matches * 8)
            
            details['technical_precision'] = precision_score
            score += precision_score
            
            # 오류 지시어 확인 (부정적 평가)
            error_penalty = 0
            error_indicators = self.quality_dimensions['accuracy']['indicators']['error_indicators']
            error_matches = sum(1 for indicator in error_indicators if indicator in text_lower)
            error_penalty = min(20, error_matches * 5)
            
            details['error_indicators'] = -error_penalty
            score -= error_penalty
            
            # 검증 표시
            verification_score = 0
            verification_indicators = self.quality_dimensions['accuracy']['indicators']['verification_marks']
            verification_matches = sum(1 for indicator in verification_indicators if indicator in text_lower)
            verification_score = min(15, verification_matches * 5)
            
            details['verification_marks'] = verification_score
            score += verification_score
            
            # 최신성 평가
            update_score = 0
            update_indicators = self.quality_dimensions['accuracy']['indicators']['update_frequency']
            update_matches = sum(1 for indicator in update_indicators if indicator in text_lower)
            update_score = min(10, update_matches * 3)
            
            details['update_frequency'] = update_score
            score += update_score
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"정확성 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_completeness(self, title: str, content: str, structure_info: Dict = None) -> Tuple[float, Dict]:
        """완성도 평가"""
        try:
            score = 50.0
            details = {}
            text_lower = f"{title} {content}".lower()
            
            # 포괄적 커버리지
            coverage_score = 0
            coverage_indicators = self.quality_dimensions['completeness']['indicators']['comprehensive_coverage']
            coverage_matches = sum(1 for indicator in coverage_indicators if indicator in text_lower)
            coverage_score = min(25, coverage_matches * 8)
            
            details['comprehensive_coverage'] = coverage_score
            score += coverage_score
            
            # 상세한 설명
            detail_score = 0
            detail_indicators = self.quality_dimensions['completeness']['indicators']['detailed_explanation']
            detail_matches = sum(1 for indicator in detail_indicators if indicator in text_lower)
            detail_score = min(20, detail_matches * 7)
            
            details['detailed_explanation'] = detail_score
            score += detail_score
            
            # 예제 제공
            example_score = 0
            example_indicators = self.quality_dimensions['completeness']['indicators']['example_provision']
            example_matches = sum(1 for indicator in example_indicators if indicator in text_lower)
            example_score = min(15, example_matches * 5)
            
            details['example_provision'] = example_score
            score += example_score
            
            # 단계별 설명
            step_score = 0
            step_indicators = self.quality_dimensions['completeness']['indicators']['step_by_step']
            step_matches = sum(1 for indicator in step_indicators if indicator in text_lower)
            step_score = min(10, step_matches * 3)
            
            details['step_by_step'] = step_score
            score += step_score
            
            # 콘텐츠 길이 보너스
            content_length = len(content)
            if content_length > 2000:
                length_bonus = min(10, (content_length - 2000) // 1000 * 2)
                score += length_bonus
                details['content_length_bonus'] = length_bonus
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"완성도 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_readability(self, title: str, content: str, structure_info: Dict = None) -> Tuple[float, Dict]:
        """가독성 평가"""
        try:
            score = 50.0
            details = {}
            text_lower = f"{title} {content}".lower()
            
            # 명확한 구조
            structure_score = 0
            structure_indicators = self.quality_dimensions['readability']['indicators']['clear_structure']
            structure_matches = sum(1 for indicator in structure_indicators if indicator in text_lower)
            structure_score = min(25, structure_matches * 8)
            
            details['clear_structure'] = structure_score
            score += structure_score
            
            # 간단한 언어
            language_score = 0
            language_indicators = self.quality_dimensions['readability']['indicators']['simple_language']
            language_matches = sum(1 for indicator in language_indicators if indicator in text_lower)
            language_score = min(20, language_matches * 7)
            
            details['simple_language'] = language_score
            score += language_score
            
            # 시각적 도구
            visual_score = 0
            visual_indicators = self.quality_dimensions['readability']['indicators']['visual_aids']
            visual_matches = sum(1 for indicator in visual_indicators if indicator in text_lower)
            visual_score = min(15, visual_matches * 5)
            
            details['visual_aids'] = visual_score
            score += visual_score
            
            # 포맷팅
            formatting_score = 0
            formatting_indicators = self.quality_dimensions['readability']['indicators']['formatting']
            formatting_matches = sum(1 for indicator in formatting_indicators if indicator in text_lower)
            formatting_score = min(10, formatting_matches * 3)
            
            # 구조 정보 활용
            if structure_info:
                if structure_info.get('heading_count', 0) > 2:
                    formatting_score += 5
                if structure_info.get('list_count', 0) > 0:
                    formatting_score += 3
                if structure_info.get('paragraph_count', 0) > 3:
                    formatting_score += 2
            
            details['formatting'] = formatting_score
            score += formatting_score
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"가독성 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_originality(self, title: str, content: str, content_type: str) -> Tuple[float, Dict]:
        """독창성 평가"""
        try:
            score = 50.0
            details = {}
            text_lower = f"{title} {content}".lower()
            
            # 독특한 관점
            perspective_score = 0
            perspective_indicators = self.quality_dimensions['originality']['indicators']['unique_perspective']
            perspective_matches = sum(1 for indicator in perspective_indicators if indicator in text_lower)
            perspective_score = min(25, perspective_matches * 8)
            
            details['unique_perspective'] = perspective_score
            score += perspective_score
            
            # 개인적 통찰
            insight_score = 0
            insight_indicators = self.quality_dimensions['originality']['indicators']['personal_insight']
            insight_matches = sum(1 for indicator in insight_indicators if indicator in text_lower)
            insight_score = min(20, insight_matches * 7)
            
            details['personal_insight'] = insight_score
            score += insight_score
            
            # 창의적 접근
            creative_score = 0
            creative_indicators = self.quality_dimensions['originality']['indicators']['creative_approach']
            creative_matches = sum(1 for indicator in creative_indicators if indicator in text_lower)
            creative_score = min(15, creative_matches * 5)
            
            details['creative_approach'] = creative_score
            score += creative_score
            
            # 사고 자극적
            thought_score = 0
            thought_indicators = self.quality_dimensions['originality']['indicators']['thought_provoking']
            thought_matches = sum(1 for indicator in thought_indicators if indicator in text_lower)
            thought_score = min(10, thought_matches * 3)
            
            details['thought_provoking'] = thought_score
            score += thought_score
            
            # 콘텐츠 타입별 조정
            if content_type == 'blog':
                score += 10  # 블로그는 개인적 특성이 중요
            elif content_type == 'news':
                score -= 5   # 뉴스는 객관성이 더 중요
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"독창성 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_language_quality(self, content: str) -> Dict[str, Any]:
        """언어 품질 평가"""
        try:
            analysis = {
                'grammar_errors': 0,
                'spelling_errors': 0,
                'good_expressions': 0,
                'vocabulary_diversity': 0,
                'sentence_variety': 0,
                'overall_language_score': 50.0
            }
            
            # 문법 오류 검사
            for pattern in self.language_quality_indicators['grammar_errors']:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                analysis['grammar_errors'] += matches
            
            # 맞춤법 오류 검사
            for pattern in self.language_quality_indicators['spelling_errors']:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                analysis['spelling_errors'] += matches
            
            # 좋은 표현 확인
            for pattern in self.language_quality_indicators['good_expressions']:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                analysis['good_expressions'] += matches
            
            # 어휘 다양성 (고유 단어 수 / 전체 단어 수)
            words = re.findall(r'[가-힣a-zA-Z]+', content)
            if words:
                unique_words = set(words)
                analysis['vocabulary_diversity'] = len(unique_words) / len(words) * 100
            
            # 문장 다양성 (문장 길이의 표준편차)
            sentences = re.split(r'[.!?]', content)
            if len(sentences) > 1:
                sentence_lengths = [len(s.strip()) for s in sentences if s.strip()]
                if sentence_lengths:
                    import statistics
                    analysis['sentence_variety'] = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
            
            # 전체 언어 품질 점수 계산
            score = 70.0
            score -= analysis['grammar_errors'] * 5  # 문법 오류 페널티
            score -= analysis['spelling_errors'] * 3  # 맞춤법 오류 페널티
            score += min(20, analysis['good_expressions'] * 2)  # 좋은 표현 보너스
            score += min(10, analysis['vocabulary_diversity'] * 0.2)  # 어휘 다양성 보너스
            
            analysis['overall_language_score'] = min(100.0, max(0.0, score))
            
            return analysis
            
        except Exception as e:
            logger.error(f"언어 품질 평가 오류: {e}")
            return {
                'grammar_errors': 0,
                'spelling_errors': 0,
                'good_expressions': 0,
                'vocabulary_diversity': 0,
                'sentence_variety': 0,
                'overall_language_score': 50.0,
                'error': str(e)
            }
    
    def _determine_quality_grade(self, score: float) -> str:
        """품질 등급 결정"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'C+'
        elif score >= 65:
            return 'C'
        elif score >= 60:
            return 'D+'
        elif score >= 55:
            return 'D'
        else:
            return 'F'
    
    def _generate_improvement_suggestions(self, dimension_scores: Dict[str, float], 
                                        detailed_analysis: Dict[str, Dict], 
                                        content_type: str) -> List[str]:
        """개선 제안사항 생성"""
        suggestions = []
        
        try:
            # 각 차원별 점수를 기준으로 개선 제안
            for dimension, score in dimension_scores.items():
                if score < 60:  # 낮은 점수의 차원에 대해 제안
                    if dimension == 'reliability':
                        suggestions.append("📊 신뢰도 개선: 출처를 명확히 하고, 전문가 의견이나 데이터를 추가하세요.")
                        suggestions.append("🔗 참고문헌이나 관련 링크를 포함하여 정보의 신뢰성을 높이세요.")
                    
                    elif dimension == 'usefulness':
                        suggestions.append("💡 유용성 개선: 실용적인 팁이나 실행 가능한 조언을 더 추가하세요.")
                        suggestions.append("🎯 독자가 바로 적용할 수 있는 구체적인 방법을 제시하세요.")
                    
                    elif dimension == 'accuracy':
                        suggestions.append("✅ 정확성 개선: 최신 정보로 업데이트하고 사실 확인을 강화하세요.")
                        suggestions.append("🔍 기술적 세부사항의 정밀도를 높이고 오류를 점검하세요.")
                    
                    elif dimension == 'completeness':
                        suggestions.append("📝 완성도 개선: 더 상세한 설명과 예제를 추가하세요.")
                        suggestions.append("📋 단계별 가이드나 체크리스트를 포함하세요.")
                    
                    elif dimension == 'readability':
                        suggestions.append("📖 가독성 개선: 명확한 제목과 소제목으로 구조를 개선하세요.")
                        suggestions.append("🎨 시각적 요소(이미지, 차트, 목록)를 활용하세요.")
                    
                    elif dimension == 'originality':
                        suggestions.append("💭 독창성 개선: 개인적 경험이나 독특한 관점을 추가하세요.")
                        suggestions.append("🌟 새로운 아이디어나 창의적 접근법을 시도하세요.")
            
            # 콘텐츠 타입별 특화 제안
            if content_type == 'news':
                suggestions.append("📰 뉴스 특화: 5W1H(누가, 언제, 어디서, 무엇을, 왜, 어떻게)를 명확히 하세요.")
            elif content_type == 'blog':
                suggestions.append("✍️ 블로그 특화: 개인적 스토리텔링과 독자와의 소통을 강화하세요.")
            elif content_type == 'tech_doc':
                suggestions.append("⚙️ 기술문서 특화: 코드 예제와 단계별 설명을 더 상세히 제공하세요.")
            elif content_type == 'tutorial':
                suggestions.append("🎓 튜토리얼 특화: 학습자가 따라할 수 있는 명확한 단계를 제시하세요.")
            
            # 언어 품질 관련 제안
            suggestions.append("📚 언어 품질: 맞춤법과 문법을 재점검하고 다양한 어휘를 활용하세요.")
            
            return suggestions[:5]  # 최대 5개 제안
            
        except Exception as e:
            logger.error(f"개선 제안사항 생성 오류: {e}")
            return ["품질 개선을 위해 내용을 재검토해 주세요."]
    
    def _generate_quality_report(self, dimension_scores: Dict[str, float], 
                               detailed_analysis: Dict[str, Dict], 
                               language_quality: Dict[str, Any],
                               quality_grade: str, content_type: str) -> str:
        """품질 리포트 생성"""
        try:
            report_lines = []
            
            # 전체 등급 및 요약
            overall_score = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 50.0
            report_lines.append(f"🏆 **전체 품질 등급: {quality_grade}** (점수: {overall_score:.1f}/100)")
            report_lines.append(f"📄 콘텐츠 타입: {content_type}")
            report_lines.append("")
            
            # 차원별 상세 분석
            report_lines.append("📊 **차원별 분석 결과**")
            
            dimension_names = {
                'reliability': '신뢰도',
                'usefulness': '유용성', 
                'accuracy': '정확성',
                'completeness': '완성도',
                'readability': '가독성',
                'originality': '독창성'
            }
            
            for dimension, score in dimension_scores.items():
                name = dimension_names.get(dimension, dimension)
                grade = self._determine_quality_grade(score)
                
                if score >= 80:
                    emoji = "🟢"
                elif score >= 60:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                
                report_lines.append(f"{emoji} **{name}**: {grade} ({score:.1f}점)")
                
                # 세부 분석 정보
                if dimension in detailed_analysis:
                    details = detailed_analysis[dimension]
                    positive_aspects = [k for k, v in details.items() if isinstance(v, (int, float)) and v > 0]
                    if positive_aspects:
                        report_lines.append(f"   ✅ 강점: {', '.join(positive_aspects[:3])}")
            
            report_lines.append("")
            
            # 언어 품질 분석
            if language_quality:
                report_lines.append("📝 **언어 품질 분석**")
                lang_score = language_quality.get('overall_language_score', 50)
                lang_grade = self._determine_quality_grade(lang_score)
                
                if lang_score >= 80:
                    emoji = "🟢"
                elif lang_score >= 60:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                
                report_lines.append(f"{emoji} **언어 품질**: {lang_grade} ({lang_score:.1f}점)")
                
                if language_quality.get('grammar_errors', 0) > 0:
                    report_lines.append(f"   ⚠️ 문법 오류: {language_quality['grammar_errors']}개")
                if language_quality.get('spelling_errors', 0) > 0:
                    report_lines.append(f"   ⚠️ 맞춤법 오류: {language_quality['spelling_errors']}개")
                if language_quality.get('good_expressions', 0) > 0:
                    report_lines.append(f"   ✅ 좋은 표현: {language_quality['good_expressions']}개")
                
                vocab_diversity = language_quality.get('vocabulary_diversity', 0)
                if vocab_diversity > 0:
                    report_lines.append(f"   📚 어휘 다양성: {vocab_diversity:.1f}%")
            
            report_lines.append("")
            
            # 종합 평가
            report_lines.append("🎯 **종합 평가**")
            if overall_score >= 85:
                report_lines.append("우수한 품질의 콘텐츠입니다. 대부분의 품질 기준을 충족하고 있습니다.")
            elif overall_score >= 70:
                report_lines.append("양호한 품질의 콘텐츠입니다. 일부 영역에서 개선의 여지가 있습니다.")
            elif overall_score >= 60:
                report_lines.append("보통 수준의 콘텐츠입니다. 여러 영역에서 개선이 필요합니다.")
            else:
                report_lines.append("품질 개선이 필요한 콘텐츠입니다. 전반적인 재검토를 권장합니다.")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"품질 리포트 생성 오류: {e}")
            return f"품질 리포트 생성 중 오류가 발생했습니다: {str(e)}"
    
    # =================== 메인 분석 메서드 ===================
    
    async def analyze_web_content(self, url: str, use_ai: bool = True) -> Optional[ContentAnalysisResult]:
        """웹 콘텐츠 종합 분석 - AI 엔진 통합"""
        start_time = datetime.now()
        
        try:
            # 캐시 확인
            cache_key = self._generate_cache_key(url, "full_analysis")
            if cache_key in self.analysis_cache:
                logger.info(f"캐시에서 분석 결과 반환: {url}")
                return self.analysis_cache[cache_key]
            
            # 웹 콘텐츠 가져오기
            content_data = await self._fetch_web_content(url)
            if not content_data:
                return self._create_error_result(url, "웹 콘텐츠를 가져올 수 없습니다")
            
            # 기본 정보 추출
            title = content_data.get('title', '')
            content = content_data.get('content', '')
            html_content = content_data.get('html', '')
            
            # 1. 콘텐츠 타입 감지 (2단계에서 구현한 고급 분류)
            soup = BeautifulSoup(html_content, 'html.parser') if html_content else None
            content_type = self._detect_content_type(title, content, url, soup)
            
            # 2. 구조 분석 및 메타데이터 추출
            structure_info = self._analyze_content_structure(html_content, url) if html_content else {}
            metadata = self._extract_metadata(html_content) if html_content else {}
            
            # 3. 기본 분석
            sentiment_score, sentiment_label = self._calculate_sentiment_score(content)
            quality_score = self._calculate_quality_score(title, content, url)
            complexity_level = self._determine_complexity_level(content)
            reading_time = self._calculate_reading_time(content)
            language = self._detect_content_language_advanced(content, metadata)
            topics = self._extract_topics(content)
            
            # =================== 4단계 추가: 고급 감정 분석 통합 ===================
            # 고급 감정 분석 수행
            advanced_sentiment = self._calculate_advanced_sentiment_score(content)
            
            # AI 기반 감정 분석 (선택적)
            ai_sentiment = {}
            if use_ai and content:
                ai_sentiment = await self._perform_ai_sentiment_analysis(content, content_type)
            
            # 감정 분석 결과 통합
            final_sentiment_score = advanced_sentiment.get('basic_sentiment_score', sentiment_score)
            final_sentiment_label = advanced_sentiment.get('basic_sentiment_label', sentiment_label)
            detailed_emotions = advanced_sentiment.get('detailed_emotions', {})
            emotion_intensity = advanced_sentiment.get('emotion_intensity', 0.0)
            emotion_confidence = advanced_sentiment.get('emotion_confidence', 0.0)
            dominant_emotion = advanced_sentiment.get('dominant_emotion', 'neutral')
            emotion_distribution = advanced_sentiment.get('emotion_distribution', {})
            contextual_sentiment = advanced_sentiment.get('contextual_sentiment', 'direct')
            
            # AI 감정 분석 결과가 있으면 신뢰도 가중평균으로 통합
            if ai_sentiment:
                ai_confidence = ai_sentiment.get('ai_confidence', 0.0)
                rule_confidence = emotion_confidence
                
                # 신뢰도 기반 가중평균
                if ai_confidence > 0.7 and rule_confidence > 0.0:
                    total_confidence = ai_confidence + rule_confidence
                    emotion_confidence = (ai_confidence * ai_confidence + rule_confidence * rule_confidence) / total_confidence
                    
                    # AI 결과가 더 신뢰도가 높으면 주요 감정 업데이트
                    if ai_confidence > rule_confidence:
                        dominant_emotion = ai_sentiment.get('ai_dominant_emotion', dominant_emotion)
                        emotion_intensity = (emotion_intensity + ai_sentiment.get('ai_intensity', 0.0)) / 2
            
            # 4. 콘텐츠 메트릭 계산
            metrics = self._calculate_content_metrics(content, structure_info)
            
            # 5. AI 기반 고급 분석 (3단계 신규 기능)
            ai_analysis = {}
            if use_ai and content:
                ai_analysis = await self._perform_ai_analysis(title, content, url, content_type)
            
            # 6. 분석 결과 통합
            analysis_result = ContentAnalysisResult(
                url=url,
                title=title,
                content_type=content_type,
                summary=ai_analysis.get('summary', content[:200] + "..."),
                key_points=ai_analysis.get('key_points', topics[:3]),
                sentiment_score=final_sentiment_score,
                sentiment_label=final_sentiment_label,
                quality_score=quality_score,
                topics=topics,
                language=language,
                reading_time=reading_time,
                complexity_level=complexity_level,
                analysis_timestamp=datetime.now().isoformat(),
                ai_model_used="gpt-4" if use_ai and ai_analysis else "rule-based",
                word_count=metrics.get('word_count', 0),
                image_count=metrics.get('image_count', 0),
                link_count=metrics.get('link_count', 0),
                error_message="",
                
                # =================== 4단계 추가: 고급 감정 분석 필드 ===================
                detailed_emotions=detailed_emotions,
                emotion_intensity=emotion_intensity,
                emotion_confidence=emotion_confidence,
                dominant_emotion=dominant_emotion,
                emotion_distribution=emotion_distribution,
                contextual_sentiment=contextual_sentiment,
                
                # =================== 4단계 추가: 고급 품질 평가 필드 (임시) ===================
                quality_dimensions={},  # 다음 작업에서 구현 예정
                quality_report="",
                improvement_suggestions=[],
                content_reliability=0.0,
                content_usefulness=0.0,
                content_accuracy=0.0
            )
            
            # 7. 캐시에 저장
            self.analysis_cache[cache_key] = analysis_result
            
            # 8. 통계 업데이트
            self._update_analysis_stats(analysis_result, start_time)
            
            logger.info(f"웹 콘텐츠 분석 완료: {url} (타입: {content_type}, 품질: {quality_score:.1f})")
            return analysis_result
            
        except Exception as e:
            logger.error(f"웹 콘텐츠 분석 오류: {e}")
            self.analysis_stats['failed_analyses'] += 1
            return self._create_error_result(url, f"분석 중 오류 발생: {str(e)}")
    
    async def _fetch_web_content(self, url: str) -> Optional[Dict[str, str]]:
        """웹 콘텐츠 가져오기 - web_search_ide 활용"""
        try:
            # web_search_ide의 visit_site 메서드 활용
            result = self.web_search.visit_site("content_analyzer", url, extract_code=False)
            
            if result.get('success'):
                return {
                    'title': result.get('title', ''),
                    'content': result.get('content_preview', ''),
                    'html': result.get('html_content', ''),  # 전체 HTML이 필요한 경우
                    'url': url
                }
            else:
                # 대안: 직접 HTTP 요청
                return await self._fetch_content_direct(url)
                
        except Exception as e:
            logger.error(f"웹 콘텐츠 가져오기 오류: {e}")
            return await self._fetch_content_direct(url)
    
    async def _fetch_content_direct(self, url: str) -> Optional[Dict[str, str]]:
        """직접 HTTP 요청으로 콘텐츠 가져오기"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # BeautifulSoup으로 파싱
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # 제목 추출
                        title_tag = soup.find('title')
                        title = title_tag.get_text().strip() if title_tag else "제목 없음"
                        
                        # 본문 텍스트 추출
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        text_content = soup.get_text()
                        clean_text = ' '.join(text_content.split())
                        
                        return {
                            'title': title,
                            'content': clean_text,
                            'html': html_content,
                            'url': url
                        }
                    else:
                        logger.warning(f"HTTP {response.status}: {url}")
                        return None
                        
        except Exception as e:
            logger.error(f"직접 콘텐츠 가져오기 오류: {e}")
            return None
    
    def _create_error_result(self, url: str, error_message: str) -> ContentAnalysisResult:
        """오류 결과 생성"""
        return ContentAnalysisResult(
            url=url,
            title="분석 실패",
            content_type="error",
            summary="",
            key_points=[],
            sentiment_score=0.0,
            sentiment_label="neutral",
            quality_score=0.0,
            topics=[],
            language="unknown",
            reading_time=0,
            complexity_level="unknown",
            analysis_timestamp=datetime.now().isoformat(),
            ai_model_used="none",
            word_count=0,
            image_count=0,
            link_count=0,
            error_message=error_message
        )
    
    def _update_analysis_stats(self, result: ContentAnalysisResult, start_time: datetime):
        """분석 통계 업데이트"""
        try:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.analysis_stats['total_analyzed'] += 1
            if not result.error_message:
                self.analysis_stats['successful_analyses'] += 1
            
            # 평균 처리 시간 업데이트
            current_avg = self.analysis_stats['average_processing_time']
            total = self.analysis_stats['total_analyzed']
            self.analysis_stats['average_processing_time'] = (current_avg * (total - 1) + processing_time) / total
            
            # 평균 품질 점수 업데이트
            if result.quality_score > 0:
                current_quality_avg = self.analysis_stats['average_quality_score']
                success_count = self.analysis_stats['successful_analyses']
                self.analysis_stats['average_quality_score'] = (current_quality_avg * (success_count - 1) + result.quality_score) / success_count
            
        except Exception as e:
            logger.error(f"통계 업데이트 오류: {e}")

    # =================== 배치 분석 메서드 ===================
    
    async def analyze_batch_urls(self, urls: List[str], max_concurrent: int = 5) -> BatchAnalysisReport:
        """배치 URL 분석"""
        start_time = datetime.now()
        
        try:
            # 캐시 확인
            urls_key = hashlib.md5(str(sorted(urls)).encode()).hexdigest()
            cache_key = f"batch_{urls_key}"
            
            if cache_key in self.batch_cache:
                logger.info("배치 분석 캐시 결과 반환")
                return self.batch_cache[cache_key]
            
            # 비동기 배치 분석
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def analyze_single_url(url):
                async with semaphore:
                    return await self.analyze_web_content(url)
            
            # 모든 URL 동시 분석
            tasks = [analyze_single_url(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 집계
            successful_results = []
            failed_count = 0
            
            for result in results:
                if isinstance(result, ContentAnalysisResult) and not result.error_message:
                    successful_results.append(result)
                else:
                    failed_count += 1
            
            # 리포트 생성
            report = self._generate_batch_report(successful_results, failed_count, len(urls), start_time)
            
            # 캐시 저장
            self.batch_cache[cache_key] = report
            
            logger.info(f"배치 분석 완료: {len(successful_results)}/{len(urls)} 성공")
            return report
            
        except Exception as e:
            logger.error(f"배치 분석 오류: {e}")
            return self._create_error_batch_report(len(urls), str(e))
    
    def _generate_batch_report(self, results: List[ContentAnalysisResult], failed_count: int, total_count: int, start_time: datetime) -> BatchAnalysisReport:
        """배치 분석 리포트 생성"""
        try:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if not results:
                return BatchAnalysisReport(
                    total_analyzed=total_count,
                    success_count=0,
                    failed_count=failed_count,
                    average_quality_score=0.0,
                    dominant_sentiment="neutral",
                    top_topics=[],
                    content_type_distribution={},
                    analysis_summary="분석된 콘텐츠가 없습니다.",
                    processing_time=processing_time,
                    report_timestamp=datetime.now().isoformat()
                )
            
            # 통계 계산
            avg_quality = sum(r.quality_score for r in results) / len(results)
            
            # 감정 분포
            sentiment_counts = {}
            for result in results:
                sentiment = result.sentiment_label
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)
            
            # 토픽 집계
            topic_counts = {}
            for result in results:
                for topic in result.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # 콘텐츠 타입 분포
            type_distribution = {}
            for result in results:
                content_type = result.content_type
                type_distribution[content_type] = type_distribution.get(content_type, 0) + 1
            
            # 요약 생성
            summary = f"총 {len(results)}개 콘텐츠 분석 완료. 평균 품질점수 {avg_quality:.1f}점, 주요 감정 {dominant_sentiment}"
            
            return BatchAnalysisReport(
                total_analyzed=total_count,
                success_count=len(results),
                failed_count=failed_count,
                average_quality_score=avg_quality,
                dominant_sentiment=dominant_sentiment,
                top_topics=top_topics,
                content_type_distribution=type_distribution,
                analysis_summary=summary,
                processing_time=processing_time,
                report_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"배치 리포트 생성 오류: {e}")
            return self._create_error_batch_report(total_count, str(e))
    
    def _create_error_batch_report(self, total_count: int, error_message: str) -> BatchAnalysisReport:
        """오류 배치 리포트 생성"""
        return BatchAnalysisReport(
            total_analyzed=total_count,
            success_count=0,
            failed_count=total_count,
            average_quality_score=0.0,
            dominant_sentiment="neutral",
            top_topics=[],
            content_type_distribution={},
            analysis_summary=f"배치 분석 실패: {error_message}",
            processing_time=0.0,
            report_timestamp=datetime.now().isoformat()
        )
    
    # =================== 4단계 추가: 정교한 품질 평가 시스템 ===================
    
    def _calculate_advanced_quality_score(self, title: str, content: str, url: str, 
                                        content_type: str, structure_info: Dict = None) -> Dict[str, Any]:
        """정교한 다차원 품질 평가"""
        try:
            # 콘텐츠 타입별 가중치 적용
            type_weights = self.content_type_quality_weights.get(content_type, 
                                                               self.content_type_quality_weights['general'])
            
            # 각 차원별 점수 계산
            dimension_scores = {}
            detailed_analysis = {}
            
            # 1. 신뢰도 (Reliability) 평가
            reliability_score, reliability_detail = self._evaluate_reliability(title, content, url, structure_info)
            dimension_scores['reliability'] = reliability_score * type_weights['reliability']
            detailed_analysis['reliability'] = reliability_detail
            
            # 2. 유용성 (Usefulness) 평가
            usefulness_score, usefulness_detail = self._evaluate_usefulness(title, content, content_type)
            dimension_scores['usefulness'] = usefulness_score * type_weights['usefulness']
            detailed_analysis['usefulness'] = usefulness_detail
            
            # 3. 정확성 (Accuracy) 평가
            accuracy_score, accuracy_detail = self._evaluate_accuracy(title, content, url)
            dimension_scores['accuracy'] = accuracy_score * type_weights['accuracy']
            detailed_analysis['accuracy'] = accuracy_detail
            
            # 4. 완성도 (Completeness) 평가
            completeness_score, completeness_detail = self._evaluate_completeness(title, content, structure_info)
            dimension_scores['completeness'] = completeness_score * type_weights['completeness']
            detailed_analysis['completeness'] = completeness_detail
            
            # 5. 가독성 (Readability) 평가
            readability_score, readability_detail = self._evaluate_readability(title, content, structure_info)
            dimension_scores['readability'] = readability_score * type_weights['readability']
            detailed_analysis['readability'] = readability_detail
            
            # 6. 독창성 (Originality) 평가
            originality_score, originality_detail = self._evaluate_originality(title, content, content_type)
            dimension_scores['originality'] = originality_score * type_weights['originality']
            detailed_analysis['originality'] = originality_detail
            
            # 언어 품질 평가
            language_quality = self._evaluate_language_quality(content)
            
            # 전체 품질 점수 계산 (가중평균)
            total_weight = sum(type_weights.values())
            overall_score = sum(dimension_scores.values()) / total_weight
            overall_score = min(100.0, max(0.0, overall_score))
            
            # 품질 등급 결정
            quality_grade = self._determine_quality_grade(overall_score)
            
            # 개선 제안사항 생성
            improvement_suggestions = self._generate_improvement_suggestions(
                dimension_scores, detailed_analysis, content_type
            )
            
            # 품질 리포트 생성
            quality_report = self._generate_quality_report(
                dimension_scores, detailed_analysis, language_quality, 
                quality_grade, content_type
            )
            
            return {
                'overall_score': overall_score,
                'quality_grade': quality_grade,
                'dimension_scores': dimension_scores,
                'detailed_analysis': detailed_analysis,
                'language_quality': language_quality,
                'improvement_suggestions': improvement_suggestions,
                'quality_report': quality_report,
                'content_type_weights': type_weights
            }
            
        except Exception as e:
            logger.error(f"고급 품질 평가 오류: {e}")
            return {
                'overall_score': 50.0,
                'quality_grade': 'C',
                'dimension_scores': {},
                'detailed_analysis': {},
                'language_quality': {},
                'improvement_suggestions': ['품질 평가 중 오류가 발생했습니다.'],
                'quality_report': '품질 평가를 완료할 수 없습니다.',
                'content_type_weights': {}
            }
    
    def _evaluate_reliability(self, title: str, content: str, url: str, structure_info: Dict = None) -> Tuple[float, Dict]:
        """신뢰도 평가"""
        try:
            score = 50.0  # 기본 점수
            details = {}
            
            domain = urlparse(url).netloc.lower()
            text_lower = f"{title} {content}".lower()
            
            # 출처 신뢰도 평가
            source_score = 0
            credible_domains = self.quality_dimensions['reliability']['indicators']['source_credibility']
            for domain_type in credible_domains:
                if domain_type in domain:
                    source_score += 20
                    break
            else:
                # 알려진 신뢰할 만한 사이트 체크
                if any(trusted in domain for trusted in ['naver', 'google', 'wikipedia', 'github']):
                    source_score += 10
            
            details['source_credibility'] = source_score
            score += source_score
            
            # 저자 전문성 평가
            expertise_score = 0
            expertise_indicators = self.quality_dimensions['reliability']['indicators']['author_expertise']
            expertise_matches = sum(1 for indicator in expertise_indicators if indicator in text_lower)
            expertise_score = min(15, expertise_matches * 5)
            
            details['author_expertise'] = expertise_score
            score += expertise_score
            
            # 인용 및 참고문헌 품질
            citation_score = 0
            citation_indicators = self.quality_dimensions['reliability']['indicators']['citation_quality']
            citation_matches = sum(1 for indicator in citation_indicators if indicator in text_lower)
            citation_score = min(10, citation_matches * 3)
            
            details['citation_quality'] = citation_score
            score += citation_score
            
            # 사실 확인 및 데이터 기반
            fact_score = 0
            fact_indicators = self.quality_dimensions['reliability']['indicators']['fact_checking']
            fact_matches = sum(1 for indicator in fact_indicators if indicator in text_lower)
            fact_score = min(10, fact_matches * 2)
            
            details['fact_checking'] = fact_score
            score += fact_score
            
            # HTTPS 사용 (보안)
            if url.startswith('https'):
                score += 5
                details['security'] = 5
            else:
                details['security'] = 0
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"신뢰도 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_usefulness(self, title: str, content: str, content_type: str) -> Tuple[float, Dict]:
        """유용성 평가"""
        try:
            score = 50.0
            details = {}
            text_lower = f"{title} {content}".lower()
            
            # 실용적 가치
            practical_score = 0
            practical_indicators = self.quality_dimensions['usefulness']['indicators']['practical_value']
            practical_matches = sum(1 for indicator in practical_indicators if indicator in text_lower)
            practical_score = min(25, practical_matches * 4)
            
            details['practical_value'] = practical_score
            score += practical_score
            
            # 실행 가능한 내용
            actionable_score = 0
            actionable_indicators = self.quality_dimensions['usefulness']['indicators']['actionable_content']
            actionable_matches = sum(1 for indicator in actionable_indicators if indicator in text_lower)
            actionable_score = min(20, actionable_matches * 3)
            
            details['actionable_content'] = actionable_score
            score += actionable_score
            
            # 문제 해결 능력
            problem_solving_score = 0
            problem_indicators = self.quality_dimensions['usefulness']['indicators']['problem_solving']
            problem_matches = sum(1 for indicator in problem_indicators if indicator in text_lower)
            problem_solving_score = min(15, problem_matches * 3)
            
            details['problem_solving'] = problem_solving_score
            score += problem_solving_score
            
            # 학습 가치
            learning_score = 0
            learning_indicators = self.quality_dimensions['usefulness']['indicators']['learning_value']
            learning_matches = sum(1 for indicator in learning_indicators if indicator in text_lower)
            learning_score = min(10, learning_matches * 2)
            
            details['learning_value'] = learning_score
            score += learning_score
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"유용성 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_accuracy(self, title: str, content: str, url: str) -> Tuple[float, Dict]:
        """정확성 평가"""
        try:
            score = 50.0
            details = {}
            text_lower = f"{title} {content}".lower()
            
            # 기술적 정밀성
            precision_score = 0
            precision_indicators = self.quality_dimensions['accuracy']['indicators']['technical_precision']
            precision_matches = sum(1 for indicator in precision_indicators if indicator in text_lower)
            precision_score = min(25, precision_matches * 8)
            
            details['technical_precision'] = precision_score
            score += precision_score
            
            # 오류 지시어 확인 (부정적 평가)
            error_penalty = 0
            error_indicators = self.quality_dimensions['accuracy']['indicators']['error_indicators']
            error_matches = sum(1 for indicator in error_indicators if indicator in text_lower)
            error_penalty = min(20, error_matches * 5)
            
            details['error_indicators'] = -error_penalty
            score -= error_penalty
            
            # 검증 표시
            verification_score = 0
            verification_indicators = self.quality_dimensions['accuracy']['indicators']['verification_marks']
            verification_matches = sum(1 for indicator in verification_indicators if indicator in text_lower)
            verification_score = min(15, verification_matches * 5)
            
            details['verification_marks'] = verification_score
            score += verification_score
            
            # 최신성 평가
            update_score = 0
            update_indicators = self.quality_dimensions['accuracy']['indicators']['update_frequency']
            update_matches = sum(1 for indicator in update_indicators if indicator in text_lower)
            update_score = min(10, update_matches * 3)
            
            details['update_frequency'] = update_score
            score += update_score
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"정확성 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_completeness(self, title: str, content: str, structure_info: Dict = None) -> Tuple[float, Dict]:
        """완성도 평가"""
        try:
            score = 50.0
            details = {}
            text_lower = f"{title} {content}".lower()
            
            # 포괄적 커버리지
            coverage_score = 0
            coverage_indicators = self.quality_dimensions['completeness']['indicators']['comprehensive_coverage']
            coverage_matches = sum(1 for indicator in coverage_indicators if indicator in text_lower)
            coverage_score = min(25, coverage_matches * 8)
            
            details['comprehensive_coverage'] = coverage_score
            score += coverage_score
            
            # 상세한 설명
            detail_score = 0
            detail_indicators = self.quality_dimensions['completeness']['indicators']['detailed_explanation']
            detail_matches = sum(1 for indicator in detail_indicators if indicator in text_lower)
            detail_score = min(20, detail_matches * 7)
            
            details['detailed_explanation'] = detail_score
            score += detail_score
            
            # 예제 제공
            example_score = 0
            example_indicators = self.quality_dimensions['completeness']['indicators']['example_provision']
            example_matches = sum(1 for indicator in example_indicators if indicator in text_lower)
            example_score = min(15, example_matches * 5)
            
            details['example_provision'] = example_score
            score += example_score
            
            # 단계별 설명
            step_score = 0
            step_indicators = self.quality_dimensions['completeness']['indicators']['step_by_step']
            step_matches = sum(1 for indicator in step_indicators if indicator in text_lower)
            step_score = min(10, step_matches * 3)
            
            details['step_by_step'] = step_score
            score += step_score
            
            # 콘텐츠 길이 보너스
            content_length = len(content)
            if content_length > 2000:
                length_bonus = min(10, (content_length - 2000) // 1000 * 2)
                score += length_bonus
                details['content_length_bonus'] = length_bonus
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"완성도 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_readability(self, title: str, content: str, structure_info: Dict = None) -> Tuple[float, Dict]:
        """가독성 평가"""
        try:
            score = 50.0
            details = {}
            text_lower = f"{title} {content}".lower()
            
            # 명확한 구조
            structure_score = 0
            structure_indicators = self.quality_dimensions['readability']['indicators']['clear_structure']
            structure_matches = sum(1 for indicator in structure_indicators if indicator in text_lower)
            structure_score = min(25, structure_matches * 8)
            
            details['clear_structure'] = structure_score
            score += structure_score
            
            # 간단한 언어
            language_score = 0
            language_indicators = self.quality_dimensions['readability']['indicators']['simple_language']
            language_matches = sum(1 for indicator in language_indicators if indicator in text_lower)
            language_score = min(20, language_matches * 7)
            
            details['simple_language'] = language_score
            score += language_score
            
            # 시각적 도구
            visual_score = 0
            visual_indicators = self.quality_dimensions['readability']['indicators']['visual_aids']
            visual_matches = sum(1 for indicator in visual_indicators if indicator in text_lower)
            visual_score = min(15, visual_matches * 5)
            
            details['visual_aids'] = visual_score
            score += visual_score
            
            # 포맷팅
            formatting_score = 0
            formatting_indicators = self.quality_dimensions['readability']['indicators']['formatting']
            formatting_matches = sum(1 for indicator in formatting_indicators if indicator in text_lower)
            formatting_score = min(10, formatting_matches * 3)
            
            # 구조 정보 활용
            if structure_info:
                if structure_info.get('heading_count', 0) > 2:
                    formatting_score += 5
                if structure_info.get('list_count', 0) > 0:
                    formatting_score += 3
                if structure_info.get('paragraph_count', 0) > 3:
                    formatting_score += 2
            
            details['formatting'] = formatting_score
            score += formatting_score
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"가독성 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_originality(self, title: str, content: str, content_type: str) -> Tuple[float, Dict]:
        """독창성 평가"""
        try:
            score = 50.0
            details = {}
            text_lower = f"{title} {content}".lower()
            
            # 독특한 관점
            perspective_score = 0
            perspective_indicators = self.quality_dimensions['originality']['indicators']['unique_perspective']
            perspective_matches = sum(1 for indicator in perspective_indicators if indicator in text_lower)
            perspective_score = min(25, perspective_matches * 8)
            
            details['unique_perspective'] = perspective_score
            score += perspective_score
            
            # 개인적 통찰
            insight_score = 0
            insight_indicators = self.quality_dimensions['originality']['indicators']['personal_insight']
            insight_matches = sum(1 for indicator in insight_indicators if indicator in text_lower)
            insight_score = min(20, insight_matches * 7)
            
            details['personal_insight'] = insight_score
            score += insight_score
            
            # 창의적 접근
            creative_score = 0
            creative_indicators = self.quality_dimensions['originality']['indicators']['creative_approach']
            creative_matches = sum(1 for indicator in creative_indicators if indicator in text_lower)
            creative_score = min(15, creative_matches * 5)
            
            details['creative_approach'] = creative_score
            score += creative_score
            
            # 사고 자극적
            thought_score = 0
            thought_indicators = self.quality_dimensions['originality']['indicators']['thought_provoking']
            thought_matches = sum(1 for indicator in thought_indicators if indicator in text_lower)
            thought_score = min(10, thought_matches * 3)
            
            details['thought_provoking'] = thought_score
            score += thought_score
            
            # 콘텐츠 타입별 조정
            if content_type == 'blog':
                score += 10  # 블로그는 개인적 특성이 중요
            elif content_type == 'news':
                score -= 5   # 뉴스는 객관성이 더 중요
            
            return min(100.0, max(0.0, score)), details
            
        except Exception as e:
            logger.error(f"독창성 평가 오류: {e}")
            return 50.0, {'error': str(e)}
    
    def _evaluate_language_quality(self, content: str) -> Dict[str, Any]:
        """언어 품질 평가"""
        try:
            analysis = {
                'grammar_errors': 0,
                'spelling_errors': 0,
                'good_expressions': 0,
                'vocabulary_diversity': 0,
                'sentence_variety': 0,
                'overall_language_score': 50.0
            }
            
            # 문법 오류 검사
            for pattern in self.language_quality_indicators['grammar_errors']:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                analysis['grammar_errors'] += matches
            
            # 맞춤법 오류 검사
            for pattern in self.language_quality_indicators['spelling_errors']:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                analysis['spelling_errors'] += matches
            
            # 좋은 표현 확인
            for pattern in self.language_quality_indicators['good_expressions']:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                analysis['good_expressions'] += matches
            
            # 어휘 다양성 (고유 단어 수 / 전체 단어 수)
            words = re.findall(r'[가-힣a-zA-Z]+', content)
            if words:
                unique_words = set(words)
                analysis['vocabulary_diversity'] = len(unique_words) / len(words) * 100
            
            # 문장 다양성 (문장 길이의 표준편차)
            sentences = re.split(r'[.!?]', content)
            if len(sentences) > 1:
                sentence_lengths = [len(s.strip()) for s in sentences if s.strip()]
                if sentence_lengths:
                    import statistics
                    analysis['sentence_variety'] = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
            
            # 전체 언어 품질 점수 계산
            score = 70.0
            score -= analysis['grammar_errors'] * 5  # 문법 오류 페널티
            score -= analysis['spelling_errors'] * 3  # 맞춤법 오류 페널티
            score += min(20, analysis['good_expressions'] * 2)  # 좋은 표현 보너스
            score += min(10, analysis['vocabulary_diversity'] * 0.2)  # 어휘 다양성 보너스
            
            analysis['overall_language_score'] = min(100.0, max(0.0, score))
            
            return analysis
            
        except Exception as e:
            logger.error(f"언어 품질 평가 오류: {e}")
            return {
                'grammar_errors': 0,
                'spelling_errors': 0,
                'good_expressions': 0,
                'vocabulary_diversity': 0,
                'sentence_variety': 0,
                'overall_language_score': 50.0,
                'error': str(e)
            }
    
    def _determine_quality_grade(self, score: float) -> str:
        """품질 등급 결정"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'C+'
        elif score >= 65:
            return 'C'
        elif score >= 60:
            return 'D+'
        elif score >= 55:
            return 'D'
        else:
            return 'F'
    
    def _generate_improvement_suggestions(self, dimension_scores: Dict[str, float], 
                                        detailed_analysis: Dict[str, Dict], 
                                        content_type: str) -> List[str]:
        """개선 제안사항 생성"""
        suggestions = []
        
        try:
            # 각 차원별 점수를 기준으로 개선 제안
            for dimension, score in dimension_scores.items():
                if score < 60:  # 낮은 점수의 차원에 대해 제안
                    if dimension == 'reliability':
                        suggestions.append("📊 신뢰도 개선: 출처를 명확히 하고, 전문가 의견이나 데이터를 추가하세요.")
                        suggestions.append("🔗 참고문헌이나 관련 링크를 포함하여 정보의 신뢰성을 높이세요.")
                    
                    elif dimension == 'usefulness':
                        suggestions.append("💡 유용성 개선: 실용적인 팁이나 실행 가능한 조언을 더 추가하세요.")
                        suggestions.append("🎯 독자가 바로 적용할 수 있는 구체적인 방법을 제시하세요.")
                    
                    elif dimension == 'accuracy':
                        suggestions.append("✅ 정확성 개선: 최신 정보로 업데이트하고 사실 확인을 강화하세요.")
                        suggestions.append("🔍 기술적 세부사항의 정밀도를 높이고 오류를 점검하세요.")
                    
                    elif dimension == 'completeness':
                        suggestions.append("📝 완성도 개선: 더 상세한 설명과 예제를 추가하세요.")
                        suggestions.append("📋 단계별 가이드나 체크리스트를 포함하세요.")
                    
                    elif dimension == 'readability':
                        suggestions.append("📖 가독성 개선: 명확한 제목과 소제목으로 구조를 개선하세요.")
                        suggestions.append("🎨 시각적 요소(이미지, 차트, 목록)를 활용하세요.")
                    
                    elif dimension == 'originality':
                        suggestions.append("💭 독창성 개선: 개인적 경험이나 독특한 관점을 추가하세요.")
                        suggestions.append("🌟 새로운 아이디어나 창의적 접근법을 시도하세요.")
            
            # 콘텐츠 타입별 특화 제안
            if content_type == 'news':
                suggestions.append("📰 뉴스 특화: 5W1H(누가, 언제, 어디서, 무엇을, 왜, 어떻게)를 명확히 하세요.")
            elif content_type == 'blog':
                suggestions.append("✍️ 블로그 특화: 개인적 스토리텔링과 독자와의 소통을 강화하세요.")
            elif content_type == 'tech_doc':
                suggestions.append("⚙️ 기술문서 특화: 코드 예제와 단계별 설명을 더 상세히 제공하세요.")
            elif content_type == 'tutorial':
                suggestions.append("🎓 튜토리얼 특화: 학습자가 따라할 수 있는 명확한 단계를 제시하세요.")
            
            # 언어 품질 관련 제안
            suggestions.append("📚 언어 품질: 맞춤법과 문법을 재점검하고 다양한 어휘를 활용하세요.")
            
            return suggestions[:5]  # 최대 5개 제안
            
        except Exception as e:
            logger.error(f"개선 제안사항 생성 오류: {e}")
            return ["품질 개선을 위해 내용을 재검토해 주세요."]
    
    def _generate_quality_report(self, dimension_scores: Dict[str, float], 
                               detailed_analysis: Dict[str, Dict], 
                               language_quality: Dict[str, Any],
                               quality_grade: str, content_type: str) -> str:
        """품질 리포트 생성"""
        try:
            report_lines = []
            
            # 전체 등급 및 요약
            overall_score = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 50.0
            report_lines.append(f"🏆 **전체 품질 등급: {quality_grade}** (점수: {overall_score:.1f}/100)")
            report_lines.append(f"📄 콘텐츠 타입: {content_type}")
            report_lines.append("")
            
            # 차원별 상세 분석
            report_lines.append("📊 **차원별 분석 결과**")
            
            dimension_names = {
                'reliability': '신뢰도',
                'usefulness': '유용성', 
                'accuracy': '정확성',
                'completeness': '완성도',
                'readability': '가독성',
                'originality': '독창성'
            }
            
            for dimension, score in dimension_scores.items():
                name = dimension_names.get(dimension, dimension)
                grade = self._determine_quality_grade(score)
                
                if score >= 80:
                    emoji = "🟢"
                elif score >= 60:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                
                report_lines.append(f"{emoji} **{name}**: {grade} ({score:.1f}점)")
                
                # 세부 분석 정보
                if dimension in detailed_analysis:
                    details = detailed_analysis[dimension]
                    positive_aspects = [k for k, v in details.items() if isinstance(v, (int, float)) and v > 0]
                    if positive_aspects:
                        report_lines.append(f"   ✅ 강점: {', '.join(positive_aspects[:3])}")
            
            report_lines.append("")
            
            # 언어 품질 분석
            if language_quality:
                report_lines.append("📝 **언어 품질 분석**")
                lang_score = language_quality.get('overall_language_score', 50)
                lang_grade = self._determine_quality_grade(lang_score)
                
                if lang_score >= 80:
                    emoji = "🟢"
                elif lang_score >= 60:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                
                report_lines.append(f"{emoji} **언어 품질**: {lang_grade} ({lang_score:.1f}점)")
                
                if language_quality.get('grammar_errors', 0) > 0:
                    report_lines.append(f"   ⚠️ 문법 오류: {language_quality['grammar_errors']}개")
                if language_quality.get('spelling_errors', 0) > 0:
                    report_lines.append(f"   ⚠️ 맞춤법 오류: {language_quality['spelling_errors']}개")
                if language_quality.get('good_expressions', 0) > 0:
                    report_lines.append(f"   ✅ 좋은 표현: {language_quality['good_expressions']}개")
                
                vocab_diversity = language_quality.get('vocabulary_diversity', 0)
                if vocab_diversity > 0:
                    report_lines.append(f"   📚 어휘 다양성: {vocab_diversity:.1f}%")
             
            report_lines.append("")
            
            # 종합 평가
            report_lines.append("🎯 **종합 평가**")
            if overall_score >= 85:
                report_lines.append("우수한 품질의 콘텐츠입니다. 대부분의 품질 기준을 충족하고 있습니다.")
            elif overall_score >= 70:
                report_lines.append("양호한 품질의 콘텐츠입니다. 일부 영역에서 개선의 여지가 있습니다.")
            elif overall_score >= 60:
                report_lines.append("보통 수준의 콘텐츠입니다. 여러 영역에서 개선이 필요합니다.")
            else:
                report_lines.append("품질 개선이 필요한 콘텐츠입니다. 전반적인 재검토를 권장합니다.")
            
            return "\n".join(report_lines)
            
        except Exception as e:
# 전역 인스턴스 생성
analyzer = None

def get_content_analyzer():
    """콘텐츠 분석기 인스턴스 반환"""
    global analyzer
    if analyzer is None:
        analyzer = IntelligentContentAnalyzer()
    return analyzer 