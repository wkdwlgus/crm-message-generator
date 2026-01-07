// 1. Skin Type (Multi-select)
export const SKIN_TYPE_OPTIONS = {
  "Combination": "복합성",
  "Dry": "건성",
  "Oily": "지성",
  "Dehydrated_Oily": "수분부족지성"
} as const;

// 2. Skin Concerns (Multi-select)
export const SKIN_CONCERN_OPTIONS = {
  "Sensitive": "민감성",
  "Acne": "트러블",
  "Lack_of_Elasticity": "탄력없음",
  "Wrinkle": "주름",
  "Dullness": "칙칙함",
  "Pores": "모공",
  "None": "고민없음",
  "Redness": "붉은기"
} as const;

// 3. Preferred Tone (Single-select)
export const TONE_OPTIONS = {
  "Cool": "쿨톤",
  "Warm": "웜톤"
} as const;

// 4. Keywords (Multi-select)
export const KEYWORD_OPTIONS = {
  "Vegan": "비건",
  "Clean_Beauty": "클린 뷰티",
  "Hypoallergenic": "저자극",
  "Dermatologist_Tested": "피부과 테스트 완료",
  "Non_Comedogenic": "논코메도제닉",
  "Fragrance_Free": "무향",
  "Anti_Aging": "안티에이징",
  "Firming": "탄력 케어",
  "Moisture": "보습",
  "Glow": "윤광",
  "Premium": "프리미엄",
  "Limited": "한정판",
  "New_Arrival": "신상",
  "Gift": "선물용",
  "Sale": "할인",
  "whitening": "미백",
  "Nutrition": "영양공급",
  "Big_Size": "대용량",
  "One_plus_One": "1+1",
  "free_gift": "사은품",
  "Cica": "시카",
  "PDRN": "피디알엔",
  "Rethinol": "레티놀",
  "Collab":"콜라보",
  "Packaging":"패키징",
  "Glitter":"글리터",
  "Set_Item":"세트상품",
  "Luxury":"럭셔리",
  "Gift_Packaging":"선물포장"
} as const;

// 5. Target Brands (26개)
export const BRAND_LIST = [
  "라 리베라", "라네즈", "마몽드", "메이크온", "보타닉센스", "비레디", "설화수", "세잔느",
  "아모레베이직", "아모레성수", "아모레퍼시픽", "아이오페", "에뛰드", "에스트라", "에이피뷰티",
  "오딧세이", "이니스프리", "일리윤", "코스알엑스", "프리메라", "피카소", "피카소 꼴레지오니",
  "한율", "해피바스", "헤라", "홀리추얼"
] as const;