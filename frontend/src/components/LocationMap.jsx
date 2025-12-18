import React, { useMemo } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";

// Fix default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

function LocationMap({ latitude, longitude, location, darkMode }) {
  // Memoize the map component to prevent unnecessary re-renders
  const mapComponent = useMemo(() => {
    // Validate coordinates
    if (!latitude || !longitude || isNaN(latitude) || isNaN(longitude)) {
      return null;
    }

    const position = [latitude, longitude];

    return (
      <MapContainer
        center={position}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={false}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url={
            darkMode
              ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          }
        />
        <Marker position={position}>
          <Popup>
            {location && (
              <>
                <strong>{location}</strong>
                <br />
              </>
            )}
            {latitude.toFixed(4)}, {longitude.toFixed(4)}
          </Popup>
        </Marker>
      </MapContainer>
    );
  }, [latitude, longitude, location, darkMode]);

  return mapComponent;
}

export default LocationMap;
