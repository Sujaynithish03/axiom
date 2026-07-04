import { useEffect, useState } from "react";
import { useAxiom } from "./store";
import Layout from "./components/Layout";
import Boardroom from "./components/Boardroom";
import Dashboard from "./components/Dashboard";
import Copilot from "./components/Copilot";
import Onboarding from "./components/Onboarding";

type View = "boardroom" | "dashboard" | "copilot" | "onboarding";

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const { connect, fetchAll } = useAxiom();

  useEffect(() => {
    connect();
    fetchAll();
  }, []);

  return (
    <Layout view={view} setView={setView}>
      {view === "boardroom" && <Boardroom />}
      {view === "dashboard" && <Dashboard />}
      {view === "copilot" && <Copilot />}
      {view === "onboarding" && <Onboarding />}
    </Layout>
  );
}
