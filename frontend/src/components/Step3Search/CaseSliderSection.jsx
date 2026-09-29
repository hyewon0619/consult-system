import { LAWYER_IMAGE_BASE_URL } from "../../config";
import React from "react";
import './LawyerSection.css';

const CaseSliderSection = ({ 
  displayData, 
  currentIndex, 
  totalCases, 
  onPrev, 
  onNext, 
  onGenerateReport, 
  isFinalStep 
}) => {
  if (!displayData) {
    return <div className="no-data-box">현재 의뢰인의 상황과 유사한 사례가 없어요</div>;
  }

  return (
    <>
      <div className="section-header">
        <h3>다른 고객님은 이렇게 해결했어요</h3>
      </div>

      <div className="case-detail-card fade-in">
        <div className="case-detail-header">
          <div className="title-area">
            <h4>{displayData.title}</h4>
            <div className="case-tags">
              {displayData.statusKeyword && displayData.statusKeyword !== "-" && (
                <span className="cat-tag">{displayData.statusKeyword}</span>
              )}
            </div>
          </div>
        </div>

        <div className="case-detail-body">
          {[
            { label: "1. 사건의 개요", text: displayData.summary },
            { label: "2. 사건의 특징", text: displayData.feature },
            { label: "3. 변호사 조력 내용", text: displayData.assistance },
            { label: "4. 사건 결과", text: displayData.result },
            { label: "5. 사건 결과의 의의", text: displayData.meaning },
          ].map((item, idx) => (
            <div key={idx} className="detail-row">
              <h5>{item.label}</h5>
              <p>{item.text || "상세 내용이 없습니다."}</p>
            </div>
          ))}
        </div>

        <div className="case-detail-footer">
          <div className="lawyer-profile">
            {displayData.lawyers ? (
              <>
                <img 
                  src={LAWYER_IMAGE_BASE_URL
                    ? `${LAWYER_IMAGE_BASE_URL}/${displayData.lawyers.split(',')[0].trim()}.png`
                    : undefined} 
                  alt="수행 변호사"
                  className="lawyer-photo"
                  onLoad={(e) => e.currentTarget.classList.add('loaded')}
                  onError={(e) => {
                    if (!e.target.dataset.tried) {
                      e.target.dataset.tried = "true";
                      e.target.src = e.target.src.replace('.png', '.jpg');
                    } else {
                      e.target.classList.add('error');
                    }
                  }}
                />
                <div className="no-img">법무</div>
              </>
            ) : (
              <div className="no-img">법무</div>
            )}
            <div className="lawyer-name">
              <span>수행 변호사</span>
              <strong>{displayData.lawyers || "법률전문팀"}</strong>
            </div>
          </div>
          {!isFinalStep && (
            <button className="btn-report" onClick={onGenerateReport}>
              나의 맞춤 리포트 생성
            </button>
          )}
        </div>
      </div>

      {/* 슬라이더 컨트롤 */}
      <div className="slider-controls-centered">
        <button className="nav-circle-btn" onClick={onPrev} disabled={currentIndex === 0}>
          &#10094;
        </button>
        <div className="case-indicator">
          <span className="current">{currentIndex + 1}</span>
          <span className="divider">/</span>
          <span className="total">{totalCases}</span>
        </div>
        <button className="nav-circle-btn" onClick={onNext} disabled={currentIndex === totalCases - 1}>
          &#10095;
        </button>
      </div>
    </>
  );
};

export default CaseSliderSection;