import { BrowserRouter, Routes, Route } from "react-router-dom";
import { LandingPage } from "./pages/LandingPage/LandingPage";
import { Register } from "./pages/Register/Register";
import { NotFound } from "./pages/NotFound/NotFound";
import { Login } from "./pages/Login/Login";
import { Onboarding } from "./pages/Onboarding/Onboarding";
import { Chat } from "./pages/Chat/Chat";
import { AddExercise } from "./pages/AddExercise/AddExercise";
import { Exercise } from "./pages/Exercise/Exercise";
import { Dashboard } from "./pages/Dashboard/dashboard";
import { Header } from "./components/Header/Header";

export function App() {
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        {/* Zur Registrierung */}
        <Route path="/register" element={<Register />} />

        {/* Zum Login */}
        <Route path="/login" element={<Login />} />

        {/* 404 Page */}
        <Route path="*" element={<NotFound />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/exercise/add" element={<AddExercise />} />
        <Route path="/exercise" element={<Exercise />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
