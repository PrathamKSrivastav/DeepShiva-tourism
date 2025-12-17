import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useMeditation } from "../hooks/useMeditation";
import MeditationPlayer from "./MeditationPlayer";

const MeditationSelector = ({ darkMode, onClose }) => {
  const [stage, setStage] = useState("courses"); // 'courses', 'chapters', 'playing'
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(null);

  const {
    courses,
    courseDetails,
    chapterScript,
    isLoading,
    error,
    fetchCourses,
    fetchCourseDetails,
    fetchChapterScript,
  } = useMeditation();

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  const handleCourseSelect = async (course) => {
    setSelectedCourse(course);
    await fetchCourseDetails(course.id);
    setStage("chapters");
  };

  const handleChapterSelect = async (chapter) => {
    setSelectedChapter(chapter);
    await fetchChapterScript(selectedCourse.id, chapter.id);
    setStage("playing");
  };

  const handleBack = () => {
    if (stage === "chapters") {
      setStage("courses");
      setSelectedCourse(null);
    } else if (stage === "playing") {
      setStage("chapters");
      setSelectedChapter(null);
    }
  };

  return (
    <>
      <AnimatePresence>
        {stage === "courses" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 ${
              darkMode ? "bg-black/70" : "bg-black/60"
            }`}
            onClick={onClose}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className={`relative w-full max-w-2xl max-h-[80vh] rounded-3xl overflow-hidden shadow-2xl ${
                darkMode
                  ? "bg-dark-surface border border-dark-border"
                  : "bg-white border border-white/20"
              }`}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div
                className={`p-6 border-b ${
                  darkMode ? "border-dark-border" : "border-white/20"
                }`}
              >
                <div className="flex items-center justify-between">
                  <h2
                    className={`text-2xl font-bold ${
                      darkMode ? "text-white" : "text-gray-900"
                    }`}
                  >
                    🧘 Meditation Courses
                  </h2>
                  <button
                    onClick={onClose}
                    className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      darkMode
                        ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                        : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                    }`}
                  >
                    ✕
                  </button>
                </div>
              </div>
              {/* Content */}
              <div className="overflow-y-auto no-scrollbar p-6 max-h-[calc(80vh-100px)]">
                {isLoading ? (
                  <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500" />
                  </div>
                ) : error ? (
                  <div
                    className={`p-4 rounded-lg text-center ${
                      darkMode
                        ? "bg-red-900/20 text-red-400"
                        : "bg-red-50 text-red-600"
                    }`}
                  >
                    Error loading courses: {error}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {courses.map((course) => (
                      <motion.button
                        key={course.id}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleCourseSelect(course)}
                        className={`p-6 rounded-2xl text-left transition-all overflow-hidden ${
                          darkMode
                            ? "bg-dark-elev hover:bg-dark-elev/80 border border-dark-border"
                            : "bg-white/60 hover:bg-white border border-white/20"
                        }`}
                      >
                        <div className="w-full h-32 mb-3 rounded-xl overflow-hidden flex items-center justify-center ">
                          <img
                            src={course.image}
                            alt={course.title}
                            className="max-h-full max-w-full object-contain"
                          />
                        </div>

                        <h3
                          className={`font-bold mb-2 ${
                            darkMode ? "text-white" : "text-gray-900"
                          }`}
                        >
                          {course.title}
                        </h3>
                        <p
                          className={`text-xs mb-3 ${
                            darkMode ? "text-dark-muted" : "text-gray-600"
                          }`}
                        >
                          {course.description}
                        </p>
                        <div className="flex items-center justify-between">
                          <span
                            className={`text-sm font-medium ${
                              darkMode ? "text-emerald-400" : "text-emerald-600"
                            }`}
                          >
                            {course.duration} min
                          </span>
                          <span
                            className={`text-xs px-2 py-1 rounded-full ${
                              darkMode
                                ? "bg-dark-surface text-dark-muted"
                                : "bg-gray-100 text-gray-600"
                            }`}
                          >
                            {course.difficulty}
                          </span>
                        </div>
                      </motion.button>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}

        {stage === "chapters" && courseDetails && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 ${
              darkMode ? "bg-black/70" : "bg-black/60"
            }`}
            onClick={onClose}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className={`relative w-full max-w-2xl max-h-[80vh] rounded-3xl overflow-hidden shadow-2xl ${
                darkMode
                  ? "bg-dark-surface border border-dark-border"
                  : "bg-white border border-white/20"
              }`}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div
                className={`p-6 border-b ${
                  darkMode ? "border-dark-border" : "border-white/20"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <button
                      onClick={handleBack}
                      className={`text-sm font-medium mb-2 flex items-center gap-2 ${
                        darkMode ? "text-emerald-400" : "text-emerald-600"
                      }`}
                    >
                      ← Back
                    </button>
                    <h2
                      className={`text-2xl font-bold ${
                        darkMode ? "text-white" : "text-gray-900"
                      }`}
                    >
                      {courseDetails.course_title}
                    </h2>
                  </div>
                  <button
                    onClick={onClose}
                    className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      darkMode
                        ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                        : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                    }`}
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="overflow-y-auto no-scrollbar p-6 max-h-[calc(80vh-100px)]">
                <div className="space-y-3">
                  {courseDetails.chapters?.map((chapter, idx) => (
                    <motion.button
                      key={chapter.id}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleChapterSelect(chapter)}
                      className={`w-full p-4 rounded-xl text-left transition-all ${
                        darkMode
                          ? "bg-dark-elev hover:bg-dark-elev/80 border border-dark-border"
                          : "bg-white/60 hover:bg-white border border-white/20"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3
                            className={`font-bold mb-1 ${
                              darkMode ? "text-white" : "text-gray-900"
                            }`}
                          >
                            Chapter {idx + 1}: {chapter.title}
                          </h3>
                          <p
                            className={`text-sm line-clamp-2 ${
                              darkMode ? "text-dark-muted" : "text-gray-600"
                            }`}
                          >
                            {chapter.script_preview}
                          </p>
                        </div>
                        <span
                          className={`text-sm font-medium ml-4 flex-shrink-0 ${
                            darkMode ? "text-emerald-400" : "text-emerald-600"
                          }`}
                        >
                          {chapter.duration} min
                        </span>
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}

        {stage === "playing" && chapterScript && (
          <MeditationPlayer
            chapter={chapterScript.chapter}
            courseTitle={courseDetails?.course_title}
            onClose={handleBack}
            darkMode={darkMode}
          />
        )}
      </AnimatePresence>
    </>
  );
};

export default MeditationSelector;
