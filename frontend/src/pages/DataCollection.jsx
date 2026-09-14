import React, { useState } from 'react';
import { Play, Square, RefreshCw, KeyRound, MousePointer, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { BehavioralTracker } from '../components/BehavioralTracker';
import { ConsentModal } from '../components/ConsentModal';

export const DataCollection = ({
  session,
  isTracking,
  keystrokeCount,
  mouseEventCount,
  onStartSession,
  onStopSession,
}) => {
  const [showConsent, setShowConsent] = useState(false);
  const [typedText, setTypedText] = useState('');
  const [targetCount, setTargetCount] = useState(0);

  // Standard benchmark typing excerpt for keystroke dynamics evaluation
  const promptText = "Continuous authentication verifies behavioral biometrics such as typing rhythm, key hold times, and mouse trajectories seamlessly without interrupting legitimate users.";

  const handleStartClicked = () => {
    setShowConsent(true);
  };

  const handleConsentAccepted = async () => {
    setShowConsent(false);
    await onStartSession();
  };

  const handleConsentDeclined = () => {
    setShowConsent(false);
  };

  // Interactive mouse target test
  const handleTargetClicked = () => {
    setTargetCount((prev) => prev + 1);
  };

  return (
    <div className="space-y-6">
      <ConsentModal
        isOpen={showConsent}
        onAccept={handleConsentAccepted}
        onDecline={handleConsentDeclined}
      />

      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-cyan-950/40 to-slate-900 border border-cyan-500/20 rounded-3xl p-6 sm:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-xl">
        <div>
          <span className="text-xs uppercase font-bold tracking-widest text-cyan-400">
            Biometric Enrollment & Research Sandbox
          </span>
          <h2 className="text-2xl sm:text-3xl font-black text-white mt-1">
            Behavioral Dynamics Collection
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-2 max-w-xl leading-relaxed">
            Interact naturally by typing the research prompt and navigating the canvas below.
            Zero character contents are retained—only millisecond timings and movement kinematics are processed.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          {!isTracking ? (
            <button
              onClick={handleStartClicked}
              className="flex-1 md:flex-none px-6 py-3.5 rounded-2xl font-bold text-xs uppercase tracking-wider bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 shadow-lg shadow-cyan-500/25 flex items-center justify-center gap-2 transition"
            >
              <Play className="w-4 h-4 fill-current" />
              Start Data Collection
            </button>
          ) : (
            <button
              onClick={onStopSession}
              className="flex-1 md:flex-none px-6 py-3.5 rounded-2xl font-bold text-xs uppercase tracking-wider bg-rose-500 hover:bg-rose-600 text-white shadow-lg shadow-rose-500/25 flex items-center justify-center gap-2 transition"
            >
              <Square className="w-4 h-4 fill-current" />
              Stop Data Collection
            </button>
          )}
        </div>
      </div>

      {/* Sensor Telemetry Cards */}
      <BehavioralTracker
        isTracking={isTracking}
        keystrokeCount={keystrokeCount}
        mouseEventCount={mouseEventCount}
      />

      {/* Interactive Testing Sandbox */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Keystroke Dynamics Testing Sandbox */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-cyan-400" />
              Keystroke Dynamics Sandbox
            </h3>
            <span className="text-[11px] text-slate-500 font-mono">
              {typedText.length} / {promptText.length} chars
            </span>
          </div>

          <div className="p-4 bg-slate-950/80 border border-slate-800/80 rounded-2xl text-xs text-slate-400 leading-relaxed font-mono select-none">
            <span className="text-slate-500 block text-[10px] uppercase font-bold mb-1">Standard Reference Prompt</span>
            "{promptText}"
          </div>

          <textarea
            disabled={!isTracking}
            value={typedText}
            onChange={(e) => setTypedText(e.target.value)}
            placeholder={
              isTracking
                ? "Start typing the benchmark prompt here naturally..."
                : "Click 'Start Data Collection' above to unlock the typing sensor."
            }
            rows={4}
            className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-2xl p-4 text-sm text-slate-200 placeholder-slate-600 focus:outline-none transition resize-none disabled:opacity-50 disabled:cursor-not-allowed"
          />

          <div className="flex justify-between items-center text-xs text-slate-500 pt-1">
            <span>Keystroke timing captured in real-time</span>
            <button
              onClick={() => setTypedText('')}
              className="text-cyan-400 hover:underline flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" /> Clear Text
            </button>
          </div>
        </div>

        {/* Mouse Kinematics Interactive Canvas */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <MousePointer className="w-4 h-4 text-blue-400" />
              Mouse Kinematics Exercise
            </h3>
            <span className="text-[11px] text-blue-400 font-mono font-semibold">
              Targets Hit: {targetCount}
            </span>
          </div>

          <p className="text-xs text-slate-400">
            Move your cursor across the track and click the targets to record velocity, acceleration, curvature, and click durations.
          </p>

          <div className="relative h-48 bg-slate-950/90 border border-dashed border-slate-800 rounded-2xl overflow-hidden flex items-center justify-center p-4">
            <button
              disabled={!isTracking}
              onClick={handleTargetClicked}
              className={`p-4 rounded-2xl font-bold text-xs uppercase tracking-wider transition-all transform active:scale-95 flex items-center gap-2 ${
                isTracking
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-slate-950 shadow-lg shadow-blue-500/20 cursor-pointer animate-pulse'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed opacity-50'
              }`}
            >
              <MousePointer className="w-4 h-4" />
              Target Click Checkpoint
            </button>
          </div>

          <div className="text-[11px] text-slate-500 flex justify-between">
            <span>Scroll & navigate inside this container</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> High Precision Kinematics
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
