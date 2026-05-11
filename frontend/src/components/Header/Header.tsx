import { Link } from "react-router-dom";
import styles from "./Header.module.css";

export const Header = () => {
  return (
    <div className={styles.header}>
      <h1>Serenity</h1>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/exercise/add">Übung hinzufügen</Link>
      </nav>
    </div>
  );
};
