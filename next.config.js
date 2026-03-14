/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
    domains: [
      'www.sephora.com',
      'cdn.shopify.com',
      'n.nordstrommedia.com',
      'images.puma.com',
    ]
  }
}

module.exports = nextConfig
