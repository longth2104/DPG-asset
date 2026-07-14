/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#D22930',
          hover: '#B02028',
        },
        primary: {
          DEFAULT: '#014f6e',
          hover: '#013d56',
        },
        cream: '#F6F1E3',
        ochre: {
          DEFAULT: '#CC9210',
          hover: '#B8830C',
        },
        muted: '#9CF3FF',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
