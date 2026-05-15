import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'export',
  basePath: 'CoTEACH/frontend',  // your repo name
  images: { unoptimized: true },
  env: {
    NEXT_PUBLIC_API_URL: 'https://coteach-backend.onrender.com'  // Render URL
  }
}

export default nextConfig