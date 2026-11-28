
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
};

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
          key={stop.id}
          center={[stop.latitude, stop.longitude]}
          radius={selectedStop?.id === stop.id ? 11 : 8}
          pathOptions={{
            color: "#ffffff",
            weight: 2,
            fillColor:
              transportColors[stop.transport_type] ?? "#64748b",
            fillOpacity: 0.95,
          }}
        >
          <Popup>
            <strong>{stop.name}</strong>
            <p>Transport: {stop.transport_type}</p>
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
