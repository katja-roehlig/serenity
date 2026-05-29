import { useLocation, useNavigate, useParams } from "react-router-dom";
import styles from "./ExerciseShow.module.css";
import { api } from "../../api/axios";
import { useEffect, useState } from "react";
import { ExerciseForm } from "../../components/ExerciseForm/ExerciseForm";
import { PencilSimpleLineIcon } from "@phosphor-icons/react";
import type { ExerciseData } from "../Exercise/Exercise";
import toast from "react-hot-toast";

export const ExerciseShow = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [exercise, setExercise] = useState<ExerciseData | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(
    location.state?.startInEditMode || false,
  );
  const getSelectedExercise = async () => {
    try {
      const response = await api.get(`/exercise/${id}`);
      setExercise(response.data);
    } catch (error) {
      console.error("Failed to load exercise", error);
    }
  };
  useEffect(() => {
    getSelectedExercise();
  }, [id]);

  const handleUpdate = async (updatedData: ExerciseData) => {
    try {
      const response = await api.put(`/exercise/${id}`, updatedData);
      console.log("Erfolg:", response.data);
      toast.success("Die Übung wurde geändert.");
      setExercise(response.data);
      setIsEditing(false);
    } catch (error) {
      console.error("Failed to update exercise", error);
      toast.error("Da ist etwas schief gelaufen beim Speichern der Übung");
    }
  };
  if (!exercise) return <div>Übung wird geladen...</div>;
  return (
    <main className={styles.exContainer}>
      {isEditing ? (
        <>
          <h2>Bearbeite eine Übung</h2>
          <ExerciseForm
            handleSubmit={handleUpdate}
            editExercise={exercise}
            onCancel={() => {
              setIsEditing(false);
              navigate("/exercise");
            }}
          />
        </>
      ) : (
        <>
          <h2>{exercise.title}</h2>
          <section className={styles.section}>
            <div className={styles.sectionHeading}>
              <h3>Ziel der Übung</h3>
            </div>
            <p className={styles.content}>{exercise.goal}</p>
          </section>
          <section className={styles.section}>
            <div className={styles.sectionHeading}>
              <h3>Fachwissen</h3>
            </div>
            <p className={styles.content}>{exercise.expertise}</p>
          </section>
          <section className={styles.section}>
            <div className={styles.sectionHeading}>
              <h3>Emotionaler Zustand</h3>
            </div>
            <p className={styles.content}>{exercise.emotions}</p>
          </section>
          <section className={styles.section}>
            <div className={styles.sectionHeading}>
              <h3>Anleitung</h3>
            </div>
            <p className={styles.content}>{exercise.instructions}</p>
          </section>
          <section className={styles.section}>
            <div className={styles.sectionHeading}>
              <h3>Media Link</h3>
            </div>
            {exercise.media ? (
              <p className={styles.content}>{exercise.media}</p>
            ) : (
              <p className={`${styles.content} ${styles.noData}`}>
                Noch keine Daten...
              </p>
            )}
          </section>
          <div className={styles.buttonContainer}>
            <button
              className={styles.editButton}
              type="button"
              onClick={() => setIsEditing(true)}
            >
              <PencilSimpleLineIcon size={28} />
              Übung bearbeiten
            </button>
            #
          </div>
        </>
      )}
    </main>
  );
};
