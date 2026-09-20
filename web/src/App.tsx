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
import Agents from "./pages/Agents";
import Evaluations from "./pages/Evaluations";
import Scenarios from "./pages/Scenarios";
import Architecture from "./pages/Architecture";

export const ROUTES = [
  "/",
  "/inbox",
  "/ap",
  "/ar",
  "/cash",
  "/stripe",
  "/close",
  "/forecast",
  "/audit",
  "/memory",
  "/agents",
  "/evaluations",
  "/scenarios",
  "/architecture",
];

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/inbox" element={<Inbox />} />
        <Route path="/ap" element={<AP />} />
        <Route path="/ar" element={<AR />} />
        <Route path="/cash" element={<Cash />} />
        <Route path="/stripe" element={<StripePage />} />
        <Route path="/close" element={<Close />} />
        <Route path="/forecast" element={<Forecast />} />
        <Route path="/audit" element={<Audit />} />
        <Route path="/memory" element={<Memory />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/evaluations" element={<Evaluations />} />
        <Route path="/scenarios" element={<Scenarios />} />
        <Route path="/architecture" element={<Architecture />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Shell>
  );
}
