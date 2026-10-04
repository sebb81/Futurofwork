import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./style.css";

class WorkspaceBoundary extends React.Component<
  { children: React.ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <div className="loading">
        <h1>WORK/2030</h1>
        <p role="alert">
          L'interface a rencontré une erreur. Vos données sont conservées sur le
          serveur.
        </p>
        <button
          className="primary-button"
          onClick={() => window.location.reload()}
        >
          Recharger l'environnement
        </button>
        <a href="/">Retour aux groupes</a>
      </div>
    ) : (
      this.props.children
    );
  }
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <WorkspaceBoundary>
      <App />
    </WorkspaceBoundary>
  </React.StrictMode>,
);
