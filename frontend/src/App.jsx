import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import Landing from "./pages/Landing";
import LocationPicker from "./pages/LocationPicker";
import AdvisoryDashboard from "./pages/AdvisoryDashboard";
import DiseaseDiagnosis from "./pages/DiseaseDiagnosis";
import VoiceQuery from "./pages/VoiceQuery";
import CooperationDashboard from "./pages/CooperationDashboard";

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/location" element={<LocationPicker />} />
          <Route path="/advisory" element={<AdvisoryDashboard />} />
          <Route path="/diagnose" element={<DiseaseDiagnosis />} />
          <Route path="/ask" element={<VoiceQuery />} />
          <Route path="/network" element={<CooperationDashboard />} />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}
