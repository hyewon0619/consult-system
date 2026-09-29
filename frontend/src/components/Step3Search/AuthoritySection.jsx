import { FIRM_NAME } from "../../config";
import React, { useState, useMemo } from "react";
import './AuthoritySection.css'

const AuthoritySection = ({ authorityStats, cityFlag }) => {
  const [selectedOrg, setSelectedOrg] = useState(null);

  const handleOrgClick = (groupKey) => {
    setSelectedOrg(selectedOrg === groupKey ? null : groupKey);
  };

  const authGroups = useMemo(() => {
    const details = authorityStats?.auth_details || [];
    const groups = details.reduce((acc, curr) => {
      const org = curr.organization || "미기입";

      if (!acc[org]) {
        acc[org] = {
          orgName: org,
          representative: curr.name,
          count: 0,
          memberList: [],
        };
      }

      acc[org].count += 1;
      acc[org].memberList.push({
        ...curr,
        department: curr.department || "미기입",
        job: curr.job || "미기입",
      });
      return acc;
    }, {});

    return Object.values(groups);
  }, [authorityStats?.auth_details]);

  return (
    <div className="authority-info-card">
      <div className="authority-content">
        {authorityStats?.incident_count > 0 ? (
          <p className="authority-banner-text">
            {FIRM_NAME}는 <strong>{authorityStats?.matched_org || "해당 기관"}</strong>
            {cityFlag ? " 지역 관련 " : "에서 "}
            <strong>{authorityStats?.auth_count || 0}명</strong>의 처분권자를 경험했고,{" "}
            <strong>{authorityStats?.incident_count}건</strong>을 함께 했어요
          </p>
        ) : (
          <p className="authority-banner-text">
            현재 <strong>전국 단위의 유사 사례</strong>를 바탕으로 
            고객님께 가장 적합한 <strong>맞춤형 법률 전략</strong>을 도출하고 있습니다
          </p>
        )}

        {/* 처분권자 명단 리스트 */}
        {authGroups.length > 0 && (
          <div className="auth-list-wrapper">
            <div className="name-tags">
              {authGroups.map((group, idx) => (
                <div key={idx} className="org-container">
                  <div
                    className={`name-tag-wrapper clickable ${selectedOrg === group.orgName ? "active" : ""}`}
                    onClick={() => handleOrgClick(group.orgName)}
                  >
                    <span className="name-tag">
                      <span className="org-text-bold">{group.orgName}</span>
                      <span className="name-text">{group.representative}</span>
                      <span className="more-indicator">
                        {group.count > 1 ? `외 ${group.count - 1}명` : ""}
                        <span className={`arrow ${selectedOrg === group.orgName ? "up" : "down"}`}>▾</span>
                      </span>
                    </span>
                  </div>

                  {selectedOrg === group.orgName && (
                    <div className="org-detail-list-rounded">
                      {group.memberList.map((person, pIdx) => (
                        <div key={pIdx} className="person-row-vertical">
                          <div className="person-header-info">
                            <div className="p-meta-group">
                                <span className="p-name">{person.name}</span>
                              {person.department && (
                                <span className="p-meta-item dept">{person.department}</span>
                              )}
                              {person.job && <span className="p-meta-item job">{person.job}</span>}
                            </div>
                          </div>
                          <div className="p-traits-vertical">
                            <div className="trait-item">
                              <span className="trait-label">개인특성</span>
                              <span className="t-badge p-trait">{person.personal_trait}</span>
                            </div>
                            <div className="trait-item">
                              <span className="trait-label">업무특성</span>
                              <span className="t-badge w-trait">{person.work_trait}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthoritySection;