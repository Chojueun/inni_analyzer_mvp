# webpage_generator.py

"""
분석 결과를 다크모드 + 인터랙티브 웹페이지로 생성
- 다크 테마 디자인
- 클릭 가능한 요소들
- 애니메이션 효과
- 반응형 디자인
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List

def process_analysis_content(result: str) -> str:
    """분석 결과를 더 읽기 쉽게 구조화"""
    paragraphs = result.split('\n\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        if para.strip():
            if para.startswith('#') or para.startswith('##'):
                formatted_paragraphs.append(f'<h3 class="content-subtitle">{para.strip("# ")}</h3>')
            elif para.startswith('-') or para.startswith('•'):
                items = para.split('\n')
                list_html = '<ul class="content-list">'
                for item in items:
                    if item.strip():
                        list_html += f'<li>{item.strip("- •")}</li>'
                list_html += '</ul>'
                formatted_paragraphs.append(list_html)
            else:
                formatted_paragraphs.append(f'<p class="content-text">{para}</p>')
    
    return '\n'.join(formatted_paragraphs)

def add_visual_elements(analysis_results: List[Dict]) -> List[Dict]:
    """분석 결과에 시각적 요소 추가"""
    enhanced_results = []
    
    for result in analysis_results:
        step_type = result.get('step', '').lower()
        
        if '요구사항' in step_type:
            icon = "🎯"
            color = "#00d4ff"
            category = "requirements"
        elif '추론' in step_type or 'reasoning' in step_type:
            icon = "🧠"
            color = "#ff6b6b"
            category = "reasoning"
        elif '사례' in step_type or 'comparison' in step_type:
            icon = "📚"
            color = "#4ecdc4"
            category = "comparison"
        elif '전략' in step_type or 'strategy' in step_type:
            icon = "��"
            color = "#45b7d1"
            category = "strategy"
        else:
            icon = "��"
            color = "#96ceb4"
            category = "analysis"
        
        enhanced_result = result.copy()
        enhanced_result['icon'] = icon
        enhanced_result['color'] = color
        enhanced_result['category'] = category
        enhanced_results.append(enhanced_result)
    
    return enhanced_results

def generate_dark_interactive_webpage(analysis_results: List[Dict], project_info: Dict) -> str:
    """다크모드 + 인터랙티브 웹페이지 HTML 생성"""
    
    # 시각적 요소 추가
    enhanced_results = add_visual_elements(analysis_results)
    
    html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_info.get('project_name', '프로젝트')} 분석 보고서</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --bg-primary: #0a0a0a;
            --bg-secondary: #1a1a1a;
            --bg-card: #2a2a2a;
            --bg-hover: #3a3a3a;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --text-muted: #808080;
            --accent-blue: #00d4ff;
            --accent-purple: #8b5cf6;
            --accent-green: #10b981;
            --accent-red: #ff6b6b;
            --accent-yellow: #fbbf24;
            --border-color: #404040;
            --shadow-light: 0 4px 6px rgba(0, 0, 0, 0.3);
            --shadow-medium: 0 8px 25px rgba(0, 0, 0, 0.4);
            --shadow-heavy: 0 15px 35px rgba(0, 0, 0, 0.5);
        }}
        
        body {{
            font-family: 'Inter', 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, #1a1a2e 50%, #16213e 100%);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        
        /* 헤더 스타일 */
        .header {{
            text-align: center;
            margin-bottom: 60px;
            padding: 60px 40px;
            background: rgba(42, 42, 42, 0.8);
            backdrop-filter: blur(20px);
            border-radius: 25px;
            box-shadow: var(--shadow-medium);
            border: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 30%, rgba(0, 212, 255, 0.1) 50%, transparent 70%);
            animation: shimmer 3s infinite;
        }}
        
        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        
        .header h1 {{
            font-size: 3.5rem;
            margin-bottom: 20px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            position: relative;
            z-index: 1;
        }}
        
        .header p {{
            font-size: 1.3rem;
            color: var(--text-secondary);
            position: relative;
            z-index: 1;
        }}
        
        /* 통계 카드 그리드 */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            margin-bottom: 60px;
        }}
        
        .stat-card {{
            background: rgba(42, 42, 42, 0.8);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px 30px;
            text-align: center;
            box-shadow: var(--shadow-medium);
            border: 1px solid var(--border-color);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            cursor: pointer;
        }}
        
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-10px) scale(1.02);
            box-shadow: var(--shadow-heavy);
            background: rgba(58, 58, 58, 0.9);
        }}
        
        .stat-card:hover::before {{
            transform: scaleX(1);
        }}
        
        .stat-icon {{
            font-size: 3rem;
            margin-bottom: 20px;
            display: block;
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover .stat-icon {{
            transform: scale(1.1);
        }}
        
        .stat-title {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 15px;
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}
        
        /* 분석 섹션 */
        .analysis-section {{
            background: rgba(42, 42, 42, 0.8);
            backdrop-filter: blur(20px);
            border-radius: 25px;
            padding: 50px 40px;
            margin-bottom: 40px;
            box-shadow: var(--shadow-medium);
            border: 1px solid var(--border-color);
        }}
        
        .section-header {{
            text-align: center;
            margin-bottom: 50px;
        }}
        
        .section-title {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 20px;
        }}
        
        .section-subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        
        /* 필터 버튼 */
        .filter-buttons {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            background: rgba(58, 58, 58, 0.8);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
        }}
        
        .filter-btn:hover, .filter-btn.active {{
            background: var(--accent-blue);
            color: var(--text-primary);
            transform: translateY(-2px);
            box-shadow: var(--shadow-light);
        }}
        
        /* 결과 카드 그리드 */
        .result-grid {{
            display: grid;
            gap: 30px;
        }}
        
        .result-card {{
            background: rgba(58, 58, 58, 0.8);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 30px;
            border-left: 5px solid var(--accent-blue);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            cursor: pointer;
            overflow: hidden;
        }}
        
        .result-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent, rgba(0, 212, 255, 0.05), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        
        .result-card:hover {{
            transform: translateX(10px) scale(1.02);
            box-shadow: var(--shadow-heavy);
            background: rgba(74, 74, 74, 0.9);
        }}
        
        .result-card:hover::before {{
            opacity: 1;
        }}
        
        .result-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            position: relative;
            z-index: 1;
        }}
        
        .result-icon {{
            font-size: 2.5rem;
            margin-right: 20px;
            transition: transform 0.3s ease;
        }}
        
        .result-card:hover .result-icon {{
            transform: rotate(10deg) scale(1.1);
        }}
        
        .result-title {{
            font-size: 1.4rem;
            font-weight: 600;
            color: var(--text-primary);
        }}
        
        .result-content {{
            font-size: 1.1rem;
            line-height: 1.7;
            color: var(--text-secondary);
            background: rgba(42, 42, 42, 0.8);
            padding: 25px;
            border-radius: 15px;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
            position: relative;
            z-index: 1;
            max-height: 200px;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        
        .result-card.expanded .result-content {{
            max-height: none;
        }}
        
        .expand-btn {{
            position: absolute;
            bottom: 10px;
            right: 10px;
            background: var(--accent-blue);
            color: var(--text-primary);
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            z-index: 2;
        }}
        
        .expand-btn:hover {{
            background: var(--accent-purple);
            transform: scale(1.05);
        }}
        
        /* 콘텐츠 스타일 */
        .content-subtitle {{
            color: var(--accent-blue);
            margin: 20px 0 10px 0;
            font-size: 1.2rem;
            font-weight: 600;
        }}
        
        .content-text {{
            margin: 10px 0;
            color: var(--text-secondary);
        }}
        
        .content-list {{
            margin: 10px 0;
            padding-left: 20px;
            color: var(--text-secondary);
        }}
        
        .content-list li {{
            margin: 5px 0;
        }}
        
        /* 푸터 */
        .footer {{
            text-align: center;
            padding: 40px;
            color: var(--text-muted);
            margin-top: 60px;
            border-top: 1px solid var(--border-color);
        }}
        
        .footer p {{
            margin: 5px 0;
        }}
        
        /* 반응형 */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2.5rem;
            }}
            .stat-card {{
                padding: 30px 20px;
            }}
            .analysis-section {{
                padding: 30px 20px;
            }}
            .filter-buttons {{
                flex-direction: column;
                align-items: center;
            }}
        }}
        
        /* 애니메이션 */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .result-card {{
            animation: fadeInUp 0.6s ease forwards;
        }}
        
        .result-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .result-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .result-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .result-card:nth-child(4) {{ animation-delay: 0.4s; }}
        .result-card:nth-child(5) {{ animation-delay: 0.5s; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌙 {project_info.get('project_name', '프로젝트')}</h1>
            <p>AI-Driven Architecture Analysis Report</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card" onclick="showDetails('project')">
                <span class="stat-icon">🏢</span>
                <div class="stat-title">프로젝트명</div>
                <div class="stat-value">{project_info.get('project_name', 'N/A')}</div>
            </div>
            <div class="stat-card" onclick="showDetails('building')">
                <span class="stat-icon">🏗️</span>
                <div class="stat-title">건물용도</div>
                <div class="stat-value">{project_info.get('building_type', 'N/A')}</div>
            </div>
            <div class="stat-card" onclick="showDetails('location')">
                <span class="stat-icon">📍</span>
                <div class="stat-title">대지위치</div>
                <div class="stat-value">{project_info.get('site_location', 'N/A')}</div>
            </div>
            <div class="stat-card" onclick="showDetails('owner')">
                <span class="stat-icon">👥</span>
                <div class="stat-title">건축주</div>
                <div class="stat-value">{project_info.get('owner', 'N/A')}</div>
            </div>
        </div>
        
        <div class="analysis-section">
            <div class="section-header">
                <h2 class="section-title">📋 분석 결과</h2>
                <p class="section-subtitle">클릭하여 상세 내용을 확인하세요</p>
            </div>
            
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="filterResults('all')">전체</button>
                <button class="filter-btn" onclick="filterResults('requirements')">요구사항</button>
                <button class="filter-btn" onclick="filterResults('reasoning')">추론</button>
                <button class="filter-btn" onclick="filterResults('comparison')">사례</button>
                <button class="filter-btn" onclick="filterResults('strategy')">전략</button>
            </div>
            
            <div class="result-grid">
"""
    
    # 분석 결과 카드들 생성
    for i, result in enumerate(enhanced_results, 1):
        processed_content = process_analysis_content(result.get('result', '분석 결과 없음'))
        
        card_html = f"""
                <div class="result-card" data-category="{result.get('category', 'analysis')}" onclick="toggleCard(this)">
                    <div class="result-header">
                        <span class="result-icon" style="color: {result.get('color', '#00d4ff')}">{result.get('icon', '📊')}</span>
                        <div class="result-title">{result.get('step', f'분석 단계 {i}')}</div>
                    </div>
                    <div class="result-content">
                        {processed_content}
                    </div>
                    <button class="expand-btn" onclick="event.stopPropagation(); toggleExpand(this)">더보기</button>
                </div>
"""
        html_template += card_html
    
    html_template += f"""
            </div>
        </div>
        
        <div class="footer">
            <p>생성일: {datetime.now().strftime("%Y년 %m월 %d일 %H:%M")}</p>
            <p>ArchInsight - AI-driven Project Insight & Workflow</p>
        </div>
    </div>
    
    <script>
        // 카드 확장/축소
        function toggleExpand(btn) {{
            const card = btn.closest('.result-card');
            card.classList.toggle('expanded');
            btn.textContent = card.classList.contains('expanded') ? '접기' : '더보기';
        }}
        
        // 카드 클릭 효과
        function toggleCard(card) {{
            card.style.transform = 'scale(0.98)';
            setTimeout(() => {{
                card.style.transform = '';
            }}, 150);
        }}
        
        // 필터링
        function filterResults(category) {{
            const cards = document.querySelectorAll('.result-card');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // 버튼 활성화 상태 변경
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // 카드 필터링
            cards.forEach(card => {{
                if (category === 'all' || card.dataset.category === category) {{
                    card.style.display = 'block';
                    card.style.animation = 'fadeInUp 0.6s ease forwards';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
        
        // 상세 정보 표시
        function showDetails(type) {{
            const details = {{
                project: '프로젝트 기본 정보',
                building: '건물 용도 및 규모',
                location: '대지 위치 및 환경',
                owner: '건축주 정보'
            }};
            
            alert(details[type] + '\\n\\n더 자세한 정보는 PDF 보고서를 확인하세요.');
        }}
        
        // 페이지 로드 시 애니메이션
        document.addEventListener('DOMContentLoaded', function() {{
            const cards = document.querySelectorAll('.result-card');
            cards.forEach((card, index) => {{
                card.style.animationDelay = `${{(index + 1) * 0.1}}s`;
            }});
        }});
    </script>
</body>
</html>
"""
    
    return html_template

def generate_card_webpage(analysis_results: List[Dict], project_info: Dict) -> str:
    """기존 함수 호환성을 위한 래퍼"""
    return generate_dark_interactive_webpage(analysis_results, project_info)

def create_webpage_download_button(analysis_results: List[Dict], project_info: Dict, show_warning: bool = True):
    """웹페이지 다운로드 버튼 생성"""
    
    if not analysis_results:
        if show_warning:
            st.warning("생성된 분석 결과가 없습니다.")
        return
    
    # HTML 생성
    html_content = generate_dark_interactive_webpage(analysis_results, project_info)
    
    # 다운로드 버튼
    st.download_button(
        label="🌙 다크모드 인터랙티브 웹페이지 다운로드",
        data=html_content,
        file_name=f"{project_info.get('project_name', '분석보고서')}_다크모드_웹페이지.html",
        mime="text/html",
        help="다크모드 + 인터랙티브 요소가 포함된 현대적인 웹페이지를 다운로드합니다.",
        key=f"dark_webpage_download_{project_info.get('project_name', 'default')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # 미리보기 표시
    st.markdown("### 🌙 다크모드 결과 미리보기")
    st.components.v1.html(html_content, height=800, scrolling=True) 