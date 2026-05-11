import { useState } from "react";
import styles from "./ExerciseForm.module.css";

interface ExerciseFormProps {
  handleSubmit(exercise: {
    title: string;
    goal: string;
    expertise: string;
    emotions: string;
    instructions: string;
    media: string | null;
  }): void;
  editExercise?: {
    id?: number;
    title: string;
    goal: string;
    expertise: string;
    emotions: string;
    instructions: string;
    media: string | null;
  };
}

export const ExerciseForm = ({
  handleSubmit,
  editExercise,
}: ExerciseFormProps) => {
  const [title, setTitle] = useState(editExercise?.title ?? "");
  const [goal, setGoal] = useState(editExercise?.goal ?? "");
  const [expertise, setExpertise] = useState(editExercise?.expertise ?? "");
  const [emotions, setEmotions] = useState(editExercise?.emotions ?? "");
  const [instructions, setInstructions] = useState(
    editExercise?.instructions ?? "",
  );
  const [media, setMedia] = useState(editExercise?.media ?? "");
  const handleExercise = (event: React.SubmitEvent) => {
    event.preventDefault();
    const exercise = {
      title: title,
      goal: goal,
      expertise: expertise,
      emotions: emotions,
      instructions: instructions,
      media: media ? media : null,
    };
    handleSubmit(exercise);
    setTitle("");
    setGoal("");
    setExpertise("");
    setEmotions("");
    setInstructions("");
    setMedia("");
  };
  return (
    <form onSubmit={handleExercise}>
      <div className={styles.inputWrapper}>
        <label htmlFor="title">Titel </label>
        <input
          className={styles.input}
          type="text"
          name="title"
          id="title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
      </div>
      <div className={styles.inputWrapper}>
        <label htmlFor="goal">Ziel der Übung: </label>
        <textarea
          className={styles.text}
          name="goal"
          id="goal"
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
        />
      </div>
      <div className={styles.inputWrapper}>
        <label htmlFor="expertise">Fachwissen: </label>
        <textarea
          className={styles.text}
          name="expertise"
          id="expertise"
          value={expertise}
          onChange={(event) => setExpertise(event.target.value)}
        />
      </div>
      <div className={styles.inputWrapper}>
        <label htmlFor="emotions">Emotionaler Zustand: </label>
        <textarea
          className={styles.text}
          name="emotions"
          id="emotions"
          value={emotions}
          onChange={(event) => setEmotions(event.target.value)}
        />
      </div>

      <div className={styles.inputWrapper}>
        <label htmlFor="instructions">Anleitung: </label>
        <textarea
          className={styles.text}
          name="instructions"
          id="instructions"
          value={instructions}
          onChange={(event) => setInstructions(event.target.value)}
        />
      </div>

      <div className={styles.inputWrapper}>
        <label htmlFor="media">Media Link (optional) </label>
        <input
          className={styles.input}
          type="text"
          name="media"
          id="media"
          value={media}
          onChange={(event) => setMedia(event.target.value)}
        />
      </div>
      <button type="submit">Übung speichern</button>
    </form>
  );
};
