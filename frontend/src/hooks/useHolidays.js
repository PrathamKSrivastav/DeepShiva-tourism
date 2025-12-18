import { useState, useCallback } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const useHolidays = () => {
  const [holidays, setHolidays] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Fetch upcoming holidays
   */
  const fetchUpcomingHolidays = useCallback(async (limit = 3) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/api/holidays/upcoming?limit=${limit}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("✅ Fetched upcoming holidays:", data);

      setHolidays(data.holidays || []);

      return data;
    } catch (err) {
      console.error("❌ Error fetching upcoming holidays:", err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch holidays by year
   */
  const fetchHolidaysByYear = useCallback(
    async (year, month = null, quarter = null) => {
      setIsLoading(true);
      setError(null);

      try {
        let url = `${API_URL}/api/holidays/year/${year}`;
        const params = new URLSearchParams();

        if (month) params.append("month", month);
        if (quarter) params.append("quarter", quarter);

        if (params.toString()) {
          url += `?${params.toString()}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("✅ Fetched holidays by year:", data);

        setHolidays(data.holidays || []);

        return data;
      } catch (err) {
        console.error("❌ Error fetching holidays by year:", err);
        setError(err.message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return {
    holidays,
    isLoading,
    error,
    fetchUpcomingHolidays,
    fetchHolidaysByYear,
  };
};
