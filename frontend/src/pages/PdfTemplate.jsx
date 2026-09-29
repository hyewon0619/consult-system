import { FIRM_NAME } from "../config";
import React from "react";
import LegalDataItem from "../components/LegalDataItem";
import { getConfidenceClass } from '../utils/statsUtils';
import "./PdfTemplate.css";

/**
 * PDF 출력을 위한 템플릿 컴포넌트
 * 화면에는 보이지 않고 PDF 생성 시에만 사용됨
 */
const PdfTemplate = ({ sessionData }) => {
  const data = sessionData.lastResult;

  const renderDistributionStats = () => {
    if (!sessionData.summaryStats || Object.entries(sessionData.summaryStats).length === 0) {
      return <p className="pdf-summary-text">유사한 사례가 없어요</p>;
    }

    const statsArray = Object.entries(sessionData.summaryStats).sort((a, b) => b[1] - a[1]);
    const totalCount = statsArray.reduce((acc, curr) => acc + curr[1], 0);
    const maxCount = Math.max(...statsArray.map(item => item[1]));

    return statsArray.map(([label, count]) => {
      const percentage = ((count / totalCount) * 100).toFixed(1);
      const barWidth = (count / maxCount) * 100;

      return (
        <div key={label} className="pdf-stat-row-container">
          <div className="pdf-stat-label-group">
            <span className="pdf-stat-label-text">{label}</span>
            <span className="pdf-stat-count-text">{percentage}%</span>
          </div>
          <div className="pdf-stat-gauge-bg">
            <div 
              className="pdf-stat-gauge-fill" 
              style={{ width: `${barWidth}%` }}
            ></div>
          </div>
        </div>
      );
    });
  };

  return (
    <div className="pdf-only-container">
      {/* 페이지 1: 고객 정보 */}
      <div className="pdf-section-info">
        <div className="pdf-header">
          <h1>상담 프리뷰</h1>
        </div>
        <h2 className="pdf-section-title">필요한 정보만 선별했어요</h2>
        <div className="pdf-topic-badge">{sessionData.topic_code || "분석 주제"}</div>

        <div className="pdf-info-box">
          <h3 className="pdf-subsection-title">고객 정보</h3>
          {data?.고객_정보 && Object.entries(data.고객_정보).map(([k, v]) => (
            <LegalDataItem key={k} label={k} value={v} isPdf={true} />
          ))}
        </div>

        {data?.상담_요약 && (
          <div className="pdf-info-box">
            <h3 className="pdf-subsection-title">특이사항</h3>
            <p className="pdf-summary-text">
              {data.상담_요약?.기타_사실관계_및_특이사항 || "특이사항 없음"}
            </p>
          </div>
        )}

        {data?.상담_설정 && (
          <div className="pdf-info-box">
            <h3 className="pdf-subsection-title">상담 설정 정보</h3>
            <div className="pdf-settings-grid">
              {Object.entries(data.상담_설정).map(([key, value]) => (
                <div key={key} className="pdf-row settings-item">
                  <strong className="pdf-label">{key.replace(/_/g, ' ')}</strong>
                  <span className="pdf-value">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="pdf-info-box">
          <h3 className="pdf-subsection-title">사건 상세</h3>
          {data?.상세_내용 && Object.entries(data.상세_내용).map(([k, v]) => (
            <LegalDataItem key={k} label={k} value={v} isPdf={true} />
          ))}
        </div>
      </div>

      {/* 페이지 2: 분석 결과 요약 */}
      <div className="pdf-section-summary">
        <h2 className="pdf-section-title">분석 결과 요약</h2>

        <div className="pdf-info-box">
          <div className="pdf-row">
            <strong>매칭된 유사 사례</strong>
            <span>{sessionData.totalCount || 0}건</span>
          </div>

          {/* 결과 분포도 섹션 */}
          <h3 className="pdf-row">
            <strong>결과 분포도</strong>
          </h3>
          <div className="pdf-stats-vertical">
            {renderDistributionStats()}
          </div>
        </div>

        <TopLawyersSection sessionData={sessionData} />
        <FeeStatisticsSection sessionData={sessionData} />
        <CaseDiagnosisSection sessionData={sessionData} />
        <AuthoritySection sessionData={sessionData} />
      </div>

      {/* 페이지 3~: 유사 사례 상세 */}
      {sessionData.similarCases?.map((caseItem, index) => (
        <CaseDetailCard key={index} caseItem={caseItem} index={index} />
      ))}
    </div>
  );
};


/**
 * 상위 변호사 섹션
 */
const TopLawyersSection = ({ sessionData }) => (
  <>
    <h2 className="pdf-section-title">해당 분야의 사건 경험이 많은 변호사님을 찾았어요</h2>
    <div className="pdf-info-box pdf-lawyers-grid">
      {sessionData.topLawyers && sessionData.topLawyers.length > 0 ? (
        sessionData.topLawyers.map((lawyer, index) => (
          <div key={index} className="pdf-lawyer-item">
            <span className="pdf-lawyer-name">{lawyer.name} 변호사</span>
            <span className="pdf-lawyer-cases">
              유사 사건 <strong>{lawyer.caseCount}건</strong> 수행
            </span>
          </div>
        ))
      ) : (
        <p className="pdf-no-data">관련 변호사 정보가 없습니다.</p>
      )}
    </div>
  </>
);

const FeeStatisticsSection = ({ sessionData }) => {
  const stats = sessionData.amountStats;
  if (!stats) return null;

  const targetPeriods = [
    { key: '2m', label: '최근 2개월' },
    { key: '6m', label: '최근 6개월' },
    { key: 'overall', label: '전체 기간' }
  ];

  const isCivil = stats.major_category === "민사";

  return (
    <>
      <h2 className="pdf-section-title">사건 유형별 약정금 통계 분석</h2>
      <div className="pdf-info-box pdf-fee-comparison-grid">
        {targetPeriods.map((period) => {
          const periodData = period.key === 'overall' ? stats.overall : stats.periods?.[period.key];
          
          // 데이터가 없는 경우 '데이터 없음' 표시 또는 null 반환
          if (!periodData || (!periodData.payment && !periodData.reward)) {
            return (
              <div key={period.key} className="pdf-fee-period-card empty">
                <div className="pdf-fee-period-label">{period.label}</div>
                <p className="pdf-no-data-small">집계 데이터 없음</p>
              </div>
            );
          }

          return (
            <div key={period.key} className="pdf-fee-period-card">
              <div className="pdf-fee-period-label">{period.label}</div>
              {/* 신뢰도 표시 */}
              {/* <div className="pdf-fee-confidence-container">
                <span className={`pdf-confidence-badge confidence-${getConfidenceClass(item.confidence.label)}`}>
                  {item.confidence.label}
                </span>
              </div> */}
              <div className="pdf-fee-card-content">
                {/* 1. 약정금 */}
                {periodData.payment && periodData.payment.median > 0 && (
                  <div className="pdf-fee-sub-item">
                    <div className="pdf-fee-sub-title">약정금</div>
                    <div className="pdf-fee-sub-value">{periodData.payment.median.toLocaleString()}원</div>
                    <div className="pdf-fee-sub-range">
                      {periodData.payment.lower_25?.toLocaleString()}~{periodData.payment.upper_75?.toLocaleString()}
                    </div>
                  </div>
                )}

                {/* 2. 성공보수 */}
                {periodData.reward && periodData.reward.median > 0 && (
                  <div className="pdf-fee-sub-item">
                    <div className="pdf-fee-sub-title">성공 보수</div>
                    <div className="pdf-fee-sub-value">{periodData.reward.median.toLocaleString()}원</div>
                    <div className="pdf-fee-sub-range">
                      {periodData.reward.lower_25?.toLocaleString()}~{periodData.reward.upper_75?.toLocaleString()}
                    </div>
                  </div>
                )}

                {/* 3. 소가 대비 비율 (민사 전용) */}
                {isCivil && periodData.reward_to_soga_ratio > 0 && (
                  <div className="pdf-fee-sub-item highlight-ratio">
                    <div className="pdf-fee-sub-title">소가 대비 성공보수</div>
                    <div className="pdf-fee-sub-value">{(periodData.reward_to_soga_ratio * 100).toFixed(1)}%</div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
};


/**
 * 사건 진단 섹션
 */
const CaseDiagnosisSection = ({ sessionData }) => (
  <div className="pdf-diagnosis-section">
    <h2 className="pdf-section-title">사건 진단</h2>
    <div className="pdf-info-box diagnosis-box">
      <div className="diagnosis-item">
        <strong className="diagnosis-label">[의뢰인 상황 분석]</strong>
        <p className="diagnosis-text">
          {sessionData.personaData?.persona_layperson || "분석된 내용이 없어요."}
        </p>
      </div>
      <div className="diagnosis-item">
        <strong className="diagnosis-label">[법률가적 관점 진단]</strong>
        <p className="diagnosis-text">
          {sessionData.personaData?.persona_lawyer || "분석된 내용이 없어요."}
        </p>
      </div>
    </div>
  </div>
);


/**
 * 통합된 관할 기관 및 처분권자 분석 섹션
 */
const AuthoritySection = ({ sessionData }) => {
  const stats = sessionData.authorityStats;
  const hasData = stats?.incident_count > 0 || stats?.auth_count > 0;
  const orgName = stats?.matched_org || (sessionData.city_flag ? "해당 지역" : "해당 기관");

  return (
    <div className="pdf-authority-analysis-wrapper">
      <h2 className="pdf-section-title">관할 기관 및 처분권자 분석</h2>
      <div className="pdf-info-box">
        {!hasData ? (
          <p className="pdf-summary-text">
            전국 단위의 {FIRM_NAME}에서 유사한 사례를 찾고 <br />
            <strong>고객님께 가장 적합한 법률 전략</strong>을 분석하고 있습니다.
          </p>
        ) : (
          <>
            <div className="diagnosis-label">[처분권자 통계]</div>
            <p className="diagnosis-text">
              • <strong>{orgName}</strong> 관련 <strong>{stats.auth_count || 0}명</strong>의 처분권자를 경험했어요.<br />
              • 이들과 이 <strong>{stats.incident_count || 0}건</strong>의 사건을 함께 수행했어요.
            </p>

            {stats.auth_details?.length > 0 && (
              <div className="pdf-auth-detail-area">
                <div className="diagnosis-label">[수행 경험이 있는 주요 처분권자 상세]</div>
                <div className="pdf-auth-list-static">
                  {stats.auth_details.slice(0, 12).map((person, idx) => (
                    <div key={idx} className="pdf-person-row">
                      <div className="pdf-person-info">
                        <span className="pdf-p-name">{person.name}</span>
                        {/* 소속, 부서, 직책 추가 */}
                        <span className="pdf-p-org-info">
                          <span>{person.organization || "미기입"}</span>
                          {person.department && <span>{person.department}</span>}
                          {person.job && <span>{person.job}</span>}
                        </span>
                      </div>
                      <div className="pdf-p-traits">
                        {person.personal_trait && <span className="pdf-t-badge">개인: {person.personal_trait}</span>}
                        {person.work_trait && <span className="pdf-t-badge">업무: {person.work_trait}</span>}
                      </div>
                    </div>
                  ))}
                  {stats.auth_details.length > 12 && (
                    <div className="pdf-auth-more-footer">
                      외 {stats.auth_details.length - 12}명의 처분권자 정보 보유
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

/**
 * 유사 사례 상세 카드
 */
const CaseDetailCard = ({ caseItem, index }) => (
  <div className="pdf-case-card">
    <h2 className="pdf-section-title">유사 사례 상세 ({index + 1})</h2>
    <h3>{caseItem.case_title}</h3>
    <div className="pdf-case-tag">{caseItem.closure_summary}</div>

    <div className="pdf-case-content">
      <h4>1. 사건의 개요</h4><p>{caseItem.case_summary}</p>
      <h4>2. 사건의 특징</h4><p>{caseItem.case_feature}</p>
      <h4>3. 변호사 조력 내용</h4><p>{caseItem.case_assistance}</p>
      <h4>4. 사건 결과</h4><p>{caseItem.case_result}</p>
      <div className="pdf-lawyer-info">
        <strong>수행 변호사:</strong> {caseItem.lawyer_names || "법률전문팀"}
      </div>
    </div>
  </div>
);

export default PdfTemplate;