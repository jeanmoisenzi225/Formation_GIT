import { useEffect, useState } from "react";
import { apiRequest } from "../api/client";
import { Garage } from "../api/types";

export function HomePage() {
  const [garages, setGarages] = useState<Garage[]>([]);
  const [city, setCity] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const query = city ? `?city=${encodeURIComponent(city)}` : "";
    apiRequest<Garage[]>(`/garages${query}`)
      .then((data) => {
        if (!cancelled) setGarages(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [city]);

  return (
    <div className="page">
      <section className="hero">
        <h1>Trouvez et suivez votre garage en Côte d'Ivoire</h1>
        <p>
          Prenez rendez-vous en ligne, suivez l'avancement des travaux sur votre véhicule et
          gardez l'historique de son entretien.
        </p>
      </section>

      <div className="card">
        <label htmlFor="city-filter">Filtrer par ville</label>
        <input
          id="city-filter"
          placeholder="Ex: Abidjan, Bouaké, Yamoussoukro..."
          value={city}
          onChange={(e) => setCity(e.target.value)}
        />
      </div>

      {loading && <p>Chargement des garages...</p>}
      {error && <p className="error">{error}</p>}

      <div className="grid">
        {garages.map((garage) => (
          <div key={garage.id} className="card">
            <h3>{garage.name}</h3>
            <p>{garage.city}</p>
            <p>{garage.address}</p>
            <p>{garage.phone}</p>
          </div>
        ))}
        {!loading && garages.length === 0 && <p>Aucun garage trouvé pour le moment.</p>}
      </div>
    </div>
  );
}
