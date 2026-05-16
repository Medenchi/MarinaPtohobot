/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '"Inter"',
          '"Helvetica Neue"',
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
        serif: ['"Cormorant Garamond"', "Georgia", "serif"],
      },
      colors: {
        ink: "#0A0A0A",
        paper: "#FAFAFA",
        line: "#E5E5E5",
        muted: "#737373",
      },
      letterSpacing: {
        tighter: "-0.02em",
      },
    },
  },
  plugins: [],
};
