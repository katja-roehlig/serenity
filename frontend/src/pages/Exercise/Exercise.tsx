import { useEffect, useRef, useState } from "react";
import { api } from "../../api/axios";
import styles from "./Exercise.module.css";
import { ExerciseForm } from "../../components/ExerciseForm/ExerciseForm";

interface ExerciseData {
  id?: number;
  title: string;
  goal: string;
  expertise: string;
  emotions: string;
  instructions: string;
  media: string;
}

export const Exercise = () => {
  const [exercises, setExercises] = useState<ExerciseData[]>([]);
  const [editExercise, setEditExercise] = useState<ExerciseData | null>(null);
  const showDialog = useRef(null);
  useEffect(() => {
    const getAllExercises = async () => {
      try {
        const response = await api.get("/exercise");
        console.log("Juhuu, das hat geklappt:", response.data);
        setExercises(response.data);
      } catch (error) {
        console.error(error);
        alert("Da ist etwas schief gelaufen.");
      }
    };
    getAllExercises();
  }, []);

  useEffect(() => {
    if (editExercise) {
      showDialog.current.showModal();
    } else {
      showDialog.current.close();
    }
  }, [editExercise]);

  const handleDelete = async (id: number) => {
    const check = window.confirm("Möchtest du diese Übung wirklich löschen?");
    if (!check) return;
    try {
      const response = await api.delete(`/exercise/${id}`);
      if (!response) {
        alert("Oh, das hat nicht geklappt. Versuche es noch einmal.");
        return;
      }
      alert("Juhuu das hat geklappt");
      const deleteId = response.data;

      setExercises((prev) =>
        prev.filter((exercise) => exercise.id !== deleteId),
      );
    } catch (error) {
      console.error(error);
      alert("Da ist etwas schief gelaufen beim Speichern der Übung");
    }
  };

  const handleUpdate = async (exercise: ExerciseData) => {
    console.log("Okay, here we go!");
    console.log(exercise);
    try {
      const response = await api.put(`/exercise/${editExercise?.id}`, exercise);
      console.log("Erfolg:", response.data);
      alert("Juhuu das hat geklappt");
      setEditExercise(null);
      const updatedEx = response.data;
      setExercises((prev) =>
        prev.map((exercise) => {
          if (exercise.id === updatedEx.id) {
            return updatedEx;
          } else {
            return exercise;
          }
        }),
      );
    } catch (error) {
      console.error(error);
      alert("Da ist etwas schief gelaufen beim Speichern der Übung");
    }
  };

  return (
    <main>
      <ul className={styles.list}>
        {exercises?.map((exercise, index) => (
          <li
            key={exercise.id}
            className={`${index % 2 === 0 ? styles.oddCard : styles.evenCard}`}
          >
            <h3>{exercise.title}</h3>
            <p className={styles.content}>{exercise.expertise}</p>
            <div className={styles.buttonContainer}>
              <button type="button" onClick={() => setEditExercise(exercise)}>
                Bearbeiten
              </button>
              <button type="button" onClick={() => handleDelete(exercise?.id)}>
                Löschen
              </button>
            </div>
          </li>
        ))}
      </ul>

      <dialog ref={showDialog} className={styles.editDialog}>
        {editExercise && (
          <>
            <h2>Bearbeite eine Übung</h2>
            <ExerciseForm
              handleSubmit={handleUpdate}
              editExercise={editExercise}
            />
            <button type="button" onClick={() => setEditExercise(null)}>
              Abbrechen
            </button>
          </>
        )}
      </dialog>
    </main>
  );
};
