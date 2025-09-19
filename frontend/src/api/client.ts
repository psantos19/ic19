import axios from "axios";

/**
 * Cliente Axios para falar com o backend FastAPI.
 *
 * ⚠️ Importante:
 * - Se estás a testar no browser (npm run start + tecla "w"), usa http://localhost:8000
 * - Se estás a testar no telemóvel via Expo Go, troca para o IP local da tua máquina
 *   (o Expo mostra no terminal, ex.: exp://192.168.68.119:8081 → usa http://192.168.68.119:8000)
 */

// --- Web (browser no PC):
const api = axios.create({ baseURL: "http://localhost:8000" });

// --- Mobile (Expo Go, mesma rede Wi-Fi):
// const api = axios.create({ baseURL: "http://192.168.68.119:8000" });

export default api;
