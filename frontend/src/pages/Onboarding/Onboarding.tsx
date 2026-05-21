import { useState } from "react";
import { api } from "../../api/axios";
import { useNavigate } from "react-router-dom";

export const Onboarding = () => {
  const userName = localStorage.getItem("userName");
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
  const [ageError, setAgeError] = useState<string>("");
  const [gender, setGender] = useState<string>("");
  const [userStrengths, setUserStrengths] = useState<string[]>([]);
  const [safePlace, setSafePlace] = useState<string>("");
  const navigate = useNavigate();
  const handleAge = (userAge: string) => {
    if (userAge === "") {
      setAge(null);
      setAgeError("");
      return;
    }
    const num = Number(userAge);
    setAge(num);
    if (num < 18) {
      setAgeError("Du musst 18 Jahre alt sein");
    } else if (num > 110) {
      setAgeError(`Bist du wirklich ${num} Jahre alt?`);
    } else setAgeError("");
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
      safe_place: safePlace,
    };
    try {
      const response = await api.post("/onboarding", data);
      console.log("Erfolg:", response.data);
      alert("Juhuu das hat geklappt");
      navigate("/chat");
    } catch (error) {
      console.error(error);
      alert("Da ist etwas schief gelaufen beim Speichern");
    }
  };
  return (
    <main>
      <h1>Huhuu {userName}</h1>
      <p>Schön, dass du da bist</p>
      <p>
        Um gleich richtig gut, für dich da sein zu können, brauchen wir ein paar
        Infos über dich.
      </p>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="age">Wie alt bist du? </label>
          <input
            type="number"
            name="age"
            id="age"
            max="110"
            value={age || ""}
            onChange={(e) => handleAge(e.target.value)}
          />
          {ageError && <p>{ageError}</p>}
        </div>
        <div>
          <p>Wie siehst du dich?</p>
          <label htmlFor="m">
            <input
              type="radio"
              name="gender"
              id="m"
              value="männlich"
              onChange={(e) => setGender(e.target.value)}
            />
            m
          </label>
          <label htmlFor="w">
            <input
              type="radio"
              name="gender"
              id="w"
              value="weiblich"
              onChange={(e) => setGender(e.target.value)}
            />
            w
          </label>
          <label htmlFor="divers">
            <input
              type="radio"
              name="gender"
              id="divers"
              value="divers"
              onChange={(e) => setGender(e.target.value)}
            />
            divers
          </label>
        </div>

        <p>Was kennst du von dir?</p>
        <ul>
          {strengths.map((strength) => (
            <li key={strength}>
              <input
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

        <label htmlFor="safe_place">
          Wo fühlst du dich richtig wohl? Beschreibe den Ort.
        </label>
        <textarea
          name="safePlace"
          id="safePlace"
          value={safePlace}
          onChange={(event) => setSafePlace(event.target.value)}
        ></textarea>
        <button type="submit">Abschicken</button>
      </form>
    </main>
  );
};
