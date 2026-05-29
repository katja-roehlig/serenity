import { useEffect, useState } from "react";
import { api } from "../../api/axios";
import { DashboardSection } from "../../components/DashboardSection/DashboardSection";
import styles from "./Dashboard.module.css";
import Masonry from "react-masonry-css";
import toast from "react-hot-toast";

export interface DashboardCategory {
  id: string;
  content: string;
  reasoning?: string[] | null;
  createdAt: string;
  expiresAt: string | null;
}

type DashboardData = Record<string, DashboardCategory[]>;

interface FormattedCategoryList {
  key: string;
  title: string;
  data: DashboardCategory[];
}

export const Dashboard = () => {
  const [sortedList, setSortedList] = useState<FormattedCategoryList[]>([]);
  const [_dashboardData, setDashboardData] = useState<DashboardData>({
    currentSituation: [],
    memory: [],
    safePlace: [],
    strengths: [],
    goal: [],
    belief: [],
    pattern: [],
  });

  const breakpointColumnsObj = {
    default: 2, // screen >= 1100
    960: 1, // screen < 768
  };

  const translationDictionary: Record<string, string> = {
    currentSituation: "Aktuelle Situation",
    strengths: "Stärken",
    memory: "Erinnerungen",
    safePlace: "Sicherer Ort",
    goal: "Ziele",
    belief: "Glaubenssätze",
    pattern: "Muster",
  };

  const getDashboardData = async (): Promise<DashboardData | undefined> => {
    try {
      const response = await api.get("/dashboard");
      console.log("Juhuu, das hat geklappt:", response.data);
      const backendData = response.data;
      setDashboardData(backendData);
      return backendData;
    } catch (error) {
      console.error(error);
      toast.error(
        "Deine Daten konnten nicht geladen werden. Versuche es später noch einmal!",
      );
      return undefined;
    }
  };

  const formatDashboardData = (backendData: DashboardData) => {
    //aus Backend-Objekt wird eine Liste
    const categoriesList = Object.entries(backendData).map(([key, value]) => {
      return {
        key: key,
        title: translationDictionary[key] || key,
        data: value || [],
      };
    });
    const sortedCategoriesList = [...categoriesList].sort((a, b) => {
      return b.data.length - a.data.length;
    });
    setSortedList(sortedCategoriesList);
  };

  useEffect(() => {
    const processData = async () => {
      const backendData = await getDashboardData();
      if (backendData) {
        formatDashboardData(backendData);
      }
    };
    processData();
  }, []);

  const handleDelete = async (id: string, category: string) => {
    const check = window.confirm(
      "Möchtest du diesen Eintrag wirklich löschen?",
    );
    if (!check) return;
    try {
      await api.delete(`/dashboard/delete/${id}`);
      toast.success("Der Eintrag wurde erfolgreich gelöscht.");
      setDashboardData((prevData) => ({
        ...prevData,
        [category]: prevData[category]?.filter((item) => item.id !== id),
      }));
    } catch (error: any) {
      console.error(error);
      const error_message = error.response?.data?.detail;
      //   der Fehlertext  aus dem Backend von HTTPException(status_code=404,
      // detail="No item found with for this user")  liegt in  error.response.data.detail
      toast.error(
        error_message ||
          "Da ist etwas schief gelaufen beim Speichern der Übung",
      );
    }
  };
  return (
    <main className={styles.main}>
      <h2>Dein Dashboard</h2>
      <Masonry
        breakpointCols={breakpointColumnsObj}
        className={styles.myMasonryGrid}
        columnClassName={styles.myMasonryGridColumn}
      >
        {sortedList.map((categoryItem) => {
          return (
            <DashboardSection
              key={categoryItem.key}
              title={categoryItem.title}
              category={categoryItem.key}
              property={categoryItem.data}
              handleDelete={handleDelete}
            />
          );
        })}
      </Masonry>
    </main>
  );
};
