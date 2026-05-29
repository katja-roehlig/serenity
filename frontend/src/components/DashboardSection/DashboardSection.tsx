import { useState } from "react";
import type { DashboardCategory } from "../../pages/Dashboard/Dashboard";
import styles from "./DashboardSection.module.css";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { DashboardModal } from "../DashboardModal/DashboardModal";

import {
  ArmchairIcon,
  ArrowsClockwiseIcon,
  CaretDoubleDownIcon,
  CaretDownIcon,
  CaretUpIcon,
  ClockCounterClockwiseIcon,
  DotsThreeVerticalIcon,
  FlagIcon,
  InfoIcon,
  MapPinLineIcon,
  PencilSimpleLineIcon,
  ShieldCheckIcon,
  TrashIcon,
  TreeStructureIcon,
  VirusIcon,
} from "@phosphor-icons/react";

export const DashboardSection = ({
  title,
  category,
  property,
  handleDelete,
}: {
  title: string;
  category: string;
  property: DashboardCategory[];
  handleDelete: (id: string, category: string) => void;
}) => {
  const hasContent = (property?.length ?? 0) > 0;
  const contentLength = property.length;
  const [isSectionOpen, setIsSectionOpen] = useState(false);
  const [visibleItemCount, setVisibleItemCount] = useState(4);
  const isGridStyle = category === "strengths";
  const displayedItems = property ? property.slice(0, visibleItemCount) : [];
  const [modalOpen, setModalOpen] = useState(false);
  const [activeItem, setActiveItem] = useState<DashboardCategory | null>(null);

  const handleOpenInfo = (item: DashboardCategory) => {
    setActiveItem(item);
    setModalOpen(true);
  };
  const iconDictionary: Record<string, React.ReactNode> = {
    strengths: <ShieldCheckIcon size={28} />,
    pattern: <ArrowsClockwiseIcon size={28} />,
    belief: <TreeStructureIcon size={28} />,
    memory: <ClockCounterClockwiseIcon size={28} />,
    safePlace: <ArmchairIcon size={28} />,
    currentSituation: <MapPinLineIcon size={28} />,
    goal: <FlagIcon size={28} />,
  };
  return (
    <section className={styles.sectionContainer}>
      <div
        className={styles.sectionHeader}
        onClick={() => setIsSectionOpen(!isSectionOpen)}
        role="button"
      >
        <div className={styles.categoryContainer}>
          {iconDictionary[category]}
          <h3>{title}</h3>
          <span className={styles.contentLength}>({contentLength})</span>
        </div>
        {hasContent &&
          (isSectionOpen ? (
            <CaretUpIcon size={20} weight="fill" />
          ) : (
            <CaretDownIcon size={20} weight="fill" />
          ))}
      </div>

      {hasContent && isSectionOpen && (
        <>
          <ul className={isGridStyle ? styles.cardGrid : styles.rowList}>
            {displayedItems?.map((item) => (
              <li
                key={item.id}
                className={`${styles.card} ${isGridStyle ? styles.cardContainer : styles.rowContainer} `}
              >
                <p className={styles.content}>{item.content}</p>
                <DropdownMenu.Root>
                  <DropdownMenu.Trigger asChild>
                    <button>
                      <DotsThreeVerticalIcon
                        size={32}
                        weight="bold"
                        className={styles.icon}
                      />
                    </button>
                  </DropdownMenu.Trigger>
                  <DropdownMenu.Content className={styles.dropdownContent}>
                    <DropdownMenu.Item
                      className={styles.dropdownItem}
                      onSelect={() => handleOpenInfo(item)}
                    >
                      <InfoIcon size={28} />
                      Info
                    </DropdownMenu.Item>

                    <DropdownMenu.Item className={styles.dropdownItem}>
                      <PencilSimpleLineIcon size={28} />
                      Bearbeiten
                    </DropdownMenu.Item>
                    <DropdownMenu.Item
                      className={styles.dropdownItem}
                      onClick={() => handleDelete(item.id, category)}
                    >
                      <TrashIcon size={28} />
                      Löschen
                    </DropdownMenu.Item>
                  </DropdownMenu.Content>
                </DropdownMenu.Root>
              </li>
            ))}

            {contentLength > visibleItemCount && (
              <div className={styles.buttonContainer}>
                <button
                  type="button"
                  className={styles.loadMoreButton}
                  onClick={() =>
                    setVisibleItemCount((prevValue) => prevValue + 4)
                  }
                >
                  <CaretDoubleDownIcon size={20} />
                </button>
              </div>
            )}
          </ul>
        </>
      )}
      <DashboardModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        item={activeItem}
        category={category}
      />
    </section>
  );
};
