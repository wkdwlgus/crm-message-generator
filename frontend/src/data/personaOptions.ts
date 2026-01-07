export type PersonaOptionSet = {
  skinTypes: string[];
  concerns: string[];
  tone: string[];    
  keywords: string[];  
};

export const PERSONA_OPTIONS: Record<string, PersonaOptionSet> = {
  "1": {
    skinTypes: ["Combination", "Dry", "Oily", "Dehydrated_Oily"],
    concerns: ["Wrinkle", "Lack_of_Elasticity", "Dullness"],
    tone: ["Warm", "Cool"],
    keywords: ["Anti_Aging", "Firming", "Premium", "Glow", "Dermatologist_Tested", "whitening", "Nutrition"],
  },

  "2": {
    skinTypes: ["Combination", "Dry", "Oily", "Dehydrated_Oily"],
    concerns: ["Acne", "Pores", "None"],
    tone: ["Warm", "Cool"],
    keywords: ["Sale", "Moisture", "Non_Comedogenic", "Big_Size", "One_plus_One", "free_gift"],
  },

  "3": {
    skinTypes: ["Combination", "Dry", "Oily", "Dehydrated_Oily"],
    concerns: ["Sensitive", "Acne", "Redness"],
    tone: ["Warm", "Cool"],
    keywords: ["Vegan", "Clean_Beauty", "Hypoallergenic", "Non_Comedogenic", "Fragrance_Free", "Dermatologist_Tested", "Cica", "PDRN", "Rethinol"],
  },

  "4": {
    skinTypes: ["Combination", "Dry", "Oily", "Dehydrated_Oily"],
    concerns: ["Dullness", "Pores"],
    tone: ["Cool", "Warm"],
    keywords: ["New_Arrival", "Limited", "Glow", "Vegan", "Clean_Beauty", "Collab", "Packaging", "Glitter"],
  },

  "5": {
    skinTypes: ["Combination", "Dry", "Oily", "Dehydrated_Oily"],
    concerns: ["Wrinkle", "Lack_of_Elasticity"],
    tone: [], // 톤 불필요
    keywords: ["Gift", "Premium", "Anti_Aging", "Firming", "Set_Item", "Luxury", "Gift_Packaging"],
  },
};