import { useEffect, useState } from "react";
import { useAxiom } from "./store";
import Layout from "./components/Layout";
import Boardroom from "./components/Boardroom";
import Dashboard from "./components/Dashboard";
import Copilot from "./components/Copilot";
import Onboarding from "./components/Onboarding";
import EngineView from "./components/EngineView";
import { ENGINES } from "./engines";

const ENGINE_KEYS = ENGINES.map((e) => e.key);

export default function App() {
  const [view, setView] = useState<string>("boardroom");
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
      {ENGINE_KEYS.includes(view) && <EngineView key={view} engineKey={view} />}
    </Layout>
  );
}
