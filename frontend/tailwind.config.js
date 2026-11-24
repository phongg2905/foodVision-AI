/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '"Plus Jakarta Sans"',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
        serif: ['"David Libre"', '"Playfair Display"', 'Georgia', 'serif'],
      },
      colors: {
        canvas: '#E8D8C6',
        surface: '#FFF8F0',
        blush: '#F4EAE0',
        terracotta: '#EA6D27',
        saffron: '#F59E28',
        persimmon: '#C65112',
        herb: '#00C48C',
        espresso: '#181512',
        stonewarm: '#595047',
      },
    },
  },
  plugins: [],
};
