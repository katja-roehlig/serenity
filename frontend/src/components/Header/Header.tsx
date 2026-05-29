import styles from "./Header.module.css";
import Logo from "../../assets/Logo-dark.svg?react";

export const Header = () => {
  return (
    <div className={styles.header}>
      <div className={styles.logContainer}>
        <div className={styles.logoContainer}>
          <h1 className={styles.logoText}>serenity</h1>
          <Logo className={styles.logo} />
        </div>
      </div>
    </div>
  );
};
