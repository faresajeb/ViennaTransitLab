
import { useEffect, useState } from "react";

type Stop = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  transport_type: string;
};

function App() {
  const [stops, setStops] = useState<Stop[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/stops")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch stops");
        }
        return response.json();
      })
      .then(setStops)
      .catch(() => setError("Could not load stops"));
  }, []);

  return (
    <main>
      <h1>ViennaTransitLab</h1>
      <h2>Transport Stops</h2>

      {error && <p>{error}</p>}

      {stops.map((stop) => (
        <p key={stop.id}>
          {stop.name} — {stop.transport_type}
        </p>
      ))}
    </main>
  );
}

export default App;
