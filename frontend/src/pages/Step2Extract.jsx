import { FIRM_NAME } from "../config";
import React, { useState, useEffect } from 'react';
import { extractLegalData } from '../services/api';
import './Step2Extract.css';

// 편집 가능한 데이터 아이템 컴포넌트
const EditableDataItem = ({ label, value, onEdit, onAddItem, onDeleteItem, path }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [isExpanded, setIsExpanded] = useState(true); // 아코디언 상태

  useEffect(() => {
    setEditValue(value);
  }, [value]);

  const handleSave = () => {
    onEdit(path, editValue);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
  };

  const handleAddItem = () => {
    if (onAddItem) {
      onAddItem(path);
    }
  };

  const handleDeleteItem = (itemIndex) => {
    if (onDeleteItem) {
      // 삭제 확인 팝업
      const confirmDelete = window.confirm('이 항목을 삭제하시겠습니까?');
      if (confirmDelete) {
        onDeleteItem([...path, itemIndex]);
      }
    }
  };

  // 1. 값이 배열인 경우
  if (Array.isArray(value) && value.length > 0) {
    return (
      <div className="depth-section">
        <div className="depth-title-wrapper" onClick={() => setIsExpanded(!isExpanded)}>
          <h4 className="depth-title">
            <span className="accordion-icon">{isExpanded ? '▼' : '▶'}</span>
            {label.replace(/_/g, ' ')} ({value.length}개)
          </h4>
          <button 
            className="add-item-btn" 
            onClick={(e) => {
              e.stopPropagation();
              handleAddItem();
            }}
          >
            + 항목 추가
          </button>
        </div>
        {isExpanded && (
          <div className="depth-body">
            <ul className="data-list">
              {value.map((item, index) => (
                <li key={index} className="list-item">
                  <div className="list-item-wrapper">
                    <div className="list-item-content">
                      {typeof item === 'object' && item !== null ? (
                        Object.entries(item).map(([k, v]) => (
                          <EditableDataItem 
                            key={k} 
                            label={k} 
                            value={v} 
                            onEdit={onEdit}
                            onAddItem={onAddItem}
                            onDeleteItem={onDeleteItem}
                            path={[...path, index, k]}
                          />
                        ))
                      ) : (
                        <EditableDataItem 
                          label={`항목 ${index + 1}`}
                          value={item}
                          onEdit={onEdit}
                          onAddItem={onAddItem}
                          onDeleteItem={onDeleteItem}
                          path={[...path, index]}
                        />
                      )}
                    </div>
                    <button 
                      className="delete-item-btn" 
                      onClick={() => handleDeleteItem(index)}
                      title="항목 삭제"
                    >
                      삭제
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // 빈 배열인 경우도 처리
  if (Array.isArray(value) && value.length === 0) {
    return (
      <div className="depth-section">
        <div className="depth-title-wrapper">
          <h4 className="depth-title">{label.replace(/_/g, ' ')} (0개)</h4>
          <button className="add-item-btn" onClick={handleAddItem}>
            + 항목 추가
          </button>
        </div>
        <div className="depth-body">
          <p className="empty-list-text">항목이 없습니다.</p>
        </div>
      </div>
    );
  }

  // 2. 값이 객체인 경우
  if (typeof value === 'object' && value !== null && !Array.isArray(value) && Object.keys(value).length > 0) {
    const itemCount = Object.keys(value).length;
    return (
      <div className="depth-section">
        <div className="depth-title-wrapper clickable" onClick={() => setIsExpanded(!isExpanded)}>
          <h4 className="depth-title">
            <span className="accordion-icon">{isExpanded ? '▼' : '▶'}</span>
            {label.replace(/_/g, ' ')} ({itemCount}개 항목)
          </h4>
        </div>
        {isExpanded && (
          <div className="depth-body">
            {Object.entries(value).map(([k, v]) => (
              <EditableDataItem 
                key={k} 
                label={k} 
                value={v} 
                onEdit={onEdit}
                onAddItem={onAddItem}
                onDeleteItem={onDeleteItem}
                path={[...path, k]}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // 3. 기본 값 렌더링 (편집 가능)
  const displayValue = (
    value === null || 
    value === undefined || 
    value === "" || 
    value === "None" || 
    value === "정보없음" || 
    value === "모름" ||
    value === -1 ||
    value === "불명확" ||
    value === "null" ||
    (Array.isArray(value) && value.length === 0)
  ) ? "-" : String(value);

  return (
    <div className="data-row editable-row">
      <span className="data-label">
        {label.replace(/_/g, ' ')}
      </span>
      {isEditing ? (
        <div className="edit-mode-wrapper">
          <input
            type="text"
            value={editValue || ''}
            onChange={(e) => setEditValue(e.target.value)}
            className="edit-input"
            autoFocus
          />
          <div className="edit-actions">
            <button onClick={handleSave} className="edit-btn save-btn">저장</button>
            <button onClick={handleCancel} className="edit-btn cancel-btn">취소</button>
          </div>
        </div>
      ) : (
        <div className="view-mode-wrapper">
          <span className="data-value">
            {displayValue}
          </span>
          <button onClick={() => setIsEditing(true)} className="edit-icon-btn">편집</button>
        </div>
      )}
    </div>
  );
};

// Raw 데이터 사이드바 컴포넌트
const RawDataSidebar = ({ rawText, isOpen, onToggle }) => {
  return (
    <>
      <div className={`sidebar-overlay ${isOpen ? 'active' : ''}`} onClick={onToggle}></div>
      <div className={`raw-data-sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h3>원본 데이터</h3>
          <button onClick={onToggle} className="close-sidebar-btn">✕</button>
        </div>
        <div className="sidebar-content">
          <pre className="raw-text">{rawText}</pre>
        </div>
      </div>
    </>
  );
};

// 메인 컴포넌트
const Step2Extract = ({ sessionData, updateSessionData, setCurrentStep }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [loadingStatus, setLoadingStatus] = useState(`${FIRM_NAME} AI가 사건을 분석하기 시작합니다...`);
  const [editedData, setEditedData] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    if (!sessionData.lastResult) {
      analyzeText();
    } else {
      setEditedData(sessionData.lastResult);
    }
  }, []);

  useEffect(() => {
    if (sessionData.lastResult) {
      setEditedData(sessionData.lastResult);
    }
  }, [sessionData.lastResult]);

  const analyzeText = async () => {
    setIsAnalyzing(true);
    setError('');

    const timer1 = setTimeout(() => setLoadingStatus("고객 정보를 추출 중입니다 ... [1/3]"), 5000);
    const timer2 = setTimeout(() => setLoadingStatus("사건 상세 정보를 추출 중입니다... [2/3]"), 60000);
    const timer3 = setTimeout(() => setLoadingStatus("상담 요약을 생성 중입니다... [3/3]"), 150000);

    try {
      const result = await extractLegalData(
        sessionData.textToAnalyze,
        sessionData.topic_code?.split(' > ').pop() || '이혼'
      );
      if (result) {
        const finalData = result.success ? result.data : result;
        updateSessionData('lastResult', finalData);
        setEditedData(finalData);
      }
    } catch (err) {
      setError('정보 추출 중 오류가 발생했습니다.');
    } finally {
      setIsAnalyzing(false);
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    }
  };

  const handleEdit = (path, newValue) => {
    const updatedData = JSON.parse(JSON.stringify(editedData));
    let current = updatedData;
    
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]];
    }
    
    current[path[path.length - 1]] = newValue;
    setEditedData(updatedData);
    updateSessionData('lastResult', updatedData);
  };

  const handleAddItem = (path) => {
    const updatedData = JSON.parse(JSON.stringify(editedData));
    let current = updatedData;
    
    for (let i = 0; i < path.length; i++) {
      current = current[path[i]];
    }
    
    // 배열에 항목 추가
    if (Array.isArray(current)) {
      // 기존 항목이 있으면 첫 번째 항목의 구조를 템플릿으로 사용
      if (current.length > 0) {
        const template = current[0];
        
        // 객체인 경우 키는 유지하고 값은 빈 문자열로
        if (typeof template === 'object' && template !== null && !Array.isArray(template)) {
          const newItem = {};
          Object.keys(template).forEach(key => {
            newItem[key] = "";
          });
          current.push(newItem);
        } else {
          // 기본 타입인 경우 빈 문자열 추가
          current.push("");
        }
      } else {
        // 빈 배열인 경우 빈 문자열 추가
        current.push("");
      }
    }
    
    setEditedData(updatedData);
    updateSessionData('lastResult', updatedData);
  };

  const handleDeleteItem = (path) => {
    const updatedData = JSON.parse(JSON.stringify(editedData));
    let current = updatedData;
    
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]];
    }
    
    const lastIndex = path[path.length - 1];
    if (Array.isArray(current)) {
      current.splice(lastIndex, 1);
    }
    
    setEditedData(updatedData);
    updateSessionData('lastResult', updatedData);
  };

  const data = editedData;

  return (
    <div className="step2-wrapper">
      <RawDataSidebar 
        rawText={sessionData.textToAnalyze || ''} 
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      <div className="step2-container">
        {!data ? (
          <div className="loading-wrapper">
            <div className="spinner"></div>
            <div className="loading-container">
              <p className="loading-status-text">{loadingStatus}</p>
              <div className="progress-bar">
                <div className="progress-bar-fill"></div>
              </div>
              <p className="loading-sub-text">
                {FIRM_NAME} AI가 사건을 정밀 분석 중입니다.
              </p>
            </div>
          </div>
        ) : (
          <div className="content-with-editor">
            <div className="main-content">
              <div className="analysis-report">
                <div className="header-actions">
                  <h2 className="step-title">사건 분석 리포트</h2>
                  <button 
                    className="toggle-sidebar-btn"
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                  >
                    원본 데이터 보기
                  </button>
                </div>

                {/* 1. 상단: 주제 코드 + 고객 정보 통합 카드 */}
                <div className="combined-header-card">
                  <div className="header-top">
                    <span className="topic-badge">{sessionData.topic_code}</span>
                    <h3>고객 기본 정보</h3>
                  </div>
                  <div className="header-body customer-info-grid">
                  {/* 행 1: 주요 인적 사항 (3열) */}
                  <div className="info-row three-cols">
                    {['성함', '성별', '연락처'].map((key) => (
                      <EditableDataItem 
                        key={key} 
                        label={key} 
                        value={data.고객_정보?.[key]} 
                        onEdit={handleEdit}
                        onAddItem={handleAddItem}
                        onDeleteItem={handleDeleteItem}
                        path={['고객_정보', key]}
                      />
                    ))}
                  </div>

                  {/* 행 2: 위치 및 기관 정보 (2열) */}
                  <div className="info-row two-cols">
                    {['주소', '관할_기관'].map((key) => (
                      <EditableDataItem 
                        key={key} 
                        label={key} 
                        value={data.고객_정보?.[key]} 
                        onEdit={handleEdit}
                        onAddItem={handleAddItem}
                        onDeleteItem={handleDeleteItem}
                        path={['고객_정보', key]}
                      />
                    ))}
                  </div>

                  {/* 기타 정보 (만약 있다면 1열로 나열) */}
                  {Object.entries(data.고객_정보 || {})
                    .filter(([k]) => !['성함', '성별', '연락처', '주소', '관할_기관'].includes(k))
                    .map(([k, v]) => (
                      <div className="info-row" key={k}>
                        <EditableDataItem 
                          label={k} value={v} 
                          onEdit={handleEdit} onAddItem={handleAddItem} onDeleteItem={handleDeleteItem}
                          path={['고객_정보', k]}
                        />
                      </div>
                    ))
                  }
                </div>
                </div>

                {/* 2. 하단: 일렬 배치 */}
                <div className="vertical-stack">
                  {/* 상세 내용 */}
                  {data.상세_내용 && (
                    <div className="combined-header-card">
                      <div className="header-top"><h3>상세 내용</h3></div>
                      <div className="card-body">
                        {Object.entries(data.상세_내용).map(([k, v]) => (
                          <EditableDataItem 
                            key={k} 
                            label={k} 
                            value={v} 
                            onEdit={handleEdit}
                            onAddItem={handleAddItem}
                            onDeleteItem={handleDeleteItem}
                            path={['상세_내용', k]}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 상담 설정 */}
                  {data.상담_설정 && (
                    <div className="combined-header-card">
                      <div className="header-top"><h3>상담 설정</h3></div>
                      <div className="card-body">
                        {Object.entries(data.상담_설정).map(([k, v]) => (
                          <EditableDataItem 
                            key={k} 
                            label={k} 
                            value={v} 
                            onEdit={handleEdit}
                            onAddItem={handleAddItem}
                            onDeleteItem={handleDeleteItem}
                            path={['상담_설정', k]}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 상담 요약 */}
                  {data.상담_요약 && (
                    <div className="combined-header-card">
                      <div className="header-top"><h3>상담 요약</h3></div>
                      <div className="card-body">
                        <div className="summary-edit-wrapper">
                          <textarea
                            className="summary-textarea"
                            value={data.상담_요약?.기타_사실관계_및_특이사항 || "특이사항이 없습니다."}
                            onChange={(e) => {
                              handleEdit(['상담_요약', '기타_사실관계_및_특이사항'], e.target.value);
                              // 자동 높이 조절
                              e.target.style.height = 'auto';
                              e.target.style.height = e.target.scrollHeight + 'px';
                            }}
                            onInput={(e) => {
                              // 초기 로드 시에도 높이 조절
                              e.target.style.height = 'auto';
                              e.target.style.height = e.target.scrollHeight + 'px';
                            }}
                            ref={(textarea) => {
                              if (textarea) {
                                textarea.style.height = 'auto';
                                textarea.style.height = textarea.scrollHeight + 'px';
                              }
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="action-section">
                  <button 
                    className="next-btn" 
                    onClick={() => {
                      updateSessionData("customerAddress", data.고객_정보?.주소 || "");
                      updateSessionData("authorityName", data.고객_정보?.관할_기관 || "");
                      updateSessionData("category", data.주제_코드 || sessionData.topic_code);
                      setCurrentStep(3);
                    }}
                  >
                    이 분석 내용을 바탕으로 유사 사례 검색
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Step2Extract;