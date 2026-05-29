import { useNavigate } from "react-router-dom";
import { api } from "../../api/axios";
import { ExerciseForm } from "../../components/ExerciseForm/ExerciseForm";
import type { ExerciseData } from "../Exercise/Exercise";
import styles from "./AddExercise.module.css";

export const AddExercise = () => {
  const navigate = useNavigate();
  const handleSubmit = async (exercise: ExerciseData) => {
    try {
      const response = await api.post("/exercise", exercise);
      console.log("Erfolg:", response.data);
      alert("Juhuu das hat geklappt");
      navigate("/exercise");
    } catch (error) {
      console.error(error);
      alert("Da ist etwas schief gelaufen beim Speichern der Übung");
    }
  };

  return (
    <main className={styles.exContainer}>
      <h2>Füge eine Übung hinzu</h2>
      <ExerciseForm
        handleSubmit={handleSubmit}
        onCancel={() => navigate("/exercise")}
      />
    </main>
  );
};
