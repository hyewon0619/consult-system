import React from 'react';

const LegalDataItem = ({ label, value, isSide = false, isPdf = false, depth = 0 }) => {
  const prefix = isPdf ? "pdf" : (isSide ? "side" : "data");
  const paddingStep = isPdf ? 15 : 12;
  const depthStyle = { paddingLeft: `${depth * paddingStep}px` };

  if (Array.isArray(value)) {
    const isEmptyArray = value.length === 0;
    return (
      <div className={`${prefix}-depth-section`} style={depthStyle}>
        <h6 className={`${prefix}-depth-title`} data-depth={depth}>
          {label.replace(/_/g, ' ')}
        </h6>
        <div className={`${prefix}-list-group`}>
          {isEmptyArray ? (
            <div className={`${prefix}-list-item-box`}>-</div>
          ) : (
            value.map((item, index) => (
              <div key={index} className={`${prefix}-list-item-box`}>
                {typeof item === 'object' ? (
                  Object.entries(item).map(([k, v]) => (
                    <LegalDataItem key={k} label={k} value={v} isSide={isSide} isPdf={isPdf} depth={depth + 1} />
                  ))
                ) : (
                  String(item || "-")
                )}
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  // 객체 데이터 처리 (재귀)
  if (value !== null && typeof value === 'object') {
    return (
      <div className={`${prefix}-depth-section`} style={depthStyle}>
        <h6 className={`${prefix}-depth-title`} data-depth={depth}>
          {label.replace(/_/g, ' ')}
        </h6>
        <div className={`${prefix}-depth-body`}>
          {Object.entries(value).map(([k, v]) => (
            <LegalDataItem key={k} label={k} value={v} isSide={isSide} isPdf={isPdf} depth={depth + 1} />
          ))}
        </div>
      </div>
    );
  }

  // 단일 데이터 처리 (-1 또는 값이 없는 경우 "-"로 표시)
  const displayValue = (value === -1 || value === null || value === undefined || value === ''|| value ==='정보없음' || value === "null") 
                       ? '-' 
                       : String(value);
  
  // 수정 포인트: '연락처', '성함', '성별' 등은 글자가 길어도 column-layout을 적용하지 않음
  const forceRowFields = ['연락처', '성함', '성별', '주소', '관할_기관', '관할기관'];
  const isForceRow = forceRowFields.includes(label);
  
  // 10글자 이상이더라도 강제 행 유지 필드가 아니면 column-layout 적용
  const isLongText = displayValue.length >= 10 && !isForceRow;
  
  const baseRowClass = isPdf ? "pdf-row" : (isSide ? "side-data-row" : "data-row");
  const finalRowClass = isLongText ? `${baseRowClass} column-layout` : baseRowClass;

  return (
    <div className={finalRowClass} style={depthStyle}>
      <strong className={`${prefix}-label`}>{label.replace(/_/g, ' ')}</strong>
      <span className={`${prefix}-value`}>{displayValue}</span>
    </div>
  );
};

export default LegalDataItem;