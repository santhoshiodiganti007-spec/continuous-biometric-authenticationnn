import React, { useState, useEffect } from 'react';
import { Clock, Radio, StopCircle, CheckCircle2, AlertTriangle } from 'lucide-react';

export const SessionMonitor = ({
  sessionId,
  isActive,
  totalEvents,
  keystrokeCount,
  mouseCount,
  onStopSession,
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    let timer;
    if (isActive) {
      timer = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isActive]);

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          Active Session Telemetry
        </h3>
        {isActive ? (
          <span className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            STREAMING
          </span>
        ) : (
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-400">
            IDLE
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 my-4">
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
          <span className="text-[11px] text-slate-500 uppercase font-medium">Session Duration</span>
          <p className="text-xl font-mono font-bold text-white mt-1">{formatTime(elapsedSeconds)}</p>
        </div>
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
          <span className="text-[11px] text-slate-500 uppercase font-medium">Total Events Ingested</span>
          <p className="text-xl font-mono font-bold text-cyan-400 mt-1">{totalEvents}</p>
        </div>
      </div>

      <div className="flex justify-between items-center text-xs text-slate-400 pt-2 border-t border-slate-800/60 mb-4">
        <span>Keys: <strong className="text-white font-mono">{keystrokeCount}</strong></span>
        <span>Mouse Moves: <strong className="text-white font-mono">{mouseCount}</strong></span>
        <span>Session: <strong className="text-cyan-400 font-mono text-[10px]">{sessionId ? sessionId.slice(0, 8) + '...' : 'None'}</strong></span>
      </div>

      {isActive && (
        <button
          onClick={onStopSession}
          className="w-full py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition flex items-center justify-center gap-2"
        >
          <StopCircle className="w-4 h-4" />
          Conclude Tracking Session
        </button>
      )}
    </div>
  );
};
