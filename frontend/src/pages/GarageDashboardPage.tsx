import { useEffect, useState } from "react";
import { apiRequest, ApiError } from "../api/client";
import { Appointment, WorkOrderStatus } from "../api/types";
import { AppointmentStatusBadge, WorkOrderStatusBadge } from "../components/StatusBadge";

const WORK_ORDER_STATUSES: WorkOrderStatus[] = [
  "NOT_STARTED",
  "IN_PROGRESS",
  "WAITING_PARTS",
  "COMPLETED",
];

export function GarageDashboardPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [comments, setComments] = useState<Record<string, string>>({});

  async function refresh() {
    const data = await apiRequest<Appointment[]>("/appointments/garage");
    setAppointments(data);
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, []);

  async function handleAppointmentStatus(id: string, status: "CONFIRMED" | "REFUSED" | "COMPLETED") {
    setError(null);
    try {
      await apiRequest(`/appointments/${id}/status`, { method: "PATCH", body: { status } });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur lors de la mise à jour");
    }
  }

  async function handleWorkOrderStatus(workOrderId: string, status: WorkOrderStatus) {
    setError(null);
    try {
      await apiRequest(`/work-orders/${workOrderId}`, {
        method: "PATCH",
        body: { status, comment: comments[workOrderId] || undefined },
      });
      setComments({ ...comments, [workOrderId]: "" });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur lors de la mise à jour du suivi");
    }
  }

  return (
    <div className="page">
      <h1>Tableau de bord du garage</h1>
      {error && <p className="error">{error}</p>}

      <div className="grid">
        {appointments.map((a) => (
          <div key={a.id} className="card">
            <div className="card-header">
              <h3>{a.client.name}</h3>
              <AppointmentStatusBadge status={a.status} />
            </div>
            <p>{new Date(a.requestedDate).toLocaleString("fr-FR")}</p>
            <p>{a.serviceType}</p>
            <p>
              Véhicule : {a.vehicle.brand} {a.vehicle.model} ({a.vehicle.plateNumber})
            </p>
            {a.description && <p>Détails : {a.description}</p>}
            <p>Contact : {a.client.phone ?? a.client.email}</p>

            {a.status === "PENDING" && (
              <div className="actions">
                <button onClick={() => handleAppointmentStatus(a.id, "CONFIRMED")}>Confirmer</button>
                <button className="secondary" onClick={() => handleAppointmentStatus(a.id, "REFUSED")}>
                  Refuser
                </button>
              </div>
            )}

            {a.workOrder && (
              <div className="work-order">
                <p>
                  Suivi des travaux : <WorkOrderStatusBadge status={a.workOrder.status} />
                </p>
                <ul>
                  {a.workOrder.updates.map((u) => (
                    <li key={u.id}>
                      {new Date(u.createdAt).toLocaleString("fr-FR")} — {u.comment ?? "Mise à jour"}
                    </li>
                  ))}
                </ul>

                {a.workOrder.status !== "COMPLETED" && (
                  <div className="actions">
                    <input
                      placeholder="Commentaire (optionnel)"
                      value={comments[a.workOrder.id] ?? ""}
                      onChange={(e) => setComments({ ...comments, [a.workOrder!.id]: e.target.value })}
                    />
                    <select
                      defaultValue=""
                      onChange={(e) => {
                        if (e.target.value) {
                          handleWorkOrderStatus(a.workOrder!.id, e.target.value as WorkOrderStatus);
                          e.target.value = "";
                        }
                      }}
                    >
                      <option value="" disabled>
                        Changer le statut...
                      </option>
                      {WORK_ORDER_STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {appointments.length === 0 && <p>Aucun rendez-vous pour le moment.</p>}
      </div>
    </div>
  );
}
