import { FormEvent, useState } from "react";
import { apiRequest, ApiError } from "../api/client";

export function GarageStaffPage() {
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);
    try {
      await apiRequest("/auth/register/staff", { method: "POST", body: form });
      setMessage(`Compte créé pour ${form.name}`);
      setForm({ name: "", email: "", password: "" });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur lors de la création du compte");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page narrow">
      <h1>Ajouter un membre de l'équipe</h1>
      <form className="card form" onSubmit={handleSubmit}>
        <label>Nom complet</label>
        <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />

        <label>Email</label>
        <input
          type="email"
          required
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />

        <label>Mot de passe</label>
        <input
          type="password"
          required
          minLength={6}
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />

        {message && <p>{message}</p>}
        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Création..." : "Créer le compte"}
        </button>
      </form>
    </div>
  );
}
