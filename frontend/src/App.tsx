import { BrowserRouter, Routes, Route } from "react-router-dom";
import { LandingPage } from "./pages/LandingPage/LandingPage";
import { NotFound } from "./pages/NotFound/NotFound";
import { Login } from "./components/Login/Login";
import { Onboarding } from "./pages/Onboarding/Onboarding";
import { Chat } from "./pages/Chat/Chat";
import { AddExercise } from "./pages/AddExercise/AddExercise";
import { Exercise } from "./pages/Exercise/Exercise";
import { Dashboard } from "./pages/Dashboard/Dashboard";
import { ExerciseShow } from "./pages/ExerciseShow/ExerciseShow";
import { SerenityLayout } from "./layouts/SerenityLayout";
import { Register } from "./components/Register/Register";
import { Settings } from "./pages/Settings/Settings";
import { TermsOfUse } from "./pages/TermsOfUse/TermsOfUse";
import { PrivacyPolicy } from "./pages/PrivacyPolicy/PrivacyPolicy";
import { Impressum } from "./pages/Impressum/Impressum";
import { Toaster } from "react-hot-toast";

export function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        reverseOrder={false}
        toastOptions={{
          className: "toast",
          success: {
            className: "toast-success",
          },
          error: {
            className: "toast-error",
          },
        }}
      />
      <Routes>
        <Route path="/" element={<LandingPage />}>
          <Route index element={<Register />} />
          <Route path="/login" element={<Login />} />
        </Route>

        {/* ab hier Apop-Layout */}
        <Route element={<SerenityLayout />}>
          <Route path="/chat" element={<Chat />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/exercise/add" element={<AddExercise />} />
          <Route path="/exercise/:id" element={<ExerciseShow />} />
          <Route path="/exercise" element={<Exercise />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/terms-of-use" element={<TermsOfUse />} />
          <Route path="/privacy-policy" element={<PrivacyPolicy />} />
          <Route path="/impressum" element={<Impressum />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
