/**
 * THERMOSAFE AI — SIH26162 Runtime Production Configuration
 * 
 * When deploying frontend and backend to separate hosting domains
 * (e.g., Frontend on Vercel/Netlify, Backend on Render/Railway),
 * specify your live backend API URL below:
 * 
 * Example:
 * window.__THERMOSAFE_API_URL__ = "https://thermosafe-backend.onrender.com";
 * 
 * If hosted on the same domain (e.g. unified deployment on Render/Railway)
 * or accessed via local dev servers, leave as empty string "" and the app
 * will automatically resolve the appropriate origin.
 */
window.__THERMOSAFE_API_URL__ = window.__THERMOSAFE_API_URL__ || "";