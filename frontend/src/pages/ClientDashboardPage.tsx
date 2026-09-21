import { FormEvent, useEffect, useState } from "react";
import { apiRequest, ApiError } from "../api/client";
import { Appointment, Garage, Vehicle } from "../api/types";
import { AppointmentStatusBadge, WorkOrderStatusBadge } from "../components/StatusBadge";

export function ClientDashboardPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [garages, setGarages] = useState<Garage[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [newVehicle, setNewVehicle] = useState({ brand: "", model: "", plateNumber: "", year: "" });
  const [booking, setBooking] = useState({
    garageId: "",
    vehicleId: "",
    requestedDate: "",
    serviceType: "",
    description: "",
  });
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    const [v, g, a] = await Promise.all([
      apiRequest<Vehicle[]>("/vehicles"),
      apiRequest<Garage[]>("/garages"),
      apiRequest<Appointment[]>("/appointments/mine"),
    ]);
    setVehicles(v);
    setGarages(g);
    setAppointments(a);
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, []);

  async function handleAddVehicle(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await apiRequest<Vehicle>("/vehicles", {
        method: "POST",
        body: {
          brand: newVehicle.brand,
          model: newVehicle.model,
          plateNumber: newVehicle.plateNumber,
          year: newVehicle.year ? Number(newVehicle.year) : undefined,
        },
      });
      setNewVehicle({ brand: "", model: "", plateNumber: "", year: "" });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur lors de l'ajout du véhicule");
    }
  }

  async function handleBook(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await apiRequest("/appointments", {
        method: "POST",
        body: {
          ...booking,
          requestedDate: new Date(booking.requestedDate).toISOString(),
        },
      });
      setBooking({ garageId: "", vehicleId: "", requestedDate: "", serviceType: "", description: "" });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur lors de la prise de rendez-vous");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancel(id: string) {
    setError(null);
    try {
      await apiRequest(`/appointments/${id}/status`, { method: "PATCH", body: { status: "CANCELLED" } });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur lors de l'annulation");
    }
  }

  return (
    <div className="page">
      <h1>Mon espace client</h1>
      {error && <p className="error">{error}</p>}

      <section>
        <h2>Mes véhicules</h2>
        <div className="grid">
          {vehicles.map((v) => (
            <div key={v.id} className="card">
              <h3>
                {v.brand} {v.model}
              </h3>
              <p>Plaque : {v.plateNumber}</p>
              {v.year && <p>Année : {v.year}</p>}
              <a href={`/vehicles/${v.id}/history`}>Voir l'historique</a>
            </div>
          ))}
        </div>

        <form className="card form" onSubmit={handleAddVehicle}>
          <h3>Ajouter un véhicule</h3>
          <label>Marque</label>
          <input
            required
            value={newVehicle.brand}
            onChange={(e) => setNewVehicle({ ...newVehicle, brand: e.target.value })}
          />
          <label>Modèle</label>
          <input
            required
            value={newVehicle.model}
            onChange={(e) => setNewVehicle({ ...newVehicle, model: e.target.value })}
          />
          <label>Plaque d'immatriculation</label>
          <input
            required
            value={newVehicle.plateNumber}
            onChange={(e) => setNewVehicle({ ...newVehicle, plateNumber: e.target.value })}
          />
          <label>Année (optionnel)</label>
          <input
            type="number"
            value={newVehicle.year}
            onChange={(e) => setNewVehicle({ ...newVehicle, year: e.target.value })}
          />
          <button type="submit">Ajouter</button>
        </form>
      </section>

      <section>
        <h2>Prendre rendez-vous</h2>
        <form className="card form" onSubmit={handleBook}>
          <label>Garage</label>
          <select
            required
            value={booking.garageId}
            onChange={(e) => setBooking({ ...booking, garageId: e.target.value })}
          >
            <option value="">Choisir un garage</option>
            {garages.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name} — {g.city}
              </option>
            ))}
          </select>

          <label>Véhicule</label>
          <select
            required
            value={booking.vehicleId}
            onChange={(e) => setBooking({ ...booking, vehicleId: e.target.value })}
          >
            <option value="">Choisir un véhicule</option>
            {vehicles.map((v) => (
              <option key={v.id} value={v.id}>
                {v.brand} {v.model} ({v.plateNumber})
              </option>
            ))}
          </select>

          <label>Date et heure souhaitées</label>
          <input
            type="datetime-local"
            required
            value={booking.requestedDate}
            onChange={(e) => setBooking({ ...booking, requestedDate: e.target.value })}
          />

          <label>Type de service</label>
          <input
            required
            placeholder="Vidange, freins, révision..."
            value={booking.serviceType}
            onChange={(e) => setBooking({ ...booking, serviceType: e.target.value })}
          />

          <label>Description (optionnel)</label>
          <textarea
            value={booking.description}
            onChange={(e) => setBooking({ ...booking, description: e.target.value })}
          />

          <button type="submit" disabled={submitting}>
            {submitting ? "Envoi..." : "Demander le rendez-vous"}
          </button>
        </form>
      </section>

      <section>
        <h2>Mes rendez-vous</h2>
        <div className="grid">
          {appointments.map((a) => (
            <div key={a.id} className="card">
              <div className="card-header">
                <h3>{a.garage.name}</h3>
                <AppointmentStatusBadge status={a.status} />
              </div>
              <p>{new Date(a.requestedDate).toLocaleString("fr-FR")}</p>
              <p>{a.serviceType}</p>
              <p>
                Véhicule : {a.vehicle.brand} {a.vehicle.model} ({a.vehicle.plateNumber})
              </p>

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
                </div>
              )}

              {(a.status === "PENDING" || a.status === "CONFIRMED") && (
                <button className="secondary" onClick={() => handleCancel(a.id)}>
                  Annuler
                </button>
              )}
            </div>
          ))}
          {appointments.length === 0 && <p>Aucun rendez-vous pour le moment.</p>}
        </div>
      </section>
    </div>
  );
}
