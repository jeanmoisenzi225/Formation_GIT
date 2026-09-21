import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../api/client";

type Tab = "client" | "garage";

export function RegisterPage() {
  const { registerClient, registerGarage } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("client");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [clientForm, setClientForm] = useState({ name: "", email: "", phone: "", password: "" });
  const [garageForm, setGarageForm] = useState({
    garageName: "",
    city: "",
    address: "",
    garagePhone: "",
    garageEmail: "",
    adminName: "",
    adminEmail: "",
    adminPassword: "",
  });

  async function handleClientSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await registerClient(clientForm);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Inscription impossible");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleGarageSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await registerGarage({
        ...garageForm,
        garageEmail: garageForm.garageEmail || undefined,
      });
      navigate("/garage");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Inscription impossible");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page narrow">
      <h1>Inscription</h1>
      <div className="tabs">
        <button className={tab === "client" ? "tab active" : "tab"} onClick={() => setTab("client")}>
          Je suis client
        </button>
        <button className={tab === "garage" ? "tab active" : "tab"} onClick={() => setTab("garage")}>
          Je gère un garage
        </button>
      </div>

      {tab === "client" ? (
        <form className="card form" onSubmit={handleClientSubmit}>
          <label>Nom complet</label>
          <input
            required
            value={clientForm.name}
            onChange={(e) => setClientForm({ ...clientForm, name: e.target.value })}
          />
          <label>Email</label>
          <input
            type="email"
            required
            value={clientForm.email}
            onChange={(e) => setClientForm({ ...clientForm, email: e.target.value })}
          />
          <label>Téléphone</label>
          <input
            value={clientForm.phone}
            onChange={(e) => setClientForm({ ...clientForm, phone: e.target.value })}
          />
          <label>Mot de passe</label>
          <input
            type="password"
            required
            minLength={6}
            value={clientForm.password}
            onChange={(e) => setClientForm({ ...clientForm, password: e.target.value })}
          />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? "Création..." : "Créer mon compte client"}
          </button>
        </form>
      ) : (
        <form className="card form" onSubmit={handleGarageSubmit}>
          <label>Nom du garage</label>
          <input
            required
            value={garageForm.garageName}
            onChange={(e) => setGarageForm({ ...garageForm, garageName: e.target.value })}
          />
          <label>Ville</label>
          <input
            required
            value={garageForm.city}
            onChange={(e) => setGarageForm({ ...garageForm, city: e.target.value })}
          />
          <label>Adresse</label>
          <input
            required
            value={garageForm.address}
            onChange={(e) => setGarageForm({ ...garageForm, address: e.target.value })}
          />
          <label>Téléphone du garage</label>
          <input
            required
            value={garageForm.garagePhone}
            onChange={(e) => setGarageForm({ ...garageForm, garagePhone: e.target.value })}
          />
          <label>Email du garage (optionnel)</label>
          <input
            type="email"
            value={garageForm.garageEmail}
            onChange={(e) => setGarageForm({ ...garageForm, garageEmail: e.target.value })}
          />
          <hr />
          <label>Nom de l'administrateur</label>
          <input
            required
            value={garageForm.adminName}
            onChange={(e) => setGarageForm({ ...garageForm, adminName: e.target.value })}
          />
          <label>Email de l'administrateur</label>
          <input
            type="email"
            required
            value={garageForm.adminEmail}
            onChange={(e) => setGarageForm({ ...garageForm, adminEmail: e.target.value })}
          />
          <label>Mot de passe</label>
          <input
            type="password"
            required
            minLength={6}
            value={garageForm.adminPassword}
            onChange={(e) => setGarageForm({ ...garageForm, adminPassword: e.target.value })}
          />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? "Création..." : "Créer le compte garage"}
          </button>
        </form>
      )}
    </div>
  );
}
