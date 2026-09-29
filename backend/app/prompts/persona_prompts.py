class LegalPromptFactory:
    def __init__(self, category: str):
        self.category = category

        self.term_map = {
            "형사": ["검사", "피고인", "피의자"],
            "손해배상": ["원고", "피고"],
            "이혼": ["원고", "피고"]
        }
        self.allowed_terms = self.term_map.get(category, ["원고", "피고"])
        self.terms_str = ", ".join(self.allowed_terms)

    def get_lawyer_config(self):
        focus_terms = {
            "이혼": "유책성",
            "손해배상": "인과관계",
            "형사": "양형 조건"
        }
        category_focus = focus_terms.get(self.category, "법률적 쟁점 및 증거")
        
        system_msg = f"당신은 {self.category} 사건 데이터를 분석하는 법률 데이터 분석 전문가입니다."
        instructions = f"""
- 의뢰인을 지칭할 때 반드시 다음 용어 중 하나만 선택하여 사용하세요: [{self.terms_str}]
- {self.category}법 전문 용어를 활용하여 **{category_focus}** 관점에서 구체적으로 프로파일링하세요.
- 절대 지어내지말고 상담 내용에 기반하여 주요한 사실 관계를 근거를 통해 논리적으로 서술하세요.
- [상담내용]에 정보가 부족하다면 "None"을 반환하고, 반드시 3문장 이내로 작성하세요.

[출력 포맷]
state: 선택한 용어 ([{self.terms_str}] 중 택 1)
persona_lawyer: 법률 용어를 사용한 전문가 관점의 서술형 분석
"""
        return {"system": system_msg, "instructions": instructions}

    def get_layperson_config(self):
        system_msg = f"당신은 {self.category} 사건의 의뢰인입니다."
        instructions = f"""
- 자신을 지칭할 때 반드시 다음 용어 중 하나만 선택하여 사용하세요: [{self.terms_str}]
- 전문적인 법률 용어 대신, 일반인의 시각에서 사건이 일어난 **배경**(Background)과 **경위**를 서술하세요.
- 절대 지어내지말고 무엇이 문제의 시작이었는지, 상대방과 어떤 상황이 있었는지를 중심으로 객관적인 사실을 기록하세요.
- [상담내용]에 정보가 부족하다면 "None"을 반환하고, 반드시 3문장 이내로 작성하세요.

[출력 포맷]
state: 선택한 용어 ([{self.terms_str}] 중 택 1)
persona_layperson: 사건의 배경과 상황에 집중한 일반인 관점의 서술
"""
        return {"system": system_msg, "instructions": instructions}
    

def get_legal_schema(persona_type: str, category: str):
    term_map = {
        "형사": ["검사", "피고인", "피의자"],
        "손해배상": ["원고", "피고"],
        "이혼": ["원고", "피고"]
    }
    allowed_states = term_map.get(category, ["원고", "피고"])

    if persona_type == "lawyer":
        return {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string", 
                    "enum": allowed_states,
                    "description": f"사건에서의 지위 ({'/'.join(allowed_states)})"
                },
                "persona_lawyer": {"type": "string", "description": f"{category} 사건의 법리적 분석 결과"}
            },
            "required": ["state", "persona_lawyer"],
            "additionalProperties": False
        }
    else:
        return {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string", 
                    "enum": allowed_states,
                    "description": f"사건에서의 지위 ({'/'.join(allowed_states)})"
                },
                "persona_layperson": {"type": "string", "description": f"{category} 사건의 발생 경위 및 배경"}
            },
            "required": ["state", "persona_layperson"],
            "additionalProperties": False
        }