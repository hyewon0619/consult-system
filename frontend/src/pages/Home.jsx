import { FIRM_NAME } from "../config";
import React from 'react';
import './Home.css';

const Home = ({ onSelectMode }) => {
  const modes = [
    { 
      id: 'demo', 
      title: '전체 프로세스 데모', 
      desc: '정보 추출부터 리포트 작성까지\n전체 과정을 체험해요',
      icon: '🚀'
    },
    {
      id: 'caseMatch',
      title: '유사 사례 매칭',
      desc: '상담 내역을 분석하여\n가장 유사한 승소 사례를 매칭해요',
      icon: '🔍'
    },
    {
      id: 'report',
      title: 'AI 업무 사례 작성',
      desc: '사례 데이터를 바탕으로\n업무 사례 리포트를 생성해요',
      icon: '🖋️'
    }
  ];

  return (
    <div className="home-fixed-wrapper">
      <div className="home-content-container">
        <header className="home-header-section">
          <h1>{FIRM_NAME} AI</h1>
          <p>업무 효율을 높이는 스마트한 법률 보조 솔루션들이 있어요.</p>
        </header>

        <div className="mode-selection-grid">
          {modes.map(mode => (
            <div key={mode.id} className="mode-card-item">
              <div className="icon-circle-container">
                <span className="mode-main-icon">{mode.icon}</span>
              </div>
              <h3>{mode.title}</h3>
              <p>{mode.desc}</p>
              <button
                className="start-action-btn"
                onClick={() => onSelectMode(mode.id)}
              >
                시작하기 →
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Home;