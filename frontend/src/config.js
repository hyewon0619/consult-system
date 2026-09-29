// 표시용 브랜딩 값.
// 공개 저장소라 실제 법인명·자산 URL 은 두지 않는다.
// 배포 환경에서는 Vite 환경변수(.env)로 덮어쓴다.

export const FIRM_NAME = import.meta.env.VITE_FIRM_NAME ?? "법무법인";

// 변호사 프로필 이미지 호스트. 비어 있으면 이미지를 렌더링하지 않는다.
export const LAWYER_IMAGE_BASE_URL = import.meta.env.VITE_LAWYER_IMAGE_BASE_URL ?? "";
