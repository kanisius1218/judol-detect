import React from "react";

import { useQueueMetrics } from "../hooks/useQueueMetrics";

const Card: React.FC<{ title: string; value: string }> = ({ title, value }) => (
  <div
    style={{
      background: "#1e293b",
      borderRadius: "1rem",
      padding: "1.5rem",
      color: "#e2e8f0",
      minWidth: "200px",
      boxShadow: "0 10px 30px rgba(15, 23, 42, 0.4)",
    }}
  >
    <p style={{ opacity: 0.6, marginBottom: "0.5rem" }}>{title}</p>
    <h2 style={{ fontSize: "2.5rem", margin: 0 }}>{value}</h2>
  </div>
);

const Dashboard: React.FC = () => {
  const metrics = useQueueMetrics();

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
      <header>
        <h1 style={{ color: "#f8fafc", fontSize: "3rem", marginBottom: "0.5rem" }}>
          SpamOps Command Center
        </h1>
        <p style={{ color: "#94a3b8", maxWidth: "40rem" }}>
          Monitor automated deletions, audit trails, and manual reviews across every supported platform in
          real-time.
        </p>
      </header>
      <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
        <Card title="Queued Deletions" value={metrics.queued.toString()} />
        <Card title="Rollback Requests" value={metrics.rollback.toString()} />
        <Card title="Manual Reviews" value={metrics.manual.toString()} />
      </div>
    </section>
  );
};

export default Dashboard;
