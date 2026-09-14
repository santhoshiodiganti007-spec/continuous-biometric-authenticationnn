import React from 'react';
import { Keyboard, MousePointer, ShieldCheck, Zap } from 'lucide-react';

export const BehavioralTracker = ({ isTracking, keystrokeCount, mouseEventCount }) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Zap className="w-4 h-4 text-cyan-400" />
          Real-Time Sensor Ingestion
        </h3>
        <span className="text-[11px] text-emerald-400 font-medium flex items-center gap-1 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
          <ShieldCheck className="w-3.5 h-3.5" />
          Zero Text Stored
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Keystroke Sensor Card */}
        <div className={`p-4 rounded-xl border transition-all duration-300 ${
          isTracking ? 'bg-slate-950/80 border-cyan-500/40' : 'bg-slate-950/40 border-slate-800'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5 text-slate-300">
              <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                <Keyboard className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-white">Keystroke Sensor</h4>
                <p className="text-[10px] text-slate-500">Flight & Hold Dynamics</p>
              </div>
            </div>
            {isTracking && (
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 pulse-cyber" />
            )}
          </div>

          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-2xl font-black font-mono text-cyan-300">
              {keystrokeCount}
            </span>
            <span className="text-[10px] uppercase font-bold text-slate-500">
              Events Buffered
            </span>
          </div>
        </div>

        {/* Mouse Sensor Card */}
        <div className={`p-4 rounded-xl border transition-all duration-300 ${
          isTracking ? 'bg-slate-950/80 border-blue-500/40' : 'bg-slate-950/40 border-slate-800'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5 text-slate-300">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                <MousePointer className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-white">Mouse Kinematics</h4>
                <p className="text-[10px] text-slate-500">Speed, Accel & Trajectory</p>
              </div>
            </div>
            {isTracking && (
              <span className="w-2.5 h-2.5 rounded-full bg-blue-400 pulse-cyber" />
            )}
          </div>

          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-2xl font-black font-mono text-blue-300">
              {mouseEventCount}
            </span>
            <span className="text-[10px] uppercase font-bold text-slate-500">
              Events Buffered
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
