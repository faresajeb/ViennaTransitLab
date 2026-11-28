
import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";

import type { TransportStop } from "../types/transport";
import "leaflet/dist/leaflet.css";

type Props = {
  stops: TransportStop[];
  selectedStop: TransportStop | null;
};

const transportColors: Record<string, string> = {
  metro: "#3b82f6",
  tram: "#ef4444",
  bus: "#22c55e",
  rail: "#f59e0b",
};

function getStopColor(modes: string[]): string {
  if (modes.length > 1) {
    return "#a855f7";
  }

  return transportColors[modes[0]] ?? "#64748b";
}

function MapController({
  selectedStop,
}: {
  selectedStop: TransportStop | null;
}) {
  const map = useMap();

  useEffect(() => {
    if (selectedStop) {
      map.flyTo(
        [selectedStop.latitude, selectedStop.longitude],
        16,
        { duration: 1.2 }
      );
    }
  }, [selectedStop, map]);

  return null;
}

export default function TransportMap({
  stops,
  selectedStop,
}: Props) {
  return (
    <MapContainer
      center={[48.2082, 16.3738]}
      zoom={13}
      className="transport-map"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <MapController selectedStop={selectedStop} />

      {stops.map((stop) => (
        <CircleMarker
          key={stop.stop_id}
          center={[stop.latitude, stop.longitude]}
          radius={
            selectedStop?.stop_id === stop.stop_id ? 11 : 8
          }
          pathOptions={{
            color: "#ffffff",
            weight: 2,
            fillColor: getStopColor(stop.modes),
            fillOpacity: 0.95,
          }}
        >
          <Popup>
            <strong>{stop.name}</strong>

            <p>Stop ID: {stop.stop_id}</p>

            <p>
              Transport modes:{" "}
              {stop.modes.join(", ") || "Unknown"}
            </p>

            <p>
              Route IDs:{" "}
              {stop.route_ids.join(", ") || "Not available"}
            </p>

            <p>
              {stop.latitude.toFixed(4)},{" "}
              {stop.longitude.toFixed(4)}
            </p>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
