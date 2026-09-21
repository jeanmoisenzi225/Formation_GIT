import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiRequest } from "../api/client";
import { Appointment } from "../api/types";
import { AppointmentStatusBadge, WorkOrderStatusBadge } from "../components/StatusBadge";

export function VehicleHistoryPage() {
  const { id } = useParams<{ id: string }>();
  const [history, setHistory] = useState<Appointment[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    apiRequest<Appointment[]>(`/vehicles/${id}/history`)
      .then(setHistory)
      .catch((err) => setError(err.message));
  }, [id]);

  return (
    <div className="page">
      <h1>Historique du véhicule</h1>
      {error && <p className="error">{error}</p>}
      <div className="grid">
        {history.map((a) => (
          <div key={a.id} className="card">
            <div className="card-header">
              <h3>{a.garage.name}</h3>
              <AppointmentStatusBadge status={a.status} />
            </div>
            <p>{new Date(a.requestedDate).toLocaleString("fr-FR")}</p>
            <p>{a.serviceType}</p>
            {a.workOrder && (
              <div className="work-order">
                <p>
                  Travaux : <WorkOrderStatusBadge status={a.workOrder.status} />
                  {a.workOrder.costEstimate ? ` — Coût estimé : ${a.workOrder.costEstimate} FCFA` : ""}
                </p>
                <ul>
                  {a.workOrder.updates.map((u) => (
                    <li key={u.id}>
                      {new Date(u.createdAt).toLocaleString("fr-FR")} — {u.comment ?? "Mise à jour"}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
        {history.length === 0 && <p>Aucun historique pour ce véhicule.</p>}
      </div>
    </div>
  );
}
