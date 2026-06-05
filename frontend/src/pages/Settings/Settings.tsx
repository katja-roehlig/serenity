import { Link, useNavigate, useOutletContext } from "react-router-dom";
import type { UserProfile } from "../../layouts/SerenityLayout";
import styles from "./Settings.module.css";
import {
  IdentificationCardIcon,
  PencilSimpleLineIcon,
  TrashIcon,
  UserIcon,
} from "@phosphor-icons/react";
import { api } from "../../api/axios";
import toast from "react-hot-toast";

export const Settings = async () => {
  // Holt die Daten direkt aus dem Outlet-Kontext von SerenityLayout
  const navigate = useNavigate();
  const [userData, _getUserProfile] =
    useOutletContext<[UserProfile, () => void]>();

  const handleDeleteUser = async () => {
    const check = window.confirm("Möchtest du dein Profil wirklich löschen?");
    if (!check) return;
    try {
      await api.delete("/settings/user");
      localStorage.removeItem(`Chat ${userData.id}`);
      toast.success("Dein Profil wurde erfolgreich gelöscht");
      navigate("/");
    } catch (error) {
      console.error(error);
      toast.error(
        "Fehler beim Löschen deines Profils. Bitte versuche es später noch einmal.",
      );
    }
  };

  return (
    <main className={styles.settingsContainer}>
      <h2>Einstellungen</h2>
      <div className={styles.userProfile}>
        <section className={styles.dataContainer}>
          <div className={styles.sectionHeader}>
            <h3 className={styles.sectionHeading}>Profildaten</h3>
            <IdentificationCardIcon size={32} />
          </div>
          <div className={styles.itemContainer}>
            <p className={styles.firstParagraph}>Benutzername</p>
            <p className={styles.secondParagraph}>{userData?.nickname}</p>
            <PencilSimpleLineIcon size={32} className={styles.icon} />
          </div>
          <div className={styles.itemContainer}>
            <p className={styles.firstParagraph}>Mailadresse</p>
            <p className={styles.secondParagraph}>{userData?.mail}</p>
            <PencilSimpleLineIcon size={32} className={styles.icon} />
          </div>
          <div className={`${styles.itemContainer} ${styles.last}`}>
            <p className={styles.firstParagraph}>Passwort ändern</p>
            <PencilSimpleLineIcon size={32} className={styles.icon} />
          </div>
          <button
            type="submit"
            onClick={handleDeleteUser}
            className={styles.profileDeleteButton}
          >
            <TrashIcon size={32} className={styles.icon} />
            Profil löschen
          </button>
        </section>

        <section className={styles.dataContainer}>
          <div className={styles.sectionHeader}>
            <h3 className={styles.sectionHeading}>Persönliche Angaben</h3>
            <UserIcon size={28} weight="bold" />
          </div>
          <div className={styles.itemContainer}>
            <p className={styles.firstParagraph}>Alter: </p>
            <p className={styles.secondParagraph}>{userData?.age}</p>
            <PencilSimpleLineIcon size={32} className={styles.icon} />
          </div>
          <div className={`${styles.itemContainer} ${styles.last}`}>
            <p className={styles.firstParagraph}>Ich bin : </p>
            <p className={styles.secondParagraph}>{userData?.gender}</p>
            <PencilSimpleLineIcon size={32} className={styles.icon} />
          </div>
        </section>
      </div>
      <section className={styles.linkContainer}>
        <Link to="/privacy-policy" className={styles.link}>
          Datenschutz
        </Link>
        <div>|</div>

        <Link to="/terms-of-use" className={styles.link}>
          Nutzervereinbarungen{" "}
        </Link>
        <div>|</div>

        <Link to="/impressum" className={styles.link}>
          Impressum
        </Link>
      </section>
    </main>
  );
};
