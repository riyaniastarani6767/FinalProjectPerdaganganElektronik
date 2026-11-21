/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        ungu: { DEFAULT: '#6C4CF1', tua: '#5236D6', muda: '#EEEAFE', pucat: '#F4F1FE', garis: '#D9D2FB', terang: '#E7E1FF' },
        pink: { DEFAULT: '#E85D9A', tua: '#A3174F', gelap: '#7A1240', muda: '#FDE8F1' },
        latar: '#F4F2FB',
        teks: { DEFAULT: '#1F1D2B', sedang: '#4A4759', redup: '#6B6880' },
        garis: '#ECEBF2'
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] }
    }
  },
  plugins: []
}
