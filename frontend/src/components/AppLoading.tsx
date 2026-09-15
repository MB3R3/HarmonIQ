function AppLoading() {
  return (
    <div
      className="app-loading"
      role="status"
      aria-label="Loading HarmonIQ"
    >
      <p className="app-loading__brand">HarmonIQ</p>
      <div className="loading-eq" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

export default AppLoading;