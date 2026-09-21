import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../api/client";

// Page de bootstrap : ne fonctionne qu'une seule fois, tant qu'aucun garage
// n'a encore été configuré côté serveur.
export function SetupGaragePage() {
  const { registerGarage } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    garageName: "",
    city: "",
    address: "",
    garagePhone: "",
    garageEmail: "",
    adminName: "",
    adminEmail: "",
    adminPassword: "",
  });

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await registerGarage({ ...form, garageEmail: form.garageEmail || undefined });
      navigate("/garage");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Configuration impossible");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page narrow">
      <h1>Configurer mon garage</h1>
      <p>
        Cette étape ne se fait qu'une seule fois, à l'ouverture de l'application. Elle crée le
        garage et son compte administrateur.
      </p>
      <form className="card form" onSubmit={handleSubmit}>
        <label>Nom du garage</label>
        <input
          required
          value={form.garageName}
          onChange={(e) => setForm({ ...form, garageName: e.target.value })}
        />
        <label>Ville</label>
        <input required value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
        <label>Adresse</label>
        <input
          required
          value={form.address}
          onChange={(e) => setForm({ ...form, address: e.target.value })}
        />
        <label>Téléphone du garage</label>
        <input
          required
          value={form.garagePhone}
          onChange={(e) => setForm({ ...form, garagePhone: e.target.value })}
        />
        <label>Email du garage (optionnel)</label>
        <input
          type="email"
          value={form.garageEmail}
          onChange={(e) => setForm({ ...form, garageEmail: e.target.value })}
        />
        <hr />
        <label>Nom de l'administrateur</label>
        <input
          required
          value={form.adminName}
          onChange={(e) => setForm({ ...form, adminName: e.target.value })}
        />
        <label>Email de l'administrateur</label>
        <input
          type="email"
          required
          value={form.adminEmail}
          onChange={(e) => setForm({ ...form, adminEmail: e.target.value })}
        />
        <label>Mot de passe</label>
        <input
          type="password"
          required
          minLength={6}
          value={form.adminPassword}
          onChange={(e) => setForm({ ...form, adminPassword: e.target.value })}
        />

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Configuration..." : "Configurer le garage"}
        </button>
      </form>
    </div>
  );
}
