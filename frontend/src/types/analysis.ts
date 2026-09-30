export interface SkillGapResult {
  matched_skills: string[];
  transferable_skills: string[];
  missing_skills: string[];
  match_percentage: number;
  radar_metrics: {
    'Core Skills'?: number;
    'Transferable'?: number;
    'System Design'?: number;
    'Tooling'?: number;
    'Claim Credibility'?: number;
    [key: string]: number | undefined;
  };
}

export interface InterviewQuestion {
  question: string;
  target_claim: string;
  rationale: string;
  difficulty: 'Junior' | 'Mid' | 'Senior' | string;
}

export interface StarRecommendation {
  skill: string;
  current_gap: string;
  suggested_bullet: string;
}

export interface AnalysisResponse {
  evaluation_id?: string;
  candidate_name?: string | null;
  role_applied: string;
  gap_analysis: SkillGapResult;
  verification_flags: string[];
  targeted_questions: InterviewQuestion[];
  prep_plan: string[];
  star_recommendations?: StarRecommendation[];
  created_at?: string | null;
}

export interface JDCreate {
  title: string;
  experience_level: string;
  required_skills: string[];
  preferred_skills?: string[];
  description: string;
}
