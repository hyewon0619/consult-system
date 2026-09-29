import React, { useState, useEffect, useRef } from "react";
import PdfTemplate from "./PdfTemplate";
import PricingStatsSection from "../components/Step3Search/PricingStatsSection";
import AuthoritySection from "../components/Step3Search/AuthoritySection"; 
import AnalysisInfoSection from "../components/Step3Search/AnalysisInfoSection";
import StatsSummarySection from "../components/Step3Search/StatsSummarySection";
import PersonaAnalysisSection from "../components/Step3Search/PersonaAnalysisSection";
import LawyerSection from "../components/Step3Search/LawyerSection";
import CaseSliderSection from "../components/Step3Search/CaseSliderSection";
import { generateAndDownloadPdf } from "../utils/PdfGenerator";
import "./Step3Search.css";

const Step3Search = ({ sessionData, updateSessionData, setCurrentStep, isFinalStep }) => {
  const [loading, setLoading] = useState(false);
  const pdfRef = useRef(null);
  const [error, setError] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isCalled, setIsCalled] = useState(false);

  // 스트리밍 상태 관리
  const [streamingStatus, setStreamingStatus] = useState("");
  const [lawyerPersona, setLawyerPersona] = useState(null);
  const [laypersonPersona, setLaypersonPersona] = useState(null);

  useEffect(() => {
    if (loading || isCalled || (sessionData.similarCases && sessionData.similarCases.length > 0)) {
      return;
    }

    const performAnalysis = async () => {
      setIsCalled(true);
      await handleFullAnalysisStreaming();
    };

    performAnalysis();
  }, [sessionData.similarCases]);
  
  const handleFullAnalysisStreaming = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch('/api/consult/search-case', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: sessionData.textToAnalyze,
          category: sessionData.category,
          customer_address: sessionData.customerAddress,
          authority_name: sessionData.authorityName
        }),
      });

      if (!response.ok) {
        const errorDetail = await response.text();
        console.error(`서버 에러 상태: ${response.status}`, errorDetail);
        throw new Error(`서버 응답 오류 (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'status':
                  setStreamingStatus(data.message);
                  break;

                case 'persona_lawyer':
                  setLawyerPersona(data.data);
                  updateSessionData("personaData", {
                    ...sessionData.personaData,
                    state: data.data.state,
                    persona_lawyer: data.data.persona_lawyer
                  });
                  break;

                case 'persona_layperson':
                  setLaypersonPersona(data.data);
                  updateSessionData("personaData", {
                    ...sessionData.personaData,
                    persona_layperson: data.data.persona_layperson
                  });
                  break;

                case 'final':
                  const finalData = data.data;
                  updateSessionData("personaData", finalData.persona);
                  updateSessionData("similarCases", finalData.similar_cases);
                  updateSessionData("winRate", finalData.win_rate);
                  updateSessionData("summaryStats", finalData.summary_stats);
                  updateSessionData("topLawyers", finalData.top_lawyers);
                  updateSessionData("totalCount", finalData.total_count);
                  updateSessionData("authorityStats", finalData.authority_stats);
                  updateSessionData("cityFlag", finalData.city_flag);
                  updateSessionData("personalData", finalData.personal_data);
                  updateSessionData("amountStats", finalData.amount_stats)
                  setLoading(false);
                  setStreamingStatus("분석 완료!");
                  break;

                case 'error':
                  setError(data.message);
                  setLoading(false);
                  break;
              }
            } catch (e) {
              console.error('JSON 파싱 에러:', e);
            }
          }
        }
      }
    } catch (err) {
      console.error('스트리밍 에러:', err);
      setError("서버와 통신 중 오류가 발생했습니다.");
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const seconds = String(now.getSeconds()).padStart(2, '0');
      const filename = `상담프리뷰_${year}-${month}-${day}_${hours}${minutes}${seconds}.pdf`;
      await generateAndDownloadPdf(pdfRef.current, filename);
    } catch (error) {
      console.error("PDF 생성 중 오류 발생:", error);
      alert("PDF 생성에 실패했습니다.");
    }
  };

  const nextCase = () => {
    if (currentIndex < (sessionData.similarCases?.length || 0) - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const prevCase = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  // 로딩 중일 때
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>{streamingStatus || "AI가 법률 데이터를 분석하고 유사 사례를 검색 중입니다..."}</p>
        
        {/* 페르소나 데이터 미리보기 */}
        {(lawyerPersona || laypersonPersona) && (
          <div className="streaming-preview">
            {lawyerPersona && (
              <div className="preview-box">
                <h4>어떤 사건이 있었냐면요..</h4>
                <p>{lawyerPersona.persona_lawyer}</p>
              </div>
            )}
            {laypersonPersona && (
              <div className="preview-box">
                <h4>의뢰인은 이렇게 말했어요...</h4>
                <p>{laypersonPersona.persona_layperson}</p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // 에러 발생 시
  if (error) {
    return <div className="error-box">{error}</div>;
  }

  const data = sessionData.lastResult;
  const currentCase = sessionData.similarCases?.[currentIndex];

  const displayData = currentCase ? {
    title: currentCase.case_title || "유사 사례 분석",
    summary: currentCase.case_summary,
    feature: currentCase.case_feature,
    assistance: currentCase.case_assistance,
    result: currentCase.case_result,
    meaning: currentCase.case_significance,
    statusKeyword: currentCase.closure_summary,
    lawyers: currentCase.lawyer_names,
    score: currentCase.score,
    isWin: currentCase.is_win
  } : null;

  return (
    <>
      {/* PDF 생성용 숨겨진 영역 */}
      <div ref={pdfRef}>
        <PdfTemplate sessionData={sessionData} />
      </div>

      {/* 상단 헤더 */}
      <div className="step3-header-container">
        <h2>사건 분석 결과</h2>
      </div>

      {/* 페르소나 데이터 */}
      <PersonaAnalysisSection personaData={sessionData.personaData} />

      <div className="step3-layout screen-only">
        {/* 왼쪽 컬럼 - 정보 추출 결과 */}
        <AnalysisInfoSection 
          data={data} 
          topicCode={sessionData.topic_code} 
          onDownloadPDF={handleDownloadPDF} 
        />

        <main className="right-cases-column">
          {/* 상단 섹션: 통계 및 처분권자 정보 */}
          <div className="right-top-section">
            
            {/* 통계 정보 카드 */}
            <StatsSummarySection 
              totalCount={sessionData.totalCount} 
              summaryStats={sessionData.summaryStats} 
            />

            {/* 처분권자 정보 카드 */}
            <AuthoritySection 
              authorityStats={sessionData.authorityStats} 
              cityFlag={sessionData.city_flag} 
            />

            {/* 통계 정보 카드 섹션*/}
            {sessionData.amountStats && (
              <PricingStatsSection amountStats={sessionData.amountStats} />
            )}
          </div>
          
          {/* 하단 섹션: 변호사 및 유사사례 */}
          <div className="right-bottom-section">
            {/* 변호사 섹션 */}
            <LawyerSection topLawyers={sessionData.topLawyers} />
          </div>
          {/* 유사 사례 섹션 헤더 */}
          <CaseSliderSection 
            displayData={displayData}
            currentIndex={currentIndex}
            totalCases={sessionData.similarCases?.length || 0}
            onPrev={prevCase}
            onNext={nextCase}
            isFinalStep={isFinalStep}
            onGenerateReport={() => {
              updateSessionData("currentCaseIdx", currentIndex);
              setCurrentStep(prev => prev + 1); 
            }}
          />
        </main>
      </div>
    </>
  );
};

export default Step3Search;