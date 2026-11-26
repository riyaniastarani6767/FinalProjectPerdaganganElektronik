/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        // Palet plum dan dusty rose (tanpa hijau)
        ungu: { DEFAULT: '#4E3A86', tua: '#3E2D6E', gelap: '#33265C', muda: '#ECE8F3', pucat: '#F6F4F9', garis: '#D8D1E6', terang: '#D9D2EA' },
        pink: { DEFAULT: '#C4547B', tua: '#9E3A60', gelap: '#7A1F45', muda: '#F5E4EA', lembut: '#E7A9C0' },
        latar: '#EEECF2',
        teks: { DEFAULT: '#1E1B24', sedang: '#4A4752', redup: '#6B6873' },
        garis: '#E5E2E8'
      },
      fontFamily: { sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'] }
    }
  },
  plugins: []
}
