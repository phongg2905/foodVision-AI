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
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
      },
      colors: {
        canvas: '#EFE6D8',
        blush: '#F7F2EA',
        terracotta: '#E87838',
        coral: '#E87838',
        herb: '#00C48C',
        espresso: '#181512',
        stonewarm: '#6E655C',
      },
    },
  },
  plugins: [],
};
