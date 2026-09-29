import html2canvas from "html2canvas";
import jsPDF from "jspdf";

/**
 * PDF 생성 유틸리티
 */
export class PdfGenerator {
  constructor() {
    this.pdf = null;
    this.pageWidth = 210;
    this.pageHeight = 297;
    this.topMargin = 15;
    this.bottomMargin = 25;
    this.sideMargin = 15;
  }

  get contentWidth() {
    return this.pageWidth - (this.sideMargin * 2);
  }

  get maxContentHeight() {
    return this.pageHeight - this.topMargin - this.bottomMargin;
  }

  /**
   * PDF 생성 메인 함수
   * @param {HTMLElement} container - PDF로 변환할 컨테이너 엘리먼트
   * @returns {Promise<jsPDF>} - 생성된 PDF 객체
   */
  async generate(container) {
    if (!container) {
      throw new Error("PDF 생성을 위한 컨테이너가 필요합니다.");
    }

    this.pdf = new jsPDF("p", "mm", "a4");
    const sections = container.querySelectorAll(
      ".pdf-section-info, .pdf-section-summary, .pdf-case-card"
    );

    let totalPdfPages = 0;

    for (let i = 0; i < sections.length; i++) {
      const element = sections[i];
      const isCaseCard = element.classList.contains('pdf-case-card');
      
      totalPdfPages = await this._processSectionElement(
        element, 
        isCaseCard, 
        totalPdfPages
      );
    }

    return this.pdf;
  }

  /**
   * 각 섹션 엘리먼트를 PDF 페이지로 변환
   * @private
   */
  async _processSectionElement(element, isCaseCard, totalPdfPages) {
    const currentTopMargin = isCaseCard ? 30 : this.topMargin;
    const currentMaxHeight = this.pageHeight - currentTopMargin - this.bottomMargin;

    const canvas = await html2canvas(element, {
      scale: 1.5,
      useCORS: true,
      logging: false,
      backgroundColor: "#ffffff",
    });

    const imgData = canvas.toDataURL("image/jpeg", 0.9);
    const imgWidth = this.contentWidth;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;

    let remainingHeight = imgHeight;
    let sourceY = 0;
    let isFirstPageOfSection = true;

    while (remainingHeight > 0) {
      if (totalPdfPages > 0) {
        this.pdf.addPage();
      }
      totalPdfPages++;

      const pageTopMargin = (isCaseCard && isFirstPageOfSection) 
        ? currentTopMargin 
        : this.topMargin;
      const pageMaxHeight = this.pageHeight - pageTopMargin - this.bottomMargin;

      const heightToPrint = Math.min(pageMaxHeight, remainingHeight);
      const sourceHeight = (heightToPrint / imgHeight) * canvas.height;

      // 캔버스에서 임시 캔버스로 일부분 추출
      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = canvas.width;
      tempCanvas.height = sourceHeight;
      const tempCtx = tempCanvas.getContext('2d');

      tempCtx.drawImage(
        canvas,
        0, sourceY,
        canvas.width, sourceHeight,
        0, 0,
        canvas.width, sourceHeight
      );

      const partialImgData = tempCanvas.toDataURL("image/jpeg", 0.9);
      this.pdf.addImage(
        partialImgData,
        "JPEG",
        this.sideMargin,
        pageTopMargin,
        imgWidth,
        heightToPrint
      );

      remainingHeight -= heightToPrint;
      sourceY += sourceHeight;
      isFirstPageOfSection = false;
    }

    return totalPdfPages;
  }

  /**
   * 생성된 PDF를 다운로드
   * @param {string} filename
   */
  save(filename = "상담 프리뷰.pdf") {
    if (!this.pdf) {
      throw new Error("먼저 PDF를 생성해야 합니다.");
    }
    this.pdf.save(filename);
  }
}

/**
 * 간편 사용을 위한 헬퍼 함수
 * @param {HTMLElement} container - PDF로 변환할 컨테이너
 * @param {string} filename - 다운로드할 파일명
 */
export async function generateAndDownloadPdf(container, filename) {
  const generator = new PdfGenerator();
  await generator.generate(container);
  generator.save(filename);
}