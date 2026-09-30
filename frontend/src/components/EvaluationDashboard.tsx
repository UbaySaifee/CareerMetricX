import { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  XCircle,
  GitFork,
  Share2,
  Check,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Sparkles,
  CalendarCheck2,
  Target,
  HelpCircle,
  Briefcase,
  User,
  ExternalLink,
  Printer,
  MessageSquareCode,
  Send,
  RefreshCw,
  SlidersHorizontal,
  Copy,
  FileText,
  X,
} from 'lucide-react';
import type { AnalysisResponse, StarRecommendation } from '../types/analysis';
import RadarVisualizer from './RadarVisualizer';

interface EvaluationDashboardProps {
  analysis: AnalysisResponse;
  onReset: () => void;
}

interface DefenseFeedback {
  score: number;
  rating: 'Strong Defense' | 'Moderate Defense' | 'Needs More Rigor';
  ratingColor: string;
  hasTradeoffs: boolean;
  hasMetrics: boolean;
  hasTechKeywords: boolean;
  strengths: string[];
  suggestions: string[];
}

function evaluateDefenseAnswer(answer: string, targetClaim: string, question: string): DefenseFeedback {
  const text = answer.trim();
  const lower = text.toLowerCase();
  const wordCount = text.split(/\s+/).filter(Boolean).length;

  if (wordCount < 6) {
    return {
      score: 20,
      rating: 'Needs More Rigor',
      ratingColor: 'text-rose-400 bg-rose-950/60 border-rose-800',
      hasTradeoffs: false,
      hasMetrics: false,
      hasTechKeywords: false,
      strengths: [],
      suggestions: ['Please write a complete technical defense (at least 20-30 words) to substantiate your architecture.'],
    };
  }

  // 1. Trade-off keywords & architectural reasoning
  const tradeoffWords = [
    'trade-off', 'tradeoff', 'because', 'instead of', 'versus', 'vs', 'chose',
    'overhead', 'bottleneck', 'compromise', 'concurrency', 'latency', 'throughput',
    'resilience', 'failure', 'failover', 'sharding', 'pooling', 'cache', 'consistency',
    'memory', 'cpu', 'async', 'scalability', 'durability', 'synchronous', 'asynchronous'
  ];
  const matchedTradeoffs = tradeoffWords.filter((w) => lower.includes(w));
  const hasTradeoffs = matchedTradeoffs.length >= 1;

  // 2. Metrics & Benchmarks (quantifiable empirical evidence)
  const metricRegex = /\b(\d+%\b|\d+x\b|\d+\s*ms\b|\d+\s*s\b|\d+k\b|\d+\s*rps\b|\d+\s*users\b|\d+\s*req|baseline|benchmark|profil|measured|load test|locust|k6|wrk|latency|telemetry)/i;
  const hasMetrics = metricRegex.test(lower);

  // 3. Technical keywords from target claim and question
  const combinedContext = `${targetClaim} ${question}`.toLowerCase();
  const technicalKeywords = [
    'fastapi', 'python', 'docker', 'kubernetes', 'postgresql', 'postgres', 'redis',
    'kafka', 'mongo', 'mongodb', 'node', 'express', 'aws', 'gcp', 'sql', 'async',
    'microservice', 'api', 'graphql', 'grpc', 'rest', 'connection pool', 'index',
    'caching', 'sharding', 'event loop', 'pub/sub', 'broker'
  ];
  const claimWords = technicalKeywords.filter((k) => combinedContext.includes(k));
  const matchedTech = claimWords.filter((k) => lower.includes(k));
  const hasTechKeywords = matchedTech.length >= 1 || wordCount >= 35;

  // Scoring weights
  let score = 25;
  const strengths: string[] = [];
  const suggestions: string[] = [];

  if (hasTradeoffs) {
    score += 30;
    strengths.push(`Articulated design trade-offs (${matchedTradeoffs.slice(0, 3).join(', ')}).`);
  } else {
    suggestions.push('Articulate explicit design trade-offs (e.g. why this choice was made over alternatives, latency vs memory overhead).');
  }

  if (hasMetrics) {
    score += 30;
    strengths.push('Referenced measurable performance metrics or empirical benchmarking baselines.');
  } else {
    suggestions.push('Include concrete quantitative metrics (e.g. baseline vs tuned latency in ms, RPS throughput, or profiling tools used).');
  }

  if (hasTechKeywords) {
    score += 15;
    strengths.push(`Directly connected response to claim technical context${matchedTech.length ? ` (${matchedTech.slice(0, 3).join(', ')})` : ''}.`);
  } else {
    suggestions.push('Explicitly reference the underlying technology stack and libraries from the target claim.');
  }

  if (wordCount >= 35) {
    score = Math.min(100, score + 10);
  }

  let rating: 'Strong Defense' | 'Moderate Defense' | 'Needs More Rigor' = 'Needs More Rigor';
  let ratingColor = 'text-rose-400 bg-rose-950/60 border-rose-800';

  if (score >= 75) {
    rating = 'Strong Defense';
    ratingColor = 'text-emerald-400 bg-emerald-950/60 border-emerald-800';
  } else if (score >= 50) {
    rating = 'Moderate Defense';
    ratingColor = 'text-amber-400 bg-amber-950/60 border-amber-800';
  }

  return {
    score,
    rating,
    ratingColor,
    hasTradeoffs,
    hasMetrics,
    hasTechKeywords,
    strengths,
    suggestions,
  };
}

export default function EvaluationDashboard({ analysis, onReset }: EvaluationDashboardProps) {
  const [copied, setCopied] = useState<boolean>(false);
  const [expandedQuestions, setExpandedQuestions] = useState<Record<number, boolean>>({
    0: true, // Expand first by default
  });
  const [completedDays, setCompletedDays] = useState<Record<number, boolean>>({});

  // Mock Defense States
  const [defenseDrafts, setDefenseDrafts] = useState<Record<number, string>>({});
  const [defenseFeedbacks, setDefenseFeedbacks] = useState<Record<number, DefenseFeedback>>({});
  const [defenseOpen, setDefenseOpen] = useState<Record<number, boolean>>({});

  // STAR Transferable Recommendation Modal State
  const [activeStarSkill, setActiveStarSkill] = useState<string | null>(null);
  const [copiedStarBullet, setCopiedStarBullet] = useState<boolean>(false);

  const matchScore = Math.round(analysis.gap_analysis.match_percentage);

  // Categorize verification flags into ATS manipulation findings and project claim checks
  const atsFlags = analysis.verification_flags.filter((flag) =>
    /ATS|Prompt Injection|Keyword-Stuffing|Excessive Skill Density|Adversarial|manipulation|Jailbreak/i.test(flag)
  );
  const claimFlags = analysis.verification_flags.filter(
    (flag) =>
      !/ATS|Prompt Injection|Keyword-Stuffing|Excessive Skill Density|Adversarial|manipulation|Jailbreak/i.test(flag)
  );

  // Resolved active STAR recommendation object
  const activeRecommendation: StarRecommendation | undefined = analysis.star_recommendations?.find(
    (r) => r.skill.toLowerCase() === activeStarSkill?.toLowerCase()
  ) || (activeStarSkill ? {
    skill: activeStarSkill,
    current_gap: `Adjacent transferable competency identified in job description for ${analysis.role_applied}.`,
    suggested_bullet: `Spearheaded technical adoption of ${activeStarSkill} to satisfy core ${analysis.role_applied} requirements: engineered decoupled service interfaces, evaluated design trade-offs against baseline architecture, and validated performance under simulated production load, lowering operational latency by 35%.`
  } : undefined);

  const handleCopyStarBullet = (bullet: string) => {
    navigator.clipboard.writeText(bullet);
    setCopiedStarBullet(true);
    setTimeout(() => setCopiedStarBullet(false), 2000);
  };

  // Determine alignment tier
  const getReadinessTier = (score: number) => {
    if (score >= 80) return { label: 'High Readiness', color: 'text-emerald-400', bg: 'bg-emerald-950/80 border-emerald-700/60' };
    if (score >= 60) return { label: 'Moderate Alignment', color: 'text-amber-400', bg: 'bg-amber-950/80 border-amber-700/60' };
    return { label: 'Remediation Needed', color: 'text-rose-400', bg: 'bg-rose-950/80 border-rose-700/60' };
  };

  const tier = getReadinessTier(matchScore);

  const toggleQuestion = (index: number) => {
    setExpandedQuestions((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const toggleDayCompletion = (dayIndex: number) => {
    setCompletedDays((prev) => ({
      ...prev,
      [dayIndex]: !prev[dayIndex],
    }));
  };

  const toggleDefenseDrawer = (index: number) => {
    setDefenseOpen((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const handleValidateDefense = (index: number, targetClaim: string, question: string) => {
    const draft = defenseDrafts[index] || '';
    const feedback = evaluateDefenseAnswer(draft, targetClaim, question);
    setDefenseFeedbacks((prev) => ({
      ...prev,
      [index]: feedback,
    }));
  };

  const handleClearDefense = (index: number) => {
    setDefenseDrafts((prev) => ({
      ...prev,
      [index]: '',
    }));
    setDefenseFeedbacks((prev) => {
      const next = { ...prev };
      delete next[index];
      return next;
    });
  };

  const completedCount = Object.values(completedDays).filter(Boolean).length;
  const totalDays = analysis.prep_plan.length || 7;
  const prepProgressPct = Math.round((completedCount / totalDays) * 100);

  const handleCopyShareLink = async () => {
    try {
      const url = new URL(window.location.href);
      if (analysis.evaluation_id) {
        url.searchParams.set('report', analysis.evaluation_id);
      }
      await navigator.clipboard.writeText(url.toString());
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  // Circular gauge constants
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (matchScore / 100) * circumference;

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-in fade-in duration-500">
      {/* Print-Only Official Dossier Banner */}
      <div className="print-only mb-6 border-b-2 border-slate-900 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">CareerMetricX Candidate Evaluation Dossier</h1>
            <p className="text-xs text-slate-600">Evidence-Grounded Capability Verification &amp; Interview Defense Report</p>
          </div>
          <div className="text-right text-xs text-slate-700 font-mono space-y-0.5">
            <p>Candidate: <strong>{analysis.candidate_name || 'Portfolio Candidate'}</strong></p>
            <p>Role Applied: <strong>{analysis.role_applied}</strong></p>
            <p>Match Score: <strong>{matchScore}%</strong> | ID: {analysis.evaluation_id ? analysis.evaluation_id.slice(0, 8) : 'LOCAL'}</p>
            <p>Generated: {new Date().toLocaleDateString()}</p>
          </div>
        </div>
      </div>

      {/* Top Header Card */}
      <section className="p-6 sm:p-8 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-2xl backdrop-blur-xl relative overflow-hidden print-card">
        {/* Glow backdrop decoration (hidden in print) */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none no-print" />
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none no-print" />

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 relative z-10">
          {/* Candidate & Role Info */}
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs font-mono text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>Verification Report: {analysis.evaluation_id ? analysis.evaluation_id.slice(0, 8) : 'Generated'}</span>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
                <User className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                  {analysis.candidate_name || 'Candidate Portfolio'}
                </h1>
                <div className="flex items-center gap-2 text-slate-400 text-sm mt-0.5">
                  <Briefcase className="w-4 h-4 text-indigo-400" />
                  <span>Target Role: <strong className="text-slate-200">{analysis.role_applied}</strong></span>
                </div>
              </div>
            </div>
          </div>

          {/* Match Score Ring Gauge & Actions */}
          <div className="flex flex-wrap items-center gap-6">
            {/* Circular Gauge */}
            <div className="flex items-center gap-4 p-3 pr-5 rounded-2xl bg-slate-950/70 border border-slate-800 shadow-inner">
              <div className="relative w-24 h-24 flex items-center justify-center">
                <svg className="w-24 h-24 transform -rotate-90">
                  <circle
                    cx="48"
                    cy="48"
                    r={radius}
                    stroke="currentColor"
                    strokeWidth="8"
                    className="text-slate-800"
                    fill="transparent"
                  />
                  <circle
                    cx="48"
                    cy="48"
                    r={radius}
                    stroke="url(#matchGradient)"
                    strokeWidth="8"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                    fill="transparent"
                  />
                  <defs>
                    <linearGradient id="matchGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#6366f1" />
                      <stop offset="50%" stopColor="#8b5cf6" />
                      <stop offset="100%" stopColor="#06b6d4" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute flex flex-col items-center justify-center text-center">
                  <span className="text-2xl font-black font-mono text-white leading-none">
                    {matchScore}%
                  </span>
                  <span className="text-[9px] uppercase tracking-wider text-slate-400 mt-0.5">
                    Match
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                <span className={`inline-block text-xs font-semibold px-2.5 py-0.5 rounded-full border ${tier.bg} ${tier.color}`}>
                  {tier.label}
                </span>
                <p className="text-xs text-slate-400 max-w-[140px] leading-tight">
                  Weighted alignment against mandatory and preferred competencies
                </p>
              </div>
            </div>

            {/* Action Buttons (Hidden in Print) */}
            <div className="flex flex-col sm:flex-row gap-2.5 no-print">
              <button
                onClick={() => window.print()}
                className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs sm:text-sm border border-slate-700 transition active:scale-95 cursor-pointer"
                title="Export evaluation dossier to PDF"
              >
                <Printer className="w-4 h-4 text-cyan-400" />
                <span>Export Dossier</span>
              </button>
              <button
                onClick={handleCopyShareLink}
                className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs sm:text-sm shadow-lg shadow-indigo-600/30 transition active:scale-95 cursor-pointer"
                title="Copy shareable link"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-300" /> : <Share2 className="w-4 h-4" />}
                <span>{copied ? 'Link Copied!' : 'Share Report'}</span>
              </button>
              <button
                onClick={onReset}
                className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs sm:text-sm border border-slate-700 transition active:scale-95 cursor-pointer"
              >
                <RotateCcw className="w-4 h-4" />
                <span>New Evaluation</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Main Analysis Visualizations Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: 5-Dimension Radar */}
        <div className="lg:col-span-5 w-full print-avoid-break">
          <RadarVisualizer metrics={analysis.gap_analysis.radar_metrics} />
        </div>

        {/* Right Column: 3-Tier Categorized Competency Pills */}
        <div className="lg:col-span-7 space-y-4 print-avoid-break">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md shadow-xl space-y-6 print-card">
            <div>
              <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                <Target className="w-4 h-4 text-indigo-400" />
                Competency Alignment Breakdown
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                4-tier evidence classification based on semantic embeddings and verified project narratives
              </p>
            </div>

            {/* 3-Column Pill Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* 1. Matched Skills (Green) */}
              <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-800/40 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      Matched
                    </span>
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-900/70 text-emerald-300 border border-emerald-700/60">
                      {analysis.gap_analysis.matched_skills.length}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 min-h-[50px]">
                    {analysis.gap_analysis.matched_skills.length > 0 ? (
                      analysis.gap_analysis.matched_skills.map((skill) => (
                        <span
                          key={skill}
                          className="px-2.5 py-1 rounded-lg bg-emerald-900/50 border border-emerald-700/50 text-emerald-200 text-xs font-medium font-mono"
                        >
                          {skill}
                        </span>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500 italic">No direct matches</p>
                    )}
                  </div>
                </div>
                <p className="text-[10px] text-emerald-400/80 mt-3 pt-2 border-t border-emerald-900/40">
                  Direct match &ge; 70%
                </p>
              </div>

              {/* 2. Transferable Skills (Yellow/Amber) with STAR Optimization */}
              <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-800/40 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                      <GitFork className="w-4 h-4 text-amber-400" />
                      Transferable
                    </span>
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-amber-900/70 text-amber-300 border border-amber-700/60">
                      {analysis.gap_analysis.transferable_skills.length}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 min-h-[50px]">
                    {analysis.gap_analysis.transferable_skills.length > 0 ? (
                      analysis.gap_analysis.transferable_skills.map((skill) => (
                        <button
                          key={skill}
                          type="button"
                          onClick={() => {
                            setActiveStarSkill(skill);
                            setCopiedStarBullet(false);
                          }}
                          className="group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-900/60 hover:bg-amber-800/80 border border-amber-700/60 hover:border-amber-400 text-amber-200 text-xs font-medium font-mono transition cursor-pointer shadow-sm hover:scale-[1.02] active:scale-95"
                          title="Click to view STAR Optimization resume rewrite"
                        >
                          <span>{skill}</span>
                          <span className="flex items-center gap-0.5 text-[9px] font-sans font-bold px-1 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 group-hover:bg-amber-400 group-hover:text-amber-950 transition">
                            <Sparkles className="w-2.5 h-2.5" />
                            STAR
                          </span>
                        </button>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500 italic">No transferable skills detected</p>
                    )}
                  </div>
                </div>
                <div className="mt-3 pt-2 border-t border-amber-900/40 flex items-center justify-between text-[10px] text-amber-400/80">
                  <span>Adjacent match 50% - 69%</span>
                  {analysis.gap_analysis.transferable_skills.length > 0 && (
                    <span className="text-amber-300/90 font-medium flex items-center gap-1 no-print">
                      <Sparkles className="w-2.5 h-2.5 text-amber-400" />
                      1-click STAR rewrites
                    </span>
                  )}
                </div>
              </div>

              {/* 3. Missing Skills (Red/Rose) */}
              <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800/40 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                      <XCircle className="w-4 h-4 text-rose-400" />
                      Missing Gaps
                    </span>
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-rose-900/70 text-rose-300 border border-rose-700/60">
                      {analysis.gap_analysis.missing_skills.length}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 min-h-[50px]">
                    {analysis.gap_analysis.missing_skills.length > 0 ? (
                      analysis.gap_analysis.missing_skills.map((skill) => (
                        <span
                          key={skill}
                          className="px-2.5 py-1 rounded-lg bg-rose-900/50 border border-rose-700/50 text-rose-200 text-xs font-medium font-mono"
                        >
                          {skill}
                        </span>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500 italic">All requirements fulfilled</p>
                    )}
                  </div>
                </div>
                <p className="text-[10px] text-rose-400/80 mt-3 pt-2 border-t border-rose-900/40">
                  Unaddressed &lt; 50%
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Integrity & ATS Manipulation Audit Alert Card (Displayed when ATS anomalies are detected) */}
      {atsFlags.length > 0 && (
        <section className="p-5 sm:p-6 rounded-2xl bg-gradient-to-r from-rose-950/50 via-amber-950/30 to-rose-950/50 border-2 border-rose-600/80 shadow-2xl shadow-rose-950/40 space-y-4 print-card print-avoid-break animate-in fade-in duration-300">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-rose-900/60 pb-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-rose-600/20 text-rose-400 border border-rose-500/50 shrink-0">
                <AlertOctagon className="w-6 h-6 animate-pulse" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base sm:text-lg font-bold text-rose-200 tracking-tight">
                    Integrity &amp; ATS Manipulation Audit Alert
                  </h3>
                  <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded-full bg-rose-900/90 text-rose-200 border border-rose-600">
                    High Risk Anomaly
                  </span>
                </div>
                <p className="text-xs text-rose-300/80 mt-0.5">
                  Automated screening identified keyword-stuffing patterns, prompt injection tokens, or excessive skill density in the source document.
                </p>
              </div>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-rose-950 text-rose-300 border border-rose-700/80 shrink-0 w-fit">
              {atsFlags.length} Integrity Notice{atsFlags.length > 1 ? 's' : ''}
            </span>
          </div>

          <div className="space-y-2.5">
            {atsFlags.map((flag, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-slate-950/85 border border-rose-800/70 flex items-start gap-3 text-xs"
              >
                <div className="p-1 rounded-md bg-rose-900/60 text-rose-300 shrink-0 mt-0.5">
                  <AlertOctagon className="w-3.5 h-3.5" />
                </div>
                <div className="space-y-1">
                  <span className="font-bold text-rose-300 uppercase tracking-wide text-[11px]">
                    ATS Anomaly Finding #{idx + 1}
                  </span>
                  <p className="text-slate-200 leading-relaxed font-sans">{flag}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-rose-900/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-[11px] text-rose-300/80">
            <span>
              <strong>Engineering Recommendation:</strong> Replace comma-separated skill lists with quantified STAR bullet points to pass strict enterprise ATS filters.
            </span>
            <span className="font-mono text-rose-400 text-[10px]">Severity: High Impact</span>
          </div>
        </section>
      )}

      {/* Claim Reliability Warning Cards */}
      <section className="space-y-4 print-avoid-break">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">
              Claim Reliability &amp; Metric Verification
            </h2>
          </div>
          <span className="text-xs text-slate-400">
            {claimFlags.length} audit notice(s)
          </span>
        </div>

        {claimFlags.length > 0 &&
        !claimFlags[0].toLowerCase().includes('all analyzed project assertions adhere') ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {claimFlags.map((flag, idx) => (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-amber-950/20 border border-amber-800/50 flex items-start gap-3 shadow-md hover:border-amber-700/70 transition print-card"
              >
                <div className="p-2 rounded-xl bg-amber-900/40 text-amber-400 shrink-0 mt-0.5">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-bold text-amber-300 uppercase tracking-wider">
                    Unsubstantiated Metric Flag #{idx + 1}
                  </span>
                  <p className="text-xs text-slate-300 leading-relaxed">{flag}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-800/40 flex items-center gap-3 print-card">
            <div className="p-2 rounded-xl bg-emerald-900/40 text-emerald-400 shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-emerald-300">
                All Assertions Realistic &amp; Grounded
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                No unbacked 100x speedups, extreme availability claims, or vague unquantified assertions were detected.
              </p>
            </div>
          </div>
        )}
      </section>

      {/* Viva Interview Questions Accordion & Candidate Mock Defense Mode */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-indigo-400" />
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">
                Targeted Viva Interrogation Questions
              </h2>
              <p className="text-xs text-slate-400">
                Probing specific resume claims, system design trade-offs, and requirement gaps
              </p>
            </div>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
            {analysis.targeted_questions.length} Questions Grounded
          </span>
        </div>

        <div className="space-y-4">
          {analysis.targeted_questions.map((q, idx) => {
            const isExpanded = !!expandedQuestions[idx];
            const isDefenseOpen = !!defenseOpen[idx];
            const currentDraft = defenseDrafts[idx] || '';
            const feedback = defenseFeedbacks[idx];

            const diffColor =
              q.difficulty === 'Senior'
                ? 'bg-violet-950/80 text-violet-300 border-violet-800'
                : q.difficulty === 'Junior'
                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
                : 'bg-amber-950/80 text-amber-300 border-amber-800';

            return (
              <div
                key={idx}
                className="rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition overflow-hidden shadow-lg print-card print-avoid-break"
              >
                {/* Accordion Question Header */}
                <button
                  type="button"
                  onClick={() => toggleQuestion(idx)}
                  className="w-full p-4 sm:p-5 text-left flex items-start justify-between gap-4 cursor-pointer focus:outline-none"
                >
                  <div className="flex items-start gap-3">
                    <span className="w-7 h-7 rounded-xl bg-indigo-950 border border-indigo-800/80 text-indigo-300 text-xs font-mono font-bold flex items-center justify-center shrink-0 mt-0.5">
                      Q{idx + 1}
                    </span>
                    <div className="space-y-1">
                      <p className="text-sm sm:text-base font-semibold text-slate-100 leading-snug">
                        {q.question}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 pt-1">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${diffColor}`}>
                          Tier: {q.difficulty}
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
                          <Target className="w-3 h-3 text-indigo-400" />
                          <span className="truncate max-w-xs sm:max-w-md">Target: {q.target_claim}</span>
                        </span>
                        {feedback && (
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${feedback.ratingColor} no-print`}>
                            Defense: {feedback.rating} ({feedback.score}%)
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-slate-400 p-1 rounded-lg bg-slate-800/50 hover:bg-slate-800 no-print">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </button>

                {/* Question Details & Rubric (Always printed via print-expand) */}
                <div className={`px-4 pb-4 sm:px-5 sm:pb-5 pt-1 border-t border-slate-800/60 bg-slate-950/40 text-xs space-y-3 ${isExpanded ? 'block' : 'hidden print-expand'}`}>
                    <div className="flex items-start gap-2 text-indigo-300 font-medium pt-1">
                      <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                      <span>Technical Defense &amp; Interrogation Rubric:</span>
                    </div>
                    <p className="text-slate-300 pl-6 leading-relaxed bg-slate-900/60 p-3 rounded-xl border border-slate-800/80">
                      {q.rationale}
                    </p>

                    {/* Candidate Mock Defense Mode Drawer (Interactive, excluded in print) */}
                    <div className="mt-3 pt-3 border-t border-slate-800/60 no-print">
                      <div className="flex items-center justify-between">
                        <button
                          type="button"
                          onClick={() => toggleDefenseDrawer(idx)}
                          className="inline-flex items-center gap-2 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition cursor-pointer"
                        >
                          <MessageSquareCode className="w-4 h-4 text-cyan-400" />
                          <span>Practice Your Defense (Mock Interview Mode)</span>
                          {isDefenseOpen ? (
                            <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                          )}
                        </button>
                        {feedback && (
                          <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded-md border ${feedback.ratingColor}`}>
                            Score: {feedback.score} / 100
                          </span>
                        )}
                      </div>

                      {/* Expandable Defense Practice Area */}
                      {isDefenseOpen && (
                        <div className="mt-3 p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3 animate-in fade-in duration-200">
                          <p className="text-[11px] text-slate-400 leading-relaxed">
                            Formulate your technical defense response. The validation engine audits your draft for
                            <strong> architectural trade-offs</strong>, <strong>empirical metrics</strong>, and <strong>claim keyword consistency</strong>.
                          </p>

                          <textarea
                            rows={3}
                            value={currentDraft}
                            onChange={(e) => {
                              const val = e.target.value;
                              setDefenseDrafts((prev) => ({ ...prev, [idx]: val }));
                            }}
                            placeholder="Draft your technical response... (e.g. 'In this service we implemented FastAPI with asyncpg connection pools. The primary trade-off was higher initial memory overhead versus eliminating connection starvation. We benchmarked using Locust and reduced latency from 180ms to 45ms under 15k RPS...')"
                            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 text-xs focus:outline-none focus:border-indigo-500 transition leading-relaxed font-sans"
                          />

                          <div className="flex items-center justify-between">
                            <span className="text-[11px] text-slate-500 font-mono">
                              Words: {currentDraft.trim() ? currentDraft.trim().split(/\s+/).length : 0}
                            </span>
                            <div className="flex items-center gap-2">
                              {currentDraft && (
                                <button
                                  type="button"
                                  onClick={() => handleClearDefense(idx)}
                                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs font-medium transition cursor-pointer flex items-center gap-1"
                                >
                                  <RefreshCw className="w-3 h-3" />
                                  <span>Clear</span>
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() => handleValidateDefense(idx, q.target_claim, q.question)}
                                disabled={!currentDraft.trim()}
                                className={`px-4 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1.5 transition cursor-pointer shadow-md ${
                                  !currentDraft.trim()
                                    ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                                    : 'bg-gradient-to-r from-indigo-600 to-cyan-500 hover:opacity-95 text-white active:scale-95'
                                }`}
                              >
                                <Send className="w-3 h-3" />
                                <span>Validate Answer</span>
                              </button>
                            </div>
                          </div>

                          {/* Instant Client-Side Validation Feedback */}
                          {feedback && (
                            <div className="mt-3 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/90 space-y-2.5 animate-in fade-in duration-200">
                              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                                <div className="flex items-center gap-2">
                                  <SlidersHorizontal className="w-4 h-4 text-indigo-400" />
                                  <span className="text-xs font-bold text-white">Defense Validation Scorecard</span>
                                </div>
                                <span className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded-full border ${feedback.ratingColor}`}>
                                  {feedback.rating} ({feedback.score}%)
                                </span>
                              </div>

                              {/* 3 Metric Verification Indicators */}
                              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                <div className={`p-2 rounded-lg border text-[11px] flex items-center justify-between ${
                                  feedback.hasTradeoffs
                                    ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-300'
                                    : 'bg-rose-950/30 border-rose-800/60 text-rose-300'
                                }`}>
                                  <span>Trade-off Analysis</span>
                                  {feedback.hasTradeoffs ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <XCircle className="w-3.5 h-3.5 text-rose-400" />}
                                </div>

                                <div className={`p-2 rounded-lg border text-[11px] flex items-center justify-between ${
                                  feedback.hasMetrics
                                    ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-300'
                                    : 'bg-rose-950/30 border-rose-800/60 text-rose-300'
                                }`}>
                                  <span>Empirical Metrics</span>
                                  {feedback.hasMetrics ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <XCircle className="w-3.5 h-3.5 text-rose-400" />}
                                </div>

                                <div className={`p-2 rounded-lg border text-[11px] flex items-center justify-between ${
                                  feedback.hasTechKeywords
                                    ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-300'
                                    : 'bg-rose-950/30 border-rose-800/60 text-rose-300'
                                }`}>
                                  <span>Claim Context Match</span>
                                  {feedback.hasTechKeywords ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <XCircle className="w-3.5 h-3.5 text-rose-400" />}
                                </div>
                              </div>

                              {/* Strengths identified */}
                              {feedback.strengths.length > 0 && (
                                <div className="space-y-1 pt-1">
                                  <p className="text-[11px] font-semibold text-emerald-400">Validated Strengths:</p>
                                  {feedback.strengths.map((str, sIdx) => (
                                    <p key={sIdx} className="text-[11px] text-slate-300 flex items-start gap-1.5 pl-1">
                                      <span className="text-emerald-400">✓</span>
                                      <span>{str}</span>
                                    </p>
                                  ))}
                                </div>
                              )}

                              {/* Actionable Recommendations */}
                              {feedback.suggestions.length > 0 && (
                                <div className="space-y-1 pt-1">
                                  <p className="text-[11px] font-semibold text-amber-400">Interrogation Defense Advice:</p>
                                  {feedback.suggestions.map((sug, sugIdx) => (
                                    <p key={sugIdx} className="text-[11px] text-slate-300 flex items-start gap-1.5 pl-1">
                                      <span className="text-amber-400">•</span>
                                      <span>{sug}</span>
                                    </p>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 7-Day Technical Prep Roadmap */}
      <section className="p-6 sm:p-8 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-6 print-card print-avoid-break">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <CalendarCheck2 className="w-5 h-5 text-indigo-400" />
              <h2 className="text-xl font-bold text-white tracking-tight">
                7-Day Engineering Remediation Roadmap
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Interactive milestone checklist targeting identified gaps for <strong className="text-slate-200">{analysis.role_applied}</strong>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-slate-300">
              Completed: <strong className="text-indigo-400">{completedCount}</strong> / {totalDays}
            </span>
            <div className="w-24 h-2 rounded-full bg-slate-800 overflow-hidden no-print">
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-300"
                style={{ width: `${prepProgressPct}%` }}
              />
            </div>
          </div>
        </div>

        {/* Roadmap Items */}
        <div className="grid grid-cols-1 gap-3">
          {analysis.prep_plan.map((dayPlan, idx) => {
            const isCompleted = !!completedDays[idx];
            return (
              <div
                key={idx}
                onClick={() => toggleDayCompletion(idx)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-start gap-4 select-none ${
                  isCompleted
                    ? 'bg-indigo-950/30 border-indigo-700/60 text-slate-400'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-200'
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 mt-0.5 border transition ${
                    isCompleted
                      ? 'bg-indigo-600 border-indigo-500 text-white'
                      : 'border-slate-700 bg-slate-800 hover:border-slate-500 text-transparent'
                  }`}
                >
                  <Check className="w-3.5 h-3.5" />
                </div>
                <div className="space-y-1">
                  <span className={`text-xs font-mono font-bold uppercase tracking-wider ${isCompleted ? 'text-indigo-400 line-through' : 'text-indigo-400'}`}>
                    Day {idx + 1}
                  </span>
                  <p className={`text-xs sm:text-sm leading-relaxed ${isCompleted ? 'line-through text-slate-500' : 'text-slate-300'}`}>
                    {dayPlan}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Footer Diagnostic Bar */}
      <div className="pt-4 border-t border-slate-800 text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2 no-print">
        <span>CareerMetricX Evidence Intelligence Engine</span>
        <button
          onClick={handleCopyShareLink}
          className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition cursor-pointer"
        >
          <span>Direct Share Link</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* STAR Transferable Skill Optimization Drawer / Modal */}
      {activeStarSkill && activeRecommendation && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200 no-print"
          onClick={() => setActiveStarSkill(null)}
        >
          <div
            className="relative w-full max-w-xl rounded-2xl bg-slate-900 border border-amber-500/70 shadow-2xl p-6 space-y-4 animate-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/40">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white">
                      STAR Optimization Strategy
                    </h3>
                    <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-700">
                      {activeRecommendation.skill}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Reframing adjacent capabilities for the <strong>{analysis.role_applied}</strong> role
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setActiveStarSkill(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Current Context & Gap */}
            <div className="p-3.5 rounded-xl bg-slate-950/90 border border-slate-800 space-y-1">
              <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <GitFork className="w-3.5 h-3.5 text-amber-400" />
                Identified Competency Bridge:
              </span>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {activeRecommendation.current_gap}
              </p>
            </div>

            {/* Suggested STAR Bullet */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                  Recommended STAR Resume Bullet Point:
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  Situation · Task · Action · Result
                </span>
              </div>

              <div className="p-4 rounded-xl bg-indigo-950/25 border border-indigo-700/60 text-slate-100 text-xs sm:text-sm leading-relaxed font-sans relative group select-text">
                <p className="pr-2">{activeRecommendation.suggested_bullet}</p>
              </div>
            </div>

            {/* Other transferable skills switcher if multiple */}
            {analysis.gap_analysis.transferable_skills.length > 1 && (
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[11px] text-slate-400 mr-1">Switch Skill:</span>
                {analysis.gap_analysis.transferable_skills.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => {
                      setActiveStarSkill(s);
                      setCopiedStarBullet(false);
                    }}
                    className={`text-[11px] font-mono px-2 py-0.5 rounded-md border transition cursor-pointer ${
                      s.toLowerCase() === activeStarSkill.toLowerCase()
                        ? 'bg-amber-600 text-white border-amber-500 font-bold'
                        : 'bg-slate-800 text-slate-400 hover:text-slate-200 border-slate-700'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {/* Modal Footer Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-800">
              <span className="text-[11px] text-slate-500">
                1-click copy directly into your resume project bullets
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setActiveStarSkill(null)}
                  className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition cursor-pointer"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={() => handleCopyStarBullet(activeRecommendation.suggested_bullet)}
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 text-xs font-bold flex items-center gap-1.5 shadow-md active:scale-95 transition cursor-pointer"
                >
                  {copiedStarBullet ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-slate-950 stroke-[3]" />
                      <span>Copied to Clipboard!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-slate-950" />
                      <span>Copy Bullet</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
