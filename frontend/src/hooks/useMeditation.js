import { useState, useCallback } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export const useMeditation = () => {
  const [courses, setCourses] = useState([]);
  const [courseDetails, setCourseDetails] = useState(null);
  const [chapterScript, setChapterScript] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCourses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/meditation/courses`);
      if (!response.ok) throw new Error("Failed to fetch courses");
      const data = await response.json();
      setCourses(data.courses || []);
      console.log("✅ Fetched meditation courses:", data.courses);
    } catch (err) {
      setError(err.message);
      console.error("❌ Error fetching courses:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchCourseDetails = useCallback(async (courseId) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/meditation/courses/${courseId}`
      );
      if (!response.ok) throw new Error("Failed to fetch course details");
      const data = await response.json();
      setCourseDetails(data);
      console.log("✅ Fetched course details:", data);
    } catch (err) {
      setError(err.message);
      console.error("❌ Error fetching course details:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchChapterScript = useCallback(async (courseId, chapterId) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/meditation/courses/${courseId}/chapters/${chapterId}`
      );
      if (!response.ok) throw new Error("Failed to fetch chapter script");
      const data = await response.json();
      setChapterScript(data);
      console.log("✅ Fetched chapter script:", data);
    } catch (err) {
      setError(err.message);
      console.error("❌ Error fetching chapter script:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    courses,
    courseDetails,
    chapterScript,
    isLoading,
    error,
    fetchCourses,
    fetchCourseDetails,
    fetchChapterScript,
  };
};
