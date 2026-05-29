import { useState } from "react";
import { api } from "../../api/axios";
import { useNavigate, useOutletContext } from "react-router-dom";
import type { UserProfile } from "../../layouts/SerenityLayout";
import styles from "./Onboarding.module.css";
import { HandWavingIcon, RocketLaunchIcon } from "@phosphor-icons/react";

export const Onboarding = () => {
  const [userData, triggerRefresh] =
    useOutletContext<[UserProfile, () => Promise<void>]>();
  const userName = userData.nickname;

  const strengths = [
    "empathisch",
    "kreativ",
    "sportlich",
    "musikalisch",
    "naturverbunden",
    "humorvoll",
    "fürsorglich",
    "feinfühlig",
    "geduldig",
    "ehrlich",
    "neugierig",
    "bewusst",
  ];
  const [age, setAge] = useState<number | "">("");
  const [ageError, setAgeError] = useState<string>("ok");
  const [gender, setGender] = useState<string>("");
  const [userStrengths, setUserStrengths] = useState<string[]>([]);
  const [safePlace, setSafePlace] = useState<string>("");
  const navigate = useNavigate();
  const handleAge = (userAge: string) => {
    const age = userAge.trim();
    if (age === "") {
      setAge("");
      setAgeError("ok");
      return;
    }
    const num = Number(age);
    setAge(num);
    if (num < 18) {
      setAgeError("Du musst 18 Jahre alt sein");
    } else if (num > 110) {
      setAgeError(`Bist du wirklich ${num} Jahre alt?`);
    } else setAgeError("ok");
  };

  const handleStrength = (choosenStrength: string) => {
    if (userStrengths.includes(choosenStrength)) {
      setUserStrengths((prev) =>
        prev.filter((strength) => strength !== choosenStrength),
      );
    } else if (userStrengths.length > 8) {
      alert("Wähle maximal acht Eigenschaften");
    } else {
      setUserStrengths((prev) => [...prev, choosenStrength]);
    }
  };

  const handleSubmit = async (event: React.SubmitEvent) => {
    event.preventDefault();
    const data = {
      age: age,
      gender: gender ? gender : null,
      strengths: userStrengths,
      safe_place: safePlace.trim(),
    };
    try {
      const response = await api.post("/onboarding", data);
      console.log("Erfolg:", response.data);
      await triggerRefresh();
      alert("Juhuu das hat geklappt");
      navigate("/chat");
    } catch (error) {
      console.error(error);
      alert("Da ist etwas schief gelaufen beim Speichern");
    }
  };
  return (
    <main className={styles.onboardingContainer}>
      <h2 className={styles.greeting}>
        Huhuu {userName} <HandWavingIcon size={32} />
      </h2>
      <p className={styles.greetingText}>
        Schön, dass du da bist!
        <br />
        Lass uns zunächst ein paar Infos sammeln, damit Serenity gleich weiß,
        wer du bist.
      </p>
      <form onSubmit={handleSubmit}>
        <section className={styles.basicInformation}>
          <div className={styles.ageContainer}>
            <label htmlFor="age">
              <h3 className={styles.question}>Wie alt bist du?</h3>
            </label>
            <input
              className={`${styles.ageInput} ${age ? styles.hasContent : ""}`}
              type="number"
              name="age"
              id="age"
              max="110"
              value={age || ""}
              onChange={(e) => handleAge(e.target.value)}
            />
            <p
              className={`${ageError === "ok" ? styles.noAgeError : styles.ageError}`}
            >
              {ageError}
            </p>
          </div>
          <div>
            <h3 className={styles.question}>Wie siehst du dich?</h3>
            <div className={styles.genderContainer}>
              <label
                className={`${styles.selectableCard} ${styles.genderCard} ${gender === "männlich" ? styles.active : ""}`}
              >
                <input
                  className={styles.hiddenElement}
                  type="radio"
                  name="gender"
                  id="m"
                  value="männlich"
                  onChange={(e) => setGender(e.target.value)}
                />
                männlich
              </label>
              <label
                htmlFor="w"
                className={`${styles.selectableCard} ${styles.genderCard} ${gender === "weiblich" ? styles.active : ""}`}
              >
                <input
                  className={styles.hiddenElement}
                  type="radio"
                  name="gender"
                  id="w"
                  value="weiblich"
                  onChange={(e) => setGender(e.target.value)}
                />
                weiblich
              </label>
              <label
                htmlFor="divers"
                className={`${styles.selectableCard} ${styles.genderCard} ${gender === "divers" ? styles.active : ""}`}
              >
                <input
                  className={styles.hiddenElement}
                  type="radio"
                  name="gender"
                  id="divers"
                  value="divers"
                  onChange={(e) => setGender(e.target.value)}
                />
                divers
              </label>
            </div>
          </div>
        </section>
        <section className={styles.strengthsContainer}>
          <div className={styles.subhintWrapper}>
            <h3 className={styles.question}>Was kennst du von dir?</h3>
            <p className={styles.subHint}>Wähle bis zu 8 Eigenschaften aus</p>
          </div>
          <ul className={styles.strengthsList}>
            {strengths.map((strength) => (
              <li
                key={strength}
                className={`${styles.selectableCard} ${userStrengths.includes(strength) ? styles.active : ""}`}
              >
                <input
                  className={styles.hiddenElement}
                  type="checkbox"
                  name=""
                  id={strength}
                  checked={userStrengths.includes(strength)}
                  onChange={() => handleStrength(strength)}
                />
                <label htmlFor={strength}>{strength}</label>
              </li>
            ))}
          </ul>
        </section>
        <section className={styles.safeContainer}>
          <label htmlFor="safe_place">
            <h3 className={styles.question}>
              Wo fühlst du dich richtig wohl? Beschreibe den Ort.
            </h3>
          </label>
          <textarea
            className={`${styles.textareaInput} ${safePlace ? styles.hasContent : ""}`}
            name="safePlace"
            id="safePlace"
            value={safePlace}
            onChange={(event) => setSafePlace(event.target.value)}
            placeholder="z.B. Ein ruhiger Wald, mein Bett bei Regen, das Meer..."
          ></textarea>
        </section>
        <div className={styles.buttonContainer}>
          <button type="submit" className={styles.button}>
            <RocketLaunchIcon size={32} />
            Los geht´s
          </button>
        </div>
      </form>
    </main>
  );
};
