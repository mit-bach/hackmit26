import { Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "./layout/Shell";
import Overview from "./pages/Overview";
import Inbox from "./pages/Inbox";
import AP from "./pages/AP";
import AR from "./pages/AR";
import Cash from "./pages/Cash";
import StripePage from "./pages/StripePage";
import Close from "./pages/Close";
import Forecast from "./pages/Forecast";
import Audit from "./pages/Audit";
import Memory from "./pages/Memory";
import Evaluations from "./pages/Evaluations";
import Simulations from "./pages/Simulations";
import Architecture from "./pages/Architecture";
import Workflow from "./pages/Workflow";
import Videos from "./pages/Videos";
import Coverage from "./pages/Coverage";
import Sandbox from "./pages/Sandbox";

export const ROUTES = [
  "/",
  "/architecture",
  "/sandbox",
  "/workflow",
  "/memory",
  "/simulations",
  "/videos",
  "/coverage",
  "/evaluations",
  "/agents",
  "/inbox",
  "/ap",
  "/ar",
  "/cash",
  "/stripe",
  "/close",
  "/forecast",
  "/audit",
  "/scenarios",
];

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/architecture" element={<Architecture />} />
        <Route path="/sandbox" element={<Sandbox />} />
        <Route path="/workflow" element={<Workflow />} />
        <Route path="/memory" element={<Memory />} />
        <Route path="/simulations" element={<Simulations />} />
        <Route path="/simulations/:id" element={<Simulations />} />
        <Route path="/videos" element={<Videos />} />
        <Route path="/coverage" element={<Coverage />} />
        <Route path="/evaluations" element={<Evaluations />} />
        <Route path="/agents" element={<Navigate to="/architecture" replace />} />
        <Route path="/inbox" element={<Inbox />} />
        <Route path="/ap" element={<AP />} />
        <Route path="/ar" element={<AR />} />
        <Route path="/cash" element={<Cash />} />
        <Route path="/stripe" element={<StripePage />} />
        <Route path="/close" element={<Close />} />
        <Route path="/forecast" element={<Forecast />} />
        <Route path="/audit" element={<Audit />} />
        <Route path="/scenarios" element={<Simulations />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Shell>
  );
}
