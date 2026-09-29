import React from "react";
import LegalDataItem from "../LegalDataItem";
import "./AnalysisInfoSection.css";

const AnalysisInfoSection = ({ data, topicCode, onDownloadPDF }) => {
  return (
    <aside className="left-info-column">
      {/* 상단 섹션: 기본 분석 정보 */}
      <div className="side-analysis-card top-section">
        <div className="side-card-header">
          <div className="header-top-row">
            <h4>필요한 정보만 선별했어요</h4>
            <button className="btn-pdf-export" onClick={onDownloadPDF}>
              PDF 내보내기
            </button>
          </div>
          <span className="side-topic-badge">{topicCode || "분석 주제"}</span>
        </div>
        
        <div className="side-card-body">
          <section className="side-section">
            <h5>고객 정보</h5>
            {data?.고객_정보 && (
              <div className="side-customer-info-container">
                {/* 행 1: 성함, 성별, 연락처 */}
                <div className="side-info-row side-three-cols">
                {['성함', '성별', '연락처'].map((key) => {
                  // 키값에 따라 클래스명 부여 (name, gender, phone)
                  const fieldClass = key === '성함' ? 'col-name' : key === '성별' ? 'col-gender' : 'col-phone';
                  return (
                    data.고객_정보[key] && (
                      <div key={key} className={fieldClass}>
                        <LegalDataItem label={key} value={data.고객_정보[key]} isSide={true} />
                      </div>
                    )
                  );
                })}
              </div>

                {/* 행 2: 주소, 관할 기관 */}
                <div className="side-info-row side-two-cols">
                  {['주소', '관할_기관'].map((key) => (
                    data.고객_정보[key] && (
                      <LegalDataItem key={key} label={key} value={data.고객_정보[key]} isSide={true} />
                    )
                  ))}
                </div>

                {/* 기타 정보 */}
                {Object.entries(data.고객_정보)
                  .filter(([k]) => !['성함', '성별', '연락처', '주소', '관할_기관'].includes(k))
                  .map(([k, v]) => (
                    <LegalDataItem key={k} label={k} value={v} isSide={true} />
                  ))
                }
              </div>
            )}
          </section>

          <section className="side-section">
            <h5>사건 상세</h5>
            {data?.상세_내용 && Object.entries(data.상세_내용).map(([k, v]) => (
              <LegalDataItem key={k} label={k} value={v} isSide={true} />
            ))}
          </section>
        </div>
      </div>

      {/* 하단 섹션: 추가 정보 */}
      <div className="side-analysis-card bottom-section">
        <div className="side-card-body">
          {data?.상담_설정 && (
            <section className="side-section">
              <h5>상담 설정</h5>
              {Object.entries(data.상담_설정).map(([k, v]) => (
                <LegalDataItem key={k} label={k} value={v} isSide={true} />
              ))}
            </section>
          )}

          {data?.상담_요약 && (
            <section className="side-section">
              <h5>특이사항</h5>
              <p className="side-summary-text">
                {data.상담_요약?.기타_사실관계_및_특이사항 || "특이사항 없음"}
              </p>
            </section>
          )}
        </div>
      </div>
    </aside>
  );
};

export default AnalysisInfoSection;