import React from 'react';
import { ShieldCheck, ShieldAlert, AlertOctagon, Activity } from 'lucide-react';

export const AuthenticationScore = ({ confidence = 0.88, classification = 'LEGITIMATE USER', lastUpdated }) => {
  const percentage = Math.round(confidence * 100);

  // Status-dependent visual styles
  let statusColor = 'text-emerald-400';
  let badgeBg = 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300';
  let strokeColor = '#10b981'; // emerald-500
  let StatusIcon = ShieldCheck;

  if (classification === 'SUSPICIOUS USER') {
    statusColor = 'text-amber-400';
    badgeBg = 'bg-amber-500/10 border-amber-500/30 text-amber-300';
    strokeColor = '#f59e0b'; // amber-500
    StatusIcon = ShieldAlert;
  } else if (classification === 'POTENTIAL INTRUDER') {
    statusColor = 'text-rose-500';
    badgeBg = 'bg-rose-500/10 border-rose-500/30 text-rose-300';
    strokeColor = '#f43f5e'; // rose-500
    StatusIcon = AlertOctagon;
  }

  // SVG circular gauge calculations
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (confidence * circumference);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          Continuous Verification Score
        </h3>
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${badgeBg} flex items-center gap-1.5`}>
          <StatusIcon className="w-3.5 h-3.5" />
          {classification}
        </span>
      </div>

      <div className="flex items-center justify-center py-4">
        <div className="relative flex items-center justify-center">
          <svg className="w-36 h-36 transform -rotate-90">
            {/* Background Track */}
            <circle
              cx="72"
              cy="72"
              r={radius}
              stroke="currentColor"
              strokeWidth="10"
              className="text-slate-800"
              fill="transparent"
            />
            {/* Value Track */}
            <circle
              cx="72"
              cy="72"
              r={radius}
              stroke={strokeColor}
              strokeWidth="10"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-700 ease-out"
            />
          </svg>

          <div className="absolute flex flex-col items-center justify-center text-center">
            <span className={`text-3xl font-black tracking-tight ${statusColor}`}>
              {percentage}%
            </span>
            <span className="text-[10px] uppercase font-bold text-slate-500 mt-0.5">
              Confidence
            </span>
          </div>
        </div>
      </div>

      <div className="mt-2 text-center">
        <p className="text-xs text-slate-400">
          Sliding Window Transformer Assessment
        </p>
        {lastUpdated && (
          <p className="text-[11px] text-slate-500 mt-1">
            Last evaluated: {new Date(lastUpdated).toLocaleTimeString()}
          </p>
        )}
      </div>
    </div>
  );
};
