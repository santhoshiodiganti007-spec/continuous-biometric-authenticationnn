import { useState, useRef, useCallback, useEffect } from 'react';
import { behaviorAPI } from '../services/api';

/**
 * Custom React Hook for Continuous Behavioral Biometrics Collection.
 * Tracks Keystroke and Mouse Dynamics with privacy preservation (zero character logging).
 */
export const useBehaviorTracking = (sessionId, onLiveUpdate) => {
  const [isTracking, setIsTracking] = useState(false);
  const [keystrokeCount, setKeystrokeCount] = useState(0);
  const [mouseEventCount, setMouseEventCount] = useState(0);
  const [lastBatchTime, setLastBatchTime] = useState(null);

  // Buffers and tracking state
  const keystrokeBufferRef = useRef([]);
  const mouseBufferRef = useRef([]);
  const activeKeysRef = useRef(new Map()); // Key code -> press timestamp
  const lastKeyReleaseTimeRef = useRef(null);
  
  const lastMousePosRef = useRef(null); // { x, y, time, speed }
  const mouseClickStartRef = useRef(null);
  const flushIntervalRef = useRef(null);

  // Helper to categorize key without saving the character
  const categorizeKey = (code) => {
    if (code.startsWith('Key') || code.startsWith('Digit')) return 'ALPHANUMERIC';
    if (code === 'Space') return 'SPACE';
    if (code === 'Backspace' || code === 'Delete') return 'BACKSPACE';
    if (code === 'Enter') return 'ENTER';
    if (code.includes('Shift') || code.includes('Control') || code.includes('Alt')) return 'MODIFIER';
    return 'OTHER';
  };

  // --- Keystroke Dynamics Listeners ---
  const handleKeyDown = useCallback((e) => {
    if (!isTracking) return;
    const now = performance.now();
    const code = e.code;

    // Avoid multiple triggers for key hold
    if (!activeKeysRef.current.has(code)) {
      activeKeysRef.current.set(code, now);
    }
  }, [isTracking]);

  const handleKeyUp = useCallback((e) => {
    if (!isTracking) return;
    const now = performance.now();
    const code = e.code;

    if (activeKeysRef.current.has(code)) {
      const pressTime = activeKeysRef.current.get(code);
      const holdDuration = Math.max(1.0, now - pressTime);
      const flightTime = lastKeyReleaseTimeRef.current ? Math.max(0.0, pressTime - lastKeyReleaseTimeRef.current) : 50.0;
      
      lastKeyReleaseTimeRef.current = now;
      activeKeysRef.current.delete(code);

      const event = {
        timestamp: Date.now(),
        press_time: pressTime,
        release_time: now,
        hold_duration: holdDuration,
        flight_time: flightTime,
        key_category: categorizeKey(code)
      };

      keystrokeBufferRef.current.push(event);
      setKeystrokeCount((prev) => prev + 1);
    }
  }, [isTracking]);

  // --- Mouse Dynamics Listeners ---
  const handleMouseMove = useCallback((e) => {
    if (!isTracking) return;
    const now = performance.now();
    const currentX = e.clientX;
    const currentY = e.clientY;

    if (lastMousePosRef.current) {
      const dt = Math.max(1.0, now - lastMousePosRef.current.time);
      const dx = currentX - lastMousePosRef.current.x;
      const dy = currentY - lastMousePosRef.current.y;
      const distance = Math.hypot(dx, dy);

      // Only record meaningful moves (greater than 2px) to prevent flooding
      if (distance > 2) {
        const speed = distance / dt; // px/ms
        const prevSpeed = lastMousePosRef.current.speed || 0.0;
        const acceleration = (speed - prevSpeed) / dt;
        const direction = Math.atan2(dy, dx);

        const mouseEvent = {
          timestamp: Date.now(),
          event_type: 'move',
          x: currentX,
          y: currentY,
          speed: speed,
          distance: distance,
          direction: direction,
          acceleration: acceleration,
          click_duration: 0.0,
          scroll_delta: 0.0
        };

        mouseBufferRef.current.push(mouseEvent);
        setMouseEventCount((prev) => prev + 1);

        lastMousePosRef.current = { x: currentX, y: currentY, time: now, speed };
      }
    } else {
      lastMousePosRef.current = { x: currentX, y: currentY, time: now, speed: 0.0 };
    }
  }, [isTracking]);

  const handleMouseDown = useCallback((e) => {
    if (!isTracking) return;
    mouseClickStartRef.current = performance.now();
  }, [isTracking]);

  const handleMouseUp = useCallback((e) => {
    if (!isTracking) return;
    const now = performance.now();
    const clickDuration = mouseClickStartRef.current ? Math.max(1.0, now - mouseClickStartRef.current) : 50.0;
    mouseClickStartRef.current = null;

    const mouseEvent = {
      timestamp: Date.now(),
      event_type: 'click',
      x: e.clientX,
      y: e.clientY,
      speed: 0.0,
      distance: 0.0,
      direction: 0.0,
      acceleration: 0.0,
      click_duration: clickDuration,
      scroll_delta: 0.0
    };

    mouseBufferRef.current.push(mouseEvent);
    setMouseEventCount((prev) => prev + 1);
  }, [isTracking]);

  const handleWheel = useCallback((e) => {
    if (!isTracking) return;
    const mouseEvent = {
      timestamp: Date.now(),
      event_type: 'scroll',
      x: e.clientX,
      y: e.clientY,
      speed: 0.0,
      distance: 0.0,
      direction: 0.0,
      acceleration: 0.0,
      click_duration: 0.0,
      scroll_delta: Math.abs(e.deltaY)
    };

    mouseBufferRef.current.push(mouseEvent);
    setMouseEventCount((prev) => prev + 1);
  }, [isTracking]);

  // --- Buffer Dispatcher ---
  const flushBuffers = useCallback(async () => {
    if (!sessionId) return;

    const keysToSend = [...keystrokeBufferRef.current];
    const mouseToSend = [...mouseBufferRef.current];

    // Reset local buffers immediately to avoid duplicate transmission
    keystrokeBufferRef.current = [];
    mouseBufferRef.current = [];

    let flushedAny = false;

    if (keysToSend.length > 0) {
      try {
        await behaviorAPI.sendKeystrokes(sessionId, keysToSend);
        flushedAny = true;
      } catch (err) {
        console.error('Failed to flush keystroke batch:', err);
        // Put back in buffer on failure
        keystrokeBufferRef.current.unshift(...keysToSend);
      }
    }

    if (mouseToSend.length > 0) {
      try {
        await behaviorAPI.sendMouse(sessionId, mouseToSend);
        flushedAny = true;
      } catch (err) {
        console.error('Failed to flush mouse batch:', err);
        mouseBufferRef.current.unshift(...mouseToSend);
      }
    }

    if (flushedAny) {
      setLastBatchTime(new Date());
      if (onLiveUpdate) {
        onLiveUpdate({
          flushedKeystrokes: keysToSend.length,
          flushedMouse: mouseToSend.length
        });
      }
    }
  }, [sessionId, onLiveUpdate]);

  // Start / Stop controls
  const startTracking = useCallback(() => {
    setIsTracking(true);
    keystrokeBufferRef.current = [];
    mouseBufferRef.current = [];
    activeKeysRef.current.clear();
    setKeystrokeCount(0);
    setMouseEventCount(0);
  }, []);

  const stopTracking = useCallback(async () => {
    setIsTracking(false);
    // Final flush
    await flushBuffers();
  }, [flushBuffers]);

  // Manage DOM event listeners
  useEffect(() => {
    if (!isTracking) return;

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('wheel', handleWheel, { passive: true });

    // Periodic flush timer every 3.5 seconds
    flushIntervalRef.current = setInterval(() => {
      flushBuffers();
    }, 3500);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('wheel', handleWheel);
      if (flushIntervalRef.current) clearInterval(flushIntervalRef.current);
    };
  }, [isTracking, handleKeyDown, handleKeyUp, handleMouseMove, handleMouseDown, handleMouseUp, handleWheel, flushBuffers]);

  return {
    isTracking,
    keystrokeCount,
    mouseEventCount,
    lastBatchTime,
    startTracking,
    stopTracking,
    flushBuffers
  };
};
