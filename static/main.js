// Datos de puntos de agua (coordenadas aproximadas)
const aquaPoints = [
  {
    name: "Río Suratá",
    type: "Río",
    lat: 7.367,      // Coordenadas surata santander
    lon: -72.984,
    status: "NORMAL",
    description:
      "Curso de agua que nace en el complejo de Santurbán y hace parte de la cuenca que abastece el área metropolitana de Bucaramanga."
  },
  {
    name: "Río Tona",
    type: "Río",
    lat: 7.202,      // Tona, Santander
    lon: -72.967,
    status: "NORMAL",
    description:
      "Río de alta montaña que atraviesa el municipio de Tona y aporta caudal a acueductos rurales y redes de abastecimiento de la región."
  },
  {
    name: "Río Zulia",
    type: "Río",
    lat: 7.933,      // El Zulia, Norte de Santander
    lon: -72.600,
    status: "NORMAL",
    description:
      "Importante afluente que se origina en el complejo Santurbán y abastece municipios del nororiente colombiano, con usos agrícolas y domésticos."
  },
  {
    name: "Laguna / zona lacustre Salazar de las Palmas",
    type: "Laguna",
    lat: 7.782,      // Salazar de las Palmas, Norte de Santander
    lon: -72.857,
    status: "NORMAL",
    description:
      "Zona de lagunas y cuerpos de agua de alta montaña cercanos a Salazar de las Palmas, fundamentales para la recarga hídrica del ecosistema paramuno."
  }
];

function initAquaMap() {
  const mapElement = document.getElementById("map");
  if (!mapElement) return;

  // Centro aproximado entre Santander y Norte de Santander
  const map = L.map("map").setView([7.55, -72.85], 8);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "© OpenStreetMap contributors"
  }).addTo(map);

  aquaPoints.forEach((p) => {
    // Color all normal for now; podrías cambiar según estado
    const color = "#004a6f";

    const marker = L.circleMarker([p.lat, p.lon], {
      radius: 8,
      color: color,
      fillColor: "#38c1b5",
      fillOpacity: 0.9
    }).addTo(map);

    const popupContent = `
      <strong>${p.name}</strong><br>
      Tipo: ${p.type}<br>
      Estado simulado: ${p.status}<br><br>
      <span style="font-size: 0.85rem;">${p.description}</span>
    `;
    marker.bindPopup(popupContent);
  });
}

// Ejecutar cuando cargue la página del mapa
document.addEventListener("DOMContentLoaded", initAquaMap);
