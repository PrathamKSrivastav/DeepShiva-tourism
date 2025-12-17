import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

const MeditationPlayer = ({ chapter, courseTitle, onClose, darkMode }) => {
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isTTSEnabled, setIsTTSEnabled] = useState(true);
  const [isMusicMuted, setIsMusicMuted] = useState(false);

  const audioRef = useRef(null);
  const segmentTimerRef = useRef(null);
  const utteranceRef = useRef(null);

  const script = chapter?.script || [];

  // Cleanup speech on unmount
  useEffect(() => {
    return () => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Handle segment progression and TTS
  useEffect(() => {
    if (!isPlaying || isPaused) {
      if (segmentTimerRef.current) clearTimeout(segmentTimerRef.current);
      return;
    }

    const currentSegment = script[currentSegmentIndex];
    if (!currentSegment) {
      setIsPlaying(false);
      return;
    }

    // Speak current segment if TTS enabled
    if (isTTSEnabled && currentSegment.text) {
      speakSegment(currentSegment.text);
    }

    // Calculate pause based on either segment pause or TTS duration
    let pauseDuration = (currentSegment.pause || 2) * 1000;

    // If TTS is enabled, add extra time for speech
    if (isTTSEnabled && currentSegment.text) {
      const estimatedSpeechTime = (currentSegment.text.length / 15) * 1000; // ~15 chars per second
      pauseDuration = Math.max(pauseDuration, estimatedSpeechTime + 500);
    }

    segmentTimerRef.current = setTimeout(() => {
      if (currentSegmentIndex < script.length - 1) {
        setCurrentSegmentIndex((prev) => prev + 1);
      } else {
        setIsPlaying(false);
        setIsSpeaking(false);
      }
    }, pauseDuration);

    return () => clearTimeout(segmentTimerRef.current);
  }, [isPlaying, isPaused, currentSegmentIndex, script, isTTSEnabled]);

  // Handle background music mute
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMusicMuted ? 0 : 0.3;
    }
  }, [isMusicMuted]);

  const speakSegment = (text) => {
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    setIsSpeaking(false);

    if (!("speechSynthesis" in window)) {
      console.log("Text-to-speech not supported");
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9; // Slightly slower for meditation
    utterance.pitch = 0.8;
    utterance.volume = 1.0;

    // Find best voice
    const voices = window.speechSynthesis.getVoices();
    const indianVoice = voices.find(
      (voice) =>
        voice.lang.includes("hi-IN") ||
        voice.name.toLowerCase().includes("india")
    );
    const naturalVoice = voices.find(
      (voice) =>
        voice.lang.startsWith("en") &&
        (voice.name.includes("Natural") ||
          voice.name.includes("Google") ||
          voice.name.includes("Premium"))
    );
    const fallbackVoice = voices.find((voice) => voice.lang.startsWith("en"));

    if (indianVoice) {
      utterance.voice = indianVoice;
    } else if (naturalVoice) {
      utterance.voice = naturalVoice;
    } else if (fallbackVoice) {
      utterance.voice = fallbackVoice;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const handlePlayPause = () => {
    console.log("Play/Pause clicked - Current state:", { isPlaying, isPaused });
    if (!isPlaying) {
      console.log("Setting to PLAYING");
      setIsPlaying(true);
      setIsPaused(false);
      // Play background music if available and not muted
      if (audioRef.current && chapter?.background_music && !isMusicMuted) {
        audioRef.current
          .play()
          .catch((err) => console.warn("Audio playback failed:", err.message));
      }
    } else if (!isPaused) {
      console.log("Setting to PAUSED");
      setIsPaused(true);
      if (audioRef.current) {
        audioRef.current.pause();
      }
      window.speechSynthesis.pause();
    } else {
      console.log("Setting to RESUMED");
      setIsPaused(false);
      if (audioRef.current && chapter?.background_music) {
        audioRef.current
          .play()
          .catch((err) => console.warn("Audio resume failed:", err.message));
      }
      window.speechSynthesis.resume();
    }
  };

  const handleStop = () => {
    setIsPlaying(false);
    setIsPaused(false);
    setCurrentSegmentIndex(0);
    setIsSpeaking(false);
    if (audioRef.current) audioRef.current.pause();
    if (segmentTimerRef.current) clearTimeout(segmentTimerRef.current);
    window.speechSynthesis.cancel();
  };

  const handleSkipNext = () => {
    if (currentSegmentIndex < script.length - 1) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      setCurrentSegmentIndex((prev) => prev + 1);
    }
  };

  const handleSkipPrev = () => {
    if (currentSegmentIndex > 0) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      setCurrentSegmentIndex((prev) => prev - 1);
    }
  };

  const handleToggleTTS = () => {
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
    setIsTTSEnabled(!isTTSEnabled);
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
        {/* Background Music Audio */}
        {chapter?.background_music && (
          <audio
            ref={audioRef}
            src={chapter.background_music}
            loop
            style={{ display: "none" }}
            volume={isMusicMuted ? 0 : 0.3}
          />
        )}

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
            Chapter {currentSegmentIndex + 1} of {script.length}
          </p>
        </div>

        {/* Main Content */}
        <div className="p-6 sm:p-8 space-y-6">
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
                  {currentSegment.text || "Meditation complete. Namaste. 🙏"}
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
              <button
                onClick={handlePlayPause}
                className="w-14 h-14 sm:w-16 sm:h-16 rounded-full flex items-center justify-center transition-all shadow-lg bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white"
                title={isPlaying ? (isPaused ? "Resume" : "Pause") : "Play"}
              >
                {!isPlaying || isPaused ? (
                  // Show PLAY icon when not playing OR when paused (to resume)
                  <svg
                    className="w-6 h-6 ml-1"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M8 5v14l11-7z" />
                  </svg>
                ) : (
                  // Show PAUSE icon when playing and not paused
                  <svg
                    className="w-6 h-6"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                  </svg>
                )}
              </button>

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
        </div>
      </motion.div>
    </motion.div>
  );
};

export default MeditationPlayer;
