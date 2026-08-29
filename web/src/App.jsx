import { useEffect, useMemo, useState } from "react";
import { Dashboard } from "./Dashboard.jsx";
import { LoadingScreen } from "./LoadingScreen.jsx";

const defaultPollSeconds = 15;

async function fetchDashboard() {
  const response = await fetch("/api/dashboard");
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Dashboard request failed");
  }

  return data;
}

export default function App() {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState(null);
  const [now, setNow] = useState(() => Date.now());

  const pollSeconds = dashboard?.pollIntervalSeconds || defaultPollSeconds;

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await fetchDashboard();
        if (!cancelled) {
          setDashboard(data);
          setError(data.error || null);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError.message);
        }
      }
    }

    load();
    const id = setInterval(load, pollSeconds * 1000);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [pollSeconds]);

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const ageSeconds = useMemo(() => {
    if (!dashboard?.updatedAt) return null;
    return Math.max(0, Math.floor((now - Date.parse(dashboard.updatedAt)) / 1000));
  }, [dashboard?.updatedAt, now]);

  if (!dashboard) {
    return <LoadingScreen error={error} />;
  }

  return <Dashboard data={dashboard} ageSeconds={ageSeconds} error={error} />;
}
