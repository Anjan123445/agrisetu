// Small representative subset for the dropdown fallback (hackathon scope).
// Coordinates are approximate state-centroid values, used only when the
// Maps picker isn't used, so getAdvisory() always receives {lat, lng}.
export const STATES = [
  {
    state: "Karnataka",
    lat: 15.3173,
    lng: 75.7139,
    districts: ["Belagavi", "Bengaluru Urban", "Mysuru", "Hubballi-Dharwad", "Kalaburagi"],
  },
  {
    state: "Maharashtra",
    lat: 19.7515,
    lng: 75.7139,
    districts: ["Pune", "Nagpur", "Nashik", "Aurangabad", "Kolhapur"],
  },
  {
    state: "Punjab",
    lat: 31.1471,
    lng: 75.3412,
    districts: ["Ludhiana", "Amritsar", "Patiala", "Bathinda", "Jalandhar"],
  },
  {
    state: "Tamil Nadu",
    lat: 11.1271,
    lng: 78.6569,
    districts: ["Coimbatore", "Madurai", "Thanjavur", "Salem", "Erode"],
  },
  {
    state: "Uttar Pradesh",
    lat: 26.8467,
    lng: 80.9462,
    districts: ["Lucknow", "Meerut", "Varanasi", "Kanpur Dehat", "Agra"],
  },
  {
    state: "Andhra Pradesh",
    lat: 15.9129,
    lng: 79.74,
    districts: ["Guntur", "Krishna", "Chittoor", "Kurnool", "Anantapur"],
  },
];
