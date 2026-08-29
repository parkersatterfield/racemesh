export function LoadingScreen({ error }) {
  return (
    <main className="loading-screen">
      <div>
        <p className="eyebrow">RaceMesh</p>
        <h1>Waiting for race data</h1>
        <p>{error || "Connecting to the timing service..."}</p>
      </div>
    </main>
  );
}
