import { FIRM_NAME } from "../config";
import React, { useState, useMemo, useEffect } from 'react';
import { generateFullReport } from '../services/api'; 
import './Step4Report.css';

const Step4Report = ({ sessionData, updateSessionData, setCurrentStep, resetSession }) => {
  // 1. 상태 관리
  const [office, setOffice] = useState('서울 주사무소');
  const [specialty, setSpecialty] = useState('민사');
  const [status, setStatus] = useState('원고');
  const [isGenerating, setIsGenerating] = useState(false);
  const [rawLLMData, setRawLLMData] = useState(null); // 백엔드에서 받은 순수 LLM 데이터
  const [editableText, setEditableText] = useState('');

  // 2. UI 실시간 반영을 위한 가공 데이터 계산
  // 지사, 전문 분야, 의뢰인 지위가 바뀔 때마다 즉시 리포트 텍스트를 재구성합니다.
  const formattedReport = useMemo(() => {
    if (!rawLLMData) return null;

    return {
      title: rawLLMData.title_core,
      overview: `${rawLLMData.dynamic_overview} ${FIRM_NAME} ${office}는 ${status} 신분인 의뢰인을 대리했습니다.`,
      features: rawLLMData.features,
      support: `${FIRM_NAME} ${office}의 ${specialty} 변호사는 아래와 같이 조력했습니다. ${rawLLMData.dynamic_support}`,
      verdict: `${FIRM_NAME} ${office}의 ${specialty} 변호사 조력으로 법원은 아래와 같이 판결했습니다. ${rawLLMData.verdict_core}`,
      meaning: rawLLMData.meaning,
      review: rawLLMData.review,
      caseId: rawLLMData.caseId // 백엔드에서 넘겨준 참조 판례 ID
    };
  }, [rawLLMData, office, specialty, status]);

  // 3. 편집기 텍스트 실시간 동기화
  useEffect(() => {
    if (formattedReport) {
      const featuresText = formattedReport.features
        .map((f, i) => `${i + 1}. ${f}`)
        .join('\n');

      const fullText = `## 제목\n${formattedReport.title}\n\n` +
        `## 사건의 개요\n${formattedReport.overview}\n\n` +
        `## 사건의 특징\n${featuresText}\n\n` +
        `## 변호사 조력 내용\n${formattedReport.support}\n\n` +
        `## 사건 결과\n${formattedReport.verdict}\n\n` +
        `## 사건 결과의 의의\n${formattedReport.meaning}\n\n` +
        `## 고객 후기\n${formattedReport.review}`;

      setEditableText(fullText);
    }
  }, [formattedReport]);

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    try {
      // 세션 데이터에서 가장 유사한 사례 선택
      const topCase = sessionData.similarCases[0];

      const response = await generateFullReport({
        persona_data: sessionData.personaData,
        example_case: topCase,
        meta_info: {   
          office,
          specialty,
          status
        }
      });

      if (response.success) {
        setRawLLMData(response.data);
        updateSessionData('finalReport', response.data);
      }
    } catch (error) {
      console.error('리포트 생성 오류:', error);
      alert('리포트 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(editableText);
    alert('리포트가 클립보드에 복사되었습니다!');
  };

  const handlePrevStep = () => setCurrentStep(prev => prev - 1);

  const handleReset = () => {
    if (window.confirm('처음부터 다시 시작하시겠습니까?')) resetSession();
  };

  // 데이터 없을 경우 예외 처리
  if (!sessionData.similarCases || sessionData.similarCases.length === 0) {
    return (
      <div className="step4-container">
        <h2 className="step-title">업무 리포트 초안</h2>
        <div className="error-wrapper">
          <p>리포트를 생성할 유사 사례 데이터가 없습니다.</p>
          <button className="btn btn-secondary" onClick={handlePrevStep}>이전 단계로</button>
        </div>
      </div>
    );
  }

  return (
    <div className="step4-container">
      <h2 className="step-title">AI 업무 리포트 초안</h2>

      <div className="meta-settings">
        <h3>리포트 옵션 설정</h3>
        <div className="settings-row">
          <div className="setting-item">
            <label>지사 선택</label>
            <select value={office} onChange={(e) => setOffice(e.target.value)}>
              <option>서울 주사무소</option>
              <option>원주 분사무소</option>
              <option>수원 분사무소</option>
            </select>
          </div>
          <div className="setting-item">
            <label>전문 분야</label>
            <select value={specialty} onChange={(e) => setSpecialty(e.target.value)}>
              <option>민사</option>
              <option>형사</option>
              <option>이혼</option>
              <option>일반사기</option>
            </select>
          </div>
          <div className="setting-item">
            <label>의뢰인 지위</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option>원고</option>
              <option>피고</option>
              <option>피의자</option>
            </select>
          </div>
        </div>
      </div>

      <div className="report-layout">
        <div className="report-preview">
          <div className="preview-header">
            <h3>{FIRM_NAME} AI가 작성한 초안입니다</h3>
            {!formattedReport && !isGenerating && (
              <button className="btn btn-primary" onClick={handleGenerateReport}>
                AI 리포트 생성 시작
              </button>
            )}
          </div>
          
          {isGenerating && (
            <div className="loading-container">
              <div className="spinner"></div>
              <p>유사 사례와 의뢰인 정보를 조합하여 리포트를 작성 중입니다...</p>
            </div>
          )}

          {formattedReport && (
            <div className="report-content">
              <h4>{formattedReport.title}</h4>
              <p className="case-reference">참조 판례 ID: {formattedReport.caseId}</p>
              <hr />
              
              <section>
                <strong>1. 사건의 개요</strong>
                <p>{formattedReport.overview}</p>
              </section>

              <section>
                <strong>2. 사건의 특징</strong>
                <div className="feature-list">
                  {formattedReport.features.map((feature, idx) => (
                    <p key={idx} className="feature-item"><span>{idx + 1}.</span> {feature}</p>
                  ))}
                </div>
              </section>

              <section>
                <strong>3. 변호사 조력 내용</strong>
                <p>{formattedReport.support}</p>
              </section>

              <section>
                <strong>4. 판결 결과</strong>
                <p>{formattedReport.verdict}</p>
              </section>

              <section>
                <strong>5. 사건 결과의 의의</strong>
                <p>{formattedReport.meaning}</p>
              </section>

              <section>
                <strong>6. 고객 후기</strong>
                <p className="review-text">{formattedReport.review}</p>
              </section>

              <p className="signature">{FIRM_NAME} 담당 변호사 귀하</p>
            </div>
          )}
        </div>

        <div className="report-editor">
          <h3>텍스트 편집기</h3>
          <textarea
            className="editor-textarea"
            value={editableText}
            onChange={(e) => setEditableText(e.target.value)}
            placeholder="AI 리포트가 생성되면 자동으로 입력됩니다."
          />
          <div className="editor-actions">
            <button className="btn btn-secondary full-width" onClick={handleCopyToClipboard} disabled={!editableText}>
              클립보드에 복사
            </button>
          </div>
        </div>
      </div>

      <div className="footer-actions">
        <button className="btn btn-outline" onClick={handlePrevStep}>이전 단계</button>
        <button className="btn btn-secondary" onClick={handleReset}>초기화</button>
      </div>
    </div>
  );
};

export default Step4Report;