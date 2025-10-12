import React from "react";
import Dashboard from "../components/Dashboard";

const App: React.FC = () => {
  return (
    <main style={{ fontFamily: "system-ui", padding: "2rem", background: "#0f172a", minHeight: "100vh" }}>
      <Dashboard />
    </main>
  );
};

export default App;
