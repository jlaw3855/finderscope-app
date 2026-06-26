interface AddressSearchProps {
  onSearch: (address: string) => void
  loading: boolean
}

export function AddressSearch({ onSearch, loading }: AddressSearchProps) {
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const address = String(formData.get('address') ?? '').trim()
    if (address) {
      onSearch(address)
    }
  }

  return (
    <section className="panel search-panel">
      <h1>Finderscope</h1>
      <p className="subtitle">
        Enter an address to see stargazing conditions for the next week and generate a custom sky map.
      </p>
      <form className="search-form" onSubmit={handleSubmit}>
        <input
          type="text"
          name="address"
          placeholder="e.g. Denver, CO or 123 Main St, Boulder, CO"
          required
          disabled={loading}
          aria-label="Address"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching…' : 'Get Forecast'}
        </button>
      </form>
    </section>
  )
}
