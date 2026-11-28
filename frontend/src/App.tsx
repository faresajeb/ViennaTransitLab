
import { useEffect, useState } from "react";
import TransportMap from "./components/TransportMap";
import { getStops } from "./services/api";
import type { TransportStop } from "./types/transport";
import "./App.css";

const filters = ["all", "metro", "tram", "bus"] as const;

type Filter = (typeof filters)[number];

function App() {
  const [stops, setStops] = useState<TransportStop[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [selectedStop, setSelectedStop] =
    useState<TransportStop | null>(null);

  useEffect(() => {
    getStops()
      .then(setStops)
      .catch(() => setError("Could not connect to the API"))
      .finally(() => setLoading(false));
  }, []);

  const filteredStops = stops.filter((stop) => {
    const matchesType =
      filter === "all" || stop.transport_type === filter;

    const matchesSearch = stop.name
      .toLowerCase()
      .includes(search.toLowerCase());

    return matchesType && matchesSearch;
  });

  const statistics = [
    {
      label: "Total stops",
      value: stops.length,
      color: "#94a3b8",
    },
    {
      label: "Metro stops",
      value: stops.filter(
        (stop) => stop.transport_type === "metro"
      ).length,
      color: "#3b82f6",
    },
    {
      label: "Tram stops",
      value: stops.filter(
        (stop) => stop.transport_type === "tram"
      ).length,
      color: "#ef4444",
    },
    {
      label: "Bus stops",
      value: stops.filter(
        (stop) => stop.transport_type === "bus"
      ).length,
      color: "#22c55e",
    },
  ];

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">VT</div>
          <div>
            <h2>ViennaTransitLab</h2>
            <span>Transport intelligence</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <nav className="navigation">
          <button className="nav-item active">
            Network overview
          </button>

          <button className="nav-item" disabled>
            Accessibility
            <small>Soon</small>
          </button>

          <button className="nav-item" disabled>
            Service frequency
            <small>Soon</small>
          </button>

          <button className="nav-item" disabled>
            Live departures
            <small>Soon</small>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="connection-status">
            <span
              className={`status-dot ${
                loading ? "pending" : error ? "offline" : "online"
              }`}
            />
            {loading
              ? "Connecting..."
              : error
                ? "API unavailable"
                : "API connected"}
          </div>
          <span>Development · v0.1.0</span>
        </div>
      </aside>

      <main className="workspace">
        <header className="page-header">
          <div>
            <p className="eyebrow">TRANSPORT ANALYTICS</p>
            <h1>Network overview</h1>
            <p className="subtitle">
              Explore Vienna's public transport infrastructure.
            </p>
          </div>

          <span className="dataset-badge">
            Mock dataset
          </span>
        </header>

        {loading && (
          <div className="notice">Loading transport data...</div>
        )}

        {error && (
          <div className="notice error">{error}</div>
        )}

        {!loading && !error && (
          <>
            <section className="stats-grid">
              {statistics.map((stat) => (
                <article className="stat-card" key={stat.label}>
                  <span>{stat.label}</span>
                  <div className="stat-bottom">
                    <strong>{stat.value}</strong>
                    <div
                      className="stat-indicator"
                      style={{ backgroundColor: stat.color }}
                    />
                  </div>
                </article>
              ))}
            </section>

            <section className="dashboard-grid">
              <article className="panel map-panel">
                <div className="panel-header">
                  <div>
                    <h2>Transport network</h2>
                    <p>Interactive station map</p>
                  </div>
                </div>

                <div className="filters">
                  {filters.map((type) => (
                    <button
                      key={type}
                      className={`filter-button ${
                        filter === type ? "selected" : ""
                      }`}
                      onClick={() => {
                        setFilter(type);
                        setSelectedStop(null);
                      }}
                    >
                      {type === "all"
                        ? "All transport"
                        : type.charAt(0).toUpperCase() +
                          type.slice(1)}
                    </button>
                  ))}
                </div>

                <TransportMap
                  stops={filteredStops}
                  selectedStop={selectedStop}
                />

                <div className="map-legend">
                  <span>
                    <i className="legend-dot metro" /> Metro
                  </span>
                  <span>
                    <i className="legend-dot tram" /> Tram
                  </span>
                  <span>
                    <i className="legend-dot bus" /> Bus
                  </span>
                </div>
              </article>

              <article className="panel stations-panel">
                <div className="panel-header">
                  <div>
                    <h2>Transport stops</h2>
                    <p>
                      {filteredStops.length} of {stops.length} stops
                    </p>
                  </div>
                </div>

                <input
                  className="station-search"
                  type="search"
                  placeholder="Search stations..."
                  aria-label="Search stations"
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setSelectedStop(null);
                  }}
                />

                <div className="station-list">
                  {filteredStops.map((stop) => (
                    <button
                      key={stop.id}
                      className={`station-item ${
                        selectedStop?.id === stop.id
                          ? "station-selected"
                          : ""
                      }`}
                      onClick={() => setSelectedStop(stop)}
                    >
                      <i
                        className={`legend-dot ${stop.transport_type}`}
                      />

                      <div>
                        <strong>{stop.name}</strong>
                        <span>{stop.transport_type}</span>
                      </div>

                      <span className="station-arrow">›</span>
                    </button>
                  ))}

                  {filteredStops.length === 0 && (
                    <p className="empty-state">
                      No matching transport stops.
                    </p>
                  )}
                </div>
              </article>
            </section>

            <footer className="workspace-footer">
              ViennaTransitLab · Development preview ·
              Data currently simulated
            </footer>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
