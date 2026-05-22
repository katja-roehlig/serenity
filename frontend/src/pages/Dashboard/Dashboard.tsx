import { useEffect, useState } from "react";
import { api } from "../../api/axios";
import { DashboardSection } from "../../components/DashboardSection/DashboardSection";

export interface DashboardCategory {
  id: string;
  content: string;
  reasoning?: string[];
  createdAt: string;
  expiresAt: string | null;
}
type DashboardData = Record<string, DashboardCategory[]>;

export const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    currentSituation: [],
    memory: [],
    safePlace: [],
    strengths: [],
    goal: [],
    belief: [],
    pattern: [],
  });

  useEffect(() => {
    const getDashboardData = async () => {
      try {
        const response = await api.get("/dashboard");
        console.log("Juhuu, das hat geklappt:", response.data);
        setDashboardData(response.data);
      } catch (error) {
        console.error(error);
        alert("Da ist etwas schief gelaufen.");
      }
    };
    getDashboardData();
  }, []);

  const {
    currentSituation,
    memory,
    safePlace,
    strengths,
    goal,
    belief,
    pattern,
  } = dashboardData;

  const handleDelete = async (id: string, category: string) => {
    const check = window.confirm("Möchtest du diese Übung wirklich löschen?");
    if (!check) return;
    try {
      await api.delete(`/dashboard/delete/${id}`);
      alert("Juhuu das hat geklappt");
      setDashboardData((prevData) => ({
        ...prevData,
        [category]: prevData[category]?.filter((item) => item.id !== id),
      }));
    } catch (error: any) {
      console.error(error);
      const error_message = error.response?.data?.detail;
      //   mein Backend_Fehlertext von HTTPException(status_code=404, detail="No item found with for this user")  liegt in  error.response.data.detail
      alert(
        error_message ||
          "Da ist etwas schief gelaufen beim Speichern der Übung",
      );
    }
  };
  return (
    <main>
      <DashboardSection
        title="Aktuelle Situation"
        property={currentSituation}
        category="current_situation"
        handleDelete={handleDelete}
      />
      <DashboardSection
        title="Stärken"
        property={strengths}
        category="strengths"
        handleDelete={handleDelete}
      />

      <DashboardSection
        title="Erinnerungen"
        property={memory}
        category="memory"
        handleDelete={handleDelete}
      />
      <DashboardSection
        title="Sicherer Ort"
        property={safePlace}
        category="safePlace"
        handleDelete={handleDelete}
      />
      <DashboardSection
        title="Ziele"
        property={goal}
        category="goal"
        handleDelete={handleDelete}
      />
      <DashboardSection
        title="Glaubenssätze"
        property={belief}
        category="belief"
        handleDelete={handleDelete}
      />
      <DashboardSection
        title="Muster"
        property={pattern}
        category="pattern"
        handleDelete={handleDelete}
      />
    </main>
  );
};
