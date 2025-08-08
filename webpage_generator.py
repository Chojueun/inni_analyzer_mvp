# webpage_generator.py

"""
분석 결과를 Card 형식 웹페이지로 생성
- Gamma 스타일의 프레젠테이션
- 반응형 디자인
- 애니메이션 효과
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List

def generate_card_webpage(analysis_results: List[Dict], project_info: Dict) -> str:
    """Card 형식 웹페이지 HTML 생성"""
    
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
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f8f9fa;
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 40px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .info-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .card-icon {{
            font-size: 2.5rem;
            margin-bottom: 15px;
        }}
        
        .card-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #555;
            margin-bottom: 10px;
        }}
        
        .card-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }}
        
        .card-description {{
            font-size: 0.9rem;
            color: #777;
        }}
        
        .strategy-overview {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .strategy-overview h2 {{
            text-align: center;
            font-size: 1.8rem;
            margin-bottom: 30px;
            color: #333;
        }}
        
        .overview-content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }}
        
        .current-situation {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #dc3545;
        }}
        
        .current-situation h3 {{
            color: #dc3545;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}
        
        .situation-item {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            padding: 8px 0;
        }}
        
        .situation-icon {{
            color: #dc3545;
            margin-right: 10px;
            font-size: 0.8rem;
        }}
        
        .flowchart {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #28a745;
        }}
        
        .flowchart h3 {{
            color: #28a745;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}
        
        .flowchart-diagram {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
        }}
        
        .flowchart-box {{
            background: white;
            padding: 12px 20px;
            border-radius: 8px;
            border: 2px solid #ddd;
            text-align: center;
            font-weight: 500;
            min-width: 150px;
        }}
        
        .flowchart-box.main {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .flowchart-box.crisis {{
            background: #dc3545;
            color: white;
            border-color: #dc3545;
        }}
        
        .flowchart-box.opportunity {{
            background: #28a745;
            color: white;
            border-color: #28a745;
        }}
        
        .analysis-results {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .analysis-results h2 {{
            text-align: center;
            font-size: 1.8rem;
            margin-bottom: 30px;
            color: #333;
        }}
        
        .result-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }}
        
        .result-card h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }}
        
        .result-content {{
            color: #555;
            line-height: 1.6;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #777;
            font-size: 0.9rem;
        }}
        
        @media (max-width: 768px) {{
            .overview-content {{
                grid-template-columns: 1fr;
            }}
            
            .info-cards {{
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {project_info.get('project_name', '프로젝트')} 분석 보고서</h1>
            <p>AI-driven Project Insight & Analysis</p>
        </div>
        
        <div class="info-cards">
            <div class="card">
                <div class="card-icon">📈</div>
                <div class="card-title">프로젝트 규모</div>
                <div class="card-value">{project_info.get('site_area', 'N/A')}</div>
                <div class="card-description">대지면적</div>
            </div>
            <div class="card">
                <div class="card-icon">🏢</div>
                <div class="card-title">건물용도</div>
                <div class="card-value">{project_info.get('building_type', 'N/A')}</div>
                <div class="card-description">주요 기능</div>
            </div>
            <div class="card">
                <div class="card-icon">📍</div>
                <div class="card-title">대지위치</div>
                <div class="card-value">{project_info.get('site_location', 'N/A')}</div>
                <div class="card-description">입지 조건</div>
            </div>
            <div class="card">
                <div class="card-icon">👥</div>
                <div class="card-title">건축주</div>
                <div class="card-value">{project_info.get('owner', 'N/A')}</div>
                <div class="card-description">프로젝트 발주</div>
            </div>
        </div>
        
        <div class="strategy-overview">
            <h2>📋 분석 개요</h2>
            <div class="overview-content">
                <div class="current-situation">
                    <h3>현재 상황</h3>
                    <div class="situation-item">
                        <span class="situation-icon">▶</span>
                        <span>프로젝트 기본 정보 분석 완료</span>
                    </div>
                    <div class="situation-item">
                        <span class="situation-icon">▶</span>
                        <span>분석 단계 {len(analysis_results)}개 진행</span>
                    </div>
                    <div class="situation-item">
                        <span class="situation-icon">▶</span>
                        <span>AI 기반 인사이트 도출</span>
                    </div>
                </div>
                <div class="flowchart">
                    <h3>분석 프로세스</h3>
                    <div class="flowchart-diagram">
                        <div class="flowchart-box main">프로젝트 분석</div>
                        <div class="flowchart-box crisis">요구사항 분석</div>
                        <div class="flowchart-box opportunity">전략 제언</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="analysis-results">
            <h2>📊 분석 결과</h2>
"""
    
    # 분석 결과 카드들 생성
    for i, result in enumerate(analysis_results, 1):
        card_html = f"""
            <div class="result-card">
                <h3>📋 {result.get('step', f'분석 단계 {i}')}</h3>
                <div class="result-content">
                    {result.get('result', '분석 결과 없음')}
                </div>
            </div>
"""
        html_template += card_html
    
    html_template += f"""
        </div>
        
        <div class="footer">
            <p>생성일: {datetime.now().strftime("%Y년 %m월 %d일 %H:%M")}</p>
            <p>ArchInsight - AI-driven Project Insight & Workflow</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_template

def create_webpage_download_button(analysis_results: List[Dict], project_info: Dict, show_warning: bool = True):
    """웹페이지 다운로드 버튼 생성"""
    
    if not analysis_results:
        if show_warning:
            st.warning("생성된 분석 결과가 없습니다.")
        return
    
    # HTML 생성
    html_content = generate_card_webpage(analysis_results, project_info)
    
    # 다운로드 버튼
    st.download_button(
        label="🌐 Card 형식 웹페이지 다운로드",
        data=html_content,
        file_name=f"{project_info.get('project_name', '분석보고서')}_웹페이지.html",
        mime="text/html",
        help="Gamma 스타일의 반응형 웹페이지를 다운로드합니다."
    )
    
    # 미리보기 표시
    st.markdown("### �� 웹페이지 미리보기")
    st.components.v1.html(html_content, height=800, scrolling=True) 