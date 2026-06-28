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
    <section className="panel search-panel" data-testid="search-panel">
      <header className="app-header">
        <h1>Finderscope</h1>
        <p className="subtitle">
          Enter an address for a 7-night stargazing forecast and local astronomy summary at
          your location.
        </p>
        <p className="app-capabilities muted">
          Night scores during darkness · 3-month events timeline · Planet visibility · Meteor
          shower peak nights
        </p>
      </header>
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
