import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <NavLink to="/" className="brand">
          Mon Garage
        </NavLink>
        <nav className="app-nav">
          {!user && (
            <>
              <NavLink to="/login">Connexion</NavLink>
              <NavLink to="/register">Inscription</NavLink>
            </>
          )}
          {user?.role === "CLIENT" && <NavLink to="/dashboard">Mon espace</NavLink>}
          {(user?.role === "GARAGE_ADMIN" || user?.role === "GARAGE_STAFF") && (
            <NavLink to="/garage">Rendez-vous</NavLink>
          )}
          {user?.role === "GARAGE_ADMIN" && <NavLink to="/garage/staff">Équipe</NavLink>}
          {user && (
            <button className="link-button" onClick={handleLogout}>
              Déconnexion ({user.name})
            </button>
          )}
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">Prise de rendez-vous et suivi des travaux du garage</footer>
    </div>
  );
}
