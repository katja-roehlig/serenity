import type { DashboardCategory } from "../../pages/Dashboard/Dashboard";

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
  return (
    <section>
      <h2>{title}</h2>

      {(property?.length ?? 0) === 0 && <p>Noch keine Daten vorhanden</p>}
      {property?.length > 0 && (
        <ul>
          {property?.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => handleDelete(item.id, category)}
              >
                X
              </button>
              <p>{item.content}</p>
              {item.expiresAt && <p>{item.expiresAt}</p>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};
