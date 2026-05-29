import { useEffect, useState } from "react";
import { api } from "../../api/axios";
import styles from "./Exercise.module.css";
import { EyeIcon, PencilSimpleIcon, TrashIcon } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";

export interface ExerciseData {
  id: number;
  title: string;
  goal: string;
  expertise: string;
  emotions: string;
  instructions: string;
  media: string;
}

export const Exercise = () => {
  const [exercises, setExercises] = useState<ExerciseData[]>([]);
  useEffect(() => {
    const getAllExercises = async () => {
      try {
        const response = await api.get("/exercise");
        console.log("Juhuu, das hat geklappt:", response.data);
        setExercises(response.data);
      } catch (error) {
        console.error("Failed to load exercises", error);
      }
    };
    getAllExercises();
  }, []);

  const handleDelete = async (id: number) => {
    const check = window.confirm("Möchtest du diese Übung wirklich löschen?");
    if (!check) return;
    try {
      const response = await api.delete(`/exercise/${id}`);
      const deleteId = response.data;

      setExercises((prev) =>
        prev.filter((exercise) => exercise.id !== deleteId),
      );
      toast.success("Die Übung wurde erfolgreich gelöscht.");
    } catch (error) {
      console.error(error);
      toast.error(
        "Da ist etwas schief gelaufen beim Löschen der Übung. Versuche es später noch einmal!",
      );
    }
  };

  return (
    <main className={styles.exContainer}>
      <h2>Übungen</h2>
      <ul className={styles.exList}>
        {exercises?.map((exercise) => (
          <li key={exercise.id} className={styles.exCard}>
            <div className={styles.cardHeading}>
              <h3>{exercise.title}</h3>
            </div>
            <div className={styles.contentContainer}>
              <p className={styles.content}>{exercise.expertise}</p>
            </div>
            <div className={styles.itemContainer}>
              <Link
                to={`/exercise/${exercise.id}`}
                type="button"
                className={styles.link}
              >
                <EyeIcon size={28} />
              </Link>
              <Link
                to={`/exercise/${exercise.id}`}
                state={{ startInEditMode: true }}
                className={styles.link}
              >
                <PencilSimpleIcon size={28} />
              </Link>
              <button
                type="button"
                className={styles.button}
                onClick={() => handleDelete(exercise.id)}
              >
                <TrashIcon size={28} />
              </button>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
};
