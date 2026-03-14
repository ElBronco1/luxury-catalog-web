'use client'

import { useState, useEffect, useRef } from 'react'

type Product = {
  b: string  // brand
  n: string  // name
  c: string  // category
  s: string  // subcategory
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

  if (!src || hasError) {
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
          src={src}
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
  const [displayedProducts, setDisplayedProducts] = useState<Product[]>([])
  const [displayCount, setDisplayCount] = useState(50)
  const [selectedBrand, setSelectedBrand] = useState<string>('')
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [selectedSubcategory, setSelectedSubcategory] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'name' | 'price'>('name')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [loadedBrands, setLoadedBrands] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [expandedProduct, setExpandedProduct] = useState<number | null>(null)

  // Load brand index
  useEffect(() => {
    fetch('/brands/index.json')
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

    fetch(`/brands/${brand.slug}.json`)
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

    if (selectedSubcategory) {
      filtered = filtered.filter(p => p.s === selectedSubcategory)
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(p =>
        p.n.toLowerCase().includes(term) ||
        p.b.toLowerCase().includes(term) ||
        p.c.toLowerCase().includes(term) ||
        p.s.toLowerCase().includes(term)
      )
    }

    filtered.sort((a, b) => {
      if (sortBy === 'price') {
        return parseFloat(a.f) - parseFloat(b.f)
      }
      return a.n.localeCompare(b.n)
    })

    setFilteredProducts(filtered)
    setDisplayCount(50) // Reset to 50 when filters change
  }, [products, selectedBrand, selectedCategory, selectedSubcategory, searchTerm, sortBy])

  // Update displayed products when displayCount changes
  useEffect(() => {
    setDisplayedProducts(filteredProducts.slice(0, displayCount))
  }, [filteredProducts, displayCount])

  // Get categories for selected brand (or all if no brand selected)
  const categories = Array.from(new Set(
    products
      .filter(p => !selectedBrand || p.b === selectedBrand)
      .map(p => p.c)
  )).sort()

  // Get subcategories for selected category
  const subcategories = Array.from(new Set(
    products
      .filter(p => !selectedBrand || p.b === selectedBrand)
      .filter(p => !selectedCategory || p.c === selectedCategory)
      .map(p => p.s)
  )).sort()

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
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <input
              type="text"
              placeholder="Buscar productos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-4 py-3 rounded-sm border border-luxury-stone/30 focus:border-luxury-gold focus:outline-none bg-white"
            />
            
            <select
              value={selectedBrand}
              onChange={(e) => {
                setSelectedBrand(e.target.value)
                setSelectedCategory('')
                setSelectedSubcategory('')
              }}
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
              onChange={(e) => {
                setSelectedCategory(e.target.value)
                setSelectedSubcategory('')
              }}
              className="px-4 py-3 rounded-sm border border-luxury-stone/30 focus:border-luxury-gold focus:outline-none bg-white"
              disabled={!selectedBrand}
            >
              <option value="">Todas las categorías</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>

            <select
              value={selectedSubcategory}
              onChange={(e) => setSelectedSubcategory(e.target.value)}
              className="px-4 py-3 rounded-sm border border-luxury-stone/30 focus:border-luxury-gold focus:outline-none bg-white"
              disabled={!selectedCategory}
            >
              <option value="">Todas las subcategorías</option>
              {subcategories.map(sub => (
                <option key={sub} value={sub}>{sub}</option>
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
                  setSelectedSubcategory('')
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
          {displayedProducts.map((product, idx) => {
            const isExpanded = expandedProduct === idx
            
            return (
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
                  <p className="text-xs text-luxury-charcoal/60">{product.s}</p>
                  <p className="font-serif text-lg text-luxury-charcoal font-semibold">
                    {product.f}
                  </p>
                  
                  {/* Expandable Details Button */}
                  <button
                    onClick={() => setExpandedProduct(isExpanded ? null : idx)}
                    className="w-full mt-3 py-2 text-xs font-sans uppercase tracking-wide text-luxury-charcoal/60 hover:text-luxury-gold transition-colors border-t border-luxury-stone/30 pt-3"
                  >
                    {isExpanded ? '− Ocultar detalles' : '+ Ver detalles'}
                  </button>
                  
                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-luxury-stone/30 space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-luxury-charcoal/60 font-sans uppercase tracking-wide">Marca:</span>
                        <span className="text-luxury-charcoal font-sans">{product.b}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-luxury-charcoal/60 font-sans uppercase tracking-wide">Categoría:</span>
                        <span className="text-luxury-charcoal font-sans">{product.c}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-luxury-charcoal/60 font-sans uppercase tracking-wide">Subcategoría:</span>
                        <span className="text-luxury-charcoal font-sans">{product.s}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Load More Button */}
        {displayCount < filteredProducts.length && (
          <div className="text-center mt-12">
            <button
              onClick={() => setDisplayCount(prev => prev + 50)}
              className="px-8 py-4 bg-luxury-gold text-luxury-charcoal font-serif text-lg rounded-sm hover:bg-luxury-charcoal hover:text-luxury-cream transition-colors shadow-md"
            >
              Cargar más productos ({filteredProducts.length - displayCount} restantes)
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
