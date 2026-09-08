import React from 'react';
import { ShieldCheck, Lock, EyeOff, AlertTriangle } from 'lucide-react';

export const ConsentModal = ({ isOpen, onAccept, onDecline }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-cyan-500/30 rounded-2xl max-w-lg w-full p-6 shadow-2xl shadow-cyan-950/50">
        <div className="flex items-center space-x-3 mb-4 text-cyan-400">
          <ShieldCheck className="w-8 h-8" />
          <h2 className="text-xl font-bold tracking-wide">Research Consent & Privacy Disclosure</h2>
        </div>

        <p className="text-sm text-slate-300 mb-4 leading-relaxed">
          You are participating in the research study:
          <span className="font-semibold text-cyan-300 block mt-1">
            "AI-Driven Continuous Authentication Using Explainable Transformers and Behavioral Biometrics"
          </span>
        </p>

        <div className="space-y-3 bg-slate-950/60 border border-slate-800 rounded-xl p-4 mb-6">
          <div className="flex items-start space-x-3">
            <Lock className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div className="text-xs text-slate-300">
              <strong className="text-white">Zero Text Logging:</strong> We record keypress timing dynamics (hold duration, flight time). The actual keys or words typed are never transmitted or stored.
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <EyeOff className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
            <div className="text-xs text-slate-300">
              <strong className="text-white">Mouse Kinematics:</strong> Mouse trajectory velocity, acceleration, and click intervals are collected solely for biometric profiling.
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs text-slate-300">
              <strong className="text-white">Continuous Verification:</strong> An Explainable Transformer model will continuously evaluate your identity against your behavioral baseline.
            </div>
          </div>
        </div>

        <div className="flex space-x-3 justify-end">
          <button
            onClick={onDecline}
            className="px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            Decline
          </button>
          <button
            onClick={onAccept}
            className="px-5 py-2 rounded-lg text-sm font-semibold bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold shadow-lg shadow-cyan-500/20 transition"
          >
            I Explicitly Consent & Start
          </button>
        </div>
      </div>
    </div>
  );
};
