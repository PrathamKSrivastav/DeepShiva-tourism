import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

// Simple in-memory URL cache (per tab)
const ttsURLCache = new Map(); // key: `${lang}|${voice}|${speed}|${text}` -> { url, durationMs }

const MeditationPlayer = ({
  chapter,
  courseTitle,
  onClose,
  darkMode,
  onNextChapter,
  hasNextChapter,
}) => {
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isTTSEnabled, setIsTTSEnabled] = useState(true);
  const [isMusicMuted, setIsMusicMuted] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [autoPlayTimer, setAutoPlayTimer] = useState(10);
  const [autoPlayStarted, setAutoPlayStarted] = useState(false);

  // NEW: Prefetch state
  const [isPrefetching, setIsPrefetching] = useState(false);
  const [prefetchProgress, setPrefetchProgress] = useState(0);
  const [prefetched, setPrefetched] = useState([]); // [{url, durationMs}] aligned with script indices

  const audioRef = useRef(null);
  const segmentTimerRef = useRef(null);
  const autoPlayIntervalRef = useRef(null);
  const ttsAudioRef = useRef(null);

  const script = chapter?.script || [];
  const voice = "af_heart";
  const lang = "a";
  const speed = "1.0";

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (ttsAudioRef.current) {
        ttsAudioRef.current.pause();
        ttsAudioRef.current.src = "";
      }
      if (autoPlayIntervalRef.current) {
        clearInterval(autoPlayIntervalRef.current);
      }
      if (segmentTimerRef.current) {
        clearTimeout(segmentTimerRef.current);
      }
    };
  }, []);

  // ---------------------------------------------------------
  // 🎵 NEW: Dedicated Effect for Background Music Control
  // ---------------------------------------------------------
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    // 1. Set Volume Lower (15%)
    audio.volume = 0.15;

    // 2. Logic to decide if music should play
    // It should play ONLY if: Global is playing, Not paused, Not muted, and Music exists
    const shouldPlayMusic =
      isPlaying && !isPaused && !isMusicMuted && chapter?.background_music;

    if (shouldPlayMusic) {
      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise.catch((e) => {
          // Auto-play prevention or load error
          console.warn("Background music play failed:", e);
        });
      }
    } else {
      audio.pause();
    }
  }, [isPlaying, isPaused, isMusicMuted, chapter]); // Re-run whenever these states change

  // Prefetch TTS for entire chapter when it loads
  useEffect(() => {
    let cancelled = false;
    async function prefetchAll() {
      if (!script.length || !isTTSEnabled) {
        setPrefetched([]);
        setIsPrefetching(false);
        setPrefetchProgress(0);
        return;
      }
      setIsPrefetching(true);
      setPrefetchProgress(0);

      const results = new Array(script.length).fill(null);

      // Helper to load blob -> URL and duration
      const blobToUrlWithDuration = (blob) =>
        new Promise((resolve) => {
          const url = URL.createObjectURL(blob);
          const a = new Audio();
          a.src = url;
          a.addEventListener("loadedmetadata", () => {
            resolve({ url, durationMs: Math.ceil((a.duration || 0) * 1000) });
          });
          a.addEventListener("error", () => resolve({ url, durationMs: 0 }));
        });

      // Limit concurrency to avoid flooding backend
      const concurrency = 3;
      let idx = 0;
      const runNext = async () => {
        if (cancelled || idx >= script.length) return;
        const i = idx++;
        const seg = script[i];
        if (!seg?.text) {
          results[i] = null;
          setPrefetchProgress((p) => p + 1);
          return runNext();
        }

        const key = `${lang}|${voice}|${speed}|${seg.text}`;
        try {
          // Check in-memory cache first
          if (ttsURLCache.has(key)) {
            results[i] = ttsURLCache.get(key);
            setPrefetchProgress((p) => p + 1);
            return runNext();
          }
          // Fetch from backend (server-side cache will speed repeats)
          const params = new URLSearchParams({
            text: seg.text,
            voice,
            lang,
            speed,
          });
          const res = await fetch(`${API_BASE_URL}/tts/kokoro?${params}`);
          if (!res.ok) throw new Error("TTS failed");
          const blob = await res.blob();
          const data = await blobToUrlWithDuration(blob);
          ttsURLCache.set(key, data);
          results[i] = data;
        } catch (e) {
          console.warn("Prefetch TTS error:", e);
          results[i] = null; // fallback to on-demand later
        } finally {
          setPrefetchProgress((p) => p + 1);
          if (!cancelled) await runNext();
        }
      };

      // Kick off workers
      await Promise.all(
        Array.from({ length: Math.min(concurrency, script.length) }, runNext)
      );
      if (!cancelled) {
        setPrefetched(results);
        setIsPrefetching(false);
      }
    }

    // Reset state when chapter changes
    setCurrentSegmentIndex(0);
    setIsPlaying(false);
    setIsPaused(false);
    setIsComplete(false);
    setAutoPlayStarted(false);
    setPrefetched([]);
    setPrefetchProgress(0);

    prefetchAll();

    return () => {
      cancelled = true;
    };
  }, [chapter?.id, script, isTTSEnabled]);

  // Fixed-cadence scheduler.
  // Segments are spaced EVENLY across the chapter's total duration, regardless
  // of individual TTS audio length. Each segment gets `slotMs = duration / N`.
  // If the TTS finishes before the slot ends → silence (breathing gap).
  // If the TTS runs longer than the slot → it's cut off when the next slot fires.
  const slotMs =
    Math.max(1, (chapter?.duration || 5) * 60 * 1000) /
    Math.max(1, script.length);

  useEffect(() => {
    if (!isPlaying || isPaused) {
      if (segmentTimerRef.current) clearTimeout(segmentTimerRef.current);
      return;
    }

    const seg = script[currentSegmentIndex];
    if (!seg) {
      setIsPlaying(false);
      setIsComplete(true);
      return;
    }

    // Start playing this segment's TTS (if enabled) — don't block on it.
    if (isTTSEnabled && seg.text) {
      playSegmentFromPrefetch(currentSegmentIndex, seg.text);
    }

    // Always schedule the next advance at the slot boundary.
    segmentTimerRef.current = setTimeout(() => {
      if (ttsAudioRef.current) ttsAudioRef.current.pause();
      setIsSpeaking(false);
      advanceOrComplete();
    }, slotMs);

    return () => {
      if (segmentTimerRef.current) clearTimeout(segmentTimerRef.current);
    };
  }, [isPlaying, isPaused, currentSegmentIndex, script, isTTSEnabled, slotMs]);

  // Play from prefetch (or fallback on-demand). Does NOT schedule the next
  // advance — that's driven by the fixed-cadence scheduler above.
  const playSegmentFromPrefetch = async (index, text) => {
    try {
      if (ttsAudioRef.current) {
        ttsAudioRef.current.pause();
        ttsAudioRef.current.src = "";
      }
      setIsSpeaking(true);

      const key = `${lang}|${voice}|${speed}|${text}`;
      let data = prefetched[index] || ttsURLCache.get(key);

      if (!data) {
        const params = new URLSearchParams({ text, voice, lang, speed });
        const res = await fetch(`${API_BASE_URL}/tts/kokoro?${params}`);
        if (!res.ok) throw new Error("TTS failed");
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        data = { url, durationMs: 0 };
      }

      ttsAudioRef.current.onended = () => setIsSpeaking(false);
      ttsAudioRef.current.src = data.url;
      await ttsAudioRef.current.play();
    } catch (e) {
      console.warn("TTS play error:", e);
      setIsSpeaking(false);
    }
  };

  const advanceOrComplete = () => {
    if (currentSegmentIndex < script.length - 1) {
      setCurrentSegmentIndex((prev) => prev + 1);
    } else {
      setIsPlaying(false);
      setIsSpeaking(false);
      setIsComplete(true);
      // audioRef pause handled by music effect
      setAutoPlayStarted(true);
    }
  };

  const handlePlayPause = () => {
    if (!isPlaying) {
      // Optional: wait until at least first segment is ready
      setIsPlaying(true);
      setIsPaused(false);
      setIsComplete(false);
      setAutoPlayStarted(false);
      // Note: Music play logic is now handled in useEffect
    } else if (!isPaused) {
      setIsPaused(true);
      // Note: Music pause logic is now handled in useEffect
      if (ttsAudioRef.current) ttsAudioRef.current.pause();
    } else {
      setIsPaused(false);
      // Note: Music resume logic is now handled in useEffect
      if (ttsAudioRef.current && ttsAudioRef.current.src) {
        ttsAudioRef.current.play().catch(() => {});
      }
    }
  };

  const handleStop = () => {
    setIsPlaying(false);
    setIsPaused(false);
    setCurrentSegmentIndex(0);
    setIsSpeaking(false);
    setIsComplete(false);
    setAutoPlayStarted(false);
    setAutoPlayTimer(10);
    // audioRef pause handled by music effect because isPlaying becomes false
    if (segmentTimerRef.current) clearTimeout(segmentTimerRef.current);
    if (autoPlayIntervalRef.current) clearInterval(autoPlayIntervalRef.current);
    if (ttsAudioRef.current) ttsAudioRef.current.pause();
  };

  const handleSkipNext = () => {
    if (currentSegmentIndex < script.length - 1) {
      if (ttsAudioRef.current) ttsAudioRef.current.pause();
      setIsSpeaking(false);
      setCurrentSegmentIndex((prev) => prev + 1);
    }
  };

  const handleSkipPrev = () => {
    if (currentSegmentIndex > 0) {
      if (ttsAudioRef.current) ttsAudioRef.current.pause();
      setIsSpeaking(false);
      setCurrentSegmentIndex((prev) => prev - 1);
    }
  };

  const handleToggleTTS = () => {
    if (isSpeaking && ttsAudioRef.current) {
      ttsAudioRef.current.pause();
      setIsSpeaking(false);
    }
    setIsTTSEnabled(!isTTSEnabled);
  };

  const handleSkipToNextChapter = () => {
    if (autoPlayIntervalRef.current) {
      clearInterval(autoPlayIntervalRef.current);
      autoPlayIntervalRef.current = null;
    }
    onNextChapter?.();
  };

  const currentSegment = script[currentSegmentIndex] || {};
  const instruction = currentSegment.instruction;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={`fixed inset-0 z-[10000] flex items-center justify-center p-4 ${
        darkMode ? "bg-black/80" : "bg-black/70"
      }`}
      onClick={onClose}
    >
      <motion.div
        layout
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        transition={{ layout: { duration: 0.3, ease: "easeInOut" } }}
        className={`relative w-full max-w-2xl rounded-3xl overflow-hidden shadow-2xl ${
          darkMode
            ? "bg-gradient-to-br from-dark-surface to-dark-elev border border-dark-border"
            : "bg-gradient-to-br from-white to-blue-50 border border-white/20"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Background Music Audio - Controlled by useEffect now */}
        {chapter?.background_music && (
          <audio
            ref={audioRef}
            src={chapter.background_music}
            loop
            style={{ display: "none" }}
          />
        )}

        {/* Kokoro TTS audio element */}
        <audio
          ref={ttsAudioRef}
          style={{ display: "none" }}
          onEnded={() => setIsSpeaking(false)}
        />

        {/* Close Button */}
        <button
          onClick={onClose}
          className={`absolute top-4 right-4 z-10 w-10 h-10 rounded-full flex items-center justify-center transition-all ${
            darkMode
              ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
              : "bg-white/80 hover:bg-white text-gray-700"
          }`}
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        {isPrefetching && (
          <div className="px-6 pt-4 pb-2">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span
                  className={`text-sm font-semibold ${
                    darkMode ? "text-emerald-300" : "text-emerald-700"
                  }`}
                >
                  🎙️ Preparing narration...
                </span>
                <span
                  className={`text-sm font-bold ${
                    darkMode ? "text-emerald-400" : "text-emerald-600"
                  }`}
                >
                  {prefetchProgress}/{script.length}
                </span>
              </div>
              {/* ✅ Prominent progress bar */}
              <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{
                    width: `${(prefetchProgress / script.length) * 100}%`,
                  }}
                  transition={{ duration: 0.3 }}
                  className="absolute h-full bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-full"
                />
              </div>
            </div>
          </div>
        )}

        {/* Header */}
        <div
          className={`p-6 sm:p-8 text-center border-b ${
            darkMode
              ? "border-dark-border bg-dark-surface"
              : "border-white/20 bg-white/40"
          }`}
        >
          <h2
            className={`text-sm uppercase tracking-wider mb-2 ${
              darkMode ? "text-emerald-400" : "text-emerald-600"
            }`}
          >
            🧘 Meditation
          </h2>
          <h1
            className={`text-2xl sm:text-3xl font-bold mb-1 ${
              darkMode ? "text-white" : "text-gray-900"
            }`}
          >
            {courseTitle}
          </h1>
          <p
            className={`text-sm ${
              darkMode ? "text-dark-muted" : "text-gray-600"
            }`}
          >
            Part {currentSegmentIndex + 1} of {script.length}
          </p>
        </div>

        {/* Main Content */}
        <div className="p-6 sm:p-8 space-y-6">
          {/* Completion Screen */}
          {isComplete ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center space-y-6"
            >
              {/* Completion Message */}
              <div className="space-y-4">
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="text-6xl"
                >
                  🙏
                </motion.div>
                <div>
                  <h3
                    className={`text-2xl font-bold mb-2 ${
                      darkMode ? "text-white" : "text-gray-900"
                    }`}
                  >
                    Namaste
                  </h3>
                  <p
                    className={`text-sm ${
                      darkMode ? "text-dark-muted" : "text-gray-600"
                    }`}
                  >
                    You have completed this meditation. May the peace remain
                    with you.
                  </p>
                </div>
              </div>

              {/* Next Chapter Button or End Session */}
              {hasNextChapter ? (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="space-y-3"
                >
                  <button
                    onClick={handleSkipToNextChapter}
                    className="w-full px-6 py-3 rounded-xl font-medium transition-all bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white shadow-lg flex items-center justify-center gap-2"
                  >
                    <span>▶️ Next Chapter</span>
                  </button>

                  {/* Auto-play countdown */}
                  {autoPlayStarted && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className={`text-xs ${
                        darkMode ? "text-dark-muted" : "text-gray-500"
                      }`}
                    >
                      Auto-playing in {autoPlayTimer} seconds...
                    </motion.p>
                  )}
                </motion.div>
              ) : (
                <button
                  onClick={onClose}
                  className="w-full px-6 py-3 rounded-xl font-medium transition-all bg-dark-elev hover:bg-dark-elev/80 text-white"
                >
                  Return to Courses
                </button>
              )}

              {/* Restart or Close */}
              <div className="flex gap-3 pt-3">
                <button
                  onClick={handleStop}
                  className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    darkMode
                      ? "bg-dark-surface hover:bg-dark-elev text-white"
                      : "bg-white/60 hover:bg-white text-gray-700"
                  }`}
                >
                  Replay This Chapter
                </button>
                <button
                  onClick={onClose}
                  className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    darkMode
                      ? "bg-dark-surface hover:bg-dark-elev text-white"
                      : "bg-white/60 hover:bg-white text-gray-700"
                  }`}
                >
                  Exit
                </button>
              </div>
            </motion.div>
          ) : (
            <>
              {/* Visual Instruction */}
              <AnimatePresence mode="wait">
                {instruction && (
                  <motion.div
                    layout
                    key={`instruction-${currentSegmentIndex}`}
                    initial={{ opacity: 0, scale: 0.9, height: 0 }}
                    animate={{ opacity: 1, scale: 1, height: "auto" }}
                    exit={{ opacity: 0, scale: 0.9, height: 0 }}
                    transition={{ duration: 0.3, ease: "easeInOut" }}
                    className={`p-6 rounded-2xl text-center ${
                      darkMode
                        ? "bg-dark-elev/50 border border-emerald-500/20"
                        : "bg-emerald-50/60 border border-emerald-200"
                    }`}
                  >
                    <div className="text-4xl sm:text-5xl mb-3">
                      {instruction === "breathe_in" && "🌬️"}
                      {instruction === "breathe_out" && "💨"}
                      {instruction === "settle" && "🧘"}
                      {instruction === "visualize" && "👁️"}
                      {instruction === "gratitude" && "🙏"}
                      {![
                        "breathe_in",
                        "breathe_out",
                        "settle",
                        "visualize",
                        "gratitude",
                      ].includes(instruction) && "✨"}
                    </div>
                    <p
                      className={`text-sm font-semibold ${
                        darkMode ? "text-emerald-300" : "text-emerald-700"
                      }`}
                    >
                      {instruction === "breathe_in" && "Breathe in slowly..."}
                      {instruction === "breathe_out" && "Exhale gently..."}
                      {instruction === "settle" && "Settle into stillness..."}
                      {instruction === "visualize" && "Visualize..."}
                      {instruction === "gratitude" && "Feel gratitude..."}
                      {![
                        "breathe_in",
                        "breathe_out",
                        "settle",
                        "visualize",
                        "gratitude",
                      ].includes(instruction) && "Reflect..."}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Script Text - Shows current text being spoken */}
              <div
                className={`p-6 rounded-2xl min-h-32 flex items-center justify-center transition-all duration-300 ${
                  darkMode
                    ? "bg-dark-elev/30 border border-dark-border"
                    : "bg-white/40 border border-white/60"
                } ${isSpeaking ? "ring-2 ring-emerald-500/50" : ""}`}
              >
                <AnimatePresence mode="wait">
                  <motion.div
                    layout
                    key={`text-${currentSegmentIndex}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3, ease: "easeInOut" }}
                    className="text-center w-full"
                  >
                    <p
                      className={`text-base sm:text-lg leading-relaxed italic transition-all ${
                        isSpeaking
                          ? darkMode
                            ? "text-emerald-300 font-semibold"
                            : "text-emerald-700 font-semibold"
                          : darkMode
                          ? "text-slate-200"
                          : "text-gray-700"
                      }`}
                    >
                      {currentSegment.text ||
                        "Meditation complete. Namaste. 🙏"}
                    </p>
                  </motion.div>
                </AnimatePresence>
              </div>

              {/* Controls */}
              <div className="space-y-4">
                {/* Control Buttons */}
                <div className="flex items-center justify-center gap-3 sm:gap-4">
                  {/* Skip Previous */}
                  <button
                    onClick={handleSkipPrev}
                    disabled={currentSegmentIndex === 0}
                    className={`w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center transition-all disabled:opacity-30 disabled:cursor-not-allowed ${
                      darkMode
                        ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                        : "bg-white/60 hover:bg-white text-gray-700"
                    }`}
                    title="Previous segment"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
                    </svg>
                  </button>

                  {/* Play/Pause Button */}
                  <div className="flex items-center justify-center gap-3 sm:gap-4">
                    <button
                      onClick={handlePlayPause}
                      disabled={isPrefetching}
                      className={`w-14 h-14 sm:w-16 sm:h-16 rounded-full flex items-center justify-center transition-all shadow-lg ${
                        isPrefetching
                          ? "bg-gray-400 dark:bg-gray-600 text-gray-300 dark:text-gray-500 cursor-not-allowed opacity-60"
                          : "bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white"
                      }`}
                      title={
                        isPrefetching
                          ? "Loading narration..."
                          : isPlaying
                          ? isPaused
                            ? "Resume"
                            : "Pause"
                          : "Play"
                      }
                    >
                      {!isPlaying || isPaused ? (
                        <svg
                          className="w-6 h-6 ml-1"
                          fill="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      ) : (
                        <svg
                          className="w-6 h-6"
                          fill="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                        </svg>
                      )}
                    </button>
                  </div>

                  {/* Skip Next */}
                  <button
                    onClick={handleSkipNext}
                    disabled={currentSegmentIndex === script.length - 1}
                    className={`w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center transition-all disabled:opacity-30 disabled:cursor-not-allowed ${
                      darkMode
                        ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                        : "bg-white/60 hover:bg-white text-gray-700"
                    }`}
                    title="Next segment"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M16 18h2V6h-2zm-11-7l8.5-6v12z" />
                    </svg>
                  </button>
                </div>

                {/* Loading indicator under controls */}
                {isPrefetching && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`text-center py-2 px-4 rounded-lg ${
                      darkMode
                        ? "bg-emerald-900/30 border border-emerald-500/30"
                        : "bg-emerald-50 border border-emerald-200"
                    }`}
                  >
                    <p
                      className={`text-xs font-medium ${
                        darkMode ? "text-emerald-300" : "text-emerald-700"
                      }`}
                    >
                      Please wait while we prepare your meditation experience...
                    </p>
                  </motion.div>
                )}

                {/* Utility Buttons */}
                <div className="flex items-center justify-center gap-2 sm:gap-3">
                  {/* Speaker Toggle */}
                  <button
                    onClick={handleToggleTTS}
                    className={`px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                      isTTSEnabled
                        ? darkMode
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : "bg-emerald-100 text-emerald-700 border border-emerald-300"
                        : darkMode
                        ? "bg-dark-surface text-dark-muted border border-dark-border"
                        : "bg-white/60 text-gray-600 border border-white/40"
                    }`}
                    title={isTTSEnabled ? "Disable speaker" : "Enable speaker"}
                  >
                    {isTTSEnabled ? (
                      <>
                        <svg
                          className="w-4 h-4"
                          fill="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
                        </svg>
                        Speaker
                      </>
                    ) : (
                      <>
                        <svg
                          className="w-4 h-4"
                          fill="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C23.16 14.9 24 13.04 24 11c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" />
                        </svg>
                        Muted
                      </>
                    )}
                  </button>

                  {/* Music Toggle */}
                  {chapter?.background_music && (
                    <button
                      onClick={() => setIsMusicMuted(!isMusicMuted)}
                      className={`px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                        !isMusicMuted
                          ? darkMode
                            ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                            : "bg-purple-100 text-purple-700 border border-purple-300"
                          : darkMode
                          ? "bg-dark-surface text-dark-muted border border-dark-border"
                          : "bg-white/60 text-gray-600 border border-white/40"
                      }`}
                      title={isMusicMuted ? "Unmute music" : "Mute music"}
                    >
                      {!isMusicMuted ? (
                        <>
                          <svg
                            className="w-4 h-4"
                            fill="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path d="M12 3v9.28c-.47-.46-.3-1.08.17-1.55.25-.23.58-.35.91-.35.69 0 1.25.56 1.25 1.25S13.69 13 13 13c-.36 0-.69-.15-.92-.4V20c0 1.66-1.34 3-3 3s-3-1.34-3-3v-.5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5V20c0 .55-.45 1-1 1s-1-.45-1-1v-6.72c-.47.46-.3 1.08.17 1.55.25.23.58.35.91.35.69 0 1.25-.56 1.25-1.25S6.69 11 6 11c-.36 0-.69.15-.92.4V12c0-1.66 1.34-3 3-3s3 1.34 3 3z" />
                          </svg>
                          Music
                        </>
                      ) : (
                        <>
                          <svg
                            className="w-4 h-4"
                            fill="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path d="M4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" />
                          </svg>
                          Muted
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default MeditationPlayer;
