import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest, ApiError } from "../api/client";
import { Garage } from "../api/types";

export function HomePage() {
  const [garage, setGarage] = useState<Garage | null>(null);
  const [notConfigured, setNotConfigured] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<Garage>("/garage")
      .then(setGarage)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) {
          setNotConfigured(true);
        } else {
          setError(err.message);
        }
      });
  }, []);

  if (notConfigured) {
    return (
      <div className="page narrow">
        <h1>Bienvenue</h1>
        <p>Cette application n'a pas encore été configurée pour votre garage.</p>
        <Link to="/setup">
          <button>Configurer mon garage</button>
        </Link>
      </div>
    );
  }

  return (
    <div className="page">
      <section className="hero">
        <h1>{garage ? garage.name : "Votre garage"}</h1>
        <p>
          Prenez rendez-vous en ligne, suivez l'avancement des travaux sur votre véhicule et
          gardez l'historique de son entretien.
        </p>
      </section>

      {error && <p className="error">{error}</p>}

      {garage && (
        <div className="card">
          <p>{garage.city}</p>
          <p>{garage.address}</p>
          <p>{garage.phone}</p>
          {garage.email && <p>{garage.email}</p>}
        </div>
      )}

      <div className="actions">
        <Link to="/register">
          <button>Créer mon compte client</button>
        </Link>
        <Link to="/login">
          <button className="secondary">Se connecter</button>
        </Link>
      </div>
    </div>
  );
}
