import styles from "./Sidebar.module.css";
import type { UserProfile } from "../../layouts/SerenityLayout";
import { Link, NavLink } from "react-router-dom";
import {
  ArchiveIcon,
  CaretDownIcon,
  CaretUpIcon,
  ClipboardTextIcon,
  DownloadSimpleIcon,
  GearIcon,
  PlusSquareIcon,
  RocketIcon,
  SignOutIcon,
  TrashIcon,
} from "@phosphor-icons/react";
import { ChatTeardropDotsIcon } from "@phosphor-icons/react";
import { useState } from "react";

export const Sidebar = ({ userData }: { userData: UserProfile }) => {
  const userName = userData.nickname.trim();
  const firstLetter = userName.charAt(0);
  const [isChatMenuOpen, setIsChatMenuOpen] = useState(false);
  const [isExerciseMenuOpen, setIsExerciseMenuOpen] = useState(false);
  return (
    <aside className={styles.sidebar}>
      <div className={styles.name}>
        <div className={styles.initial}>
          <div className={styles.firstLetter}>{firstLetter}</div>
        </div>
        <div>{userName}</div>
      </div>

      <nav className={styles.navMenu}>
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `${styles.navItem} ${isActive ? styles.active : ""}`
          }
        >
          <div className={styles.wrapper}>
            <GearIcon size={28} />
            <span>Einstellungen</span>
          </div>
        </NavLink>
        {userData.hasOnboarding ? (
          <>
            <NavLink
              to="/chat"
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ""}`
              }
            >
              <div className={styles.wrapper}>
                <ChatTeardropDotsIcon size={28} />
                <span>Chat</span>
              </div>
              <button
                type="button"
                className={styles.arrowButton}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setIsChatMenuOpen(!isChatMenuOpen);
                }}
              >
                {isChatMenuOpen ? (
                  <CaretUpIcon size={20} weight="fill" />
                ) : (
                  <CaretDownIcon size={20} weight="fill" />
                )}
              </button>
            </NavLink>
            {isChatMenuOpen && (
              <div className={styles.submenu}>
                <button className={styles.submenuButton}>
                  <TrashIcon size={24} />
                  Zurücksetzen
                </button>

                <button className={styles.submenuButton}>
                  <DownloadSimpleIcon size={24} />
                  Speichern
                </button>
              </div>
            )}
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ""}`
              }
            >
              <div className={styles.wrapper}>
                <ClipboardTextIcon size={28} />
                <span>Dashboard</span>
              </div>
            </NavLink>
          </>
        ) : (
          <NavLink
            to="/onboarding"
            className={({ isActive }) =>
              `${styles.navItem} ${isActive ? styles.active : ""}`
            }
          >
            <div className={styles.wrapper}>
              <RocketIcon size={32} />
              <span>Onboarding </span>
            </div>
          </NavLink>
        )}
        {userData.isAdmin && (
          <>
            <NavLink
              to="/exercise"
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ""}`
              }
            >
              <div className={styles.wrapper}>
                <ArchiveIcon size={28} />
                <span>Übungen </span>
              </div>
              <button
                type="button"
                className={styles.arrowButton}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setIsExerciseMenuOpen(!isExerciseMenuOpen);
                }}
              >
                {isExerciseMenuOpen ? (
                  <CaretUpIcon size={20} weight="fill" />
                ) : (
                  <CaretDownIcon size={20} weight="fill" />
                )}
              </button>
            </NavLink>
            {isExerciseMenuOpen && (
              <div className={styles.submenu}>
                <Link to="/exercise/add" className={styles.submenuButton}>
                  <PlusSquareIcon size={28} />
                  Hinzufügen
                </Link>
              </div>
            )}
          </>
        )}
        <button className={styles.logout}>
          <SignOutIcon size={32} />
          Logout
        </button>
      </nav>
    </aside>
  );
};
