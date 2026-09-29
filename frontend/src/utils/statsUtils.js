export const getConfidenceClass = (label) => {
  switch (label) {
    case '매우 높음':
      return 'very-high';
    case '높음':
      return 'high';
    case '보통':
      return 'medium';
    case '참고용(데이터 부족)':
    default:
      return 'low';
  }
};