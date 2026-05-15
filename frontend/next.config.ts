import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'export',
  basePath: '/CoTEACH',  // your repo name
  images: { unoptimized: true },
  env: {
    NEXT_PUBLIC_API_URL: 'https://coteach-2q9m.onrender.com/'  // Render URL
  }
}

export default nextConfig