
export type TransportStop = {
  stop_id: string;
  station_id: string | null;
  name: string;
  latitude: number;
  longitude: number;
  modes: string[];
  route_ids: string[];
};
