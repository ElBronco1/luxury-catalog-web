'use client'

import { useState, useEffect, useRef } from 'react'

// Helper to get base path from Next.js config
const getBasePath = () => {
  if (typeof window !== 'undefined') {
    // Extract basePath from the current URL path
    const pathParts = window.location.pathname.split('/')
    // If URL starts with /luxury-catalog-web/, that's our basePath
    if (pathParts[1] === 'luxury-catalog-web') {
      return '/luxury-catalog-web'
    }
  }
  return ''
}

type Product = {
  b: string  // brand
  n: string  // name
  c: string  // category
  f: string  // finalPrice
  i: string  // image
}

type BrandIndex = {
  name: string
  slug: string
  count: number
  images: number
  size_kb: number
}

// Lazy Image Component
function LazyImage({ src, alt, className }: { src: string; alt: string; className: string }) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [isInView, setIsInView] = useState(true) // Changed to true - always load images
  const [hasError, setHasError] = useState(false)
  const imgRef = useRef<HTMLDivElement>(null)

  // Prepend basePath to image URLs
  const basePath = getBasePath()
  const fullImageSrc = src && src.startsWith('/') ? `${basePath}${src}` : src

  if (!fullImageSrc || hasError) {
    return (
      <div ref={imgRef} className="aspect-square bg-gradient-to-br from-luxury-stone to-luxury-cream flex items-center justify-center">
        <div className="text-center p-6">
          <div className="text-3xl text-luxury-gold mb-3">✦</div>
          <div className="text-xs font-sans text-gray-400 uppercase tracking-widest">
            {alt.split(' ').slice(0, 2).join(' ')}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div ref={imgRef} className="aspect-square bg-luxury-stone overflow-hidden relative">
      {!isLoaded && (
        <div className="absolute inset-0 bg-gradient-to-br from-luxury-stone to-luxury-cream animate-pulse" />
      )}
      {isInView && (
        <img
          src={fullImageSrc}
          alt={alt}
          className={`${className} ${isLoaded ? 'opacity-100' : 'opacity-0'} transition-opacity duration-700`}
          onLoad={() => setIsLoaded(true)}
          onError={() => setHasError(true)}
        />
      )}
    </div>
  )
}

export default function Home() {
  const [brandIndex, setBrandIndex] = useState<BrandIndex[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([])
  const [selectedBrand, setSelectedBrand] = useState<string>('')
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'name' | 'price'>('name')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [loadedBrands, setLoadedBrands] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)

  // Load brand index
  useEffect(() => {
    const basePath = getBasePath()
    fetch(`${basePath}/brands/index.json`)
      .then(res => res.json())
      .then(data => {
        setBrandIndex(data)
        setLoading(false)
      })
      .catch(err => console.error('Error loading brand index:', err))
  }, [])

  // Load brand data when selected
  useEffect(() => {
    if (!selectedBrand || loadedBrands.has(selectedBrand)) return

    const brand = brandIndex.find(b => b.name === selectedBrand)
    if (!brand) return

    const basePath = getBasePath()
    fetch(`${basePath}/brands/${brand.slug}.json`)
      .then(res => res.json())
      .then(data => {
        setProducts(prev => [...prev, ...data])
        setLoadedBrands(prev => new Set(Array.from(prev).concat(selectedBrand)))
      })
      .catch(err => console.error(`Error loading ${selectedBrand}:`, err))
  }, [selectedBrand, brandIndex, loadedBrands])

  // Filter and sort
  useEffect(() => {
    let filtered = products

    if (selectedBrand) {
      filtered = filtered.filter(p => p.b === selectedBrand)
    }

    if (selectedCategory) {
      filtered = filtered.filter(p => p.c === selectedCategory)
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(p =>
        p.n.toLowerCase().includes(term) ||
        p.b.toLowerCase().includes(term) ||
        p.c.toLowerCase().includes(term)
      )
    }

    filtered.sort((a, b) => {
      if (sortBy === 'price') {
        return parseFloat(a.f) - parseFloat(b.f)
      }
      return a.n.localeCompare(b.n)
    })

    setFilteredProducts(filtered)
  }, [products, selectedBrand, selectedCategory, searchTerm, sortBy])

  const categories = Array.from(new Set(products.map(p => p.c))).sort()

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl text-luxury-gold mb-4">✦</div>
          <p className="text-luxury-charcoal font-serif text-xl">Cargando catálogo...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-stone-50">
      {/* Header */}
      <div className="bg-luxury-cream border-b border-luxury-stone">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-8">
          <h1 className="font-serif font-light text-4xl md:text-5xl text-luxury-charcoal mb-2">
            Catálogo de Lujo
          </h1>
          <p className="text-luxury-charcoal/60 text-sm md:text-base">
            {brandIndex.reduce((sum, b) => sum + b.count, 0).toLocaleString()} productos de {brandIndex.length} marcas premium
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-luxury-stone/95 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <input
              type="text"
              placeholder="Buscar productos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-4 py-3 rounded-sm border border-luxury-stone/30 focus:border-luxury-gold focus:outline-none bg-white"
            />
            
            <select
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
              className="px-4 py-3 rounded-sm border border-luxury-stone/30 focus:border-luxury-gold focus:outline-none bg-white"
            >
              <option value="">Todas las marcas</option>
              {brandIndex.map(brand => (
                <option key={brand.slug} value={brand.name}>
                  {brand.name} ({brand.count})
                </option>
              ))}
            </select>

            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-3 rounded-sm border border-luxury-stone/30 focus:border-luxury-gold focus:outline-none bg-white"
            >
              <option value="">Todas las categorías</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>

            <div className="flex gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'name' | 'price')}
                className="flex-1 px-4 py-3 rounded-sm border border-luxury-stone/30 focus:border-luxury-gold focus:outline-none bg-white"
              >
                <option value="name">Ordenar: Nombre</option>
                <option value="price">Ordenar: Precio</option>
              </select>
              
              <button
                onClick={() => {
                  setSelectedBrand('')
                  setSelectedCategory('')
                  setSearchTerm('')
                }}
                className="px-4 py-3 bg-luxury-charcoal text-white rounded-sm hover:bg-luxury-gold transition-colors text-sm"
              >
                Limpiar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Products */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-12 py-8">
        {filteredProducts.length === 0 && (
          <div className="text-center py-16">
            <p className="text-luxury-charcoal/60">
              {selectedBrand ? 'Selecciona una marca para ver productos' : 'No se encontraron productos'}
            </p>
          </div>
        )}

        <div className={viewMode === 'grid' 
          ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-6" 
          : "space-y-4"
        }>
          {filteredProducts.map((product, idx) => (
            <div key={idx} className="bg-luxury-cream rounded-sm border border-luxury-stone overflow-hidden hover:shadow-lg transition-shadow">
              <LazyImage
                src={product.i}
                alt={product.n}
                className="w-full h-full object-cover"
              />
              <div className="p-4 space-y-2">
                <p className="text-xs text-luxury-gold uppercase tracking-widest font-sans">
                  {product.b}
                </p>
                <h3 className="font-serif text-sm text-luxury-charcoal line-clamp-2">
                  {product.n}
                </h3>
                <p className="text-xs text-luxury-charcoal/60">{product.c}</p>
                <p className="font-serif text-lg text-luxury-charcoal font-semibold">
                  ${product.f}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
