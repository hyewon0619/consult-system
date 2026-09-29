import React from "react";
import './StatsSummarySection.css'

const StatsSummarySection = ({ totalCount, summaryStats }) => {
  return (
    <div className="stats-summary-card">
      {/* 매칭 건수 */}
      <div className="stat-item">
        <h3>매칭된 유사 사례</h3>
        <p>{totalCount || 0}건</p>
      </div>

      {/* 결과 분포 (게이지 바) */}
      <div className="stat-item">
        <div className="summary-stats-vertical">
          {summaryStats && Object.entries(summaryStats).length > 0 ? (
            (() => {
              // 건수 기준 내림차순 정렬
              const statsArray = Object.entries(summaryStats).sort((a, b) => b[1] - a[1]);
              const total = statsArray.reduce((acc, curr) => acc + curr[1], 0);
              const maxCount = Math.max(...statsArray.map((item) => item[1]));

              return statsArray.map(([label, count]) => {
                const percentage = ((count / total) * 100).toFixed(1);
                const barWidth = (count / maxCount) * 100;

                return (
                  <div key={label} className="stat-row-container">
                    <div className="stat-label-group">
                      <span className="stat-label-text">{label}</span>
                      <span className="stat-count-text">{percentage}%</span>
                    </div>
                    <div className="stat-gauge-bg">
                      <div
                        className="stat-gauge-fill"
                        style={{ width: `${barWidth}%` }}
                      ></div>
                    </div>
                  </div>
                );
              });
            })()
          ) : (
            <p className="no-data-msg">유사한 사례가 없어요</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatsSummarySection;