import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  Activity,
  AlertTriangle,
  History,
  TrendingUp,
  Cpu,
  RefreshCw,
  Play,
  Square,
  Sparkles
} from 'lucide-react';
import { AuthenticationScore } from '../components/AuthenticationScore';
import { ExplainabilityChart } from '../components/ExplainabilityChart';
import { SessionMonitor } from '../components/SessionMonitor';
import { BehavioralTracker } from '../components/BehavioralTracker';
import { ConsentModal } from '../components/ConsentModal';
import { predictAPI, explainAPI } from '../services/api';

export const Dashboard = ({
  session,
  isTracking,
  keystrokeCount,
  mouseEventCount,
  onStartSession,
  onStopSession,
  user
}) => {
  const [showConsent, setShowConsent] = useState(false);
  const [prediction, setPrediction] = useState('LEGITIMATE USER');
  const [confidence, setConfidence] = useState(0.92);
  const [lastEvaluated, setLastEvaluated] = useState(null);
  const [features, setFeatures] = useState([]);
  const [attentionWeights, setAttentionWeights] = useState([]);
  const [history, setHistory] = useState([]);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [alerts, setAlerts] = useState([]);

  // Trigger continuous model inference on the active session
  const runEvaluation = useCallback(async () => {
    if (!session?.id) return;
    setIsEvaluating(true);
    try {
      const predRes = await predictAPI.predict(session.id);
      setPrediction(predRes.prediction);
      setConfidence(predRes.confidence);
      setLastEvaluated(new Date());
      setFeatures(predRes.important_features || []);
      setAttentionWeights(predRes.attention_weights || []);

      // Check alert thresholds
      if (predRes.prediction === 'POTENTIAL INTRUDER') {
        setAlerts((prev) => [
          {
            id: Date.now(),
            type: 'danger',
            message: `Intrusion Alert: Behavioral patterns deviate strongly from baseline (${Math.round(predRes.confidence * 100)}% confidence).`,
            time: new Date().toLocaleTimeString()
          },
          ...prev.slice(0, 4)
        ]);
      } else if (predRes.prediction === 'SUSPICIOUS USER') {
        setAlerts((prev) => [
          {
            id: Date.now(),
            type: 'warning',
            message: `Anomaly Warning: Moderate behavioral divergence detected (${Math.round(predRes.confidence * 100)}%).`,
            time: new Date().toLocaleTimeString()
          },
          ...prev.slice(0, 4)
        ]);
      }

      // Fetch history for timeline
      const histRes = await predictAPI.getHistory(session.id);
      setHistory(histRes || []);
    } catch (err) {
      console.warn('Continuous evaluation note:', err.response?.data?.detail || err.message);
    } finally {
      setIsEvaluating(false);
    }
  }, [session?.id]);

  // Periodic continuous evaluation while tracking is active (every 5 seconds)
  useEffect(() => {
    let interval;
    if (session?.id && isTracking) {
      // Run initial evaluation after brief buffer
      const initialTimer = setTimeout(() => runEvaluation(), 3000);
      interval = setInterval(() => {
        runEvaluation();
      }, 5000);
      return () => {
        clearTimeout(initialTimer);
        clearInterval(interval);
      };
    }
  }, [session?.id, isTracking, runEvaluation]);

  const handleStartClicked = () => {
    setShowConsent(true);
  };

  const handleConsentAccepted = async () => {
    setShowConsent(false);
    await onStartSession();
  };

  return (
    <div className="space-y-6">
      <ConsentModal
        isOpen={showConsent}
        onAccept={handleConsentAccepted}
        onDecline={() => setShowConsent(false)}
      />

      {/* Top Bar / Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-xl backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold uppercase tracking-wider">
            <Shield className="w-4 h-4" />
            Continuous Verification Console
          </div>
          <h1 className="text-2xl font-black text-white mt-1">
            Real-Time Biometrics Dashboard
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Subject ID: <span className="font-mono text-cyan-300 font-semibold">{user?.username}</span> | 
            Protocol: <span className="text-slate-300 font-medium">Sliding-Window Self-Attention Transformer</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          {session?.id && (
            <button
              onClick={runEvaluation}
              disabled={isEvaluating}
              className="px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isEvaluating ? 'animate-spin' : ''}`} />
              Run Model Pass
            </button>
          )}

          {!isTracking ? (
            <button
              onClick={handleStartClicked}
              className="px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 shadow-lg shadow-cyan-500/20 flex items-center gap-2 transition"
            >
              <Play className="w-4 h-4 fill-current" />
              Start Continuous Session
            </button>
          ) : (
            <button
              onClick={onStopSession}
              className="px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider bg-rose-500 hover:bg-rose-600 text-white shadow-lg shadow-rose-500/20 flex items-center gap-2 transition"
            >
              <Square className="w-4 h-4 fill-current" />
              Conclude Session
            </button>
          )}
        </div>
      </div>

      {/* Real-Time Alerts if any */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3.5 rounded-2xl border flex items-center justify-between text-xs transition-all ${
                alert.type === 'danger'
                  ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span className="font-medium">{alert.message}</span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">{alert.time}</span>
            </div>
          ))}
        </div>
      )}

      {/* Main Grid: Score Gauge, Session Telemetry, Sensors */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <AuthenticationScore
          confidence={confidence}
          classification={prediction}
          lastUpdated={lastEvaluated}
        />

        <SessionMonitor
          sessionId={session?.id}
          isActive={isTracking}
          totalEvents={keystrokeCount + mouseEventCount}
          keystrokeCount={keystrokeCount}
          mouseCount={mouseEventCount}
          onStopSession={onStopSession}
        />

        <BehavioralTracker
          isTracking={isTracking}
          keystrokeCount={keystrokeCount}
          mouseEventCount={mouseEventCount}
        />
      </div>

      {/* Explainable AI & History Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ExplainabilityChart
          features={features}
          attentionWeights={attentionWeights}
        />

        {/* Verification History Log */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <History className="w-4 h-4 text-cyan-400" />
              Continuous Verification History
            </h3>
            <span className="text-xs text-slate-500 font-mono">
              {history.length} snapshots
            </span>
          </div>

          <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
            {history.length > 0 ? (
              history.slice().reverse().map((item) => {
                let badgeClass = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
                if (item.classification === 'SUSPICIOUS USER') {
                  badgeClass = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
                } else if (item.classification === 'POTENTIAL INTRUDER') {
                  badgeClass = 'text-rose-400 bg-rose-500/10 border-rose-500/20';
                }

                return (
                  <div
                    key={item.id}
                    className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-0.5 rounded-full border text-[10px] font-bold ${badgeClass}`}>
                        {item.classification}
                      </span>
                      <span className="font-mono text-slate-300 font-semibold">
                        {Math.round(item.probability * 100)}%
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-500 font-mono">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-12 text-slate-500 text-xs">
                No historical verification windows recorded yet. Start tracking to stream real biometric events.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
