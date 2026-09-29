import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5분
  headers: {
    'Content-Type': 'application/json',
  },
});

// STT: 음성 파일 변환
export const transcribeAudio = async (files) => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });

  const response = await apiClient.post('/consult/transcribe', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Step 2: 핵심 정보 추출
export const extractLegalData = async (text, topicCode) => {
  const response = await apiClient.post('/consult/extract', {
    text,
    topic_code: topicCode,
  });
  return response.data;
};

// Step 3: 최종 분석 (persona 생성)
export const getFinalAnalysis = async ({ 
  text,
  category,
  customer_address = "전국",
  authority_name = "미기입"
} = {}) => {
  const response = await apiClient.post('/consult/search-case', { 
    text, 
    category, 
    customer_address, 
    authority_name 
  });
  
  return response.data;
};

// Step 4: 통합 리포트 생성 (한 번의 요청으로 백엔드에서 병렬 처리 및 결합)
export const generateFullReport = async ({ persona_data, example_case, meta_info }) => {
  const response = await apiClient.post('/generate-full-report', {
    persona_data,
    example_case,
    office: meta_info.office,
    specialty: meta_info.specialty,
    status: meta_info.status
  });
  return response.data;
};

export default apiClient;