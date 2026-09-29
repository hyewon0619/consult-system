import React, { useState, useEffect, useRef } from 'react';
import { transcribeAudio } from '../services/api';
import './Step1Input.css';

const CATEGORY_DATA = {
  "가사": { "가사": ["이혼"] },
  "형사": { "고소고발": ["기타"],
           "경제범죄": ["일반사기"] },
  "민사": { "민사": ["손해배상"]
  }
};

const Step1Input = ({ sessionData, updateSessionData, setCurrentStep, activeMode }) => {
  const [inputContent, setInputContent] = useState('');
  const [activeTab, setActiveTab] = useState('text');

  const textareaRef = useRef(null);

  const [largeCategory, setLargeCategory] = useState('가사');
  const [mediumCategory, setMediumCategory] = useState('가사');
  const [smallCategory, setSmallCategory] = useState('이혼');

  const [audioFiles, setAudioFiles] = useState([]);
  const [isTranscribing, setIsTranscribing] = useState(false);
  // [삭제됨] skipStep2 상태 제거
  const [warning, setWarning] = useState('');

  const handleLargeCategoryChange = (e) => {
    const newLarge = e.target.value;
    const newMedium = Object.keys(CATEGORY_DATA[newLarge])[0];
    const newSmall = CATEGORY_DATA[newLarge][newMedium][0];

    setLargeCategory(newLarge);
    setMediumCategory(newMedium);
    setSmallCategory(newSmall);
  };

  const handleMediumCategoryChange = (e) => {
    const newMedium = e.target.value;
    const newSmall = CATEGORY_DATA[largeCategory][newMedium][0];

    setMediumCategory(newMedium);
    setSmallCategory(newSmall);
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    setAudioFiles(files);
  };

  const handleTranscribe = async () => {
    if (audioFiles.length === 0) {
      setWarning('음성 파일을 선택해주세요.');
      return;
    }
    setIsTranscribing(true);
    setWarning('');
    try {
      const result = await transcribeAudio(audioFiles);
      if (result.success) {
        setInputContent(result.text);
        setActiveTab('text');
      }
    } catch (error) {
      setWarning('음성 변환 중 오류가 발생했습니다.');
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleAnalyze = () => {
    if (!largeCategory || !mediumCategory || !smallCategory) {
      setWarning('사건 분류를 선택해주세요.');
      return;
    }
    if (!inputContent || inputContent.trim() === '') {
      setWarning('상담 내용을 입력해주세요.');
      return;
    }

    const topicCode = `${largeCategory} > ${mediumCategory} > ${smallCategory}`;
    updateSessionData('topic_code', topicCode);
    updateSessionData('textToAnalyze', inputContent);
    updateSessionData('category', smallCategory);

    if (activeMode === 'report') {
      setCurrentStep(3);
    } else {
      setCurrentStep(2);
    }
  };

  useEffect(() => {
    if (activeTab === 'text' && textareaRef.current) {
      textareaRef.current.style.height = 'auto'; // 높이 초기화
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`; // 내용 높이만큼 설정
    }
  }, [inputContent, activeTab]);

  return (
    <div className="step1-fixed-wrapper">
      <div className="step1-container">
        <h2 className="step-title">상담 내용을 알려주세요</h2>

        <div className="content-wrapper">
          {/* 상단 카테고리 선택 영역 */}
          <div className="category-section">
            <p className="section-label">사건 분류</p>
            <div className="dropdown-group">
              <select value={largeCategory} onChange={handleLargeCategoryChange}>
                {Object.keys(CATEGORY_DATA).map(lc => <option key={lc} value={lc}>{lc}</option>)}
              </select>

              {/* 중분류 */}
              <select value={mediumCategory} onChange={handleMediumCategoryChange}>
                {largeCategory && CATEGORY_DATA[largeCategory] && Object.keys(CATEGORY_DATA[largeCategory]).map(mc => (
                  <option key={mc} value={mc}>{mc}</option>
                ))}
              </select>

              {/* 소분류 */}
              <select value={smallCategory} onChange={(e) => setSmallCategory(e.target.value)}>
                {mediumCategory && CATEGORY_DATA[largeCategory][mediumCategory] && CATEGORY_DATA[largeCategory][mediumCategory].map(sc => (
                  <option key={sc} value={sc}>{sc}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 중간 탭 영역 */}
          <div className="tab-container">
            <button className={`tab ${activeTab === 'text' ? 'active' : ''}`} onClick={() => setActiveTab('text')}>직접 입력</button>
            <button className={`tab ${activeTab === 'audio' ? 'active' : ''}`} onClick={() => setActiveTab('audio')}>음성 파일 변환</button>
          </div>

          {/* 입력 본문 영역 (스크롤 고정의 핵심) */}
          <div className="input-body-area">
            {activeTab === 'text' ? (
              <textarea
                ref={textareaRef}
                className="text-input auto-expand"
                value={inputContent}
                onChange={(e) => setInputContent(e.target.value)}
                placeholder="상담 내용을 상세히 입력해요"
                disabled={isTranscribing}
                rows={1}
              />
            ) : (
              <div className="audio-input-section">
                <div className="file-upload-header">
                  <input type="file" id="file-upload" multiple accept="audio/*" onChange={handleFileChange} disabled={isTranscribing} className="file-input-hidden" />
                  <label htmlFor="file-upload" className="btn btn-outline file-select-btn">
                    + 파일 선택하기
                  </label>
                </div>

                {audioFiles.length > 0 && (
                  <div className="file-list">
                    <p className="file-list-title">업로드된 파일 ({audioFiles.length}개)</p>
                    <div className="file-items-wrapper">
                      {audioFiles.map((file, index) => (
                        <div key={index} className="file-item">
                          <span className="file-icon">🎵</span>
                          <div className="file-info">
                            <span className="file-name">{file.name}</span>
                            <span className="file-size">{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  className="btn btn-secondary transcribe-btn"
                  onClick={handleTranscribe}
                  disabled={isTranscribing || audioFiles.length === 0}
                >
                  {isTranscribing ? '변환 중...' : '음성 파일 변환 시작'}
                </button>
              </div>
            )}
          </div>

          {/* 하단 액션 영역 */}
          <div className="bottom-action-area">
            {warning && <div className="warning-message">{warning}</div>}

            <div className="action-row">
              {/* [삭제됨] 체크박스 영역 제거 */}
              <button className="btn btn-primary analyze-btn" onClick={handleAnalyze} disabled={isTranscribing}>
                {activeMode === 'report' ? '사례 검색하기' : '내용 분석하기'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Step1Input;