import React, { useState } from 'react';
import './PricingStatsSection.css';
import { getConfidenceClass } from '../../utils/statsUtils';

const PricingStatsSection = ({ amountStats }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('overall');
  
  const periods = [
    { key: '2m', label: '최근 2개월' },
    { key: '4m', label: '최근 4개월' },
    { key: '6m', label: '최근 6개월' },
    { key: '12m', label: '최근 1년' },
    { key: 'overall', label: '전체' }
  ];

  // 현재 선택된 기간의 데이터 추출
  const currentData = selectedPeriod === 'overall' 
    ? amountStats?.overall 
    : amountStats?.periods?.[selectedPeriod];

  // 민사 여부 판단 (백엔드에서 넘겨준 major_category 확인 또는 soga 데이터 존재 여부)
  const isCivil = amountStats?.major_category === "민사" || !!currentData?.soga;

  if (!currentData) {
    return (
      <div className="stats-info-section fade-in">
        <div className="section-header">
          <h3>해당 사건 유형의 약정금 통계</h3>
          <div className="period-selector">
            {periods.map((p) => (
              <button
                key={p.key}
                className={`period-tab ${selectedPeriod === p.key ? 'active' : ''}`}
                onClick={() => setSelectedPeriod(p.key)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <div className="no-data-message">
          해당 기간의 충분한 통계 데이터가 없습니다.
        </div>
      </div>
    );
  }

  // 렌더링할 카드 목록 정의
  const cardConfigs = [
    { key: 'payment', title: '약정금', type: 'currency' },
    { key: 'reward', title: '성공 보수', type: 'currency' },
  ];

  // 민사일 경우에만 소가 및 비율 카드 추가
  if (isCivil) {
    // cardConfigs.push({ key: 'soga', title: '소가', type: 'currency' });
    cardConfigs.push({ key: 'reward_to_soga_ratio', title: '소가 대비 성공보수 비율', type: 'percentage' });
  }

  return (
    <div className="stats-info-section fade-in">
      <div className="section-header">
        <h3>해당 사건 유형의 약정금 통계</h3>
        <div className="period-selector">
          {periods.map((p) => (
            <button
              key={p.key}
              className={`period-tab ${selectedPeriod === p.key ? 'active' : ''}`}
              onClick={() => setSelectedPeriod(p.key)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="stats-cards-grid">
        {cardConfigs.map(({ key, title, type }) => {
          const stat = currentData[key];

          if (!stat || stat === 0) return null;

          return (
            <div key={key} className={`stat-card ${key === 'reward_to_soga_ratio' ? 'ratio-card' : ''}`}>
              <div className="stat-card-header">
                <h4>{title}</h4>
              </div>
              
              <div className="stat-card-body">
                {type === 'currency' ? (
                  <>
                    <div className="stat-value-row">
                      <span className="stat-label">중간값</span>
                      <span className="stat-value main">
                        {stat.median?.toLocaleString()}원
                      </span>
                    </div>
                    <div className="stat-range">
                      <div className="range-item">
                        <span className="range-label">하위 25%</span>
                        <span className="range-value">{stat.lower_25?.toLocaleString()}원</span>
                      </div>
                      <div className="range-divider">~</div>
                      <div className="range-item">
                        <span className="range-label">상위 25%</span>
                        <span className="range-value">{stat.upper_75?.toLocaleString()}원</span>
                      </div>
                    </div>
                  </>
                ) : (
                  /* 비율(Percentage) 표시 로직 */
                  <div className="stat-value-row ratio-display">
                    <span className="stat-label">평균 비율</span>
                    <span className="stat-value main ratio">
                      {(stat * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PricingStatsSection;