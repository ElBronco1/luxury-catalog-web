import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const { url } = req.query

  if (!url || typeof url !== 'string') {
    return res.status(400).json({ error: 'Missing url parameter' })
  }

  try {
    const urlObj = new URL(url)
    
    // Build headers based on domain
    const headers: Record<string, string> = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.9',
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache',
    }
    
    // Add referer for specific domains
    if (urlObj.hostname.includes('sephora.com')) {
      headers['Referer'] = 'https://www.sephora.com/'
    } else if (urlObj.hostname.includes('pandora.net')) {
      headers['Referer'] = 'https://us.pandora.net/'
      headers['Origin'] = 'https://us.pandora.net'
    } else if (urlObj.hostname.includes('victoriassecret.com')) {
      headers['Referer'] = 'https://www.victoriassecret.com/'
    } else if (urlObj.hostname.includes('shopify.com')) {
      headers['Referer'] = urlObj.origin
    }
    
    // Fetch the image with proper headers to bypass CDN restrictions
    const imageRes = await fetch(url, { headers })

    if (!imageRes.ok) {
      return res.status(imageRes.status).json({ error: 'Failed to fetch image' })
    }

    const contentType = imageRes.headers.get('content-type')
    const buffer = await imageRes.arrayBuffer()

    // Set cache headers
    res.setHeader('Content-Type', contentType || 'image/jpeg')
    res.setHeader('Cache-Control', 'public, max-age=31536000, immutable')
    
    res.send(Buffer.from(buffer))
  } catch (error) {
    console.error('Image proxy error:', error)
    res.status(500).json({ error: 'Failed to proxy image' })
  }
}
