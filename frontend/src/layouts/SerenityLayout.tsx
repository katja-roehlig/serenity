import { Outlet } from "react-router-dom";
import { Header } from "../components/Header/Header";
import { Sidebar } from "../components/Sidebar/Sidebar";
import styles from "./SerenityLayout.module.css";
import { useEffect, useState } from "react";
import { api } from "../api/axios";

export interface UserProfile {
  id: number;
  mail: string;
  nickname: string;
  isAdmin: boolean;
  hasOnboarding: boolean;
  age: number;
  gender: string;
}

export const SerenityLayout = () => {
  const [userData, setUserData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const getUserProfile = async () => {
    try {
      const response = await api.get("/user/profile");
      setUserData(response.data);
    } catch (error) {
      console.error("Failed to load user profile fpr frontend", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    SerenityLayout;
    getUserProfile();
  }, []);

  if (isLoading)
    return <div>Einen Moment bitte. Serenity sucht deine Daten...</div>;

  return (
    <div className={styles.appContainer}>
      <Header />
      <div className={styles.mainContent}>
        <Sidebar userData={userData!} />
        <main className={styles.pageContainer}>
          <Outlet context={[userData, getUserProfile]} />
        </main>
      </div>
    </div>
  );
};
