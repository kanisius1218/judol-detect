import { useEffect, useState } from "react";

type Metrics = {
  queued: number;
  rollback: number;
  manual: number;
};

const INITIAL_METRICS: Metrics = { queued: 12, rollback: 1, manual: 4 };

export const useQueueMetrics = () => {
  const [metrics, setMetrics] = useState<Metrics>(INITIAL_METRICS);

  useEffect(() => {
    const timer = setInterval(() => {
      setMetrics((prev) => ({
        queued: prev.queued + Math.round(Math.random()),
        rollback: prev.rollback,
        manual: prev.manual,
      }));
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  return metrics;
};
