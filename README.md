# 상담 서포트 시스템

법률 상담 현장에서 변호사를 실시간으로 보조하는 시스템입니다.
상담 녹음을 받아 **음성 → 사실관계 추출 → 유사 사례 검색 → 상담 리포트 생성**까지
네 단계를 이어 붙였습니다.

문제의식은 이렇습니다. 같은 사무실 안에서도 변호사마다 상담 성과 차이가 큽니다.
그 차이의 상당 부분은 실력이 아니라 **상담 자리에서 꺼내 쓸 수 있는 정보의 양**에서
옵니다. 비슷한 사건을 많이 다뤄 본 변호사는 예상 결과와 비용 범위를 바로 말할 수
있지만, 그렇지 않으면 "검토 후 연락드리겠다"로 끝납니다. 이 시스템은 그 정보를
상담 중에 화면으로 공급해서 격차를 줄이는 것을 목표로 합니다.

```
Python 3.12 · FastAPI · React 19 + Vite · MySQL · Elasticsearch(Nori) · FAISS · Whisper
```

> **데이터에 관하여**
> 이 저장소는 공개본이라 **실제 상담·사건 데이터를 일절 포함하지 않습니다.**
> 대신 운영 데이터와 스키마가 동일한 합성 데이터 생성기를 함께 둡니다
> (`backend/scripts/generate_sample_data.py`). 등장하는 인물·사건번호·기관은
> 전부 시드 고정 난수로 조합한 것입니다.

---

## 동작 방식

```
[1] 상담 녹음 업로드
        │  Whisper STT
        ▼
[2] 사실관계 추출              LLM 이 쟁점·당사자·청구취지를 구조화된 JSON 으로 뽑는다
        │                      (사건 유형별 프롬프트: 이혼 / 손해배상 / 형사)
        ▼
[3] 유사 사례 검색              Elasticsearch 하이브리드 검색
        │                        · dense_vector  — 임베딩 코사인 유사도
        │                        · Nori 형태소    — 법률 용어 사용자 사전 적용
        │                      → 승소율 통계 · 담당 변호사 · 예상 비용 산출
        ▼
[4] 상담 리포트                의뢰인에게 바로 건넬 PDF 초안을 생성한다
```

### 설계에서 신경 쓴 지점

**검색을 FAISS 에서 Elasticsearch 로 옮겼습니다.**
초기에는 FAISS 로 벡터 검색만 했는데, 법률 도메인에서는 "2019다12345" 같은 사건번호나
"상간소송" 같은 용어가 **정확히** 걸려야 하는 경우가 많았습니다. 벡터 유사도만으로는
이걸 놓칩니다. ES 로 옮기면서 `dense_vector` 와 Nori 형태소 검색을 한 쿼리에서
결합했고, 법률 용어 사용자 사전(`user_dict.txt`)을 토크나이저에 물려
`혼인파탄`·`면접교섭` 같은 복합어가 쪼개지지 않게 했습니다.
마이그레이션 경로는 `gen_es_index.py` 에 남아 있습니다.

**사건 유형마다 프롬프트를 분리했습니다.**
이혼·손해배상·형사는 뽑아야 할 사실관계가 전혀 다릅니다. 하나의 범용 프롬프트로는
이혼 사건의 `기여도`나 형사 사건의 `양형인자` 같은 항목을 안정적으로 못 뽑습니다.
`app/prompts/` 아래에 유형별로 나누고, 각 프롬프트에 JSON 스키마를 붙여
출력 형식을 고정했습니다.

**회사 고유 정보는 설정으로 뺐습니다.**
법인명·자산 URL 은 `settings.FIRM_NAME` / `frontend/src/config.js` 에서 주입합니다.
기본값은 중립적인 값이라, 클론한 그대로 돌려도 특정 조직이 드러나지 않습니다.

---

## 구조

```
backend/
├── app/
│   ├── api/v1/model.py         /consult/{transcribe,extract,search-case} · /generate-full-report
│   ├── core/engine.py          단계별 파이프라인 오케스트레이션
│   ├── services/
│   │   ├── llm_service.py      LLM 호출 · 스키마 강제
│   │   ├── search_engine.py    ES 하이브리드 검색
│   │   ├── cal_amount.py       예상 비용 산정
│   │   └── user_dict.txt       Nori 사용자 사전 (법률 용어)
│   ├── prompts/                사건 유형별 프롬프트 + JSON 스키마
│   └── common/config.py        설정 (법인명·API 키·ES 호스트)
├── gen_es_index.py             FAISS → Elasticsearch 색인
└── scripts/
    ├── generate_sample_data.py 합성 데이터 생성기
    └── load_old_cases.py       사례 DB 적재

frontend/src/
├── pages/                      Step1 입력 → Step2 추출 → Step3 검색 → Step4 리포트
├── components/Step3Search/     통계 · 변호사 · 페르소나 · 비용 섹션
└── utils/PdfGenerator.jsx      리포트 PDF 출력
```

---

## 실행

### 사전 준비

**Elasticsearch Nori 플러그인** — 한국어 형태소 분석에 필요합니다.

```bash
# Elasticsearch 설치 경로의 bin 폴더에서
./elasticsearch-plugin install analysis-nori
```

**환경 변수** — `backend/.env` 를 만듭니다.

```bash
DATABASE_URL=mysql+asyncmy://user:password@localhost:3306/consult
OPENAI_API_KEY=sk-...
ES_HOST=http://localhost:9200

# 선택: 비워 두면 중립적인 기본값이 쓰입니다
FIRM_NAME=법무법인
LAWYER_IMAGE_BASE_URL=
```

### 백엔드

```bash
cd backend
poetry config virtualenvs.create false
poetry install --no-root

python scripts/generate_sample_data.py   # 합성 데이터 생성
python scripts/load_old_cases.py         # DB 적재
python gen_es_index.py                   # ES 색인

python manage.py                         # 서버 기동
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

---

## 라이선스

MIT
