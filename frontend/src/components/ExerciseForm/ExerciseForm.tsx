import { useState } from "react";
import styles from "./ExerciseForm.module.css";
import { ArrowUDownLeftIcon, UploadSimpleIcon } from "@phosphor-icons/react";

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
  onCancel(): void;
}

export const ExerciseForm = ({
  handleSubmit,
  editExercise,
  onCancel,
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
        <label htmlFor="title" className={styles.label}>
          <h3>Titel </h3>
        </label>
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
        <label htmlFor="goal" className={styles.label}>
          <h3>Ziel der Übung:</h3>
        </label>
        <textarea
          className={styles.text}
          name="goal"
          id="goal"
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
        />
      </div>
      <div className={styles.inputWrapper}>
        <label htmlFor="expertise" className={styles.label}>
          <h3>Fachwissen:</h3>{" "}
        </label>
        <textarea
          className={styles.text}
          name="expertise"
          id="expertise"
          value={expertise}
          onChange={(event) => setExpertise(event.target.value)}
        />
      </div>
      <div className={styles.inputWrapper}>
        <label htmlFor="emotions" className={styles.label}>
          <h3>Emotionaler Zustand: </h3>{" "}
        </label>
        <textarea
          className={styles.text}
          name="emotions"
          id="emotions"
          value={emotions}
          onChange={(event) => setEmotions(event.target.value)}
        />
      </div>

      <div className={styles.inputWrapper}>
        <label htmlFor="instructions" className={styles.label}>
          <h3>Anleitung</h3>{" "}
        </label>
        <textarea
          className={styles.text}
          name="instructions"
          id="instructions"
          value={instructions}
          onChange={(event) => setInstructions(event.target.value)}
        />
      </div>

      <div className={styles.inputWrapper}>
        <label htmlFor="media" className={styles.label}>
          <h3>Media Link (optional)</h3>
        </label>
        <input
          className={styles.input}
          type="text"
          name="media"
          id="media"
          value={media}
          onChange={(event) => setMedia(event.target.value)}
        />
      </div>
      <div className={styles.buttonContainer}>
        <button className={styles.exButton} type="button" onClick={onCancel}>
          <ArrowUDownLeftIcon size={28} />
          Abbrechen
        </button>
        <button className={styles.exButton} type="submit">
          <UploadSimpleIcon size={28} />
          Speichern
        </button>
      </div>
    </form>
  );
};
