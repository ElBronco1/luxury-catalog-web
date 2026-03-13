/** @type {import('next').NextConfig} */
const nextConfig = {
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
