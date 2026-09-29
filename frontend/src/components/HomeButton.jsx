import React from 'react';
import './Homebutton.css';

const HomeButton = () => {

  const goHome = () => {
    if (window.confirm("첫 페이지로 돌아가시겠습니까? 입력한 내용은 저장되지 않습니다.")) {
      window.location.href = '/';
    }
  };

  return (
    <button className="home-btn" onClick={goHome} aria-label="처음으로 돌아가기">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="28" height="28" viewBox="0 0 24 24"
        fill="none" stroke="currentColor" strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round"
      >
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
        <polyline points="9 22 9 12 15 12 15 22"></polyline>
      </svg>
    </button>
  );
};

export default HomeButton;