/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Malgun Gothic', 'Apple SD Gothic Neo', 'Inter', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: []
}
