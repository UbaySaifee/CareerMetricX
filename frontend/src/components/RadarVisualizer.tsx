import React from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { ShieldCheck, Cpu, GitFork, Wrench, Sparkles } from 'lucide-react';

interface RadarVisualizerProps {
  metrics: {
    'Core Skills'?: number;
    'Transferable'?: number;
    'System Design'?: number;
    'Tooling'?: number;
    'Claim Credibility'?: number;
    [key: string]: number | undefined;
  };
}

interface MetricDatum {
  dimension: string;
  score: number;
  fullMark: number;
}

const DIMENSION_ICONS: Record<string, React.ReactNode> = {
  'Core Skills': <Sparkles className="w-3.5 h-3.5 text-cyan-400" />,
  'Transferable': <GitFork className="w-3.5 h-3.5 text-violet-400" />,
  'System Design': <Cpu className="w-3.5 h-3.5 text-indigo-400" />,
  'Tooling': <Wrench className="w-3.5 h-3.5 text-emerald-400" />,
  'Claim Credibility': <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />,
};

interface TooltipPayloadItem {
  value: number;
  payload: MetricDatum;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    const item = payload[0];
    return (
      <div className="bg-slate-900/95 border border-slate-700/80 px-3 py-2 rounded-xl shadow-xl backdrop-blur-md text-xs">
        <p className="font-semibold text-white flex items-center gap-1.5">
          {DIMENSION_ICONS[item.payload.dimension]}
          {item.payload.dimension}
        </p>
        <p className="text-indigo-300 font-mono mt-1 font-bold">
          Score: {item.value.toFixed(1)} / 100
        </p>
      </div>
    );
  }
  return null;
}

export default function RadarVisualizer({ metrics }: RadarVisualizerProps) {
  const chartData: MetricDatum[] = [
    { dimension: 'Core Skills', score: metrics['Core Skills'] ?? 0, fullMark: 100 },
    { dimension: 'Transferable', score: metrics['Transferable'] ?? 0, fullMark: 100 },
    { dimension: 'System Design', score: metrics['System Design'] ?? 0, fullMark: 100 },
    { dimension: 'Tooling', score: metrics['Tooling'] ?? 0, fullMark: 100 },
    { dimension: 'Claim Credibility', score: metrics['Claim Credibility'] ?? 0, fullMark: 100 },
  ];

  return (
    <div className="w-full bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md shadow-xl flex flex-col justify-between">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-2">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse"></span>
            5-Dimension Competency Radar
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Holistic verification vector evaluating knowledge depth &amp; claim credibility
          </p>
        </div>
        <span className="text-xs font-mono font-medium px-2.5 py-1 rounded-full bg-indigo-950/70 border border-indigo-800/60 text-indigo-300">
          Max: 100
        </span>
      </div>

      {/* Recharts Radar Visualization */}
      <div className="w-full h-72 sm:h-80 my-2">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
            <PolarGrid stroke="#334155" strokeDasharray="3 3" />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 600 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: '#64748b', fontSize: 10 }}
              stroke="#1e293b"
            />
            <Tooltip content={<CustomTooltip />} />
            <Radar
              name="Competency"
              dataKey="score"
              stroke="#818cf8"
              strokeWidth={2.5}
              fill="#6366f1"
              fillOpacity={0.45}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Breakdown Score Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-3 border-t border-slate-800/80">
        {chartData.map((d) => (
          <div
            key={d.dimension}
            className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition"
          >
            <div className="flex items-center gap-1.5 text-slate-400 text-[11px] font-medium truncate">
              {DIMENSION_ICONS[d.dimension]}
              <span className="truncate">{d.dimension}</span>
            </div>
            <div className="flex items-baseline justify-between mt-1.5">
              <span className="text-sm sm:text-base font-bold font-mono text-white">
                {d.score.toFixed(0)}%
              </span>
              <div className="w-12 h-1.5 rounded-full bg-slate-800 overflow-hidden ml-2">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400"
                  style={{ width: `${Math.min(100, Math.max(0, d.score))}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
