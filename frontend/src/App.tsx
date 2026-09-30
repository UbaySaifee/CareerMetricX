import React, { useState, useEffect, useRef } from 'react';
import {
  ShieldCheck,
  Upload,
  FileText,
  X,
  Plus,
  Sparkles,
  ArrowRight,
  Terminal,
  Loader2,
  FileSearch,
  BrainCircuit,
  Target,
  AlertCircle,
  Briefcase,
} from 'lucide-react';
import EvaluationDashboard from './components/EvaluationDashboard';
import type { AnalysisResponse, JDCreate } from './types/analysis';

const RAW_API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api/v1';
const API_BASE_URL = RAW_API_BASE.endsWith('/api/v1')
  ? RAW_API_BASE
  : `${RAW_API_BASE.replace(/\/$/, '')}/api/v1`;

const SUGGESTED_SKILLS = [
  'Python',
  'FastAPI',
  'PostgreSQL',
  'Docker',
  'Kubernetes',
  'Kafka',
  'Redis',
  'AWS',
  'TypeScript',
  'React',
  'Microservices',
  'GraphQL',
  'CI/CD',
  'System Design',
  'MongoDB',
];

const SAMPLE_JD: JDCreate = {
  title: 'Senior Backend Engineer',
  experience_level: 'Senior',
  required_skills: ['Python', 'FastAPI', 'Docker', 'PostgreSQL', 'Kafka', 'Kubernetes'],
  preferred_skills: ['Redis', 'AWS'],
  description: `We are looking for a Senior Backend Engineer to architect, build, and scale our core event-driven microservices platform. You will be responsible for designing high-throughput REST and streaming APIs, containerizing deployment pipelines with Docker and Kubernetes, and ensuring database reliability with PostgreSQL and Redis caching.

Requirements:
- 5+ years of software engineering experience with strong proficiency in Python and FastAPI.
- Deep hands-on experience with relational databases (PostgreSQL) and message brokers (Kafka or RabbitMQ).
- Production experience containerizing and orchestrating services using Docker and Kubernetes.
- Experience with cloud infrastructure (AWS or GCP) and CI/CD pipelines.`,
};

const SAMPLE_RESUME_TEXT = `David Kim
david.kim@example.com | San Francisco, CA | github.com/davidkim

Professional Summary
Senior Backend Engineer with 6+ years of experience engineering high-throughput distributed systems and asynchronous APIs using Python, FastAPI, and PostgreSQL. Proven track record optimizing latency and scaling event streaming architectures.

Technical Skills
Languages & Frameworks: Python, FastAPI, Django, PostgreSQL, Redis, Docker, Git
Architecture: Microservices, RESTful APIs, Event-Driven Architecture, Caching, Asynchronous Programming

Work Experience
Senior Software Engineer | Apex Cloud Systems (2021 - Present)
- Architected high-throughput async REST microservices in FastAPI and PostgreSQL, serving 15k requests/sec at sub-50ms latency.
- Containerized development and deployment workflows using Docker, decreasing onboarding setup time by 40%.
- Integrated Redis cache clusters for high-frequency queries, achieving a 10x database query response speedup.
- Designed database migrations and connection pooling strategies with asyncpg handling 2k concurrent connections.

Software Engineer | Nexus Data Solutions (2018 - 2021)
- Developed data ingestion pipelines using Python and PostgreSQL handling 5M daily telemetry records.
- Configured automated integration test suites with pytest achieving 92% coverage across core services.
- Spearheaded migration from monolithic service to Dockerized microservices.`;

export default function App() {
  // Navigation / View State
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingStep, setLoadingStep] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Resume Upload State
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Job Description Form State
  const [jobTitle, setJobTitle] = useState<string>('Senior Backend Engineer');
  const [experienceLevel, setExperienceLevel] = useState<string>('Senior');
  const [requiredSkills, setRequiredSkills] = useState<string[]>([
    'Python',
    'FastAPI',
    'Docker',
    'PostgreSQL',
    'Kafka',
  ]);
  const [customSkillInput, setCustomSkillInput] = useState<string>('');
  const [description, setDescription] = useState<string>(SAMPLE_JD.description);

  // System Health
  const [healthStatus, setHealthStatus] = useState<string>('Checking...');

  // Check URL query parameters for ?report=<id> on initial mount

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const reportId = params.get('report');
    if (reportId) {
      let isMounted = true;
      (async () => {
        setLoading(true);
        setLoadingStep('Retrieving stored evaluation report...');
        try {
          const res = await fetch(`${API_BASE_URL}/analyzer/report/${reportId}`);
          if (!res.ok) throw new Error('Evaluation report not found.');
          const data: AnalysisResponse = await res.json();
          if (isMounted) setAnalysis(data);
        } catch (err: unknown) {
          if (isMounted) {
            const msg = err instanceof Error ? err.message : 'Failed to retrieve report.';
            setErrorMessage(msg);
          }
        } finally {
          if (isMounted) setLoading(false);
        }
      })();
      return () => {
        isMounted = false;
      };
    }

    // Health probe
    fetch(`${API_BASE_URL}/health`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setHealthStatus(data.status);
      })
      .catch(() => setHealthStatus('Offline'));
  }, []);



  // Drag and Drop Handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    setErrorMessage(null);
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'doc', 'txt'].includes(ext || '')) {
      setErrorMessage('Unsupported file format. Please upload a .pdf, .docx, or .txt resume.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage('File size exceeds the 10MB limit.');
      return;
    }
    setResumeFile(file);
  };

  // Skill Tags Management
  const toggleSuggestedSkill = (skill: string) => {
    if (requiredSkills.includes(skill)) {
      setRequiredSkills(requiredSkills.filter((s) => s !== skill));
    } else {
      setRequiredSkills([...requiredSkills, skill]);
    }
  };

  const handleAddCustomSkill = () => {
    const trimmed = customSkillInput.trim();
    if (trimmed && !requiredSkills.includes(trimmed)) {
      setRequiredSkills([...requiredSkills, trimmed]);
      setCustomSkillInput('');
    }
  };

  const handleKeyDownSkill = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddCustomSkill();
    }
  };

  const removeSkill = (skill: string) => {
    setRequiredSkills(requiredSkills.filter((s) => s !== skill));
  };

  // Quick fill sample data
  const handleLoadSample = () => {
    setJobTitle(SAMPLE_JD.title);
    setExperienceLevel(SAMPLE_JD.experience_level);
    setRequiredSkills([...SAMPLE_JD.required_skills]);
    setDescription(SAMPLE_JD.description);

    // Create a mock sample text file
    const sampleBlob = new Blob([SAMPLE_RESUME_TEXT], { type: 'text/plain' });
    const sampleFile = new File([sampleBlob], 'david_kim_senior_resume.txt', { type: 'text/plain' });
    setResumeFile(sampleFile);
    setErrorMessage(null);
  };

  // Submit Evaluation Handler
  const handleSubmitEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeFile) {
      setErrorMessage('Please upload a resume file (.pdf, .docx, or .txt).');
      return;
    }
    if (!jobTitle.trim()) {
      setErrorMessage('Please provide a target job title.');
      return;
    }
    if (requiredSkills.length === 0) {
      setErrorMessage('Please add at least one required skill competency.');
      return;
    }

    setErrorMessage(null);
    setLoading(true);

    // Loading step animation sequence
    setLoadingStep('Extracting candidate sections and project narratives...');
    const t1 = setTimeout(() => {
      setLoadingStep('Computing SentenceTransformer embeddings & cosine similarity...');
    }, 1200);
    const t2 = setTimeout(() => {
      setLoadingStep('Auditing project claims for unbacked metric multipliers...');
    }, 2400);
    const t3 = setTimeout(() => {
      setLoadingStep('Synthesizing grounded viva questions & 7-day remediation plan...');
    }, 3600);

    try {
      const jdPayload: JDCreate = {
        title: jobTitle.trim(),
        experience_level: experienceLevel,
        required_skills: requiredSkills,
        preferred_skills: ['Redis', 'AWS'],
        description: description.trim() || `Target role: ${jobTitle}`,
      };

      const formData = new FormData();
      formData.append('resume', resumeFile);
      formData.append('jd_payload', JSON.stringify(jdPayload));

      const response = await fetch(`${API_BASE_URL}/analyzer/evaluate`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => null);
        throw new Error(errJson?.detail || `Evaluation failed with status ${response.status}`);
      }

      const result: AnalysisResponse = await response.json();
      setAnalysis(result);

      // Update URL query parameter
      if (result.evaluation_id) {
        const url = new URL(window.location.href);
        url.searchParams.set('report', result.evaluation_id);
        window.history.pushState({}, '', url.toString());
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Evaluation request failed.';
      setErrorMessage(msg);
    } finally {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      setLoading(false);
    }
  };

  const handleResetAnalysis = () => {
    setAnalysis(null);
    setErrorMessage(null);
    const url = new URL(window.location.href);
    url.searchParams.delete('report');
    window.history.pushState({}, '', url.pathname);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div
            onClick={handleResetAnalysis}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
                CareerMetricX
              </span>
              <span className="hidden sm:inline-block ml-2 text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-indigo-900/50 text-indigo-300 border border-indigo-700/50">
                Evidence Engine
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700">
              <span
                className={`w-2 h-2 rounded-full ${
                  healthStatus === 'healthy'
                    ? 'bg-emerald-400'
                    : healthStatus === 'degraded'
                    ? 'bg-amber-400'
                    : 'bg-emerald-400'
                }`}
              ></span>
              <span className="text-slate-400 hidden sm:inline">Backend API:</span>
              <span className="font-mono text-slate-200">Online</span>
            </div>
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="text-xs font-medium text-slate-300 hover:text-white px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
            >
              OpenAPI Docs
            </a>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 flex flex-col">
        {loading ? (
          /* Animated Processing State */
          <div className="flex-1 flex flex-col items-center justify-center p-8 max-w-xl mx-auto text-center space-y-6 animate-in fade-in duration-300">
            <div className="relative w-24 h-24 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping"></div>
              <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-500 flex items-center justify-center text-white shadow-2xl shadow-indigo-500/40">
                <Loader2 className="w-10 h-10 animate-spin" />
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-2xl font-extrabold text-white tracking-tight">
                Verifying Engineering Capabilities
              </h2>
              <p className="text-sm font-mono text-indigo-300 min-h-[24px] animate-pulse">
                {loadingStep}
              </p>
            </div>

            <div className="w-full bg-slate-900 rounded-xl p-4 border border-slate-800 text-xs text-slate-400 text-left space-y-2">
              <div className="flex items-center gap-2 text-slate-300 font-semibold border-b border-slate-800 pb-2">
                <Terminal className="w-4 h-4 text-indigo-400" />
                <span>Verification Pipeline Active</span>
              </div>
              <p>• Extracting semantic claims from projects and experience</p>
              <p>• Computing all-MiniLM-L6-v2 cosine similarity matrix</p>
              <p>• Running claim reliability audit against engineering constraints</p>
              <p>• Formulating viva interrogation questions</p>
            </div>
          </div>
        ) : analysis ? (
          /* Render Evaluation Dashboard */
          <EvaluationDashboard analysis={analysis} onReset={handleResetAnalysis} />
        ) : (
          /* Resume Upload & JD Input Form View */
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full space-y-10">
            {/* Hero Banner */}
            <div className="text-center max-w-3xl mx-auto space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-800/60 text-indigo-400 text-xs font-semibold shadow-sm">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Evidence-Grounded Capability Verification &amp; Interview Intelligence</span>
              </div>

              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
                Measure your skills. <br />
                <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent">
                  Prove your readiness.
                </span>
              </h1>

              <p className="text-sm sm:text-base text-slate-400 leading-relaxed max-w-2xl mx-auto">
                No more ATS keyword superficiality. Match candidate project claims with target role
                requirements, audit metrics for credibility, and prepare for viva defense.
              </p>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleLoadSample}
                  className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-indigo-500/40 hover:border-indigo-400 text-xs text-indigo-300 hover:text-white transition shadow-sm cursor-pointer"
                >
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Try Demo: Auto-Load Senior Backend Engineer Sample</span>
                </button>
              </div>
            </div>

            {/* Error Callout */}
            {errorMessage && (
              <div className="max-w-4xl mx-auto p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 flex items-center gap-3 text-rose-200 text-sm animate-in fade-in">
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
                <span className="flex-1">{errorMessage}</span>
                <button
                  onClick={() => setErrorMessage(null)}
                  className="text-rose-400 hover:text-rose-200"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Upload & Form Section */}
            <form
              onSubmit={handleSubmitEvaluation}
              className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-start"
            >
              {/* Left Column: Drag & Drop Resume Upload */}
              <div className="lg:col-span-5 space-y-4">
                <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                      <Upload className="w-4 h-4 text-indigo-400" />
                      1. Upload Resume
                    </h2>
                    <span className="text-[11px] text-slate-400 font-mono">PDF, DOCX, TXT</span>
                  </div>

                  {/* Drag-and-drop zone */}
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-2xl p-6 text-center transition-all cursor-pointer flex flex-col items-center justify-center min-h-[220px] ${
                      isDragging
                        ? 'border-indigo-400 bg-indigo-950/40 scale-[1.01]'
                        : resumeFile
                        ? 'border-emerald-600/70 bg-emerald-950/20'
                        : 'border-slate-700/80 bg-slate-950/50 hover:border-slate-600 hover:bg-slate-950/80'
                    }`}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.docx,.doc,.txt"
                      onChange={handleFileInputChange}
                      className="hidden"
                    />

                    {resumeFile ? (
                      <div className="space-y-3">
                        <div className="w-12 h-12 rounded-xl bg-emerald-900/50 border border-emerald-700/60 text-emerald-400 flex items-center justify-center mx-auto">
                          <FileText className="w-6 h-6" />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-white truncate max-w-xs mx-auto">
                            {resumeFile.name}
                          </p>
                          <p className="text-xs text-slate-400 font-mono mt-0.5">
                            {(resumeFile.size / 1024).toFixed(1)} KB • Ready for evaluation
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setResumeFile(null);
                          }}
                          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Change File</span>
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="w-12 h-12 rounded-2xl bg-indigo-950/70 border border-indigo-800/60 text-indigo-400 flex items-center justify-center mx-auto group-hover:scale-110 transition">
                          <Upload className="w-6 h-6" />
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-semibold text-white">
                            Drag &amp; drop resume file here
                          </p>
                          <p className="text-xs text-slate-400">or click to browse from local computer</p>
                        </div>
                        <span className="inline-block text-[11px] text-slate-500 font-mono">
                          Max size: 10MB
                        </span>
                      </div>
                    )}
                  </div>

                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    CareerMetricX parses projects, bullet assertions, and technology stacks for
                    evidence-backed verification.
                  </p>
                </div>
              </div>

              {/* Right Column: Structured Job Description Inputs */}
              <div className="lg:col-span-7 space-y-4">
                <div className="p-6 sm:p-8 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                      <Briefcase className="w-4 h-4 text-indigo-400" />
                      2. Target Job Description &amp; Requirements
                    </h2>
                    <span className="text-xs text-slate-400">Mandatory Schema</span>
                  </div>

                  {/* Job Title & Experience Level */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="sm:col-span-2 space-y-1.5">
                      <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                        Job Title / Role
                      </label>
                      <input
                        type="text"
                        value={jobTitle}
                        onChange={(e) => setJobTitle(e.target.value)}
                        placeholder="e.g. Senior Backend Engineer"
                        className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/70 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 transition"
                        required
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                        Experience Level
                      </label>
                      <select
                        value={experienceLevel}
                        onChange={(e) => setExperienceLevel(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/70 border border-slate-700/80 text-white text-sm focus:outline-none focus:border-indigo-500 transition cursor-pointer"
                      >
                        <option value="Junior">Junior (0-2 yrs)</option>
                        <option value="Mid">Mid-Level (3-5 yrs)</option>
                        <option value="Senior">Senior (5-8 yrs)</option>
                        <option value="Lead">Lead / Architect (8+ yrs)</option>
                      </select>
                    </div>
                  </div>

                  {/* Required Skills Tag Selector */}
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                        Required Core Skills ({requiredSkills.length})
                      </label>
                      <span className="text-[11px] text-slate-500">Click suggested pills or type custom</span>
                    </div>

                    {/* Active Selected Skills */}
                    <div className="flex flex-wrap gap-2 p-3 rounded-xl bg-slate-950/70 border border-slate-800 min-h-[50px]">
                      {requiredSkills.length > 0 ? (
                        requiredSkills.map((skill) => (
                          <span
                            key={skill}
                            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-indigo-950 border border-indigo-700/70 text-indigo-200 text-xs font-mono font-medium shadow-sm"
                          >
                            <span>{skill}</span>
                            <button
                              type="button"
                              onClick={() => removeSkill(skill)}
                              className="text-indigo-400 hover:text-white transition"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </span>
                        ))
                      ) : (
                        <p className="text-xs text-slate-500 italic py-1">
                          No skills selected. Click suggestions below or add your own.
                        </p>
                      )}
                    </div>

                    {/* Custom Skill Input */}
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={customSkillInput}
                        onChange={(e) => setCustomSkillInput(e.target.value)}
                        onKeyDown={handleKeyDownSkill}
                        placeholder="Add custom skill (e.g. Cassandra, gRPC, Terraform)..."
                        className="flex-1 px-3.5 py-2 rounded-xl bg-slate-950/60 border border-slate-800 text-white placeholder-slate-500 text-xs focus:outline-none focus:border-indigo-500 transition"
                      />
                      <button
                        type="button"
                        onClick={handleAddCustomSkill}
                        className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1 transition"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Add</span>
                      </button>
                    </div>

                    {/* Quick Suggested Skill Pills */}
                    <div className="space-y-1.5 pt-1">
                      <p className="text-[11px] text-slate-400 font-medium">Popular Skill Suggestions:</p>
                      <div className="flex flex-wrap gap-1.5">
                        {SUGGESTED_SKILLS.map((skill) => {
                          const isSelected = requiredSkills.includes(skill);
                          return (
                            <button
                              type="button"
                              key={skill}
                              onClick={() => toggleSuggestedSkill(skill)}
                              className={`text-[11px] font-mono px-2.5 py-1 rounded-lg border transition ${
                                isSelected
                                  ? 'bg-indigo-600/30 border-indigo-500 text-indigo-300'
                                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                              }`}
                            >
                              {isSelected ? `✓ ${skill}` : `+ ${skill}`}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  {/* Full Text JD Description */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      Job Description Narrative
                    </label>
                    <textarea
                      rows={4}
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Paste the full job description text here..."
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/70 border border-slate-700/80 text-white placeholder-slate-500 text-xs sm:text-sm focus:outline-none focus:border-indigo-500 transition leading-relaxed"
                    />
                  </div>

                  {/* Submit Action */}
                  <div className="pt-2">
                    <button
                      type="submit"
                      disabled={loading || !resumeFile}
                      className={`w-full py-3.5 px-6 rounded-2xl font-bold text-sm flex items-center justify-center gap-2 shadow-xl transition-all cursor-pointer ${
                        !resumeFile
                          ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                          : 'bg-gradient-to-r from-indigo-600 via-violet-600 to-cyan-500 text-white hover:opacity-95 shadow-indigo-600/25 active:scale-[0.99]'
                      }`}
                    >
                      <Sparkles className="w-4 h-4 text-cyan-300" />
                      <span>Execute Semantic Capability Verification</span>
                      <ArrowRight className="w-4 h-4 ml-1" />
                    </button>
                  </div>
                </div>
              </div>
            </form>

            {/* How It Works Explainer Grid */}
            <div className="w-full max-w-5xl mx-auto pt-8 border-t border-slate-800/80 space-y-6">
              <div className="text-center space-y-1">
                <p className="text-xs font-bold uppercase tracking-widest text-indigo-400">
                  Scientific Methodology
                </p>
                <h3 className="text-xl font-bold text-white">
                  The Non-Negotiable Core Verification Loop
                </h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
                  <FileSearch className="w-6 h-6 text-cyan-400 mb-2" />
                  <h4 className="text-sm font-bold text-white">1. Claim Extraction</h4>
                  <p className="text-xs text-slate-400 mt-1">
                    Normalized section parsing of project bullet points &amp; stated achievements.
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
                  <ShieldCheck className="w-6 h-6 text-emerald-400 mb-2" />
                  <h4 className="text-sm font-bold text-white">2. Provenance Matching</h4>
                  <p className="text-xs text-slate-400 mt-1">
                    Embedding cosine similarity against mandatory competencies (&ge;70% match).
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
                  <BrainCircuit className="w-6 h-6 text-indigo-400 mb-2" />
                  <h4 className="text-sm font-bold text-white">3. Viva Questioning</h4>
                  <p className="text-xs text-slate-400 mt-1">
                    Synthesizing technical defense questions challenging unbacked 100x speedups.
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
                  <Target className="w-6 h-6 text-amber-400 mb-2" />
                  <h4 className="text-sm font-bold text-white">4. 7-Day Plan</h4>
                  <p className="text-xs text-slate-400 mt-1">
                    Targeted day-by-day practical engineering remediation for identified gaps.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-300">CareerMetricX</span>
            <span>—</span>
            <span>Evidence-Grounded Capability Verification &amp; Interview Intelligence</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="/docs" target="_blank" rel="noreferrer" className="hover:text-slate-300 transition">
              FastAPI Contract
            </a>
            <span className="text-slate-400">v1.0.0</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
