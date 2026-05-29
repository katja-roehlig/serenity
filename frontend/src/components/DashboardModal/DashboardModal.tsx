import * as Dialog from "@radix-ui/react-dialog";
import styles from "./DashboardModal.module.css";
import type { DashboardCategory } from "../../pages/Dashboard/Dashboard";

interface DashboardModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  item: DashboardCategory | null;
  category: string;
}

export function DashboardModal({
  open,
  onOpenChange,
  item,
  category,
}: DashboardModalProps) {
  if (!item) return null;
  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleDateString("de-DE", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  };
  const isSmallInfo = category === "safePlace" || category === "memory";

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className={styles.dialogOverlay} />
        <Dialog.Content
          className={`${styles.dialogContent} ${isSmallInfo ? styles.smallContent : ""}`}
        >
          <Dialog.Title className={styles.visuallyHidden}>
            <p>Details</p>
          </Dialog.Title>
          {category === "currentSituation" && (
            <>
              <p>
                Diese Information wird am{" "}
                <strong>{formatDate(item.expiresAt)}</strong>
                gelöscht.
              </p>
              <p>Um sie zu behalten, speichere sie als Erinnerung</p>
              <button>Speichern</button>
            </>
          )}
          {category !== "currentSituation" && !isSmallInfo && (
            <>
              <p>Erfasst am: {formatDate(item.createdAt)}</p>
              <p>Sie wurde in folgenden Zusammenhängen von Serenity erfasst:</p>
              <p>{item.reasoning}</p>
            </>
          )}
          {isSmallInfo && (
            <div className={styles.smallInfoWrapper}>
              <p>
                📍 Erfasst am: <strong>{formatDate(item.createdAt!)}</strong>
              </p>
            </div>
          )}
          <Dialog.Close asChild>
            <button className={styles.closeButton}>Schließen</button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
