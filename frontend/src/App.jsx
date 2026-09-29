import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Stepper from './components/Stepper';
import Home from './pages/Home';
import Step1Input from './pages/Step1Input';
import Step2Extract from './pages/Step2Extract';
import Step3Search from './pages/Step3Search';
import Step4Report from './pages/Step4Report';
import HomeButton from './components/HomeButton';
import './App.css';

function App() {
  const [currentStep, setCurrentStep] = useState(0);
  const [activeMode, setActiveMode] = useState(null);

  const [sessionData, setSessionData] = useState({
    textToAnalyze: '',
    lastResult: null,
    personaData: null,
    similarCases: [],
    currentCaseIdx: 0,
    rawRes1: null,
    rawRes2: null,
  });

  const modeConfigs = {
    demo: [
      { id: 1, label: '상담 내용 입력' },
      { id: 2, label: '핵심 정보 추출' },
      { id: 3, label: '유사 사례 검색' },
      { id: 4, label: '업무 리포트 작성' }
    ],
    caseMatch: [
      { id: 1, label: '상담 내용 입력' },
      { id: 2, label: '핵심 정보 추출' },
      { id: 3, label: '유사 사례 검색' }
    ],
    report: [
      { id: 1, label: '상담 내용 입력' },
      { id: 2, label: '유사 사례 검색' },
      { id: 3, label: '업무 리포트 작성' }
    ]
  };

  const handleSelectMode = (mode) => {
    setActiveMode(mode);
    setCurrentStep(1);
  };

  const updateSessionData = (key, value) => {
    setSessionData(prev => ({ ...prev, [key]: value }));
  };

  const resetSession = () => {
    setSessionData({
      textToAnalyze: '',
      lastResult: null,
      personaData: null,
      similarCases: [],
      currentCaseIdx: 0,
      rawRes1: null,
      rawRes2: null,
    });
    setCurrentStep(0);
    setActiveMode(null);
  };

  return (
    <Router>
      <div className="app-container">
        <div className="main-content">
          <div className="container">
            {currentStep > 0 && <HomeButton />}

            {currentStep > 0 && (
              <Stepper 
                currentStep={currentStep} 
                steps={modeConfigs[activeMode]} 
              />
            )}
            
            <Routes>
              <Route path="/" element={
                <>
                  {currentStep === 0 && <Home onSelectMode={handleSelectMode} />}
                  
                  {activeMode === 'demo' && (
                    <>
                      {currentStep === 1 && <Step1Input sessionData={sessionData} updateSessionData={updateSessionData} setCurrentStep={setCurrentStep} />}
                      {currentStep === 2 && <Step2Extract sessionData={sessionData} updateSessionData={updateSessionData} setCurrentStep={setCurrentStep} />}
                      {currentStep === 3 && <Step3Search sessionData={sessionData} updateSessionData={updateSessionData} setCurrentStep={setCurrentStep} />}
                      {currentStep === 4 && <Step4Report sessionData={sessionData} updateSessionData={updateSessionData} setCurrentStep={setCurrentStep} resetSession={resetSession} />}
                    </>
                  )}

                  {activeMode === 'caseMatch' && (
                    <>
                      {currentStep === 1 && <Step1Input sessionData={sessionData} updateSessionData={updateSessionData} setCurrentStep={setCurrentStep} />}
                      {currentStep === 2 && <Step2Extract sessionData={sessionData} updateSessionData={updateSessionData} setCurrentStep={setCurrentStep} />}
                      {currentStep === 3 && <Step3Search sessionData={sessionData} updateSessionData={updateSessionData} setCurrentStep={setCurrentStep} isFinalStep={true} />}
                    </>
                  )}

                  {activeMode === 'report' && (
                    <>
                      {currentStep === 1 && <Step1Input sessionData={sessionData} updateSessionData={updateSessionData} setCurrentStep={setCurrentStep} />}
                      {currentStep === 2 && <Step3Search sessionData={sessionData} updateSessionData={updateSessionData} setCurrentStep={setCurrentStep} />}
                      {currentStep === 3 && <Step4Report sessionData={sessionData} updateSessionData={updateSessionData} setCurrentStep={setCurrentStep} resetSession={resetSession} />}
                    </>
                  )}
                </>
              } />
            </Routes>
          </div>
        </div>
      </div>
    </Router>
  );
}

export default App;