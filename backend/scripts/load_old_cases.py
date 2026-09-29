import asyncio
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from app.db.session import Base, engine, AsyncSessionLocal

# 1. 모든 키를 반영한 테이블 모델 정의
class OldCase(Base):
    __tablename__ = "old_cases"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    metaTitle = Column(Text, nullable=True)
    metaDescription = Column(Text, nullable=True)
    metaKeywords = Column(Text)
    content = Column(Text, nullable=True)
    pinned = Column(Boolean, default=False)
    subTitle = Column(Text, nullable=True)
    thumbnailPath = Column(String(500), nullable=True)
    subType = Column(String(100), nullable=True)
    centerSeq = Column(Integer, nullable=True)
    branchInformationId = Column(Integer, nullable=True)
    processStep = Column(String(100), nullable=True)
    published_at = Column(DateTime)

    # 복잡한 구조는 무조건 JSON!
    thumbnails = Column(JSON, nullable=True)
    lawyers = Column(JSON, nullable=True)
    businessCategory = Column(JSON, nullable=True)
    businessCategories = Column(JSON, nullable=True)
    hashTags = Column(JSON, nullable=True)
    contents = Column(JSON, nullable=True)
    businessProcess = Column(JSON, nullable=True)


async def setup_and_migrate():
    # --- [STEP 1] 테이블 생성 ---
    async with engine.begin() as conn:
        print("🛠️ 테이블 생성 또는 확인 중...")
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 테이블 준비 완료!")

    # --- [STEP 2] JSON 데이터 읽기 ---
    try:
        with open('scripts/old_case.json', 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    except FileNotFoundError:
        print("❌ 'scripts/old_case.json' 파일을 찾을 수 없습니다. 경로를 확인해주세요!")
        return

    # --- [STEP 3] 데이터 적재 ---
    async with AsyncSessionLocal() as session:
        try:
            print(f"🚀 총 {len(old_data)}건의 데이터를 DB에 적재합니다...")
            
            for item in old_data:
                # 날짜 변환 (Z 제거 및 isoformat 대응)
                pub_date = None
                raw_date = item.get('publishedAt')
                if raw_date:
                    pub_date = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))

                # 모델 생성
                new_case = OldCase(
                    id=item.get('id'),
                    title=item.get('title'),
                    result=item.get('result'),
                    description=item.get('description'),
                    metaTitle=item.get('metaTitle'),
                    metaDescription=item.get('metaDescription'),
                    metaKeywords=item.get('metaKeywords'),
                    content=item.get('content'),
                    pinned=item.get('pinned', False),
                    subTitle=item.get('subTitle'),
                    thumbnailPath=item.get('thumbnailPath'),
                    thumbnails=item.get('thumbnails'),
                    lawyers=item.get('lawyers'),
                    businessCategory=item.get('businessCategory'),
                    subType=item.get('subType'),
                    businessCategories=item.get('businessCategories'),
                    hashTags=item.get('hashTags'),
                    contents=item.get('contents'),
                    centerSeq=item.get('centerSeq'),
                    businessProcess=item.get('businessProcess'),
                    branchInformationId=item.get('branchInformationId'),
                    processStep=item.get('processStep'),
                    published_at=pub_date
                )
                # 동일한 ID가 있을 경우 업데이트하고 싶다면 session.merge(new_case) 사용
                session.add(new_case)
            
            await session.commit()
            print("✨ 축하합니다! 모든 데이터가 누락 없이 성공적으로 적재되었습니다.")

        except Exception as e:
            await session.rollback()
            print(f"❌ 작업 중 오류 발생: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(setup_and_migrate())