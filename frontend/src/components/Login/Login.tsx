import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/axios";
import styles from "./Login.module.css";
import toast from "react-hot-toast";
import { EyeIcon, EyeSlashIcon } from "@phosphor-icons/react";

export const Login = () => {
  const [mail, setMail] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (event: React.SubmitEvent) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append("username", mail); // Wichtig: FastAPI erwartet'username'
    formData.append("password", password);

    try {
      const response = await api.post("/login", formData);
      const token: string = response.data.accessToken;
      // const nickname: string = response.data.nickname;
      localStorage.setItem("token", token);
      //localStorage.setItem("userName", nickname);
      console.log("Erfolg:", response.data);
      if (response.data.hasOnboarding === true) {
        navigate("/chat");
      } else {
        navigate("/onboarding");
      }
      toast.success("Yeah - gleich geht es los!");
    } catch (error) {
      console.error("Login fehlgeschlagen:", error);
      toast.error("Da ist etwas schief gelaufen");
    }
  };
  return (
    <div className={styles.loginContainer}>
      <p className={styles.greeting}>
        Schön, <br />
        dass du da bist!
      </p>
      <form onSubmit={handleSubmit} className={styles.formContainer}>
        <div className={styles.inputContainer}>
          <label className={styles.label} htmlFor="mail">
            Deine Mailadresse:
          </label>
          <input
            className={styles.input}
            autoComplete="one-time-code"
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
          <div className={styles.passwordContainer}>
            <input
              className={styles.input}
              type={`${showPassword ? "text" : "password"}`}
              name="password"
              id="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <button
              type="button"
              className={styles.passwordButton}
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeSlashIcon size={24} />
              ) : (
                <EyeIcon size={24} />
              )}
            </button>
          </div>
        </div>
        <button type="submit" className={styles.button}>
          Los geht´s
        </button>
      </form>
    </div>
  );
};
