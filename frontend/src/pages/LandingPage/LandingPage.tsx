import styles from "./LandingPage.module.css";
import Logo from "../../assets/Logo-light.svg?react";
import { Outlet } from "react-router-dom";

export const LandingPage = () => {
  return (
    <main className={styles.landingPage}>
      <div className={styles.textContainer}>
        <p className={styles.lpText}>Ankommen. Durchatmen.</p>
      </div>
      <div className={styles.logContainer}>
        <div className={styles.logoContainer}>
          <h1 className={styles.logoText}>serenity</h1>
          <Logo className={styles.logo} />
        </div>
        <Outlet />
      </div>
    </main>
  );
};
