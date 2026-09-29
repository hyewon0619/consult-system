import React from "react";
import './PersonaAnalysisSection.css'

const PersonaAnalysisSection = ({ personaData }) => {
  if (!personaData) return null;

  return (
    <section className="persona-analysis-wrapper">
      <div className="persona-section-header">
        <h3>AI가 분석한 결과예요</h3>
      </div>

      <div className="persona-container">
        {/* 의뢰인 관점 */}
        <div className="persona-box layperson">
          <div className="persona-label">
            <span className="perspective-tag">의뢰인 관점</span>
            <span className="state-highlight">
              <strong>의뢰인({personaData.state || "정보없음"})</strong>은 이렇게 생각했어요
            </span>
          </div>
          <div className="persona-content">
            <p className="persona-text">{personaData.persona_layperson}</p>
          </div>
        </div>

        {/* 변호사 관점 */}
        <div className="persona-box lawyer">
          <div className="persona-label">
            <span className="perspective-tag">변호사 관점</span>
            <span className="strategy-highlight">이렇게 대답할 수 있어요</span>
          </div>
          <div className="persona-content">
            <p className="persona-text">{personaData.persona_lawyer}</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PersonaAnalysisSection;