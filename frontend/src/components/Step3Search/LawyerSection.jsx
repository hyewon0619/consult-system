import React from "react";
import './LawyerSection.css';

const LawyerSection = ({ topLawyers }) => {
  if (!topLawyers || topLawyers.length === 0) return null;

  return (
    <div className="lawyers-section fade-in">
      <h3>해당 분야의 사건 경험이 많은 변호사님을 찾았어요</h3>
      <div className="lawyer-cards">
        {topLawyers.map((lawyer, index) => (
          <div key={index} className="lawyer-card">
            <div className="lawyer-img-wrapper">
              <img 
                src={lawyer.imgUrl} 
                className="lawyer-photo"
                alt={lawyer.name}
                onLoad={(e) => e.currentTarget.classList.add('loaded')}
                onError={(e) => e.currentTarget.classList.add('error')}
              />
              <div className="no-img">법무</div>
            </div>
            <div className="lawyer-info">
              <h4>{lawyer.name} 변호사</h4>
              <p>유사 사건 <strong>{lawyer.caseCount}건</strong> 수행</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LawyerSection;