import React from 'react';
import './Stepper.css';

const Stepper = ({ currentStep, steps = [] }) => {
  if (steps.length === 0) return null;

  return (
    <div className="stepper-container">
      {steps.map((step, index) => {
        // 실제 스텝 번호 (1, 2, 3...)
        const stepNumber = index + 1;
        
        return (
          <React.Fragment key={step.id}>
            <div className={`step ${currentStep >= stepNumber ? 'active' : ''}`}>
              <div className="step-circle">
                {currentStep > stepNumber ? '✓' : stepNumber}
              </div>
              <div className="step-label">{step.label}</div>
            </div>
            
            {/* 마지막 단계가 아닐 때만 선을 그림 */}
            {index < steps.length - 1 && (
              <div className={`step-line ${currentStep > stepNumber ? 'active' : ''}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default Stepper;