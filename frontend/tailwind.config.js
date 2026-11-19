/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sajona: {
          crimson: "#991B1B",
          crimsonHover: "#7F1D1D",
          leaf: "#15803D",
          leafHover: "#166534",
          slate: "#1F2937",
          surface: "#F8FAFC",
        },
      },
    },
  },
  plugins: [],
};
