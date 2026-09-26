/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#d9e5ff",
          500: "#3b6cf6",
          600: "#2b53d4",
          700: "#2342a8",
        },
      },
    },
  },
  plugins: [],
};
