/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ntu: {
          red: '#EF3340',
          blue: '#003D7C',
          'red-light': '#FF4757',
          'red-dark': '#D12938',
          'blue-light': '#0056A8',
          'blue-dark': '#002654'
        }
      }
    },
  },
  plugins: [],
}
