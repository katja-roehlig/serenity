import { api } from "../../api/axios";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import styles from "./Register.module.css";
import { SignInIcon } from "@phosphor-icons/react";
import toast from "react-hot-toast";

export const Register = () => {
  const [name, setName] = useState("");
  const [mail, setMail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const handleSubmit = async (event: React.SubmitEvent) => {
    event.preventDefault();
    try {
      const response = await api.post("/register", {
        nickname: name,
        mail: mail,
        password: password,
      });
      console.log("Erfolg:", response.data);
      toast.success("Juhuu, das hat geklappt 🙃");
      navigate("/login");
    } catch (error) {
      console.error(error);
      toast.error("Da ist etwas schief gelaufen. Versuche es noch einmal!");
    }
  };
  return (
    <div className={styles.registerContainer}>
      <form onSubmit={handleSubmit} className={styles.formContainer}>
        <div className={styles.inputContainer}>
          <label htmlFor="name" className={styles.label}>
            Wie möchtest du genannt werden?{" "}
          </label>
          <input
            className={styles.input}
            type="text"
            name="name"
            id="name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </div>
        <div className={styles.inputContainer}>
          <label htmlFor="mail" className={styles.label}>
            Deine Mailadresse:{" "}
          </label>
          <input
            className={styles.input}
            type="email"
            name="mail"
            id="mail"
            value={mail}
            onChange={(event) => setMail(event.target.value)}
          />
        </div>
        <div className={styles.inputContainer}>
          <label htmlFor="password" className={styles.label}>
            Dein Passwort:{" "}
          </label>
          <input
            className={styles.input}
            type="password"
            name="password"
            id="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        <button type="submit" className={styles.button}>
          Registrieren
        </button>
      </form>
      <div className={styles.linkContainer}>
        <p>Schon ein Profil? </p>
        <SignInIcon size={32} className={styles.signIn} />
        <Link to="/Login" className={styles.link}>
          Login
        </Link>
      </div>
    </div>
  );
};
