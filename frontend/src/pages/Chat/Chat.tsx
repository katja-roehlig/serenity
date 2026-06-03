import { useEffect, useRef, useState } from "react";
import { api } from "../../api/axios";
import styles from "./Chat.module.css";
import { ArrowFatUpIcon } from "@phosphor-icons/react";
import { useOutletContext } from "react-router-dom";
import type { UserProfile } from "../../layouts/SerenityLayout";
import toast from "react-hot-toast";
import ReactMarkdown from "react-markdown";

type ChatItem = { id: string; role: string; content: string };

export const Chat = () => {
  const [userData, _getUserProfile] =
    useOutletContext<[UserProfile, () => void]>();
  const userName = userData.nickname;
  const [messages, setMessages] = useState<ChatItem[]>(() => {
    const savedChat = localStorage.getItem(`Chat ${userData.id}`);
    if (savedChat) return JSON.parse(savedChat) as ChatItem[];
    return [
      {
        id: Date.now().toString(),
        role: "assistant",
        content: `Hey **${userName}**!  \n\nIch bin Serenity, dein persönlicher Coach.  \nWie geht es dir heute?`,
      },
    ];
  });
  const [content, setContent] = useState("");
  const [isWaiting, setIsWaiting] = useState(false);
  const cursorRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const handleResetChat = () => {
      setMessages([
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `Hey **${userName}**!  \n\nWas kann ich heute für dich tun?`,
        },
      ]);
    };
    window.addEventListener("resetChat", handleResetChat);
    // eine Funktion nach return im useEffect() wird erst beim Verlassen der Seite ausgeführt
    return () => {
      window.removeEventListener("reset", handleResetChat);
    };
  }, [userName]);
  const handleChat = (event: React.SubmitEvent) => {
    setIsWaiting(true);
    event.preventDefault();
    if (!content.trim()) return;
    const newMessage = {
        id: Date.now().toString(),
        role: "user",
        content: content,
      },
      updatedMessages = [...messages, newMessage];
    setMessages(updatedMessages);
    localStorage.setItem(
      `Chat ${userData.id}`,
      JSON.stringify(updatedMessages),
    );
    setContent("");
    send_data(updatedMessages, newMessage);
  };

  const send_data = async (messages: ChatItem[], newMessage: ChatItem) => {
    if (messages.length <= 1) return;
    try {
      const response = await api.post("/chat", newMessage);
      console.log("Juhuu, das hat geklappt:", response.data);

      if (response.data && response.data.content) {
        const aiMessage = { ...response.data, id: Date.now().toString() };
        const allMessages = [...messages, aiMessage];
        localStorage.setItem(
          `Chat ${userData.id}`,
          JSON.stringify(allMessages),
        );
        setMessages(allMessages);
      } else {
        console.error("Error: The response from the server is incomplete");
        toast.error(
          "Serenity ist gerade sprachlos. Bitte versuche es noch einmal!",
        );
      }
    } catch (error) {
      console.error(error);
      toast.error("Da ist etwas schief gelaufen. Versuche es noch einmal!");
    } finally {
      setIsWaiting(false);
      cursorRef.current?.focus();
    }
  };

  return (
    <main className={styles.chatContainer}>
      <div className={styles.layoutWrapper}>
        <ul className={styles.messageList}>
          {messages?.map((message) => (
            <li key={message.id}>
              <div
                className={`${styles.chatBubble}
             ${message.role == "user" ? styles.userChat : styles.kiChat}`}
              >
                {message.role === "user" ? (
                  message.content
                ) : (
                  <div className={styles.markdownContent}>
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </li>
          ))}
          {<div ref={messagesEndRef} />}
        </ul>
      </div>
      <form onSubmit={handleChat} className={styles.formContainer}>
        <label htmlFor="content" className={styles.label}>
          User Message
        </label>
        <div className={styles.writingContainer}>
          <div className={styles.warning}>
            <textarea
              className={styles.input}
              name="content"
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              onKeyDown={(e) => {
                // Wenn Enter gedrückt wird OHNE die Shift-Taste, wird abgeschickt
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  e.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Schreib etwas ..."
              autoFocus
            ></textarea>
            <button
              type="submit"
              disabled={isWaiting ? true : false}
              className={styles.submitButton}
            >
              <ArrowFatUpIcon size={24} />
            </button>
          </div>
        </div>
      </form>
    </main>
  );
};
